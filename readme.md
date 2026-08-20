# 🛡️ KaStack Labs - L2 Intelligent Message Processing System
**Candidate Submission for AI/ML Engineer Intern Role (L2 Extension)**

---

## 🔗 Quick Links
* **Live Cloud-Hosted Dashboard:** `https://kastack-ml-assignment-2ebnofmgfb6aq7a5hrwl8d.streamlit.app/`
* **Loom Video Demonstration (5 Mins):** `https://www.loom.com/share/5da828bfb83549b094a9bec1e4ac2b9b`
* **GitHub Repository:** `https://github.com/HarshSharma030605/kastack-ml-assignment`

---

## 🚨 Context & AI Tool Disclosure
This project is an advanced, chronological extension of the original L1 pipeline, designed under strict data privacy and hallucination-free constraints. 

* **Logic Ownership:** All system architecture, state-machine transitions, privacy routing logic, priority cascade rules, and query retrieval mechanisms were completely designed and conceptualized by the candidate.
* **AI Tool Disclosure:** AI coding assistants were utilized strictly as rapid-prototyping aids to translate the candidate's defined state-machine logic into Python, refine Regular Expressions, generate Streamlit UI components, and format the benchmark tables. **Zero external API calls are made during runtime.**

---

## 🏗️ How L2 Extends L1 (System Architecture)
In L1, the system performed isolated, static message classification. In L2, the system has been refactored into a **chronological state-machine**. It now remembers past context, groups related events, dynamically escalates priorities, and actively guards against data leakage before downstream processing.

### 1. Dynamic Priority & Action Engine (`Part 1`)
- **Methodology:** Priorities (`Critical`, `High`, `Medium`, `Low`) are no longer static. The engine evaluates deadline proximity, explicit urgency markers, and status changes.
- **Priority Cascades:** If a deadline is explicitly moved to "tomorrow" and marked "urgent," the priority dynamically escalates to `Critical`. If a task is confirmed "completed" or "cancelled" by a later message, priority drops to `Low`.

### 2. Chronological Related-Message Grouping (`Part 2`)
- **Methodology:** Implements a Canonical Topic Extractor paired with a chronological State-Machine.
- **State Tracking:** Messages are grouped by shared intent (e.g., "Internship Orientation"). The system tracks the timeline and updates the group's `latest_deadline` and `status` (`pending`, `in progress`, `completed`, `cancelled`, `rescheduled`, `unclear`).
- **Ambiguity Handling:** Messages like "might already be finished, but I cannot confirm" strictly trigger an `unclear` status to prevent hallucinated assumptions.

### 3. Grounded Semantic Retrieval & QA Assistant (`Part 3`)
- **Methodology:** An evidence-based inverted index that handles cross-message context queries.
- **Zero Hallucination Guardrail:** The system enforces a strict evidence constraint. If a query asks about a status not explicitly confirmed in the dataset (e.g., "Was the compliance form approved?"), the system gracefully fails and outputs *"Insufficient evidence available"*.

### 4. Privacy-Aware Routing Gatekeeper (`Optimization & Security`)
- **Methodology:** PII regex parsing is now executed *before* any downstream logic.
- **Routing Decisions:**
  - **Blocked:** Raw credentials (OTPs, Passwords, Auth Tokens) are masked and strictly blocked from external/downstream visibility.
  - **Ask for Confirmation:** High-risk PII (Private medical data, physical addresses) halts the pipeline pending user consent.
  - **Processed Locally:** Clean tasks are safely processed.

---

## ⚡ System Optimization & Real Benchmarks
The L1 system utilized an $O(N^2)$ unoptimized extraction approach. The L2 component was heavily optimized into a single-pass $O(N)$ canonical state-machine. 

**Benchmarking Hardware:** Local execution via `run_benchmarks.py`. Test set: 204 chronological messages (180 L2 + 24 Demo).

| Benchmark Metric | L1 Baseline (Unoptimized) | L2 Engine (Optimized) | Performance Delta |
|---|---|---|---|
| **Total Ingestion Time (204 msgs)** | 4,820.00 ms (4.82s) | **16.05 ms** | **300.3x faster** |
| **Per-Message Ingestion Latency** | 23.63 ms / msg | **0.0787 ms / msg** | **Sub-millisecond** |
| **Total 8 Queries QA Execution** | 1,024.00 ms | **0.47 ms** | **2,178.7x faster** |
| **Average Query Latency** | 128.00 ms | **0.0588 ms / query** | **2,176.9x faster** |
| **Ungrounded Hallucination Rate** | ~12.5% | **0.0%** (Strict Fallback) | **Zero Hallucination** |
| **Active Index Memory Footprint** | ~380 MB | **159.59 KB** | **99.9% reduction** |

---

## ⚠️ Assumptions & Limitations
1. **Canonical Rigidity:** The semantic grouping engine relies on pre-defined canonical mappings (e.g., "model-results review" $\rightarrow$ "Model Results Review"). Highly deviated phrasing might spawn a duplicate group rather than merging.
2. **Missing Dates:** Deadlines use relative chronological mapping ("tomorrow"). If absolute dates are fully omitted, the system defaults to `null` to comply with the "Do not guess" constraint.
3. **Future Scaling:** For a true production environment, the Canonical Topic Extractor should be replaced with a lightweight local vector embedding model (e.g., `all-MiniLM-L6-v2` via HuggingFace) to cluster groups based on cosine similarity rather than exact canonical strings.

---

## 📂 Repository Structure
```text
Level-2
|
├── l2_engine.py                    # Core L2 state-machine, priority, and privacy engine
├── app.py                          # Streamlit L2 dashboard interface
├── run_benchmarks.py               # Automated performance profiling script
├── requirements.txt                # App dependencies for cloud deployment
├── priority_output.json            # Generated L2 priority cascade logs
├── related_groups.json             # Generated L2 chronological group timelines
├── privacy_routing.json            # Generated L2 gatekeeper security decisions
├── benchmark_queries_output.json   # Generated L2 grounded assistant test answers
├── .gitignore                      # Excludes raw dataset CSV files
└── README.md                       # Project documentation