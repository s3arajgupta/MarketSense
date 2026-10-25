# Appendix B: System Functionalities Mapped to Modular Courses (MR, RS, CGS)

This document provides a line-item mapping of **MarketSense AI** system capabilities against the core concepts, techniques, and skills taught across the three modular courses of the NUS-ISS Graduate Certificate in Intelligent Reasoning Systems (GC1):
1. **MR:** Machine Reasoning
2. **RS:** Reasoning Systems
3. **CGS:** Cognitive Systems

Cross-referenced with the official syllabus summary in [`documentations/GC1 Prompt 1.pdf`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/documentations/GC1%20Prompt%201.pdf) and the assessment review in [`documentations/compliance.md`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/documentations/compliance.md).

---

## 1. Master Course Mapping Matrix

| Course | Curriculum Concept / Technique | MarketSense Subsystem / Feature | Concrete File & Implementation Reference |
| :---: | :--- | :--- | :--- |
| **MR** | **Constraint Satisfaction Problems (CSP)** | Price floor bounds, cash principal guarantee, drawdown limits, circuit breaker freeze. | [`engine/pricing.py:L40-L75`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/pricing.py), [`app.py:L749-L757`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py) |
| **MR** | **Rule-Based Inference: Forward Chaining** | Event-driven shock propagation from macro driver to downstream asset classes. | [`engine/pricing.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/pricing.py), [`intelligence/knowledge_graph.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/knowledge_graph.py) |
| **MR** | **Business Rules & Process Logic** | Tax holding rules (STCG 25% vs LTCG 10%), brokerage fees, leverage penalty triggers. | [`engine/friction.py:L20-L65`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/friction.py), [`engine/pricing.py:L50-L60`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/pricing.py) |
| **MR** | **Symbolic Graph Search & Traversal** | Directed multigraph traversal, resistance-weighted shortest path calculation. | [`intelligence/knowledge_graph.py:L87-L145`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/knowledge_graph.py) |
| **MR** | **Four Reasoning Methodologies (Abduction & Deduction)** | Deductive pricing guardrails; abductive diagnosis of portfolio drawdown root causes. | [`intelligence/prompts.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/prompts.py), [`intelligence/mentor.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/mentor.py) |
| **RS** | **Hybrid / Neuro-Symbolic Architecture** | Complete decoupling of deterministic pricing computation from natural language reasoning. | [`documentations/architecture.jpg`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/documentations/architecture.jpg), [`app.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py) |
| **RS** | **Multi-Level Explainability (XAI)** | Model-level (formulaic), Data-level (historical twin citations), Process-level (graph paths). | [`app.py:L600-L660`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py), [`intelligence/knowledge_graph.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/knowledge_graph.py) |
| **RS** | **Counterfactual Reasoning ("What-If")** | Re-evaluation of portfolio outcome against 4 institutional reference strategies under identical shock. | [`engine/simulator.py:L84-L160`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/simulator.py), [`app.py:L663-L720`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py) |
| **RS** | **Benchmarking & Normative Comparison** | Parallel simulation against Dalio All-Weather, 60/40, and 100% Equity + CPI hurdle. | [`engine/benchmarks.py:L20-L90`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/benchmarks.py) |
| **CGS** | **Tripartite Deliberative/Reactive Cognitive Architecture** | Fast reactive simulation loop (<10ms) paired with slow deliberative LLM/RAG loop. | [`app.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py), [`intelligence/mentor.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/mentor.py) |
| **CGS** | **Causal Knowledge Graph & Interactive Physics** | 36-node, 48-edge NetworkX graph visualized via interactive force-directed Pyvis canvas. | [`data/knowledge/causal_graph.json`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/data/knowledge/causal_graph.json), [`app.py:L650-L660`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py) |
| **CGS** | **Retrieval-Augmented Generation (RAG v2)** | ChromaDB vector store (52 chunks, `all-MiniLM-L6-v2`) pairing shocks with twin historical crises. | [`intelligence/rag_engine.py:L25-L110`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/rag_engine.py), [`data/knowledge/`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/data/knowledge/) |
| **CGS** | **Natural Language User Interface (Chatbot / AI Mentor)** | Socratic multi-turn mentorship, real-time token streaming, career retrospectives. | [`intelligence/mentor.py:L84-L216`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/mentor.py), [`app.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py) |
| **CGS** | **Dual Runtime & Edge Execution** | Cloud Google Gemini 2.5 Flash + local 100% offline air-gapped Ollama daemon. | [`intelligence/gemini_provider.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/gemini_provider.py), [`intelligence/ollama_provider.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/ollama_provider.py) |

---

## 2. Detailed Course Breakdown

### 2.1 Machine Reasoning (MR)

#### A. Constraint Satisfaction Problems (CSP) & Boundary Verification
- **Theory:** As defined in `GC1 Prompt 1.pdf` (Section 1.3), a CSP models a domain using variables, domains, and hard constraints to eliminate illegal states.
- **MarketSense Integration:**
  - **Capital & Price Bounds:** Asset prices are strictly constrained by $P_{t+1} \ge \$0.01$ and single-quarter drops are capped at $-85\%$.
  - **Risk-Free Cash Invariant:** `CASH_MMF` principal is mathematically guaranteed non-declining, preserving purchasing power baseline mechanics.
  - **Circuit Breaker Constraint:** When `event_phase == "SHOCKED"`, an execution constraint freezes selling actions in `app.py`, emulating liquidity freezes.

#### B. Rule-Based Inference & Forward Chaining
- **Theory:** Forward Chaining evaluates working memory facts against rule antecedents to fire consequents.
- **MarketSense Integration:**
  - Working Memory holds the current market state and active crisis card.
  - The Pricing Engine acts as a forward-chaining evaluator: if `debt_ratio > 0.40`, fire `DebtPenalty = 0.35 * (debt_ratio - 0.40)`, amplifying drawdowns.
  - Friction rules evaluate `quarters_held < 4 \implies \text{STCG Rate} = 25\%$; $\text{else} \implies \text{LTCG Rate} = 10\%$.

#### C. Abductive Reasoning (Diagnostic Root Cause Analysis)
- **Theory:** Given an observed effect $B$ and knowledge that $A \to B$, infer $A$ as the most probable explanation (`GC1 Prompt 1.pdf`, Section 2.1).
- **MarketSense Integration:**
  - When the trainee's portfolio experiences a sharp drawdown in Information Technology, the system performs abductive diagnosis: observing the $-14\%$ sector drop, traversing the causal graph back to the primary macro trigger (Central Bank Rate Hike $\to$ Equity Discount Rate expansion), and presenting this diagnostic trail in the debrief.

---

### 2.2 Reasoning Systems (RS)

#### A. Neuro-Symbolic Hybrid Architecture
- **Theory:** Shifts from isolated models to system-level orchestration (`GC1 Prompt 1.pdf`, Module 1). Combines symbolic rules with generative neural models.
- **MarketSense Integration:**
  - The symbolic layer (pricing engine, friction engine, NetworkX graph) guarantees numerical correctness and regulatory auditability.
  - The neural layer (Gemini / Ollama) provides natural language synthesis, contextual empathy, and pedagogical Socratic questioning.

#### B. Multi-Level Explainability Framework (XAI)
- **Theory:** Explainability architected at three distinct operational levels (`GC1 Prompt 1.pdf`, Section 1.3):
  1. **Model-Level:** Transparent, closed-form parametric equations for asset pricing.
  2. **Data-Level:** Direct lineage tracing linking active shocks to verified historical crisis twins (e.g., 2022 Rate Shock $\leftrightarrow$ 1980 Volcker Shock).
  3. **Process-Level:** Step-by-step causal graph traversal logging the exact sequence of edges evaluated ($A \to B \to C$).

#### C. Counterfactual Reasoning ("What-If" Analysis)
- **Theory:** Evaluates alternative candidate actions against historical ground truth.
- **MarketSense Integration:**
  - In `engine/simulator.py`, the `compute_counterfactual()` function computes exact mathematical outcomes had the user allocated capital according to Ray Dalio All-Weather, Pure Cash, Gold Defense, or Tech Aggressive strategies during the identical macroeconomic crisis.

---

### 2.3 Cognitive Systems (CGS)

#### A. Tripartite Deliberative/Reactive Cognitive Architecture
- **Theory:** Complete cognitive system operating across two processing pathways overseen by metacognition (`GC1 Prompt 1.pdf`, Page 32):
  1. **Fast Reactive Loop:** Sub-millisecond execution for deterministic price shifts, dividend compounding, and trade friction.
  2. **Slow Deliberative Loop:** Multi-step reasoning pipeline combining vector retrieval (RAG) and knowledge graph traversal.
  3. **Metacognition / Supervision:** Fallback controllers that monitor Ollama availability, fallback to Cloud Gemini if unreachable, and clamp model hallucination.

#### B. Macroeconomic Causal Knowledge Graph
- **Theory:** Explicit representation of domain entities (nodes) and typed semantic relations (edges) structured as triples (`GC1 Prompt 1.pdf`, Section 3).
- **MarketSense Integration:**
  - 36 nodes across 4 tiers: Macro Drivers, Transmission Channels, Economic Sectors, Asset Classes.
  - 48 directed weighted edges with resistance scores and sign polarities ($+1$ or $-1$).
  - Rendered in-browser using a force-directed physics engine (`Pyvis` / `Vis.js`) with glowing active paths.

#### C. Retrieval-Augmented Generation (RAG v2)
- **Theory:** Grounds LLM generation in verified domain knowledge chunks (`GC1 Prompt 1.pdf`, Module 5 & Section 5).
- **MarketSense Integration:**
  - 52 vectorized chunks in ChromaDB with `all-MiniLM-L6-v2` dense embeddings.
  - Curated wisdom from Graham, Dalio, Marks, Lynch, Bogle, Taleb, plus 22 empirical crisis twin precedents with quantitative comparative metrics.

#### D. Socratic AI Mentor & Natural Language Interface
- **Theory:** Human mode of communication and tool orchestration (`GC1 Prompt 1.pdf`, Section 6 & 7).
- **MarketSense Integration:**
  - Multi-turn conversational interface for post-event debriefs, pre-trade previews, and 30-year career retrospectives.
  - Enforces strict Socratic pedagogy: never reveals future prices or orders trades; instead questions assumptions using cited investment principles.
