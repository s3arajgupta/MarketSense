# Appendix C: Installation & User Guide

## MarketSense AI: A Neuro-Symbolic Portfolio Flight Simulator

This institutional user manual provides end-to-end instructions for installing, configuring, running, and interacting with **MarketSense AI**.

---

### 1. System Requirements & Prerequisites

#### 1.1 Software Dependencies
- **Operating System:** Windows 10/11, macOS (Intel / Apple Silicon), or Linux (Ubuntu 20.04+).
- **Python Runtime:** Python 3.10, 3.11, or 3.12 (Python 3.14 compatible).
- **Package Manager:** `pip` (bundled with Python).
- **Web Browser:** Google Chrome, Brave, Firefox, or Microsoft Edge (modern Chromium recommended for WebGL/Vis.js hardware acceleration).

#### 1.2 Hardware Specifications

| Runtime Mode | Minimum Hardware | Recommended Hardware | Storage Footprint |
| :--- | :--- | :--- | :--- |
| **Cloud API (Google Gemini)** | 1 vCPU, 512 MB RAM | 2 vCPUs, 1–2 GB RAM | ~250 MB total (Dependencies & Cache) |
| **Local Offline (Ollama - CPU)** | 4 vCPUs, 8 GB RAM | 8 vCPUs, 16–32 GB RAM (AVX2 support) | ~5 GB (Ollama + 8B Q4 Model Weights) |
| **Local Offline (Ollama - GPU)** | 4 vCPUs, 16 GB RAM, 6 GB VRAM | 8 vCPUs, 32 GB RAM, 8–12 GB VRAM (RTX 3060+) | ~5 GB (Ollama + 8B Q4 Model Weights) |

---

### 2. Step-by-Step Installation

#### Step 1: Clone the Repository
Open your terminal (PowerShell on Windows, Bash/Zsh on macOS/Linux):
```bash
git clone https://github.com/s3arajgupta/MarketSense.git
cd MarketSense
```

#### Step 2: Create and Activate a Python Virtual Environment
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```
- **macOS / Linux:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

#### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```
*Note:* Dependencies include `streamlit`, `pandas`, `plotly`, `networkx`, `pyvis`, `chromadb`, and `google-genai`.

---

### 3. LLM Configuration (Dual Runtime Setup)

MarketSense operates seamlessly under two distinct runtime environments:

#### Option A: Cloud Google Gemini API (Recommended — Zero Download)
1. Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey).
2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
3. Open `.env` in any text editor and populate your key:
   ```env
   GEMINI_API_KEY="your-actual-api-key-here"
   LLM_PROVIDER="gemini"
   ```

