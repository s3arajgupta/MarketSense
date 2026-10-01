# MarketSense AI — Salient Application Features

This document provides a continuous, institutional-grade catalog of the core architectural, financial, and pedagogical features implemented in **MarketSense AI**.

---

## 1. Multi-Asset Institutional Universe
- **24 Granular Financial Instruments:**
  - **Equities (18 Assets):** 6 sectors (Information Technology, Financials, Healthcare, Consumer Discretionary, Industrials, Energy) $\times$ 3 market capitalizations (Large Cap, Mid Cap, Small Cap).
  - **Commodities (2 Assets):** Gold (`COMM_GOLD`) and Crude Energy Basket (`COMM_OIL`).
  - **Fixed Income (2 Assets):** Short-Term Sovereign T-Bills (`FI_TBILL_SHORT`) and 10-Year Sovereign Bonds (`FI_BOND_LONG`).
  - **Cash Equivalents (1 Asset):** High-yield Singapore Dollar Money Market Fund (`CASH_MMF`).
  - **Digital Assets (1 Asset):** Bitcoin (`CRYPTO_BTC`).
- **Asset Metadata & Fundamental Sensitivity:**
  - Every asset models `beta`, `debt_ratio` (vulnerability to rate hikes), `cash_resilience` (survival probability during credit freezes), and `dividend_yield` (quarterly cash-flow generation).

---

## 2. Macroeconomic Crisis & Event Engine
- **22 Historically Grounded Crisis Cards:**
  - Spans **Seasonal / Structural** cycles (Earnings Season, Tech Breakthrough, Tax Year-End) and **Sudden Black Swan Shocks** (1973 Oil Embargo, 1997 Asian Financial Crisis, 2000 Dot-Com Crash, 2008 Global Financial Crisis, 2011 Sovereign Debt Crisis, 2020 COVID Crash, 2022 Fed Rate Hike Shock, 2023 Bank Run / SVB Collapse).
- **Two-Phase Event Lifecycle:**
  - **Seasonal Events:** Enter a `PLANNING` window, allowing tactical portfolio rebalancing *before* market impact.
  - **Sudden Black Swans:** Enter a `SHOCKED` phase with immediate market price adjustments.

---

## 3. Circuit Breaker & Behavioral Discipline
- **Locked Selling During Black Swan Shocks:**
  - In a sudden macro shock, the simulation freezes selling to emulate real-world market halts and liquidity evaporation.
  - Investors cannot front-run crashes at pre-shock valuations; they must advance the quarter and let pre-existing diversification and cash buffers absorb the shock.
  - Tests discipline, patience, and contrarian stamina rather than panic-selling at market bottoms.

---

## 4. Institutional Financial Friction & Tax Drag
- **Differential Capital Gains Tax (STCG vs. LTCG):**
  - **Short-Term Capital Gains (STCG - 25%):** Applied to profitable positions held for fewer than 4 quarters (<1 year).
  - **Long-Term Capital Gains (LTCG - 10%):** Rewarded to patient investors holding assets for 4 or more quarters ($\ge$1 year).
- **Institutional Brokerage Costs:**
  - 0.15% transaction fee on all gross trade values.
- **Pre-Trade Friction & Tax Preview:**
  - Real-time calculator displays Gross Proceeds, Estimated Tax (STCG/LTCG breakdown), Brokerage Cost, and Net Cash Credited before confirming a trade.

---

## 5. Parallel Passive Institutional Benchmarks
Tracks three institutional reference portfolios dynamically alongside the trainee:
1. **100% Pure Equity Index:** Unhedged market risk proxy.
2. **Classic 60/40 Benchmark:** 60% Global Equities, 20% Short T-Bills, 20% Long Sovereign Bonds.
3. **Ray Dalio All-Weather Portfolio (Risk Parity):**
   - 30% Equities, 40% Long Sovereign Bonds, 15% Short T-Bills, 7.5% Physical Gold, 7.5% Commodities.
   - Provides all-season downside protection across shifting growth and inflation regimes.

---

## 6. Institutional Hybrid Inflation & Purchasing Power Hurdle
- **Dynamic Event-Driven Inflation:**
  - Every macro crisis card dynamically sets the macroeconomic inflation rate (e.g., Oil Shocks at 8.9% p.a., Rate Hikes at 7.8% p.a., Tech Booms at 1.8% p.a., Baseline at 2.5% p.a.).
- **Cumulative CPI Hurdle Line:**
  - Displayed on the benchmark Plotly chart as an Amber/Orange dashed-dot line (`#FFA500`), compounding quarterly from S$100,000 baseline purchasing power.
