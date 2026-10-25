# MarketSense AI — Streamlit UI Architecture & Component Guide

> **System Overview:** MarketSense is an institutional-grade investment flight simulator built in Python using Streamlit. It merges deterministic quantitative finance models with grounded explainable AI (XAI) and Socratic mentorship, training investors across 30 simulated years (120 quarters) of macroeconomic market shocks.

---

## 1. UI Design System & Aesthetic Principles

| Aesthetic Pillar | Design Implementation | Purpose & User Experience |
| :--- | :--- | :--- |
| **Dark-Themed Institutional Palette** | Slate & Charcoal base (`#0E1117`, `#1E293B`, `#0B0F19`) | Mimics institutional terminals (Bloomberg, FactSet) for focused, high-contrast financial data readability. |
| **Compact Vertical Density** | Custom CSS overriding `.block-container` padding (`1.25rem` top) | Eliminates wasted whitespace, bringing high-priority KPIs and interactive controls into the immediate primary viewport. |
| **Color-Coded Semantic Signals** | Green (`#10B981`) for expansionary/positive alpha; Red (`#EF4444`) for contractionary/drag; Amber (`#F59E0B`) for warnings & root macro shocks. | Instant recognition of portfolio status, causal polarity, and market risks. |
| **Persistent Time-Travel Flight Controls** | Sticky floating glassmorphism toolbar in the main pane + synchronized controls anchored in the sidebar. | Trainees can advance time, pause, or fast-forward from anywhere on the page without scrolling back to the top. |
| **Visual Explainability (XAI)** | Physics-based force-directed Pyvis canvas with prominent 20–24px bold labels, glowing halos, and directional transmission arrows. | Demystifies macroeconomic contagion, making causal ripples transparent and engaging. |

---

## 2. Page Layout & Component Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                STREAMLIT SIDEBAR                                       │
│  • Simulator Controls & Portfolio Reset (S$100k starting capital)                      │
│  • Dual-Engine LLM Runtime Switcher (Cloud Gemini vs Air-Gapped Local Ollama)         │
│  • 🎮 Persistent Quick Time-Travel Controls (Play, Fast, Pause, Advance Qtr)           │
└────────────────────────────────────────┬───────────────────────────────────────────────┘
                                         │
┌────────────────────────────────────────▼───────────────────────────────────────────────┐
│                    TOP STATUS METRICS RIBBON (Compact Institutional KPIs)              │
│  [Timeline: Q12/120]  [Portfolio NAV: S$108,450]  [Cash: 28.5%]  [Alpha: +4.2%]  [Tax] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                 STICKY FLOATING FLIGHT CONTROLS TOOLBAR (Glides as you scroll)          │
│  [▶️ Play]  [⏩ Fast Forward (3x)]  [⏸️ Pause]  [🎲 Draw Event]  [➡️ Advance Qtr] [Progress] │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                     DYNAMIC MACRO SHOCK & CRISIS TRANSMISSION BANNER                   │
│  • Active Event Headline & Category (e.g. Emergency 100bps Policy Rate Hike)           │
│  • Top Sector Catalyst | Worst Sector Shock | Macro CPI Inflation | NAV Delta Impact   │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                         ANALYTICS & EXPLAINABILITY TABS                                │
│  ┌───────────────────────┬────────────────────────┬─────────────────────────────────┐  │
│  │ 📈 Trajectory Charts  │ 💼 Asset Allocation   │ 🔥 Sector Sensitivities         │  │
│  ├───────────────────────┴────────────────────────┴─────────────────────────────────┤  │
│  │ 🌐 Causal XAI Graph   │ 🔮 Counterfactual What-If │ 🤖 AI Mentor Socratic Debrief │  │
│  └──────────────────────────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                        TRADING & REBALANCING DESK                                      │
│  • Buy / Sell Order Actions with Gross Value, Brokerage Fee, and Capital Gains Tax     │
│  • Circuit Breaker Alert (Locks selling during sudden black swan shocks)               │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Specifications

### 3.1 — Top Status Metrics Ribbon (Compact Institutional KPIs)

Positioned at the very top of the application, styled with custom CSS to maximize vertical space efficiency:
- **Timeline:** Displays active Quarter (`Q{quarter}`) and Year (`Year {Y} of 30`).
- **Portfolio NAV:** Current total net asset value in SGD, accompanied by real purchasing-power return (Fisher equation adjusted against CPI hurdle) and nominal return delta.
- **Liquid Cash:** Available uninvested capital in the Cash Money Market Fund (`CASH_MMF`), displaying SGD value and portfolio allocation percentage.
- **Alpha vs S&P:** Trainee excess return over the 100% Equity Index benchmark.
- **Friction Paid:** Lifetime capital gains taxes paid (STCG + LTCG) and institutional brokerage commissions deducted.