#### Option B: Local Air-Gapped Ollama (100% Offline Privacy)
1. Download and install Ollama from [ollama.ai](https://ollama.ai).
2. Pull your desired open-weights model in your terminal:
   ```bash
   ollama pull llama3.1:8b        # Recommended for balanced reasoning (~4.7 GB)
   # Or for ultra-lightweight CPU execution:
   ollama pull phi3:mini           # Ultra-compact (~2.2 GB)
   ```
3. Update `.env` (or select "💻 Local (Air-Gapped Ollama)" inside the application sidebar):
   ```env
   LLM_PROVIDER="ollama"
   OLLAMA_MODEL="llama3.1:8b"
   OLLAMA_HOST="http://localhost:11434"
   ```

*Graceful Degradation Note:* If no LLM provider is configured or Ollama is unreachable, MarketSense will continue running all financial pricing, portfolio accounting, knowledge graphs, and benchmarks without crashing.

---

### 4. Launching the Application

Execute the Streamlit entrypoint:
```bash
streamlit run app.py
```
Upon startup, Streamlit will automatically open your default browser to:
```
http://localhost:8501
```

*First-Run Note:* On the very first launch, ChromaDB downloads its lightweight sentence transformer embedding model (`all-MiniLM-L6-v2`, ~79 MB) to local cache. This takes 10–20 seconds and happens only once.

---

### 5. Application User Guide & Walkthrough

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        MARKETSENSE AI FLIGHT SIMULATOR TOP RIBBON                      │
│ [NAV: S$100,000] [Nominal P&L: +0.0%] [Real P&L: +0.0%] [Cash: S$30,000] [Quarter: Q0]│
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ LEFT COLUMN: Market Intelligence & XAI   │ RIGHT COLUMN: Command Desk & Operations     │
│ ├── Tab 1: 📈 Performance vs Benchmarks  │ ├── 🎮 Simulation Flight Controls (Play/FF) │
│ ├── Tab 2: 💼 Holdings & Tax Ledger      │ ├── 🌍 Macro Event Console (Crisis Cards)   │
│ ├── Tab 3: 🗺️ Sector Heatmap             │ ├── ⚙️ Trading Desk (Buy / Sell + Friction) │
│ ├── Tab 4: 🌐 Causal XAI Graph (Pyvis)   │ └── 🤖 Socratic AI Mentor Console           │
│ └── Tab 5: 🔮 Counterfactual 'What-If'   │                                             │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

#### 5.1 Top Status Ribbon
- **Net Asset Value (NAV):** Total portfolio valuation in Singapore Dollars (Cash + Market Value of open positions).
- **Nominal Return (%):** Raw dollar percentage change from the initial S$100,000 baseline.
- **Real Purchasing Power Return (%):** Return deflated by the cumulative CPI hurdle via the **Fisher Equation**:
  $$\text{Real Return} = \left(\frac{1 + r_{\text{nominal}}}{1 + i_{\text{cumulative}}} - 1\right) \times 100$$
- **Liquid Cash Reserve:** Available capital in the high-yield SGD Money Market Fund (`CASH_MMF`).
- **Active Quarter & Horizon:** Displays current time step (Q1 to Q120 / 30 Years).

---

#### 5.2 Left Column: The 5 Intelligence Tabs

##### Tab 1: 📈 Performance vs. Institutional Benchmarks
- Interactive Plotly chart comparing your active portfolio against:
  1. **Dalio All-Weather:** Risk-parity benchmark (Yellow dashed line).
  2. **Classic 60/40:** Traditional balanced portfolio (Blue dotted line).
  3. **100% Pure Equity Index:** Unhedged market risk proxy (Red line).
  4. **CPI Inflation Hurdle:** Cumulative purchasing power benchmark (Amber dash-dot line).

##### Tab 2: 💼 Holdings & Tax Ledger
- Tabular breakdown of all open positions: units held, current price, allocation percentage, unrealized P&L, and **Tax Rate Status**:
  - `STCG (25%)` — held for $< 4$ quarters.
  - `LTCG (10%)` — held for $\ge 4$ quarters (tax-advantaged).

##### Tab 3: 🗺️ Sector Heatmap
- Displays quarterly percentage shifts across all 6 economic sectors following macro shocks.

##### Tab 4: 🌐 Symbolic Macroeconomic Causal Graph (XAI)
- **Interactive Force-Directed Network:** Visualizes how shocks ripple from Macro Drivers (Red) $\to$ Financial Channels (Orange) $\to$ Economic Sectors (Blue) $\to$ Asset Classes (Green).
- **Active Pathway Highlighting:** Active transmission edges glow green (expansionary) or red (contractionary).
- **Scenario Inspector:** Dropdown allows inspection of causal transmission chains for all 22 crisis scenarios.
- **Historical Twin Precedent:** Displays comparative metrics from empirical history (e.g. 1980 Volcker Shock).

##### Tab 5: 🔮 Counterfactual "What-If" Sandbox
- Evaluates what your NAV and return *would have been* during the active crisis under 4 reference strategies:
  1. *Ray Dalio All-Weather*
  2. *Pure Cash Fortress*
  3. *Precious Metals Defensive*
  4. *Aggressive Tech & Innovation*
- Outputs Alpha / Drag metrics and asset-by-asset movement contributions.

---

#### 5.3 Right Column: Command Desk & Operations

##### A. Simulation Flight Controls
- **▶️ Play Simulation:** Runs continuously quarter-by-quarter (~0.8s per quarter).
- **⏩ Fast Forward (3x):** Accelerated time travel (~0.2s per quarter) simulating 30 years in ~24 seconds.
- **⏸️ Pause Simulation:** Freezes playback instantly to allow tactical rebalancing, research, or AI debriefing.
- **➡️ Next Quarter / 🎲 Draw Event:** Step-by-step turn-based progression.

##### B. Trading & Rebalancing Desk
1. **Buying Assets:**
   - Select asset and specify investment amount (SGD).
   - Real-time caption displays 0.15% brokerage fee and total cash required.
2. **Selling Assets & Friction Preview:**
   - Select open position and units to trim.
   - **Pre-Trade Friction Preview** calculates Gross Proceeds, Estimated Tax (STCG vs LTCG breakdown), Brokerage Cost, and Net Cash Credited before confirming order.
   - **Circuit Breaker:** If a sudden Black Swan shock is active, selling is locked until the quarter is advanced, enforcing disciplined holding.

##### C. Socratic AI Mentor
- **Post-Event Debrief:** Generates a real-time Socratic explanation of why your portfolio gained or lost value, citing the underlying causal path and historical investment literature.
- **Career Retrospective:** Available after 12+ quarters; conducts a holistic audit of your asset allocation discipline, inflation survival, and turnover drag.

---

### 6. Automated Testing & Verification

Run the automated pytest test suite:
```bash
pytest
```
*Expected Output:*
```
============================= test session starts =============================
platform win32 -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0
collected 25 items

tests\test_engine.py ..........                                          [ 40%]
tests\test_intelligence.py .....                                         [ 60%]
tests\test_knowledge_graph.py ..........                                 [100%]

======================== 25 passed in 4.08s ========================
```

---

### 7. Troubleshooting & FAQs

- **Q: Ollama connection fails with "Ollama daemon unreachable".**  
  *Fix:* Ensure the Ollama daemon is running in the background (`ollama serve` or open the Ollama desktop app). Test by navigating to `http://localhost:11434` in your browser.
- **Q: Gemini API returns authentication errors.**  
  *Fix:* Verify that `GEMINI_API_KEY` in `.env` contains a valid key from Google AI Studio without extra spaces or quotation errors.
- **Q: Streamlit port 8501 is already in use.**  
  *Fix:* Launch on an alternate port: `streamlit run app.py --server.port 8502`.
- **Q: Windows PowerShell script execution policy error.**  
  *Fix:* Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` to allow `.venv` activation.
