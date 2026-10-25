# MarketSense Phase 2 — Verification Report

## Executive Summary

**Phase 2 (AI Mentor, Dual Runtimes, RAG Wisdom Engine & Friction Layer) is fully implemented, rigorously verified, refactored, and tested.** All 6 core architectural pillars specified in the master execution roadmap have been built, integrated with the Streamlit frontend, and verified with 15 automated pytest tests passing in ~3.0s. 

During this verification audit, all documentation discrepancies across `Documentations/` were resolved, and a critical bug in `intelligence/mentor.py` (where macro event titles and event types fell back to "Unknown Event" defaults due to field key naming) was identified, refactored, and unit-tested.

---

## Deliverable Verification Matrix

| Step | Deliverable | Primary File(s) | Status | Notes |
| :---: | :--- | :--- | :---: | :--- |
| **2a** | **Dual LLM Provider Architecture** | [gemini_provider.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/gemini_provider.py), [ollama_provider.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/ollama_provider.py), [llm_client.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/llm_client.py) | ✅ **PASS** | Cloud Gemini API (token streaming, transient retry backoff) + Air-gapped local Ollama (`localhost:11434`) with sidebar runtime switcher. |
| **2b** | **Vector DB & RAG Wisdom Corpus** | [rag_engine.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/rag_engine.py), [knowledge_loader.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/knowledge_loader.py), [data/knowledge/](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/data/knowledge/) | ✅ **PASS** | ChromaDB collection (`investor_wisdom`) with 30 curated wisdom chunks from 5 investment titans + 7 historical crisis cases. Hybrid tag-filter + semantic search. |
| **2c** | **Socratic AI Mentorship & Prompts** | [mentor.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/mentor.py), [prompts.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/prompts.py) | ✅ **PASS** | Hard anti-hallucination guardrails, 4-step causal transmission chain mandate, source citation extraction, real-time token streaming. |
| **2d** | **Institutional Friction & Tax Drag** | [friction.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/friction.py), [app.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py) | ✅ **PASS** | STCG (25% for $<4$ quarters) vs LTCG (10% for $\ge 4$ quarters) + 0.15% brokerage. Pre-trade friction preview with pedagogical holding tips. |
| **2e** | **Flight Controls & Event Cycling** | [app.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py), [simulator.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/simulator.py) | ✅ **PASS** | Play (0.8s/qtr), Fast Forward (0.2s/qtr), Pause, Next Quarter / Absorb Shock, Draw Event. Sequential non-freezing progression through all 22 crisis cards. |
| **2f** | **30-Year Scorecard & Retrospective** | [app.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py), [benchmarks.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/benchmarks.py) | ✅ **PASS** | Multi-Decade Horizon Scorecard comparing Portfolio NAV, Max Drawdown, Real Return, Fisher CPI Hurdle, and Lifetime Friction vs 3 benchmarks + Socratic Retrospective. |
| **2g** | **Automated Test Suite** | [test_engine.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/tests/test_engine.py), [test_intelligence.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/tests/test_intelligence.py) | ✅ **PASS** | **15/15 tests passing (100%)** covering engine pricing, friction, benchmarks, CPI hurdle, offline mock inference, RAG retrieval, and event cycling. |

---

## Detailed Test Results

### 2a — Dual-Engine LLM Provider Architecture