### 3.2 — Sticky Floating Flight Controls Toolbar

Pinned with `position: sticky; top: 2.875rem` and glassmorphic blur:
- **▶️ Play Simulation:** Runs continuously quarter-by-quarter (~0.8s per quarter). Automatically computes macroeconomic price movements, updates benchmarks, compounds CPI inflation, and re-renders plots.
- **⏩ Fast Forward (3x):** Accelerated continuous simulation (~0.2s per quarter), executing 30 years (120 quarters) in ~24 seconds.
- **⏸️ Pause Simulation:** Halts playback instantly on the current quarter to allow the trainee to inspect holdings, conduct counterfactual experiments, trade, or debrief with the AI Mentor.
- **🎲 Draw Event (Manual Mode):** Draws an upcoming scenario ahead of time to allow planning (if seasonal) or triggers a surprise shock.
- **➡️ Next Quarter / ➡️ Absorb Shock:** Advances exactly 1 quarter. Dynamically shifts its label to alert the user if a pending shock needs to be absorbed into asset prices.
- **Timeline Progress Bar:** Real-time visual progress bar tracking progress through the 120-quarter horizon.

*(Note: Identical controls are mirrored in the sidebar, providing accessible time travel regardless of scroll position.)*

### 3.3 — Dynamic Macro Shock & Crisis Transmission Banner

Displays key macroeconomic telemetry for the active event:
- **Event Header:** Event Title, Event Type (Seasonal vs Sudden), and Macroeconomic Category.
- **Top Sector Catalyst:** Sector experiencing the highest positive tailwind (e.g. Energy during an oil shock).
- **Worst Sector Shock:** Sector suffering the sharpest price compression (e.g. Technology during a rate hike).
- **Macro CPI Inflation:** Annualized quarterly inflation rate used by the Fisher equation hurdle.
- **Portfolio Impact Callout:** Concrete dollar and percentage NAV shift experienced by the trainee's specific allocation during the quarter.

---

## 4. Analytics & Explainable AI (XAI) Tabs

### Tab 1: 📈 Benchmark & Wealth Trajectory
- **Plotly Dark Interactive Chart:**
  - Real-time multi-line time-series plotting:
    1. **Your Portfolio** (Thick Blue line with hoverable NAV and drawdowns).
    2. **Ray Dalio All-Weather** (30% Equities, 40% Long Bonds, 15% T-Bills, 7.5% Gold, 7.5% Commodities).
    3. **Classic 60/40 Portfolio** (60% Equities, 40% Long Bonds).
    4. **100% Equity Index** (Pure Equity Benchmark).
    5. **CPI Inflation Hurdle** (Compounded purchasing power preservation line).
- **Hover Data:** Displays quarter number, active crisis event name, and precise NAV for each strategy.

### Tab 2: 💼 Asset Allocation & Capital Gains Status
- **Interactive Holdings Table:** Displays all 24 instruments in the portfolio:
  - Asset Name, Sector, Units Held, Current Price (SGD), Total Market Value (SGD), Portfolio Allocation %, Unrealized P&L %, and Tax Rate Status.
- **Tax Rate Aging:** Dynamically flags whether a position qualifies for Long-Term Capital Gains (**LTCG 10%** for positions held $\ge 4$ quarters) or Short-Term Capital Gains (**STCG 25%** for positions held $< 4$ quarters).

### Tab 3: 🔥 Macro Sector Sensitivities
- **Sector Sensitivity Heatmap:** Tabulates quarterly percentage shifts across all 6 core economic sectors:
  - Information Technology, FMCG & Consumer Staples, Banking & Financial Services, Healthcare & Pharmaceuticals, Energy & Utilities, Real Estate & Infrastructure.

### Tab 4: 🌐 Symbolic Macroeconomic Causal Graph (XAI)
- **Pyvis Physics Interactive Network:**
  - Rendered via modern `st.iframe(src, height=600, width="stretch")` (cleanly replacing deprecated `st.components.v1.html`).
  - Force-directed layout modeling 36 nodes (11 Drivers, 12 Channels, 6 Sectors, 7 Asset Classes) and 48 directed weighted edges.
  - **Prominent Visual Hierarchy:**
    - Root shock node highlighted with a **`⚡` prefix, large size (46px), and glowing amber halo**.
    - Active downstream nodes rendered with **large 20px bold white labels with high-contrast outlines**.
    - Inactive background nodes **faded and reduced** to eliminate visual clutter.
    - Active causal edges glow **Vibrant Emerald (`#10B981`)** for expansionary or **Rose Red (`#EF4444`)** for contractionary transmission.
  - **Interactive Event Selector:** Trainees can pick any of the 22 crisis scenarios to inspect its transmission network.
  - **On-Screen Navigation:** Built-in zoom in, zoom out, fit-to-screen, and panning controls.
  - **Grounded Historical Twin Precedent:** Displays matching historical twin episodes (e.g. 1980 Volcker Shock vs 2022 Rate Hike) directly in the tab.

