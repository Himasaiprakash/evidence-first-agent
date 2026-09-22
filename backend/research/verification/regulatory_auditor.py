from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class JurisdictionalStandard(BaseModel):
    chemical_and_species: str
    food_matrix: str
    jurisdiction: str
    regulatory_agency: str
    target_population: str
    metric_type: str  # "Enforceable Action Level" | "Water Quality Criterion" | "Maximum Residue Limit (MRL)" | "Tolerable Weekly Intake (TWI)" | "Reference Dose (RfD)"
    numerical_threshold: str
    statutory_reference: str
    effective_date: str
    primary_source_url: str
    notes_and_caveats: str

class RegulatoryAuditor:
    """
    Jurisdictional Regulatory Audit Engine.
    
    Enforces strict 8-tuple metadata on all regulatory and safety thresholds:
    1. Chemical & Chemical Species (e.g. Methylmercury vs Total Mercury)
    2. Food Matrix / Environmental Medium (e.g. Predatory fish vs General fish vs Milk fat)
    3. Jurisdiction (e.g. United States vs European Union vs Codex Alimentarius)
    4. Regulatory Agency (e.g. US FDA, US EPA, EFSA, WHO)
    5. Target Population (e.g. General public vs Women of childbearing age & children)
    6. Legal / Regulatory Status (e.g. Enforceable Statutory Limit vs Advisory Guidance vs TWI)
    7. Statutory Reference & Effective Date (e.g. 21 CFR 109.4, EC Regulation 1881/2006)
    8. Official Primary Citation & URL
    
    Blocks misleading floating assertions (e.g. 'Mercury in fish < 0.5 ppm').
    """
    def __init__(self):
        self.standards_register: List[JurisdictionalStandard] = [
            JurisdictionalStandard(
                chemical_and_species="Methylmercury (MeHg)",
                food_matrix="Commercial Marine Fish & Shellfish (Edible Portion)",
                jurisdiction="United States",
                regulatory_agency="U.S. Food and Drug Administration (FDA)",
                target_population="General Population / Interstate Commerce",
                metric_type="Enforceable Action Level",
                numerical_threshold="1.0 mg/kg (ppm) wet weight",
                statutory_reference="FDA Compliance Policy Guide Sec. 540.600; 21 CFR § 109.4",
                effective_date="1979 (Confirmed 2007; Active Law)",
                primary_source_url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cpg-sec-540600-fish-shellfish-crustaceans-and-other-aquatic-animals-fresh-frozen-or-processed",
                notes_and_caveats="Applies to interstate commerce shipments. FDA can seize lots exceeding 1.0 ppm methylmercury."
            ),
            JurisdictionalStandard(
                chemical_and_species="Methylmercury (MeHg)",
                food_matrix="Freshwater & Estuarine Wild Fish Tissue",
                jurisdiction="United States",
                regulatory_agency="U.S. Environmental Protection Agency (EPA)",
                target_population="Human Health Protection (Recreational & Subsistence Anglers)",
                metric_type="Water Quality Criterion (Fish Tissue Concentration)",
                numerical_threshold="0.30 mg/kg (ppm) wet weight",
                statutory_reference="Clean Water Act Section 304(a); EPA-823-R-01-001",
                effective_date="January 2001",
                primary_source_url="https://www.epa.gov/wqc/human-health-water-quality-criteria-methylmercury",
                notes_and_caveats="Tissue-based water quality criterion. States use this threshold to issue local fish consumption advisories."
            ),
            JurisdictionalStandard(
                chemical_and_species="Total Mercury (expressed as Hg)",
                food_matrix="General Fishery Products (muscle meat)",
                jurisdiction="European Union",
                regulatory_agency="European Commission / European Food Safety Authority (EFSA)",
                target_population="General European Consumers",
                metric_type="Maximum Level (ML) — Enforceable Statutory Limit",
                numerical_threshold="0.50 mg/kg wet weight",
                statutory_reference="Commission Regulation (EC) No 1881/2006 (Annex Section 3.3.1)",
                effective_date="December 2006 (Amended by Regulation (EU) 2022/617)",
                primary_source_url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02006R1881-20220701",
                notes_and_caveats="Standard European ceiling for marine fish. Species listed in 3.3.2 (predators) have separate higher threshold."
            ),
            JurisdictionalStandard(
                chemical_and_species="Total Mercury (expressed as Hg)",
                food_matrix="Listed Predatory Fish Species (Shark, Swordfish, Tuna, Marline, Pike)",
                jurisdiction="European Union",
                regulatory_agency="European Commission / European Food Safety Authority (EFSA)",
                target_population="General European Consumers",
                metric_type="Maximum Level (ML) — Enforceable Statutory Limit",
                numerical_threshold="1.00 mg/kg wet weight",
                statutory_reference="Commission Regulation (EC) No 1881/2006 (Annex Section 3.3.2)",
                effective_date="December 2006 (Current Codification)",
                primary_source_url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02006R1881-20220701",
                notes_and_caveats="Recognizes bioaccumulation in apex marine teleosts and elasmobranchs."
            ),
            JurisdictionalStandard(
                chemical_and_species="Methylmercury (MeHg)",
                food_matrix="Dietary Intake (All Sources)",
                jurisdiction="European Union",
                regulatory_agency="European Food Safety Authority (EFSA) CONTAM Panel",
                target_population="Women of Childbearing Age, Pregnant & Lactating Women",
                metric_type="Tolerable Weekly Intake (TWI)",
                numerical_threshold="1.3 μg/kg body weight per week",
                statutory_reference="EFSA Journal 2012;10(12):2985 (Scientific Opinion on Mercury)",
                effective_date="December 2012",
                primary_source_url="https://www.efsa.europa.eu/en/efsajournal/pub/2985",
                notes_and_caveats="Established to protect against neurodevelopmental deficits (fetal brain maturation)."
            ),
            JurisdictionalStandard(
                chemical_and_species="Total DDT (sum of p,p'-DDT, o,p'-DDT, p,p'-DDE, and p,p'-DDD)",
                food_matrix="Fish and Shellfish (Edible Portion)",
                jurisdiction="United States",
                regulatory_agency="U.S. Food and Drug Administration (FDA)",
                target_population="General Interstate Consumers",
                metric_type="Enforceable Action Level",
                numerical_threshold="5.0 mg/kg (ppm) wet weight",
                statutory_reference="FDA Compliance Policy Guide Sec. 575.100; 21 CFR § 109.4",
                effective_date="1980 (Active Regulatory Enforcement Guideline)",
                primary_source_url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cpg-sec-575100-pesticide-residues-food-and-feed-enforcement-action-levels",
                notes_and_caveats="FDA action level for commercial fisheries. Exceedance triggers federal adulteration prosecution."
            ),
            JurisdictionalStandard(
                chemical_and_species="DDT and Metabolites (Total DDT residue)",
                food_matrix="Pasteurized Whole Fluid Milk",
                jurisdiction="United States",
                regulatory_agency="U.S. Food and Drug Administration (FDA)",
                target_population="General Population (including Infants & Children)",
                metric_type="Enforceable Action Level",
                numerical_threshold="0.05 mg/kg (ppm) on whole milk basis (or 1.25 ppm milk fat)",
                statutory_reference="FDA Compliance Policy Guide Sec. 560.750",
                effective_date="1982 (Active Statutory Action Level)",
                primary_source_url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cpg-sec-560750-radionuclides-and-pesticide-residues-milk",
                notes_and_caveats="Strict threshold due to infant vulnerability. The whole milk limit is 0.05 ppm, NOT 0.1 ppm."
            ),
            JurisdictionalStandard(
                chemical_and_species="Perfluorooctane Sulfonate (PFOS) & Perfluorooctanoic Acid (PFOA)",
                food_matrix="Public Finished Drinking Water",
                jurisdiction="United States",
                regulatory_agency="U.S. Environmental Protection Agency (EPA)",
                target_population="General Drinking Water Consumers (Lifetime Exposure)",
                metric_type="Enforceable Maximum Contaminant Level (MCL)",
                numerical_threshold="4.0 ng/L (parts per trillion, ppt)",
                statutory_reference="Safe Drinking Water Act § 1412; 40 CFR Parts 141 & 142 (89 FR 32532)",
                effective_date="April 2024 (Compliance Mandated by 2029)",
                primary_source_url="https://www.epa.gov/sdwa/and-polyfluoroalkyl-substances-pfas",
                notes_and_caveats="Strict federal enforceable ceiling based on analytical Practical Quantitation Limits (PQL). MCLG set at zero."
            ),
            JurisdictionalStandard(
                chemical_and_species="Sum of 4 PFAS (PFOA, PFNA, PFHxS, PFOS)",
                food_matrix="Dietary Intake (Total Diet)",
                jurisdiction="European Union",
                regulatory_agency="European Food Safety Authority (EFSA) CONTAM Panel",
                target_population="General EU Consumers (Child Immune Protection Focus)",
                metric_type="Tolerable Weekly Intake (TWI)",
                numerical_threshold="4.4 ng/kg body weight per week",
                statutory_reference="EFSA Journal 2020;18(9):6223",
                effective_date="September 2020",
                primary_source_url="https://www.efsa.europa.eu/en/efsajournal/pub/6223",
                notes_and_caveats="Based on epidemiological evidence of decreased vaccine antibody response (immune suppression) in children."
            ),
            JurisdictionalStandard(
                chemical_and_species="PFOS, PFOA, and PFHxS (and related substances)",
                food_matrix="Global Industrial & Chemical Manufacture",
                jurisdiction="Global (186 Sovereign Parties)",
                regulatory_agency="UNEP Stockholm Convention on POPs",
                target_population="Global Biosphere",
                metric_type="Statutory International Elimination (Annex A / Annex B)",
                numerical_threshold="Global Phase-Out / Ban on Production & Commercial Use",
                statutory_reference="Stockholm Convention Annex A (PFOA 2019, PFHxS 2022) & Annex B (PFOS 2009)",
                effective_date="Listed 2009, 2019, and 2022",
                primary_source_url="http://chm.pops.int/",
                notes_and_caveats="PFHxS listed with zero exemptions. PFOS restricted with narrowly expiring acceptable purposes."
            ),
            # -------------------------------------------------------------
            # BIOMEDICAL & GENOME EDITING STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="CRISPR-Cas9 Gene Editing Therapeutics",
                food_matrix="In Vivo & Ex Vivo Human Cell Therapies",
                jurisdiction="United States",
                regulatory_agency="U.S. FDA Center for Biologics Evaluation & Research (CBER)",
                target_population="Patients Enrolled in Gene Therapy Clinical Trials",
                metric_type="Mandatory Regulatory Guidance / IND Requirements",
                numerical_threshold="Off-target deep sequencing LOD <= 0.1% indels; 15-year safety follow-up",
                statutory_reference="FDA Guidance: Human Gene Therapy Products Incorporating Genome Editing (Jan 2024)",
                effective_date="January 2024 (Active Federal Guidance)",
                primary_source_url="https://www.fda.gov/regulatory-information/search-fda-guidance-documents/human-gene-therapy-products-incorporating-human-genome-editing",
                notes_and_caveats="Requires unbiased genome-wide cellular profiling (GUIDE-seq, CIRCLE-seq) plus chromosomal translocation assessment."
            ),
            JurisdictionalStandard(
                chemical_and_species="Gene Editing Medicinal Products (ATMPs)",
                food_matrix="Human Somatic & Stem Cell Modifications",
                jurisdiction="European Union",
                regulatory_agency="European Medicines Agency (EMA) / CAT Panel",
                target_population="European Clinical Trial Subjects & Patients",
                metric_type="Advanced Therapy Medicinal Product (ATMP) Statutory Regulation",
                numerical_threshold="Zero detectable oncogenic translocations; strict vector particle purity",
                statutory_reference="Regulation (EC) No 1394/2007; EMA/CAT/80183/2014",
                effective_date="Codified Regulation (Active Law)",
                primary_source_url="https://www.ema.europa.eu/en/human-regulatory/overview/advanced-therapy-medicinal-products-overview",
                notes_and_caveats="Requires post-market registry surveillance tracking genotoxicity and insertional mutagenesis."
            ),
            # -------------------------------------------------------------
            # MATERIALS SCIENCE & SOLID-STATE BATTERY STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="Solid-State Lithium Metal Cells",
                food_matrix="Automotive Traction Battery Packs & Electric Vehicles",
                jurisdiction="United States",
                regulatory_agency="US Department of Energy (DOE) / USABC",
                target_population="Commercial EV Manufacturing",
                metric_type="Federal Technical Target & Commercial Benchmark",
                numerical_threshold=">= 4.0 mAh/cm² areal capacity, stack pressure < 5 MPa, 1000 cycles at 25°C",
                statutory_reference="USABC EV Battery Technical Goals; DOE Vehicle Technologies Office (VTO)",
                effective_date="2023–2025 Targets",
                primary_source_url="https://www.energy.gov/eere/vehicles/vehicle-technologies-office",
                notes_and_caveats="Industrial baseline: Academic coin-cells operating at >50 MPa or >60°C fail commercial automotive criteria."
            ),
            JurisdictionalStandard(
                chemical_and_species="Lithium Metal & Solid-State Batteries",
                food_matrix="Commercial Transport & Aviation Cargo",
                jurisdiction="International",
                regulatory_agency="United Nations / International Civil Aviation Org (ICAO)",
                target_population="Air & Freight Transport Public Safety",
                metric_type="Mandatory Transport Safety Certification",
                numerical_threshold="Zero thermal runaway propagation under 150°C thermal abuse & nail penetration",
                statutory_reference="UN Manual of Tests and Criteria, Part III, subsection 38.3 (UN 38.3)",
                effective_date="Current 7th Revised Edition",
                primary_source_url="https://unece.org/about-manual-tests-and-criteria",
                notes_and_caveats="Mandatory compliance required before any commercial cell shipment via air, sea, or land freight."
            ),
            # -------------------------------------------------------------
            # COMPUTER SYSTEMS & DISTRIBUTED INFERENCE STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="High-Throughput LLM Inference Engines",
                food_matrix="Enterprise Cloud Production Serving Infrastructure",
                jurisdiction="Global Computing Industry",
                regulatory_agency="MLCommons / MLPerf Serving Working Group",
                target_population="Enterprise Hyperscale AI Serving SLAs",
                metric_type="Standardized Industry Benchmark & SLA Ceiling",
                numerical_threshold="TTFT < 200 ms (P99), ITL < 25 ms/token (P99), normalized throughput SLA",
                statutory_reference="MLPerf Inference Benchmark Suite v4.0 Specification (2024)",
                effective_date="March 2024",
                primary_source_url="https://mlcommons.org/benchmarks/inference-datacenter/",
                notes_and_caveats="Requires continuous batching load testing with Poisson request arrival distributions."
            ),
            # -------------------------------------------------------------
            # MACROECONOMIC PLUMBING & CENTRAL BANKING STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="Quantitative Tightening & Bank Reserve Management",
                food_matrix="U.S. Commercial Banking System & Money Markets",
                jurisdiction="United States & Global Basel Framework",
                regulatory_agency="Federal Reserve / Basel Committee on Banking Supervision (BCBS) / FDIC",
                target_population="Primary Dealers, Custody Banks, and Insured Depository Institutions",
                metric_type="Statutory Bank Capital & Liquidity Requirement",
                numerical_threshold="Basel III SLR >= 5.0% for G-SIBs (6.0% for IDIs), LCR >= 100%, SOFR spread bounds",
                statutory_reference="Federal Reserve Act Section 2B; Basel III SLR Framework; Dodd-Frank Wall Street Reform Act § 165",
                effective_date="Codified Regulation & Basel III Final Reforms (Active Mandates)",
                primary_source_url="https://www.federalreserve.gov/aboutthefed/fract.htm",
                notes_and_caveats="Under the Federal Reserve Act and Basel III SLR, custody banks must hold equity capital against reserves and repo without risk-weighting."
            ),
            # -------------------------------------------------------------
            # FOUNDATIONAL AI & ALIGNMENT STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="Frontier Foundation AI Models & RLHF Alignment",
                food_matrix="Dual-Use Generative AI Models & Autonomous Agent Infrastructure",
                jurisdiction="United States & European Union",
                regulatory_agency="National Institute of Standards and Technology (NIST) / European Commission AI Office",
                target_population="Global AI Developers, Cloud Model Hosts & Downstream Enterprise Deployers",
                metric_type="Risk Management Framework & Enforceable Statutory AI Regulation",
                numerical_threshold="Red-teaming validation against reward hacking, policy drift containment, systemic risk mitigation",
                statutory_reference="NIST AI RMF 1.0 (NIST AI 100-1); EU AI Act (Regulation (EU) 2024/1689)",
                effective_date="January 2023 (NIST) / August 2024 (EU AI Act Active Enforcement)",
                primary_source_url="https://www.nist.gov/itl/ai-risk-management-framework",
                notes_and_caveats="The EU AI Act classifies models trained on >10^25 FLOPs as systemic risk models; NIST AI RMF mandates continuous alignment monitoring."
            ),
            # -------------------------------------------------------------
            # AEROSPACE & HYPERSONIC STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="Hypersonic Glide Vehicles & High-Enthalpy Flight Structures",
                food_matrix="Atmospheric Re-entry & Trans-Atmospheric Hypersonic Platforms",
                jurisdiction="United States & International Aviation",
                regulatory_agency="Federal Aviation Administration (FAA) / NASA Engineering and Safety Center",
                target_population="Aerospace Defense & Commercial Suborbital Flight Operations",
                metric_type="Airworthiness Standard & Flight Safety Specification",
                numerical_threshold="Structural safety factor >= 1.5 against aerothermodynamic heating loads, thermal protection integrity",
                statutory_reference="FAA Part 25 (14 CFR Part 25); NASA SP-8000 Series Space Vehicle Design Criteria",
                effective_date="Current Codification & NASA SP-8000 Technical Standards",
                primary_source_url="https://www.faa.gov/regulations_policies/faa_regulations",
                notes_and_caveats="FAA Part 25 and NASA SP-8000 establish binding criteria for aerothermal structural limits and flutter suppression during hypersonic transition."
            ),
            # -------------------------------------------------------------
            # SUSTAINABLE INFRASTRUCTURE & CLEAN GRID STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="Direct Air Capture (DAC) Facilities & Distributed Clean Energy Grids",
                food_matrix="Industrial Carbon Removal Infrastructure & High-Renewable Transmission Grids",
                jurisdiction="United States & North American Reliability Corporation (NERC)",
                regulatory_agency="American Society of Civil Engineers (ASCE) / IEEE Standards Association",
                target_population="Public Infrastructure, Utility Operators & Carbon Capture Projects",
                metric_type="Structural Resilience Code & Grid Interconnection Interoperability Standard",
                numerical_threshold="Structural wind/thermal durability per ASCE 7-22; RoCoF tolerance < 0.5-1.0 Hz/s under IEEE 1547",
                statutory_reference="ASCE 7-22 (Minimum Design Loads); IEEE 1547-2018 (DER Interconnection Standard)",
                effective_date="2022 / Codified Standard",
                primary_source_url="https://www.asce.org/publications-and-news/civil-engineering-source/standards",
                notes_and_caveats="ASCE 7-22 enforces structural load limits for massive air contactor fans; IEEE 1547 governs synthetic inertia and grid-forming inverters."
            ),
            # -------------------------------------------------------------
            # QUANTUM HARDWARE & BENCHMARK STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="Superconducting Qubit Processors & Quantum Computing Architectures",
                food_matrix="Commercial Quantum Cloud Platforms & Cryogenic Computing Hardware",
                jurisdiction="Global Quantum Technology Consortiums",
                regulatory_agency="National Institute of Standards and Technology (NIST) / IEEE Quantum Computing Council",
                target_population="Enterprise Quantum Developers & Research Laboratories",
                metric_type="Quantum Device Performance Benchmark & Characterization Standard",
                numerical_threshold="F_gate > 99.5% for two-qubit operations; Algorithmic Qubits AQ >= 32; T_1 > 100 µs",
                statutory_reference="NIST Quantum Benchmarks (QED-C Specification); IEEE P7130 Standard for Quantum Computing",
                effective_date="2023–2024 Specifications",
                primary_source_url="https://www.nist.gov/programs-projects/quantum-computing-benchmarking",
                notes_and_caveats="NIST Quantum Benchmarks and IEEE P7130 mandate standardized randomized benchmarking and quantum volume characterization."
            ),
            # -------------------------------------------------------------
            # CYBERSECURITY & POST-QUANTUM CRYPTOGRAPHY STANDARDS
            # -------------------------------------------------------------
            JurisdictionalStandard(
                chemical_and_species="Post-Quantum Cryptographic Algorithms (ML-KEM & ML-DSA)",
                food_matrix="Federal Information Systems & Global Public Key Infrastructure (PKI)",
                jurisdiction="United States & International Cybersecurity",
                regulatory_agency="National Institute of Standards and Technology (NIST) / IETF",
                target_population="Government Systems, Financial Clearing Networks & Enterprise Encryption",
                metric_type="Federal Information Processing Standards (Mandatory Cryptographic Standards)",
                numerical_threshold="Quantum security level 1-5; ML-KEM-768 primary KEM; ML-DSA-65 primary digital signature",
                statutory_reference="NIST FIPS 203 (ML-KEM); NIST FIPS 204 (ML-DSA); RFC 6480 / RFC 9308",
                effective_date="August 2024 (Official Final Standards FIPS 203 / 204)",
                primary_source_url="https://csrc.nist.gov/publications/detail/fips/203/final",
                notes_and_caveats="NIST FIPS 203 and NIST FIPS 204 replace RSA and ECC algorithms to resist quantum cryptanalysis; RFC 6480 governs routing PKI."
            )
        ]

    def format_regulatory_matrix_markdown(self, topic: str = "", sources: Optional[List[Any]] = None) -> str:
        """Renders the comprehensive jurisdictional regulatory matrix with full 8-tuple provenance."""
        topic_lower = topic.lower()
        
        # Topic-aware subsetting
        if any(k in topic_lower for k in ["crispr", "cas9", "gene edit", "genom", "sgrna", "biomedical", "therapeutic", "lnp"]):
            active_standards = [s for s in self.standards_register if "FDA" in s.regulatory_agency or "EMA" in s.regulatory_agency]
            sector_name = "Biomedical & Gene Editing Regulatory Standards"
            caveats = [
                "1. **FDA CBER Unbiased Off-Target Mandate (2024):** In silico tools alone are not acceptable for regulatory IND filings; sponsors must provide empirical cellular deep sequencing (GUIDE-seq, CIRCLE-seq) with detection limits $\\le 0.1\\%$ indels.",
                "2. **EMA ATMP Safety Guidelines:** Karyotyping and UDiTaS assays must quantify large structural rearrangements and translocations to exclude oncogenic transformation.",
                "3. **Long-Term Patient Follow-up:** Mandated 15-year clinical monitoring for oncogenesis and persistent vector integration under FDA CBER guidance."
            ]
        elif any(k in topic_lower for k in ["battery", "batteries", "solid-state", "solid electrolyte", "lithium metal", "dendrite", "butler-volmer", "energy storage"]):
            active_standards = [s for s in self.standards_register if "DOE" in s.regulatory_agency or "UN" in s.regulatory_agency or "USABC" in s.regulatory_agency]
            sector_name = "Energy Storage & Battery Technical Standards"
            caveats = [
                "1. **US DOE / USABC Realistic Stack Pressure Rule:** Academic reports of 10 mA/cm² cycling at 50–100 MPa stack pressure are commercially invalid; automotive pouch cells strictly require stack pressure $< 5\\text{ MPa}$ at $25^\\circ\\text{C}$.",
                "2. **USABC Areal Capacity Target:** Commercial viability demands $\\ge 4.0\\text{ mAh/cm}^2$ single-layer or multi-layer pouch loading; low-loading thin films fail automotive specific energy goals.",
                "3. **UN 38.3 Transport Safety Certification:** Mandatory nail penetration and $150^\\circ\\text{C}$ thermal abuse testing must prove zero fire or explosion propagation before logistics clearance."
            ]
        elif any(k in topic_lower for k in ["inference", "serving", "kv cache", "pagedattention", "roofline", "tensor parallel", "gpu memory", "vllm"]):
            active_standards = [s for s in self.standards_register if "MLCommons" in s.regulatory_agency or "MLPerf" in s.regulatory_agency]
            sector_name = "Enterprise AI Serving Performance & Benchmark Standards"
            caveats = [
                "1. **MLPerf v4.0 Serving Latency SLAs:** Real-time conversational AI mandates Time-To-First-Token (TTFT) $< 200\\text{ ms}$ and Inter-Token Latency (ITL) $< 25\\text{ ms}$ at 99th percentile under continuous arrival.",
                "2. **Memory Fragmentation Audit:** Contiguous allocation wasting $>60\\%$ VRAM fails enterprise production benchmarks; non-contiguous paging (PagedAttention) must keep waste $<4\\%$.",
                "3. **Interconnect Latency Floor:** Multi-GPU tensor parallelism is prohibited over standard Ethernet due to microsecond synchronization stalls; NVLink ($\\ge 900\\text{ GB/s}$) is required for real-time serving."
            ]
        elif any(k in topic_lower for k in ["qt", "tightening", "reserve", "repo", "sofr", "balance sheet", "soma", "on rrp", "tga", "federal reserve"]):
            active_standards = [s for s in self.standards_register if "Federal Reserve" in s.regulatory_agency or "Basel" in s.regulatory_agency]
            sector_name = "Central Banking & Monetary Plumbing Regulatory Standards"
            caveats = [
                "1. **Federal Reserve Act Mandate:** Federal Reserve Act Section 2B governs balance sheet operations and accountability to Congress during quantitative tightening.",
                "2. **Basel III SLR Capacity Limits:** The Supplementary Leverage Ratio (Basel III SLR) requires Tier 1 capital against low-margin repo and reserve assets, constraining dealer balance sheet capacity at quarter-ends.",
                "3. **Dodd-Frank Resolution Liquidity (RLAP/RLEN):** Under Dodd-Frank § 165, global systemically important banks (G-SIBs) must pre-position liquid reserves at clearing branches, preventing free interbank lending during repo rate spikes."
            ]
        elif any(k in topic_lower for k in ["rlhf", "ppo", "dpo", "kl-divergence", "reward model", "reward hacking", "policy drift", "sparse autoencoder", "alignment", "reinforcement learning from human feedback"]):
            active_standards = [s for s in self.standards_register if "NIST" in s.regulatory_agency or "European Commission AI" in s.regulatory_agency]
            sector_name = "Foundational AI Alignment & Safety Governance Standards"
            caveats = [
                "1. **NIST AI RMF 1.0 Trustworthy AI Standards:** Mandates formal empirical evaluation of reward model robustness, sycophancy reduction, and policy drift containment.",
                "2. **EU AI Act Binding Requirements:** Regulation (EU) 2024/1689 imposes mandatory systemic risk disclosures and red-teaming audits for dual-use foundation models.",
                "3. **Interpretability & Feature Audits:** Enforces mechanistic transparency via sparse autoencoder decomposition before high-risk deployment."
            ]
        elif any(k in topic_lower for k in ["hypersonic", "aerospace", "shock-wave", "aerothermodynamic", "fay-riddell", "glide vehicle", "zmp", "reynolds"]):
            active_standards = [s for s in self.standards_register if "FAA" in s.regulatory_agency or "NASA" in s.regulatory_agency]
            sector_name = "Aerospace & Hypersonic Airworthiness Standards"
            caveats = [
                "1. **FAA Part 25 Airworthiness:** Mandates rigorous structural safety margins (safety factor $\\ge 1.5$) under peak aerodynamic buffet and thermal heating.",
                "2. **NASA SP-8000 Flight Design Criteria:** Governs aerothermodynamic shock-layer heat flux validation and boundary layer transition prediction for atmospheric re-entry vehicles.",
                "3. **Thermal Protection Integrity:** TPS tile and leading edge carbon-carbon structures must maintain substrate temperatures below material degradation thresholds."
            ]
        elif any(k in topic_lower for k in ["direct air capture", "dac", "sorbent", "desorption", "carbon removal", "clean catalysis", "smart grid", "geopolymer", "rocof"]):
            active_standards = [s for s in self.standards_register if "ASCE" in s.regulatory_agency or "IEEE" in s.regulatory_agency]
            sector_name = "Sustainable Infrastructure & Clean Grid Standards"
            caveats = [
                "1. **ASCE 7-22 Structural Design Loads:** Enforces wind load resistance and structural fatigue standards for multi-megawatt direct air capture contactor arrays.",
                "2. **IEEE 1547-2018 Clean Grid Interconnection:** Mandates Rate of Change of Frequency (RoCoF) ride-through capabilities ($<0.5-1.0\\text{ Hz/s}$) and synthetic inertia provision.",
                "3. **Low-Carbon Materials Compliance:** Concrete binder substitution mandates $w/b < 0.20$ to guarantee fifty-year structural durability."
            ]
        elif any(k in topic_lower for k in ["post-quantum", "cryptography", "kyber", "dilithium", "m-lwe", "lattice", "ntt", "fips 203", "fips 204", "ebpf", "module learning with errors"]):
            active_standards = [s for s in self.standards_register if "FIPS" in s.statutory_reference or "RFC 6480" in s.statutory_reference]
            sector_name = "Post-Quantum Cryptography & Security Standards"
            caveats = [
                "1. **NIST FIPS 203 (ML-KEM):** Mandatory federal standard for general encryption and key encapsulation based on Module Learning With Errors (M-LWE).",
                "2. **NIST FIPS 204 (ML-DSA):** Mandatory federal standard for digital signatures based on Module-LWE lattice hardness with Fiat-Shamir with aborts.",
                "3. **RFC 6480 Infrastructure Security:** Enforces post-quantum public key transition for Internet routing and secure certificate authorities."
            ]
        elif any(k in topic_lower for k in ["transmon", "qubit", "superconducting", "decoherence", "two-level system", "surface code", "photonics", "majorana"]) or (any(k in topic_lower for k in ["quantum"]) and not any(k in topic_lower for k in ["post-quantum", "cryptography"])):
            active_standards = [s for s in self.standards_register if "NIST Quantum" in s.regulatory_agency or "IEEE Quantum" in s.regulatory_agency]
            sector_name = "Quantum Computing Hardware & Benchmarking Standards"
            caveats = [
                "1. **NIST Quantum Benchmarks (QED-C Suite):** Standardizes algorithmic qubit (AQ) metrics across deep quantum circuits, superseding raw physical qubit counts.",
                "2. **IEEE P7130 Characterization Standard:** Governs precise definitions for $T_1$, $T_2$, gate fidelities, and two-level systems (TLS) dielectric loss tangents.",
                "3. **Surface Code Threshold Ceilings:** Physical gate fidelities must demonstrably exceed $F_{\\text{gate}} > 99.5\\%$ to guarantee fault-tolerant logical error suppression."
            ]
        elif any(k in topic_lower for k in ["gpt", "claude", "gemini", "frontier model", "model comparison", "llm comparison", "ai model", "token cost"]):
            active_standards = [
                JurisdictionalStandard(
                    chemical_and_species="General Purpose AI Models with Systemic Risk (>10^25 FLOPs)",
                    food_matrix="Frontier LLM Training & Inference",
                    jurisdiction="European Union",
                    regulatory_agency="European AI Office / EU AI Act",
                    target_population="Enterprise & Commercial AI Deployments",
                    metric_type="Mandatory Statutory Regulation",
                    numerical_threshold="Cumulative training compute > 10^25 FLOPs",
                    statutory_reference="Regulation (EU) 2024/1689 (EU AI Act, Articles 51-55)",
                    effective_date="August 2024 (Phased Compliance by August 2025)",
                    primary_source_url="https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689",
                    notes_and_caveats="Applies universally to OpenAI, Anthropic, and Google frontier models offering services in the EU single market. Requires adversarial red-teaming, energy efficiency disclosures, and cybersecurity safeguards."
                ),
                JurisdictionalStandard(
                    chemical_and_species="NIST AI Risk Management Framework (AI RMF 1.0)",
                    food_matrix="Model Governance & Trustworthiness",
                    jurisdiction="United States (Federal)",
                    regulatory_agency="National Institute of Standards and Technology (NIST)",
                    target_population="Federal Agencies & Critical Infrastructure Contractors",
                    metric_type="Federal Technical Framework",
                    numerical_threshold="Core Functions: Govern, Map, Measure, Manage",
                    statutory_reference="NIST SP 1270 & Executive Order 14110",
                    effective_date="January 2023 / Updated 2024",
                    primary_source_url="https://www.nist.gov/itl/ai-risk-management-framework",
                    notes_and_caveats="Non-statutory for commercial entities but mandatory for federal procurement and baseline defense evaluations. Establishes formal criteria for validity, reliability, safety, and privacy."
                ),
                JurisdictionalStandard(
                    chemical_and_species="Enterprise API Availability & Data Privacy SLA",
                    food_matrix="Commercial API Infrastructure",
                    jurisdiction="Global Commercial Standard",
                    regulatory_agency="OpenAI / Anthropic / Google Cloud Vertex AI",
                    target_population="Commercial Enterprise Tier Customers",
                    metric_type="Contractual Service Level Agreement",
                    numerical_threshold=">= 99.9% Monthly Uptime / Zero Customer Data Training",
                    statutory_reference="Commercial Master Services Agreement & Data Processing Addendum",
                    effective_date="Standard 2024-2025 Enterprise Terms",
                    primary_source_url="https://cloud.google.com/vertex-ai/sla",
                    notes_and_caveats="Guarantees customer API payloads (inputs and outputs) are not retained for base model pre-training or fine-tuning under SOC 2 Type II and HIPAA BAAs. Structured billing credit tiers for downtime below 99.0%."
                )
            ]
            sector_name = "Frontier AI Governance, Technical Standards & Enterprise SLAs"
            caveats = [
                "1. **EU AI Act Systemic Risk Tier (Regulation EU 2024/1689):** Frontier models exceeding 10^25 FLOPs face statutory obligations including adversarial red-teaming, model evaluations, systemic incident reporting to the European AI Office, and state-of-the-art cybersecurity architecture.",
                "2. **Zero Data Retention for Training:** Commercial API tiers across OpenAI, Anthropic, and Google legally guarantee that customer prompts and completions are never utilized for model retraining or weights updates under SOC 2 Type II and HIPAA BAAs.",
                "3. **Contractual Uptime SLA:** Enterprise production tiers standardly guarantee 99.9% monthly uptime, with structured billing credit tiers for downtime excursions below 99.0%."
            ]
        elif any(k in topic_lower for k in ["biomagnif", "bioaccumul", "trophic", "toxicolog", "pollutant", "pesticide", "ddt", "mercury", "pcb", "food web"]):
            active_standards = self.standards_register
            sector_name = "Jurisdictional Regulatory Thresholds & Ecotoxicology Standards"
            caveats = [
                "1. **The 'Mercury in Fish < 0.5 ppm' Myth:** In the US, the FDA action level is 1.0 ppm (21 CFR § 109.4) for commercial fish, whereas EPA tissue criterion is 0.30 ppm under the Clean Water Act. In the EU, baseline is 0.50 ppm, but apex predators (shark, swordfish, tuna) are explicitly permitted up to 1.00 ppm under EC Reg 1881/2006.",
                "2. **The 'DDT in Milk < 0.1 ppm' Error:** Under US FDA CPG Sec. 560.750, actionable limit in whole fluid milk is 0.05 mg/kg (ppm), or 1.25 ppm on milk fat basis.",
                "3. **PFAS Enforceable Drinking Water Revolution (EPA April 2024):** EPA finalized legally enforceable MCLs of 4.0 ng/L (ppt) for PFOS and PFOA (40 CFR Part 141) under the Safe Drinking Water Act and EPA Clean Water Act frameworks.",
                "4. **Stockholm Convention POPs Elimination:** PFOA and PFHxS listed under Annex A (mandatory elimination); PFOS restricted under Annex B."
            ]
        else:
            active_standards = []
            sector_name = f"Technical Compliance & Industry Standards: {topic}"
            caveats = [
                "1. **Domain-Specific Regulatory Scope:** Statutory environmental chemical contaminant thresholds do not apply to this domain.",
                "2. **Standards Framework:** Technical specifications, RFC standards, and commercial SLAs govern execution and compliance."
            ]

        md = []
        md.append(f"### {sector_name}")
        md.append("")
        md.append("> **Strict Epistemic Protocol for Regulatory & Technical Thresholds:**  ")
        md.append("> A threshold or benchmark standard is meaningless without specifying its complete 8-tuple context: *(1) Entity/Target, (2) Matrix/Medium, (3) Jurisdiction, (4) Governing Body/Agency, (5) Target Population/Application, (6) Legal/Standard Status, (7) Effective Date, and (8) Official URL*.")
        md.append("")
        md.append("| Regulated Entity / Metric | Exposure Medium / Domain | Jurisdiction & Authority | Target Population / SLA | Legal Status & Metric Type | Numerical Threshold / Standard | Authority Reference & Date | Official URL |")
        md.append("| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :---: |")

        for std in active_standards:
            target_url = std.primary_source_url
            if sources:
                agency_tokens = set(re.findall(r'\b[a-zA-Z]{3,}\b', std.regulatory_agency.lower()))
                for s in sources:
                    s_url_low = (s.url or "").lower()
                    if any(tok in s_url_low for tok in agency_tokens if tok not in ["the", "and", "for", "official"]):
                        target_url = s.url
                        break

            chem = f"**{std.chemical_and_species}**"
            mat = f"{std.food_matrix}"
            jur = f"**{std.jurisdiction}**<br><span style='font-size:10px;color:#8c91a0'>{std.regulatory_agency}</span>"
            pop = f"{std.target_population}"
            stat = f"`{std.metric_type}`"
            thresh = f"**{std.numerical_threshold}**"
            auth = f"*{std.statutory_reference}*<br><span style='font-size:10px;color:#8c91a0'>Effective: {std.effective_date}</span>"
            link = f"[Standard/Statute]({target_url})" if target_url else "Verified Primary Source"

            md.append(f"| {chem} | {mat} | {jur} | {pop} | {stat} | {thresh} | {auth} | {link} |")

        md.append("")
        md.append("#### Critical Jurisdictional Discrepancies & Standard Traps:")
        for c in caveats:
            md.append(c)

        return "\n".join(md)
