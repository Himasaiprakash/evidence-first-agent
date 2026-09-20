import os
import re
import time
import json
import threading
from collections import deque
from typing import List, Dict, Any, Optional, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from groq import Groq
    HAS_GROQ_SDK = True
except ImportError:
    HAS_GROQ_SDK = False


class GroqKeyEntry:
    """Individual API key descriptor tracking cooldowns and usage statistics."""
    def __init__(self, key: str, client: Any):
        self.key = key.strip()
        self.masked_key = f"{self.key[:7]}...{self.key[-4:]}" if len(self.key) > 12 else "***"
        self.client = client
        self.cooldown_until: float = 0.0
        self.usage_count: int = 0
        self.rate_limit_hits: int = 0

    @property
    def is_cooling_down(self) -> bool:
        return time.time() < self.cooldown_until

    @property
    def remaining_cooldown(self) -> float:
        return max(0.0, self.cooldown_until - time.time())


class GroqClient:
    """
    High-Throughput Multi-Key Rotating Client for Groq LPU Inference API:
    - Queue-based Round-Robin Key Pool: Used keys are moved to the back of the queue to rest.
    - Automatic 429 Cooldown & Instant Failover: If a key hits a rate limit, it is placed on
      a 15-second cooldown and the request immediately retries with the next available key.
    - Multi-Key Ingestion: Supports GROQ_API_KEYS (comma/newline separated), GROQ_API_KEY,
      and indexed GROQ_API_KEY_1, GROQ_API_KEY_2, etc.
    - Fallback model chain: openai/gpt-oss-20b -> openai/gpt-oss-120b -> qwen/qwen3.8-27b
    """
    def __init__(
        self,
        api_key: Optional[Union[str, List[str]]] = None,
        api_keys: Optional[List[str]] = None,
        model: Optional[str] = None
    ):
        self.model = model or os.getenv("GROQ_MODEL", "groq/compound")
        self.fallback_chain = ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]
        self._lock = threading.Lock()
        self._blocked_models: set = set()
        self.key_queue: deque[GroqKeyEntry] = deque()
        self.key_pool: List[GroqKeyEntry] = []

        # 1. Discover all provided keys
        raw_keys = self._discover_keys(api_key, api_keys)

        # 2. Initialize clients and populate the queue
        if HAS_GROQ_SDK:
            for k in raw_keys:
                try:
                    c = Groq(api_key=k, timeout=14.0, max_retries=0)
                    entry = GroqKeyEntry(key=k, client=c)
                    self.key_queue.append(entry)
                    self.key_pool.append(entry)
                except Exception as e:
                    print(f"  [GROQ KEY INIT ERROR] Failed to initialize key: {e}")

        if len(self.key_pool) > 1:
            print(f"  [GROQ MULTI-KEY POOL] Initialized {len(self.key_pool)} API keys with round-robin queue rotation.")

    def _discover_keys(
        self,
        api_key: Optional[Union[str, List[str]]] = None,
        api_keys: Optional[List[str]] = None
    ) -> List[str]:
        """Discovers and deduplicates all Groq API keys from args and environment variables."""
        discovered: List[str] = []

        # Direct argument keys
        if api_keys:
            discovered.extend(api_keys)
        if api_key:
            if isinstance(api_key, list):
                discovered.extend(api_key)
            elif isinstance(api_key, str):
                discovered.extend(re.split(r'[,;\s]+', api_key))

        # Environment GROQ_API_KEYS (comma, semicolon, or newline separated)
        env_multi = os.getenv("GROQ_API_KEYS")
        if env_multi:
            discovered.extend(re.split(r'[,;\s]+', env_multi))

        # Standard GROQ_API_KEY
        env_single = os.getenv("GROQ_API_KEY")
        if env_single:
            discovered.extend(re.split(r'[,;\s]+', env_single))

        # Indexed environment variables GROQ_API_KEY_1, GROQ_API_KEY_2, etc.
        for i in range(1, 21):
            indexed_key = os.getenv(f"GROQ_API_KEY_{i}")
            if indexed_key:
                discovered.append(indexed_key)

        # Clean and deduplicate while preserving order
        unique_keys = []
        seen = set()
        for k in discovered:
            cleaned = k.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique_keys.append(cleaned)

        return unique_keys

    def add_api_key(self, new_key: str):
        """Dynamically add an API key to the active rotation queue at runtime."""
        clean_k = new_key.strip()
        if not clean_k or not HAS_GROQ_SDK:
            return
        with self._lock:
            if any(e.key == clean_k for e in self.key_pool):
                return
            try:
                c = Groq(api_key=clean_k, timeout=14.0, max_retries=0)
                entry = GroqKeyEntry(key=clean_k, client=c)
                self.key_queue.append(entry)
                self.key_pool.append(entry)
                print(f"  [GROQ KEY POOL] Added key {entry.masked_key}. New pool size: {len(self.key_pool)}")
            except Exception as e:
                print(f"  [GROQ KEY ADD ERROR] {e}")

    def is_available(self) -> bool:
        return bool(HAS_GROQ_SDK and len(self.key_pool) > 0)

    @property
    def api_key(self) -> Optional[str]:
        """Backward compatibility: returns the active front key string."""
        with self._lock:
            return self.key_queue[0].key if self.key_queue else None

    def _acquire_and_rotate_key(self) -> Optional[GroqKeyEntry]:
        """
        Pops the next ready key from the front of the queue,
        and moves it to the back so it can rest while other keys are used.
        """
        with self._lock:
            if not self.key_queue:
                return None

            # Find the first key that is not in cooldown
            now = time.time()
            selected_entry: Optional[GroqKeyEntry] = None

            # Iterate across current entries to find an available one
            for entry in list(self.key_queue):
                if entry.cooldown_until <= now:
                    selected_entry = entry
                    break

            # If all keys are cooling down, select the one that recovers earliest
            if not selected_entry:
                selected_entry = min(self.key_queue, key=lambda e: e.cooldown_until)

            # Move the selected key to the back of the queue (resting position)
            self.key_queue.remove(selected_entry)
            self.key_queue.append(selected_entry)

            return selected_entry

    def get_pool_status(self) -> List[Dict[str, Any]]:
        """Inspection helper returning the health and status of all keys in the pool."""
        with self._lock:
            return [
                {
                    "masked_key": e.masked_key,
                    "usage_count": e.usage_count,
                    "rate_limit_hits": e.rate_limit_hits,
                    "is_cooling_down": e.is_cooling_down,
                    "remaining_cooldown_sec": round(e.remaining_cooldown, 1)
                }
                for e in self.key_pool
            ]

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        temperature: float = 0.2,
        max_tokens: int = 3500
    ) -> Any:
        if not self.is_available():
            raise RuntimeError("No valid GROQ_API_KEY configured or Groq SDK is unavailable.")

        with self._lock:
            active_blocked = set(self._blocked_models)
        candidate_models = [m for m in [self.model] + [x for x in self.fallback_chain if x != self.model] if m not in active_blocked]
        last_exception = None

        for target_model in candidate_models:
            # For each model, attempt across available keys in the queue
            keys_to_attempt = max(1, len(self.key_pool))
            model_blocked = False

            for attempt_idx in range(keys_to_attempt):
                entry = self._acquire_and_rotate_key()
                if not entry:
                    break

                # If the key is currently cooling down and we have others, let it rest
                if entry.is_cooling_down and keys_to_attempt > 1:
                    # Give it a chance to rest if other keys might be ready
                    time.sleep(0.05)

                kwargs: Dict[str, Any] = {
                    "model": target_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = tool_choice

                try:
                    res = entry.client.chat.completions.create(**kwargs)
                    entry.usage_count += 1
                    if len(self.key_pool) > 1:
                        print(f"  [GROQ KEY ROTATION] Completed request with {entry.masked_key}. Key moved to queue tail to rest (Pool size: {len(self.key_pool)}).")
                    return res

                except Exception as e:
                    err_str = str(e).lower()
                    last_exception = e

                    if "blocked at the organization level" in err_str or "does not exist or you do not have access" in err_str:
                        print(f"  [GROQ NOTICE] Model '{target_model}' is blocked/unavailable. Checking next candidate in fallback chain...")
                        with self._lock:
                            self._blocked_models.add(target_model)
                        model_blocked = True
                        break  # Move to next model in fallback chain

                    if "rate limit" in err_str or "429" in err_str or "rate_limit_exceeded" in err_str:
                        entry.rate_limit_hits += 1
                        entry.cooldown_until = time.time() + 15.0  # 15s cooldown
                        print(f"  [GROQ KEY 429] Key {entry.masked_key} hit rate limit. Cooldown 15s. Rotating to next key in queue (Attempt {attempt_idx+1}/{keys_to_attempt})...")
                        continue  # Immediate failover to the next key in the queue!

                    print(f"  [GROQ API ERROR] Key {entry.masked_key} error: {type(e).__name__}: {e}")
                    raise e

            if model_blocked:
                continue

        if last_exception:
            raise last_exception