### Tab 5: 🔮 Counterfactual "What-If" Simulation Sandbox
- **Instant Scenario Re-Play:**
  - Allows trainees to test what their NAV and returns *would have been* under alternative allocations during the exact shock just resolved:
    1. *Ray Dalio All-Weather* (Diversified Risk Parity)
    2. *Pure Cash Fortress* (100% Cash MMF)
    3. *Gold Defense Hedge* (50% Gold, 25% Silver, 25% Cash)
    4. *Tech Aggressive Growth* (100% IT Large/Mid/Small Cap)
- **Metrics Output:** Trainee Actual NAV vs Counterfactual NAV, Alpha / Drag Delta, and an educational verdict.
- **Asset-by-Asset Contribution Table:** Detailed breakdown of how each asset weight contributed to the counterfactual return.

### Tab 6: 🤖 AI Mentor Socratic Debrief
- **Real-Time Token Streaming:** Debrief streams progressively via `st.write_stream()`.
- **4-Section Pedagogical Structure:**
  1. 📉 **What Happened:** Concise 2-3 sentence overview of the macroeconomic shock.
  2. 🔗 **Causal Chain:** Step-by-step transmission trace grounded in the verified NetworkX knowledge graph.
  3. 📚 **What the Masters Say:** Citations from Graham, Dalio, Marks, Lynch, Bogle, or Taleb.
  4. 💡 **Your Portfolio:** Tactical critique of trainee holdings, cash drag, and purchasing power preservation.
- **Source Citations Expander:** Auditable book and author citations displayed in collapsible trays.
- **Career Retrospective (After 12+ Quarters):** Comprehensive evaluation of the trainee's 30-year multi-decade compounding journey.

---

## 5. Trading & Rebalancing Desk

Located below the analytics tabs to facilitate informed decision-making:
- **Order Action Toggle:** Switch between `Buy (Deploy Cash)` and `Sell (Trim Position)`.
- **Pre-Trade Friction & Tax Preview:**
  - When buying: Calculates 0.15% brokerage fee and total cash required.
  - When selling: Displays Gross Proceeds, Average Cost Basis, Realized Gain/Loss, Applicable Tax (STCG 25% vs LTCG 10%), Brokerage Fee (0.15%), Net Cash Added, and a contextual behavioral tip.
- **Black Swan Circuit Breaker:**
  - Selling is automatically disabled during unexpected sudden black swan events (`SHOCKED` phase).
  - Trainees must absorb the shock before trading, reinforcing the core lesson that portfolio diversification is the only true defense against liquidity freezes.

---

## 6. Streamlit Session State Architecture

| Key | Type | Description |
| :--- | :--- | :--- |
| `st.session_state.portfolio` | `Portfolio` | Core portfolio tracking cash, holdings, transaction history, tax lots, and returns. |
| `st.session_state.benchmarks` | `BenchmarkTracker` | Tracks 100% Equity, 60/40, All-Weather, and CPI inflation hurdle. |
| `st.session_state.current_prices` | `dict[str, float]` | Current market price per unit for all 24 instruments. |
| `st.session_state.active_event` | `dict` | Currently drawn or active macroeconomic crisis event card. |
| `st.session_state.event_phase` | `str` | State machine phase: `READY_FOR_EVENT`, `PLANNING`, `SHOCKED`, or `RESOLVED`. |
| `st.session_state.is_playing` | `bool` | Flag controlling whether simulation is continuously auto-stepping. |
| `st.session_state.is_fast` | `bool` | Flag controlling whether playback runs at 1x (~0.8s) or 3x (~0.2s) speed. |
| `st.session_state.runtime_mode` | `str` | Active LLM inference runtime (`"gemini"` or `"ollama"`). |
| `st.session_state.mentor` | `AIMentor` | Instantiated AI Mentor orchestrator with RAG engine and Knowledge Graph. |
| `st.session_state.mentor_debrief` | `str` | Cached Socratic debrief text for the active resolved quarter. |

---

## 7. Responsive Breakpoints & Device Adaptation

- **Desktop Widescreen ($\ge 1200\text{px}$):** Default multi-column layout with side-by-side metric ribbons, 4-column legend, and expanded Plotly charts.
- **Laptop / Tablet ($768\text{px} - 1199\text{px}$):** Columns stack gracefully; Pyvis interactive graph maintains full touch and gesture support for pinch-to-zoom and dragging.
- **Sidebar Collapse:** Sidebar collapses via Streamlit hamburger menu without interrupting running simulation playback.