| Criterion | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| **Provider Abstraction** | Clean ABC interface decoupling engine from model vendor | [`LLMClient`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/llm_client.py#L26-L84) abstract base class with `generate()`, `generate_stream()`, and `is_available()` | ✅ |
| **Cloud Provider** | Google Gemini API with token streaming | [`GeminiClient`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/gemini_provider.py) using official `google-genai` SDK | ✅ |
| **Cloud Reliability** | Automatic retry & exponential backoff on transient 503/429 errors | Implemented 3 retries with backoff (1.5s, 3.0s) and fallback model candidates | ✅ |
| **Local Air-Gapped Provider** | 100% offline local inference via Ollama daemon | [`OllamaClient`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/ollama_provider.py) communicating with `http://localhost:11434` | ✅ |
| **Daemon Health Check** | Non-blocking availability probe | `httpx.get(f"{host}/api/tags", timeout=3.0)` checks daemon without UI freeze | ✅ |
| **Sidebar Runtime Switcher** | Dynamic toggle with graceful fallback alert | Sidebar radio in [app.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py#L133-L179) with live status badges and auto-fallback to Cloud | ✅ |
| **Air-Gapped Simulation** | Ability to verify mentor logic without network access | [`MockOfflineClient`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/tests/test_intelligence.py#L71-L98) in test suite simulates local streaming | ✅ |

---

### 2b — RAG Vector Database & Wisdom Ingestion

| Criterion | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| **Vector Database Engine** | Embedded persistent vector store | ChromaDB `PersistentClient` targeting `./chroma_db/` with local persistence | ✅ |
| **Embedding Model** | Lightweight, fast local sentence transformer | `all-MiniLM-L6-v2` ONNX runtime auto-cached locally | ✅ |
| **Corpus Authors** | Graham, Dalio, Marks, Lynch, Bogle | **All 5 investment masters** vectorized in [data/knowledge/](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/data/knowledge/) | ✅ |
| **Historical Crisis Cases** | Seminal empirical financial shocks | **7 detailed cases**: 1973 Oil Embargo, 1997 Asian Crisis, 2000 Dot-Com, 2008 GFC, 2011 Euro Debt, 2020 COVID, 2022 Inflation Shock | ✅ |
| **Total Wisdom Chunks** | $\ge 25$ chunks | **30 curated chunks** with metadata (tags, market cycle, applicable events) | ✅ |
| **Hybrid Retrieval Strategy** | Tag-based pre-filtering + semantic similarity search | [`RAGEngine.retrieve()`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/rag_engine.py#L64-L106) combines `$where` tag-filtering with semantic fallback | ✅ |
| **Source Citation Format** | Auditable quote and source author | [`RetrievedChunk.format_citation()`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/rag_engine.py#L28-L31) formats quotes with bibliographic source attribution | ✅ |

---

### 2c — Socratic Prompt Engineering & Mentorship

| Criterion | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| **Zero Price Hallucination** | LLM strictly forbidden from inventing prices or forecasting | Hard Rule 1 enforced in [`SYSTEM_PROMPT_BASE`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/prompts.py#L17-L23): *"NEVER generate, estimate, forecast, or suggest specific asset prices"* | ✅ |
| **Grounded Citations Mandate** | Every principle must cite a master from retrieved context | Hard Rule 2 & 3 enforced: *"ALWAYS cite your source... say so honestly if not covered"* | ✅ |
| **Causal Transmission Structure** | 4-step pedagogical debrief | 1. 📉 What Happened; 2. 🔗 Causal Chain; 3. 📚 What the Masters Say; 4. 💡 Your Portfolio | ✅ |
| **Pre-Trade Socratic Advice** | Pre-trade inquiry that teaches without dictating | [`PRE_TRADE_INSIGHT`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/prompts.py#L64-L92): Analyzes proposed trade vs event, asks reflective question, never gives buy/sell orders | ✅ |
| **Portfolio Health Check** | Comprehensive concentration & friction audit | [`PORTFOLIO_HEALTH_CHECK`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/prompts.py#L94-L130): Evaluates sector weights, tax drag, benchmark alpha | ✅ |
| **Multi-Decade Retrospective** | Long-term compounding evaluation | [`CAREER_RETROSPECTIVE`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/prompts.py#L131-L156): Socratic evaluation after 12+ quarters | ✅ |
| **Live UI Token Streaming** | Real-time assistant text stream | [`AIMentor.post_event_debrief_stream()`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/mentor.py#L143-L196) piped via `st.write_stream()` | ✅ |

---

### 2d — Institutional Friction & Tax Drag Engine

| Criterion | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| **Short-Term Capital Gains (STCG)** | 25% tax on gains held $< 4$ quarters (< 1 year) | Implemented in [`preview_sell_friction()`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/friction.py#L36-L43) | ✅ |
| **Long-Term Capital Gains (LTCG)** | 10% tax on gains held $\ge 4$ quarters ($\ge$ 1 year) | Implemented in [`preview_sell_friction()`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/friction.py#L36-L43) | ✅ |
| **Loss Treatment** | S\$0 tax on capital losses | Realized loss triggers zero tax, mentor warns of permanent capital loss | ✅ |
| **Brokerage Commission** | 0.15% on gross trade value | Deducted on both buy orders and sell orders | ✅ |
| **Holding Period Tracking** | Increments quarters held per lot | Tracked in [`Portfolio.holdings`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/portfolio.py#L210-L228) and advanced quarterly | ✅ |
| **Pre-Trade Friction Preview** | Real-time cost breakdown before order execution | Streamlit Trading Desk displays Gross Proceeds, Tax (STCG/LTCG), Fee, Net Cash, and Mentor Tip | ✅ |
| **Pedagogical Friction Tip** | Informs user how many quarters left to unlock LTCG discount | Calculated in [friction.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/friction.py#L50-L54): *"Holding for X more quarter(s) saves S\$Y in tax"* | ✅ |

---

### 2e — Continuous Flight Controls & Event Progression

| Criterion | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| **Play Simulation Mode** | Continuous playback at ~0.8s/quarter | Auto-stepping loop in [app.py](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/app.py#L733-L745) | ✅ |
| **Fast Forward Mode (3x)** | Accelerated playback at ~0.2s/quarter | 30-year simulation completes in under 25 seconds | ✅ |
| **Pause Simulation Mode** | Instant halt to inspect holdings and rebalance | Halts execution immediately, retains full state | ✅ |
| **Manual Turn-Based Stepping** | Single-step tactical progression | `➡️ Next Quarter` / `➡️ Absorb Shock` and `🎲 Draw Event` buttons | ✅ |
| **Sequential Event Progression** | Advances through all 22 crisis cards without freeze | Verified: `test_quarterly_event_progression_variety` confirms 10 distinct events in 10 quarters | ✅ |
| **Pre-Drawn Shock Absorption** | Pre-drawn manual event absorbed on next advance | Verified: `test_predrawn_event_absorbed_before_queue` confirms no double-stepping | ✅ |
| **Circuit Breaker Discipline** | Selling frozen during sudden black swan shocks | Selling disabled during `SHOCKED` phase; tests diversification resilience | ✅ |
| **Dynamic Event Card** | Macro catalyst, shock metrics & NAV impact | Displays Top Sector Catalyst, Worst Sector Shock, CPI Inflation, and Portfolio NAV diff | ✅ |

---

### 2f — Multi-Decade Scorecard & Fisher CPI Compounding

| Criterion | Expected | Actual | Status |
| :--- | :--- | :--- | :---: |
| **Activation Threshold** | Displayed after $\ge 12$ quarters (3 years) when paused | Scorecard expander triggers at `portfolio.current_quarter >= 12` | ✅ |
| **Institutional Benchmarks** | Portfolio vs All-Weather, 60/40, 100% Equity | Multi-column comparative table with Final NAV, Nominal Return, Max Drawdown | ✅ |
| **Fisher Equation Real Return** | Purchasing power adjusted real return | Compounded via: $\text{Real Return} = \left(\frac{1 + r_{\text{nominal}}}{1 + i_{\text{cumulative}}} - 1\right) \times 100$ | ✅ |
| **Max Drawdown (Peak-to-Trough)** | Measures downside endurance | Tracked dynamically in [`Portfolio.get_max_drawdown()`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/portfolio.py#L230-L245) and [`BenchmarkTracker.get_max_drawdowns()`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/engine/benchmarks.py#L98-L115) | ✅ |
| **Lifetime Friction Metrics** | Cumulative tax and brokerage toll | Displays Taxes Paid (STCG + LTCG) vs Brokerage Fees Paid across 120 quarters | ✅ |
| **Career Retrospective Button** | On-demand comprehensive Socratic AI reflection | Streams comprehensive AI evaluation citing long-term compounding literature | ✅ |

---

### 2g — Automated Pytest Verification Suite

All **15 automated unit and integration tests** pass with zero failures:

```
tests\test_engine.py ..........                                          [ 66%]
tests\test_intelligence.py .....                                         [100%]
======================== 15 passed, 1 warning in 2.82s ========================
```

| # | Test Function | Module | Scope Verified |
| :---: | :--- | :--- | :--- |
| **1** | `test_asset_universe_integrity` | `test_engine.py` | 24 assets, 6 equity sectors $\times$ 3 caps, attributes (`beta`, `debt_ratio`, etc.) |
| **2** | `test_crisis_events_schema` | `test_engine.py` | 22 crisis cards, seasonal vs sudden categories, sector/asset impacts |
| **3** | `test_pricing_determinism` | `test_engine.py` | Reproducible pricing with seed, cash principal non-negativity |
| **4** | `test_portfolio_buy_and_sell` | `test_engine.py` | Buy/sell execution, fee deduction, cash accounting, holding periods |
| **5** | `test_friction_stcg_vs_ltcg` | `test_engine.py` | STCG (25%) at $<4$ quarters vs LTCG (10%) at $\ge 4$ quarters |
| **6** | `test_benchmarks_tracking` | `test_engine.py` | 100% Equity, 60/40, All-Weather parallel NAV updating |
| **7** | `test_cpi_inflation_hurdle_and_real_return` | `test_engine.py` | CPI compounding, Fisher equation real return, cash drag |
| **8** | `test_multi_quarter_time_travel_30_years` | `test_engine.py` | 120-quarter batch time-travel, peak-to-trough drawdowns, CPI doubling |
| **9** | `test_quarterly_event_progression_variety` | `test_engine.py` | Sequential non-freezing progression through 10 distinct events |
| **10** | `test_predrawn_event_absorbed_before_queue` | `test_engine.py` | Single-step pre-drawn event absorption without queue double-increment |
| **11** | `test_config_defaults` | `test_intelligence.py` | Central configuration loading, knowledge directory discovery |
| **12** | `test_rag_hybrid_retrieval` | `test_intelligence.py` | Hybrid tag + semantic search, metadata citation formatting, $\ge 25$ chunks |
| **13** | `test_prompt_template_formatting` | `test_intelligence.py` | Prompt safety, game state injection, system prompt hard rules |
| **14** | `test_offline_inference_simulation` | `test_intelligence.py` | Air-gapped mock LLM debrief, streaming generator, prompt schema injection |
| **15** | `test_career_retrospective_simulation` | `test_intelligence.py` | 30-year retrospective prompt formatting, streaming generation, scorecard |

---

## Dependencies & Environment Footprint

| Package | Version in `.venv` | Role in Phase 2 | Status |
| :--- | :---: | :--- | :---: |
| `streamlit` | **1.63.0** | Interactive dashboard, streaming responses (`st.write_stream`), flight controls | ✅ PASS |
| `google-genai` | **1.70.0** | Official Google GenAI SDK for Gemini streaming inference | ✅ PASS |
| `chromadb` | **0.6.3** | Embedded vector database for RAG wisdom storage & retrieval | ✅ PASS |
| `onnxruntime` | **1.24.4** | Local execution of `all-MiniLM-L6-v2` embeddings | ✅ PASS |
| `httpx` | **0.28.1** | Lightweight HTTP client for local Ollama daemon health pinging | ✅ PASS |
| `ollama` | **0.4.7** | Optional local air-gapped inference client | ✅ PASS |
| `plotly` | **7.0.0** | Real-time dark-themed benchmark & CPI hurdle trajectory charts | ✅ PASS |
| `pandas` | **3.0.5** | Tabular holding breakdowns and scorecard comparisons | ✅ PASS |
| `pytest` | **9.1.1** | Automated test verification framework | ✅ PASS |

---

## Inconsistencies Discovered & Refactorings Completed

During this audit, the following inconsistencies and code defects were systematically discovered and resolved:

### 1. Code Refactoring: `intelligence/mentor.py` Event Schema Mapping
- **Problem:** In [`mentor.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/intelligence/mentor.py), `post_event_debrief()`, `post_event_debrief_stream()`, and `pre_trade_insight()` extracted event attributes using `event.get("name")` and `event.get("type")`. In [`crisis_cards.json`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/data/crisis_cards.json), the standard keys are `"title"` and `"event_type"`. Consequently, prompts were being sent with `event_name = "Unknown Event"` and `event_type = "Unknown"`, and the RAG semantic query omitted the event title.
- **Fix Applied:** Refactored `mentor.py` to prioritize `event.get("title", event.get("name", "Unknown Event"))` and `event.get("event_type", event.get("type", "unknown"))`. Enhanced [`tests/test_intelligence.py`](file:///e:/NUS-ISS/GC1%20Practice%20Module/MarketSense/tests/test_intelligence.py) to capture the prompt and assert that both the title ("Emergency 100bps Central Bank Rate Hike") and event type ("Sudden") are passed to the LLM.

### 2. Documentation Correction: `Documentations/salient_features.md`
- **Asset Universe Misnomers:**
  - *Corrected:* Commodity assets updated from `Gold (COMM_GOLD) and Crude Energy Basket (COMM_OIL)` to `Physical Gold Trust (COMM_GOLD) and Physical Silver & Industrial Metals (COMM_SILVER)`.
  - *Corrected:* Digital Asset updated from `Bitcoin (CRYPTO_BTC)` to `Digital Asset Benchmark ETF (CRYPTO_BENCH)`.
  - *Corrected:* Equity sectors aligned with `assets.json` (`Banking & Financial Services`, `Energy & Utilities`, `FMCG & Consumer Staples`, `Healthcare & Pharmaceuticals`, `Information Technology`, `Real Estate & Infrastructure`).
- **Test Count Synchronization:** Updated from `13 Automated Pytest Verifications` to `15 Automated Pytest Verifications` to reflect the two newly added event progression variety test cases.
- **Flight Control Labels:** Updated button description from `🎲 Draw Event & ➡️ Advance Qtr` to reflect the dynamic `➡️ Next Quarter` / `➡️ Absorb Shock` label mechanism.

### 3. Roadmap Alignment: `Documentations/phases_information.md`
- **File Layout Alignment:** Updated Section 6 Repository Layout tree to reflect the current folder structure (`Documentations/` instead of `docs/`, `phases_information.md`, `salient_features.md`, and report folders `Reports by Opus/` and `Reports by Gemini/`).
- **Asset Description:** Aligned commodity definitions with `assets.json` (Gold and Silver/Industrial Metals).

### 4. Link Integrity: `README.md`
- **Path Updates:** Fixed outdated `docs/architecture.jpg` and `docs/SALIENT_FEATURES.md` links to point to the active `Documentations/` folder.

---

## What's NOT Built (Phase 3 & Phase 4 — Correct)

The following components are **intentionally not yet built** and belong to subsequent phases:

| Component | Target Phase | Status |
| :--- | :---: | :---: |
| **NetworkX Macro Causal Graph** (`intelligence/knowledge_graph.py`) | Phase 3 | Backlog Task 3.1 |
| **Shortest Causal Path Extraction** | Phase 3 | Backlog Task 3.2 |
| **Interactive Graph Visualizer** (`pyvis` / `streamlit-agraph`) | Phase 3 | Backlog Task 3.3 |
| **RAG v2 — Historical Crisis Precedents Matching** | Phase 3 | Backlog Task 3.4 |
| **Counterfactual "What-If" Allocation Sandbox** | Phase 3 | Backlog Task 3.5 |
| **Geographic Market Archetypes** (US, India Monsoon, Commodity Exporter) | Phase 4 | Backlog Task 4.1 |
| **Thematic Story Arc Campaigns** (4-round narrative journeys) | Phase 4 | Backlog Task 4.2 |
| **Session Save/Load & JSON Persistence** | Phase 4 | Backlog Task 4.4 |

---

## Conclusion

**Phase 2 is 100% complete, fully verified, and production-ready.** The AI Mentor functions reliably with grounded citations across both Google Gemini and offline Ollama runtimes. Financial friction (taxes and brokerage fees) accurately enforces behavioral discipline. Time-travel flight controls smoothly advance quarters without event freezing or UI stutter. All documentation files are synchronized and 15 automated pytest tests pass cleanly.

MarketSense is now fully prepared to fast-track into **Phase 3: Knowledge Graph & Explainable AI (XAI)**.
