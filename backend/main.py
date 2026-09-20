import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes.research import router as research_router
from backend.api.routes.learn import router as learn_router
from backend.api.routes.build import router as build_router
from backend.api.routes.chat import router as chat_router
from backend.api.routes.graph import router as graph_router

app = FastAPI(
    title="Evidence-First Autonomous Knowledge Platform",
    description="Executive-grade deterministic, verifiable, evidence-grounded research, learning & building agent",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(research_router)
app.include_router(learn_router)
app.include_router(build_router)
app.include_router(chat_router)
app.include_router(graph_router)

# Mount frontend static assets
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_dashboard():
    index_file = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {
        "status": "online",
        "system": "Evidence-First Autonomous Knowledge Platform",
        "version": "1.0.0"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "Evidence-First Autonomous Knowledge Platform",
        "version": "1.0.0",
        "endpoints": {
            "research": "/api/research/workspaces",
            "learn": "/api/learn/curriculum/{workspace_id}",
            "build": "/api/build/project/{workspace_id}",
            "chat": "/api/chat/query",
            "graph": "/api/graph/{workspace_id}"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8010, reload=True)