- **Fisher Equation Real Return Metric:**
  - Top status bar displays real purchasing power return alongside nominal return:
    $$\text{Real Return} = \left(\frac{1 + r_{\text{nominal}}}{1 + i_{\text{cumulative}}} - 1\right) \times 100$$
- **Dalio's Cash Drag & Money Illusion:**
  - Instead of artificially deducting money from bank accounts, the simulation visually and mathematically exposes how cash loses purchasing power against the rising CPI hurdle.

---

## 7. Dual-Engine AI Mentor (Cloud Gemini vs. Air-Gapped Ollama)
- **Runtime Selector in Sidebar:**
  - **☁️ Cloud (Google Gemini 2.5 Flash):** High-speed (~1.5s) token streaming via Google GenAI SDK.
  - **💻 Local (Air-Gapped Ollama):** 100% private, offline inference over local HTTP daemon (`localhost:11434`), zero cloud telemetry.
- **Graceful Detection & Fallback:**
  - Automatically pings the Ollama daemon; if unreachable, alerts the user, provides an offline setup link, and falls back to Cloud mode without application crash.

---

## 8. Socratic Grounded AI Reasoning (RAG)
- **Curated Wisdom Corpus:**
  - Vectorized knowledge base containing wisdom chunks from **Benjamin Graham**, **Ray Dalio**, **Howard Marks**, **Peter Lynch**, **John Bogle**, and **Nassim Nicholas Taleb**, plus 7 landmark historical crisis case studies.
- **Hard Guardrails:**
  - Strictly grounded in cited investment literature (quotes + authors).
  - Never predicts future asset prices or gives prescriptive trade orders.
  - Emphasizes the **Causal Chain:** $\text{Macro Event} \to \text{Transmission Mechanism} \to \text{Sector Impact} \to \text{Portfolio Exposure}$.

---

## 9. Comprehensive Automated Test Suite
- **13 Automated Pytest Verifications (`tests/`):**
  - Asset universe schema & attribute integrity.
  - Crisis event categorization & inflation rates.
  - Deterministic pricing engine bounds & cash non-negativity.
  - Buy/Sell mechanics, average cost basis, and cash accounting.
  - STCG (25%) vs. LTCG (10%) threshold calculations.
  - Passive benchmark tracking (100% Equity, 60/40, All-Weather).
  - CPI Hurdle quarterly compounding and Fisher equation real return accuracy.
  - 30-year (120-quarter) accelerated simulation execution & drawdown validity.
  - RAG hybrid retrieval and metadata citations.
  - Prompt template formatting and guardrails.
  - Mock offline inference simulation for air-gapped environments.
  - Multi-decade career retrospective prompt formatting and streaming.

---

## 10. Simulation Flight Controls: Continuous Time Travel (Play / Pause / Fast Forward)
- **Interactive Simulation Player:**
  - **▶️ Play Simulation:** Runs continuously quarter-by-quarter (~0.8s per quarter). In each step, an authentic crisis card event is drawn from the library, macroeconomic price shocks are calculated, benchmarks compound dynamic inflation, and the chart updates dynamically.
  - **⏸️ Pause Simulation:** Halts playback instantly on the current quarter so the trainee can inspect the event headline/precedent/inflation in the right column, execute tactical trades, review holdings, or request a Socratic debrief from the AI Mentor.
  - **⏩ Fast Forward:** Runs continuously at accelerated speed (~0.2s per quarter / 3x speed), allowing 30 years (120 quarters) to unfold in under 20 seconds while still executing all crisis events and updating charts.
  - **🎲 Draw Event & ➡️ Advance Qtr:** Full manual single-step mode remains intact for tactical turn-based play.
- **Dynamic Event Transmission:**
  - Every quarter processed in Play or Fast Forward mode accounts for real crisis card impacts: sector shifts, dividend accrual, cash money market interest, and capital gains tax aging.
- **Multi-Decade Horizon Scorecard (Paused after 3+ Years):**
  - Displays a comprehensive institutional comparison table across Your Portfolio, Dalio All-Weather, Classic 60/40, 100% Equity, and the CPI Hurdle.
  - Tracks **Maximum Drawdown (Peak-to-Trough Loss)** to measure survival across market crashes.
  - Calculates total lifetime friction drag (taxes vs brokerage fees).
- **AI Mentor Multi-Decade Career Retrospective:**
  - Socratic evaluation analyzing whether the trainee's strategy defeated inflation, suffered from cash drag, or surrendered excessive wealth to portfolio turnover.

