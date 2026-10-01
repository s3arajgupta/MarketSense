"""
MarketSense AI - Portfolio Flight Simulator
Interactive Streamlit Application
"""
import json
import time
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from engine.portfolio import Portfolio
from engine.pricing import calculate_new_prices
from engine.benchmarks import BenchmarkTracker
from engine.friction import preview_sell_friction, preview_buy_friction
from engine.simulator import simulate_multi_quarters

INITIAL_TARGET_WEIGHTS = {
    "EQ_IT_LC": 0.10,
    "EQ_FMCG_LC": 0.10,
    "EQ_FIN_LC": 0.10,
    "EQ_HLTH_LC": 0.10,
    "COMM_GOLD": 0.10,
    "FI_TBILL_SHORT": 0.15,
    "CRYPTO_BENCH": 0.05,
    "CASH_MMF": 0.30,
}

# Phase 2: AI Mentor (graceful degradation if not configured)
try:
    from config import is_llm_configured
    from intelligence.mentor import AIMentor, MentorResponse
    from intelligence.gemini_provider import GeminiClient
    from intelligence.ollama_provider import OllamaClient
    LLM_AVAILABLE = is_llm_configured()
except ImportError:
    LLM_AVAILABLE = False

# 1. Page Configuration
st.set_page_config(
    page_title="MarketSense AI | Investment Flight Simulator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Data Loaders
@st.cache_data
def load_assets():
    with open("data/assets.json", "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_events():
    with open("data/crisis_cards.json", "r", encoding="utf-8") as f:
        return json.load(f)["events"]

assets_data = load_assets()
assets_list = assets_data["assets"]
assets_dict = {a["id"]: a for a in assets_list}
events_list = load_events()

def reset_simulation():
    """Resets simulation state to institutional S$100k diversified portfolio (30% Cash, 70% Invested)."""
    p = Portfolio(initial_cash=100000.0, base_currency="SGD")
    
    # Deploy exactly S$70,000 across 7 diversified institutional assets
    p.buy("EQ_IT_LC", 10000.0, 100.0, fee_rate=0.0)      # 10% Tech (100 units)
    p.buy("EQ_FMCG_LC", 10000.0, 100.0, fee_rate=0.0)    # 10% FMCG (100 units)
    p.buy("EQ_FIN_LC", 10000.0, 100.0, fee_rate=0.0)     # 10% Banking (100 units)
    p.buy("EQ_HLTH_LC", 10000.0, 100.0, fee_rate=0.0)    # 10% Healthcare (100 units)
    p.buy("COMM_GOLD", 10000.0, 100.0, fee_rate=0.0)     # 10% Gold Trust (100 units)
    p.buy("FI_TBILL_SHORT", 15000.0, 100.0, fee_rate=0.0)# 15% Sovereign T-Bills (150 units)
    p.buy("CRYPTO_BENCH", 5000.0, 100.0, fee_rate=0.0)   # 5% Digital Asset (50 units)
    # Remaining Cash: Exactly S$30,000 (30.0%)

    # Initial Q0 snapshot
    p.history = [{
        "quarter": 0,
        "nav": 100000.0,
        "cash": 30000.0,
        "event_title": "Initial Balanced Portfolio",
        "total_return_pct": 0.0,
        "dividends_this_qtr": 0.0
    }]

    st.session_state.portfolio = p
    st.session_state.benchmarks = BenchmarkTracker(initial_capital=100000.0)
    st.session_state.current_prices = {a["id"]: a["base_price"] for a in assets_list}
    st.session_state.active_event = None
    st.session_state.last_pct_changes = {}
    st.session_state.last_sector_changes = {}
    st.session_state.event_queue_idx = 0
    st.session_state.event_phase = "READY_FOR_EVENT"
    st.session_state.initialized = True
    st.session_state.mentor_debrief = None  # Stores latest mentor response
    st.session_state.last_resolved_event = None
    st.session_state.last_price_impacts = {}
    st.session_state.mentor_loading = False
    st.session_state.career_scorecard = None
    st.session_state.career_retrospective = None
    st.session_state.is_playing = False
    st.session_state.is_fast = False

# 3. Session State Initialization
if "initialized" not in st.session_state:
    reset_simulation()

# Initialize AI Mentor (once per session)
if "mentor" not in st.session_state:
    if LLM_AVAILABLE:
        try:
            st.session_state.mentor = AIMentor()
        except Exception:
            st.session_state.mentor = None
    else:
        st.session_state.mentor = None

portfolio: Portfolio = st.session_state.portfolio
benchmarks: BenchmarkTracker = st.session_state.benchmarks
current_prices = st.session_state.current_prices

# Sidebar Controls
with st.sidebar:
    st.markdown("### 🛠️ Simulator Controls")
    st.write("**Starting Capital:** S$100,000.00")
    st.write("**Base Currency:** SGD (Singapore Dollar)")
    st.write(f"**Loaded Market Events:** {len(events_list)} Scenarios")
    st.divider()
    if st.button("🔄 Reset Portfolio (S$30k Cash + S$70k Holdings)", width="stretch"):
        reset_simulation()
        st.rerun()
    st.caption("Resets cash to S$30,000 and restores the 7-asset balanced allocation.")

    # Dynamic LLM Provider Runtime Selector
    st.divider()
    st.markdown("### 🤖 AI Mentor Runtime")

    current_mode = st.session_state.get("runtime_mode", "gemini")
    mode_options = ["☁️ Cloud (Gemini API)", "💻 Local (Offline Ollama)"]
    mode_idx = 1 if current_mode == "ollama" else 0

    runtime_selection = st.radio(
        "Inference Engine",
        mode_options,
        index=mode_idx,
        help="Select whether AI reasoning executes via Cloud API or local air-gapped machine."
    )

    chosen_mode = "ollama" if "Offline" in runtime_selection else "gemini"

    if chosen_mode != st.session_state.get("runtime_mode") or st.session_state.get("mentor") is None:
        if chosen_mode == "ollama":
            test_ollama = OllamaClient()
            if test_ollama.is_available():
                st.session_state.mentor = AIMentor(llm_client=test_ollama)
                st.session_state.runtime_mode = "ollama"
                st.session_state.provider_status = ("success", "🟢 Local Ollama runtime active (air-gapped)")
            else:
                st.session_state.provider_status = (
                    "warning",
                    "⚠️ **Ollama daemon not detected at localhost:11434.** "
                    "To run in 100% offline mode, launch Ollama on your local machine. "
                    "Falling back to Cloud provider.\n\n"
                    "👉 [View Offline Setup in README.md](https://github.com/s3arajgupta/MarketSense#how-to-run-real-offline-inference-with-ollama)"
                )
                st.session_state.mentor = AIMentor(llm_client=GeminiClient())
                st.session_state.runtime_mode = "gemini"
        else:
            st.session_state.mentor = AIMentor(llm_client=GeminiClient())
            st.session_state.runtime_mode = "gemini"
            st.session_state.provider_status = ("info", "⚡ Cloud Gemini API active (~1.5s streaming)")

    status_type, status_msg = st.session_state.get("provider_status", ("info", "⚡ Cloud Gemini API active (~1.5s streaming)"))
    if status_type == "warning":
        st.warning(status_msg)
    elif status_type == "success":
        st.success(status_msg)
    else:
        st.caption(status_msg)

def step_simulation_quarter():
    """
    Advances simulation by exactly 1 quarter with full crisis card impact:
    - Draws next macro event from the crisis deck (or uses pre-drawn pending event)
    - Updates asset prices deterministically
    - Updates benchmarks with macro inflation
    - Advances portfolio (dividends, cash interest, LTCG aging)
    - Records price impacts for display and AI mentor
    """
    # If the user pre-drew an event in manual planning/shocked mode, consume that event.
    # Otherwise (e.g. continuous play or clicking Next Quarter), draw the next event from the queue.
    if st.session_state.get("event_phase") in ("PLANNING", "SHOCKED") and st.session_state.get("active_event"):
        ev = st.session_state.active_event
    else:
        ev = events_list[st.session_state.event_queue_idx % len(events_list)]
        st.session_state.event_queue_idx += 1

    calc_res = calculate_new_prices(st.session_state.current_prices, ev, assets_list)
    st.session_state.current_prices = calc_res["new_prices"]
    st.session_state.last_pct_changes = calc_res["pct_changes"]
    st.session_state.last_sector_changes = calc_res["sector_changes"]

    ev_inflation = ev.get("annualized_inflation", 0.025)
    benchmarks.update(
        calc_res["pct_changes"],
        assets_list,
        portfolio.current_quarter + 1,
        annualized_inflation=ev_inflation
    )
    portfolio.advance_quarter(calc_res["new_prices"], assets_list, ev.get("title", ev.get("name", "Market Event")))

    st.session_state.last_resolved_event = ev
    price_impacts = {}
    for a in assets_list:
        aid = a["id"]
        if aid in calc_res["pct_changes"]:
            price_impacts[a["name"]] = calc_res["pct_changes"][aid] * 100.0
    st.session_state.last_price_impacts = price_impacts
    st.session_state.active_event = ev
    st.session_state.event_phase = "RESOLVED"
    st.session_state.mentor_debrief = None

# 4. Top Status Header & Flight Controls
cur_nav = portfolio.get_nav(current_prices)
total_return_pct = ((cur_nav - portfolio.initial_cash) / portfolio.initial_cash) * 100.0
alpha_vs_equity = total_return_pct - (((benchmarks.nav_100_equity - 100000.0) / 100000.0) * 100.0)
real_return_pct = benchmarks.get_real_return_pct(total_return_pct)

# Top Status Metrics Row
top_c1, top_c2, top_c3, top_c4, top_c5 = st.columns([1.1, 1.4, 1.3, 1.2, 1.1])
top_c1.metric("Timeline", f"Quarter Q{portfolio.current_quarter}", f"Year {(portfolio.current_quarter // 4) + 1} of 30")
top_c2.metric(
    "Portfolio NAV",
    f"S${cur_nav:,.2f}",
    f"Real: {real_return_pct:+.1f}% (Nom: {total_return_pct:+.1f}%)",
    help="Real return is purchasing-power adjusted against the cumulative CPI inflation hurdle using the Fisher equation."
)
top_c3.metric("Liquid Cash", f"S${portfolio.cash:,.2f}", f"{(portfolio.cash / cur_nav * 100.0):.1f}% Alloc")
top_c4.metric("Alpha vs S&P", f"{alpha_vs_equity:+.2f}%")
top_c5.metric("Friction Paid", f"S${(portfolio.total_tax_paid + portfolio.total_brokerage_paid):,.0f}", f"Tax: S${portfolio.total_tax_paid:,.0f}")

st.markdown("---")

# ── Simulation Playback Flight Controls ──
is_playing = st.session_state.get("is_playing", False)
is_fast = st.session_state.get("is_fast", False)

p_c1, p_c2, p_c3, p_c4, p_c5 = st.columns([1.3, 1.3, 1.3, 1.3, 2.5])

if is_playing:
    with p_c1:
        if st.button("⏸️ Pause Simulation", type="primary", width="stretch", help="Halt simulation on current quarter to inspect or trade"):
            st.session_state.is_playing = False
            st.session_state.is_fast = False
            st.rerun()

    with p_c2:
        if is_fast:
            if st.button("▶️ Normal Speed (1x)", width="stretch", help="Slow down playback to 1x normal speed (~0.8s/quarter)"):
                st.session_state.is_fast = False
                st.rerun()
        else:
            if st.button("⏩ Fast Forward (3x)", width="stretch", help="Speed up simulation to 3x speed (~0.2s/quarter)"):
                st.session_state.is_fast = True
                st.rerun()

    with p_c3:
        st.button("🎲 Draw Event", width="stretch", disabled=True)

    with p_c4:
        st.button("➡️ Advance Qtr", width="stretch", disabled=True)

    with p_c5:
        speed_tag = "⚡ Fast Forwarding (3x Speed)" if is_fast else "🟢 Playing Simulation (1x Speed)"
        prog = min(1.0, portfolio.current_quarter / 120.0)
        st.progress(prog, text=f"{speed_tag} | Q{portfolio.current_quarter}/120 (Year {portfolio.current_quarter // 4}/30)")

else:
    with p_c1:
        if st.button("▶️ Play Simulation", type="primary", width="stretch", help="Run simulation continuously quarter-by-quarter"):
            st.session_state.is_playing = True
            st.session_state.is_fast = False
            st.rerun()

    with p_c2:
        if st.button("⏩ Fast Forward", width="stretch", help="Run simulation continuously at 3x fast speed"):
            st.session_state.is_playing = True
            st.session_state.is_fast = True
            st.rerun()

    with p_c3:
        has_pending_event = st.session_state.event_phase in ("PLANNING", "SHOCKED")
        draw_disabled = (portfolio.current_quarter >= 120) or has_pending_event
        if st.button("🎲 Draw Event", width="stretch", disabled=draw_disabled, help="Manually draw upcoming scenario to preview or plan"):
            ev = events_list[st.session_state.event_queue_idx % len(events_list)]
            st.session_state.event_queue_idx += 1
            st.session_state.active_event = ev
            st.session_state.event_phase = "PLANNING" if ev.get("event_type") == "Seasonal" else "SHOCKED"
            st.session_state.mentor_debrief = None
            st.rerun()

    with p_c4:
        advance_disabled = (portfolio.current_quarter >= 120)
        has_pending_event = st.session_state.event_phase in ("PLANNING", "SHOCKED")
        adv_btn_label = "➡️ Absorb Shock" if has_pending_event else "➡️ Next Quarter"
        adv_btn_help = "Absorb pending event shock into asset prices and complete quarter" if has_pending_event else "Simulate next quarter with upcoming macro scenario"
        if st.button(adv_btn_label, width="stretch", disabled=advance_disabled, help=adv_btn_help):
            step_simulation_quarter()
            st.rerun()

    with p_c5:
        prog = min(1.0, portfolio.current_quarter / 120.0)
        st.progress(prog, text=f"Timeline Horizon: Q{portfolio.current_quarter}/120 (Year {portfolio.current_quarter // 4}/30)")

# ── 🏛️ Multi-Decade Performance Scorecard (Rendered if paused after 3+ years) ──
if not is_playing and portfolio.current_quarter >= 12:
    with st.expander(f"🏛️ Multi-Decade Horizon Scorecard (Year {portfolio.current_quarter // 4} / Q{portfolio.current_quarter})", expanded=(portfolio.current_quarter >= 120)):
        aw_ret = ((benchmarks.nav_all_weather - 100000.0) / 100000.0) * 100.0
        b6040_ret = ((benchmarks.nav_60_40 - 100000.0) / 100000.0) * 100.0
        eq_ret = ((benchmarks.nav_100_equity - 100000.0) / 100000.0) * 100.0
        cum_cpi = benchmarks.get_history()[-1].get("cumulative_cpi_pct", 0.0)
        bm_dds = benchmarks.get_max_drawdowns()
        port_dd = portfolio.get_max_drawdown()

        sc_c1, sc_c2, sc_c3, sc_c4, sc_c5 = st.columns(5)
        sc_c1.metric("Final NAV", f"S${cur_nav:,.2f}", f"Nom: {total_return_pct:+.1f}%")
        sc_c2.metric("Real Return", f"{real_return_pct:+.1f}%", help="Purchasing-power adjusted via Fisher equation against CPI hurdle")
        sc_c3.metric("Max Drawdown", f"{port_dd:.1f}%", f"vs S&P: {bm_dds.get('100_equity', 0.0):.1f}%", delta_color="inverse")
        sc_c4.metric("CPI Inflation Hurdle", f"S${benchmarks.cpi_hurdle:,.0f}", f"+{cum_cpi:.1f}%")
        sc_c5.metric("Friction Paid", f"S${(portfolio.total_tax_paid + portfolio.total_brokerage_paid):,.0f}", f"Tax: S${portfolio.total_tax_paid:,.0f}")

        # Institutional Comparison Table
        score_df = pd.DataFrame([
            {"Strategy / Benchmark": "Your Portfolio", "Final NAV": f"S${cur_nav:,.2f}", "Nominal Return": f"{total_return_pct:+.1f}%", "Real Return (CPI-Adj)": f"{real_return_pct:+.1f}%", "Max Drawdown": f"{port_dd:.1f}%", "Total Friction": f"S${(portfolio.total_tax_paid + portfolio.total_brokerage_paid):,.0f}"},
            {"Strategy / Benchmark": "Ray Dalio All-Weather", "Final NAV": f"S${benchmarks.nav_all_weather:,.2f}", "Nominal Return": f"{aw_ret:+.1f}%", "Real Return (CPI-Adj)": f"{benchmarks.get_real_return_pct(aw_ret):+.1f}%", "Max Drawdown": f"{bm_dds.get('all_weather', 0.0):.1f}%", "Total Friction": "S$0"},
            {"Strategy / Benchmark": "Classic 60/40 Portfolio", "Final NAV": f"S${benchmarks.nav_60_40:,.2f}", "Nominal Return": f"{b6040_ret:+.1f}%", "Real Return (CPI-Adj)": f"{benchmarks.get_real_return_pct(b6040_ret):+.1f}%", "Max Drawdown": f"{bm_dds.get('60_40', 0.0):.1f}%", "Total Friction": "S$0"},
            {"Strategy / Benchmark": "100% Pure Equity Index", "Final NAV": f"S${benchmarks.nav_100_equity:,.2f}", "Nominal Return": f"{eq_ret:+.1f}%", "Real Return (CPI-Adj)": f"{benchmarks.get_real_return_pct(eq_ret):+.1f}%", "Max Drawdown": f"{bm_dds.get('100_equity', 0.0):.1f}%", "Total Friction": "S$0"},
            {"Strategy / Benchmark": "CPI Inflation Hurdle", "Final NAV": f"S${benchmarks.cpi_hurdle:,.2f}", "Nominal Return": f"+{cum_cpi:.1f}%", "Real Return (CPI-Adj)": "0.0%", "Max Drawdown": "0.0%", "Total Friction": "S$0"},
        ])
        st.dataframe(score_df, width="stretch", hide_index=True)

        mentor = st.session_state.get("mentor")
        if mentor:
            if st.session_state.get("career_retrospective"):
                with st.chat_message("assistant"):
                    st.markdown(st.session_state.career_retrospective)
            else:
                if st.button("🎓 Generate AI Mentor Multi-Decade Retrospective", width="stretch", key="btn_retro"):
                    sc_data = {
                        "initial_capital": 100000.0,
                        "final_nav": cur_nav,
                        "nominal_return_pct": total_return_pct,
                        "real_return_pct": real_return_pct,
                        "max_drawdown_portfolio": port_dd,
                        "total_friction": portfolio.total_tax_paid + portfolio.total_brokerage_paid,
                        "taxes_paid": portfolio.total_tax_paid,
                        "fees_paid": portfolio.total_brokerage_paid,
                        "dividends_earned": portfolio.total_dividends_earned,
                        "aw_nav": benchmarks.nav_all_weather,
                        "aw_return_pct": round(aw_ret, 2),
                        "aw_dd": bm_dds.get("all_weather", 0.0),
                        "b6040_nav": benchmarks.nav_60_40,
                        "b6040_return_pct": round(b6040_ret, 2),
                        "b6040_dd": bm_dds.get("60_40", 0.0),
                        "eq_nav": benchmarks.nav_100_equity,
                        "eq_return_pct": round(eq_ret, 2),
                        "eq_dd": bm_dds.get("100_equity", 0.0),
                        "cpi_hurdle": benchmarks.cpi_hurdle,
                        "cum_cpi_pct": cum_cpi,
                    }
                    try:
                        stream, citations, provider, model = mentor.career_retrospective_stream(portfolio.current_quarter, sc_data)
                        with st.chat_message("assistant"):
                            full_retro = st.write_stream(stream)
                        st.session_state.career_retrospective = full_retro
                    except Exception as e:
                        st.error(f"Mentor retrospective unavailable: {e}")

st.divider()

# 5. Main Split Layout
left_col, right_col = st.columns([0.58, 0.42])

# ----------------- LEFT COLUMN: Portfolio & Market Intelligence -----------------
with left_col:
    tab_charts, tab_holdings, tab_heatmap = st.tabs([
        "📈 Performance vs. Benchmarks",
        "💼 Holdings & Tax Ledger",
        "🗺️ Sector Heatmap"
    ])

    with tab_charts:
        st.subheader("NAV Trajectory vs. Institutional Benchmarks")
        
        p_hist = portfolio.history
        b_hist = benchmarks.get_history()

        quarters = [b["quarter"] for b in b_hist]
        trainee_navs = [p["nav"] for p in p_hist]
        if len(trainee_navs) < len(quarters):
            trainee_navs.append(cur_nav)
        trainee_navs = trainee_navs[:len(quarters)]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=quarters, y=trainee_navs,
            mode='lines+markers', name='Your Portfolio (Active)',
            line=dict(color='#00D26A', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=quarters, y=[b["all_weather"] for b in b_hist],
            mode='lines', name='Dalio All-Weather (Risk Parity)',
            line=dict(color='#FCD535', width=2, dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=quarters, y=[b["60_40"] for b in b_hist],
            mode='lines', name='Classic 60/40 (Equity/Bond)',
            line=dict(color='#00A3FF', width=2, dash='dot')
        ))
        fig.add_trace(go.Scatter(
            x=quarters, y=[b["100_equity"] for b in b_hist],
            mode='lines', name='100% Pure Equity Index',
            line=dict(color='#FF495F', width=1.5)
        ))
        fig.add_trace(go.Scatter(
            x=quarters, y=[b.get("cpi_hurdle", 100000.0) for b in b_hist],
            mode='lines', name='CPI Inflation Hurdle (Purchasing Power)',
            line=dict(color='#FFA500', width=2, dash='dashdot')
        ))

        fig.update_layout(
            template='plotly_dark',
            xaxis_title="Quarter",
            yaxis_title="Net Asset Value (SGD)",
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400
        )
        st.plotly_chart(fig, width="stretch")

    with tab_holdings:
        st.subheader("Current Asset Allocation & Capital Gains Status")
        breakdown = portfolio.get_holdings_breakdown(current_prices, assets_dict)
        df_holdings = pd.DataFrame(breakdown)

        display_cols = ["name", "sector", "units", "current_price", "market_value", "weight_pct", "unrealized_pnl_pct", "tax_status"]
        df_display = df_holdings[display_cols].copy()
        df_display.columns = ["Asset Name", "Sector", "Units", "Price (SGD)", "Value (SGD)", "Alloc %", "P&L %", "Tax Rate Status"]
        
        st.dataframe(
            df_display.style.format({
                "Price (SGD)": "S${:,.2f}",
                "Value (SGD)": "S${:,.2f}",
                "Alloc %": "{:.1f}%",
                "P&L %": "{:+.2f}%"
            }),
            width="stretch",
            hide_index=True
        )

    with tab_heatmap:
        st.subheader("Macro Sector Sensitivities (Last Quarter)")
        if st.session_state.last_sector_changes:
            sec_df = pd.DataFrame([
                {"Sector": s, "Quarterly Shift %": chg * 100.0}
                for s, chg in st.session_state.last_sector_changes.items()
            ])
            st.dataframe(
                sec_df.style.format({"Quarterly Shift %": "{:+.2f}%"}),
                width="stretch",
                hide_index=True
            )
        else:
            st.info("Sector movements will populate after the first market shock is processed.")

    # ── Trading & Rebalancing Desk (Positioned below Portfolio & Benchmarks) ──
    st.divider()
    st.subheader("⚙️ Trading & Rebalancing Desk")

    order_type = st.radio("Order Action", ["Buy (Deploy Cash)", "Sell (Trim Position)"], horizontal=True)

    if order_type == "Buy (Deploy Cash)":
        buy_asset_id = st.selectbox(
            "Select Asset to Purchase",
            options=[a["id"] for a in assets_list if a["id"] != "CASH_MMF"],
            format_func=lambda x: f"[{assets_dict[x]['ticker']}] {assets_dict[x]['name']}"
        )
        cur_p = current_prices.get(buy_asset_id, 100.0)
        max_buy = max(100.0, portfolio.cash)
        buy_amount = st.number_input("Amount to Invest (SGD)", min_value=100.0, max_value=max_buy, value=min(5000.0, max_buy), step=500.0)

        buy_friction = preview_buy_friction(buy_amount)
        st.caption(f"Brokerage Fee (0.15%): S${buy_friction['brokerage_fee']:.2f} | Total Cash Required: S${buy_friction['total_cash_required']:.2f}")

        if st.button("Confirm Buy Order", type="primary", width="stretch"):
            res = portfolio.buy(buy_asset_id, buy_amount, cur_p)
            if res["success"]:
                st.success(f"Bought {res['units_bought']:.2f} units of {assets_dict[buy_asset_id]['ticker']}!")
                st.rerun()
            else:
                st.error(res["message"])

    else:  # Sell
        is_shock_locked = st.session_state.event_phase == "SHOCKED"
        if is_shock_locked:
            st.error(
                "🔒 **Circuit Breaker: Selling Locked During Sudden Black Swan**\n\n"
                "In an unexpected macroeconomic shock, markets gap down instantaneously and liquidity dries up. "
                "Investors cannot front-run the crisis at pre-shock valuations.\n\n"
                "**Testing Discipline & Patience:** Advance the quarter to let the market absorb the shock. "
                "Your pre-existing asset diversification and cash reserves will determine how well your portfolio weathers this event."
            )

        held_ids = [aid for aid, h in portfolio.holdings.items() if h["units"] > 0]
        if held_ids:
            sell_asset_id = st.selectbox(
                "Select Position to Sell",
                options=held_ids,
                format_func=lambda x: f"[{assets_dict[x]['ticker']}] {assets_dict[x]['name']} ({portfolio.holdings[x]['units']:.2f} units held)",
                disabled=is_shock_locked,
            )
            pos = portfolio.holdings[sell_asset_id]
            cur_p = current_prices.get(sell_asset_id, pos["avg_cost"])
            units_to_sell = st.number_input(
                "Units to Sell",
                min_value=0.001,
                max_value=float(pos["units"]),
                value=float(pos["units"]),
                step=1.0,
                disabled=is_shock_locked,
            )

            f_prev = preview_sell_friction(units_to_sell, cur_p, pos["avg_cost"], pos["quarters_held"])
            
            st.markdown("##### ⚠️ Pre-Trade Friction Preview")
            f_col1, f_col2, f_col3 = st.columns(3)
            f_col1.metric("Gross Proceeds", f"S${f_prev['gross_proceeds']:,.2f}")
            f_col2.metric("Taxes & Fees", f"-S${f_prev['total_friction']:,.2f}", f_prev['tax_type'])
            f_col3.metric("Net Cash Added", f"S${f_prev['net_proceeds']:,.2f}")
            st.caption(f"💡 **Mentor Note:** {f_prev['mentor_tip']}")

            sell_btn_label = "🔒 Selling Frozen (Shock in Progress)" if is_shock_locked else "Confirm Sell Order (Deduct Taxes & Fees)"
            if st.button(sell_btn_label, type="primary", width="stretch", disabled=is_shock_locked):
                res = portfolio.sell(sell_asset_id, units_to_sell, cur_p)
                if res["success"]:
                    st.success(f"Sold {units_to_sell:.2f} units. Net S${res['net_proceeds']:,.2f} credited to cash.")
                    st.rerun()
                else:
                    st.error(res["message"])
        else:
            st.info("No open positions held. Use cash to buy assets first.")

# ----------------- RIGHT COLUMN: Command Desk & Market Events -----------------
with right_col:
    active_ev = st.session_state.active_event
    if active_ev:
        is_seasonal = active_ev.get("event_type") == "Seasonal"
        is_pending = st.session_state.event_phase in ("PLANNING", "SHOCKED")
        
        # Check if positive opportunity or crisis
        avg_sector_imp = sum(active_ev.get("sector_impacts", {}).values()) / max(1, len(active_ev.get("sector_impacts", {})))
        is_opportunity = avg_sector_imp > 0.02

        if is_opportunity:
            badge_type = "🚀 GROWTH CATALYST & OPPORTUNITY"
            badge_color = "green"
        elif is_seasonal:
            badge_type = "📅 FORECAST / SEASONAL EVENT"
            badge_color = "blue"
        else:
            badge_type = "💥 SUDDEN BLACK SWAN SHOCK"
            badge_color = "red"

        # Quarter timeline tag
        if is_pending:
            q_num = portfolio.current_quarter + 1
            status_tag = f"⏳ Upcoming Scenario • Quarter Q{q_num} (Year {((q_num - 1) // 4) + 1})"
        else:
            q_num = max(1, portfolio.current_quarter)
            status_tag = f"🎯 Active Scenario • Quarter Q{q_num} (Year {((q_num - 1) // 4) + 1})"

        st.caption(f"**{status_tag}**")
        st.markdown(f"**:{badge_color}[{badge_type}]**")
        st.markdown(f"### {active_ev['title']}")
        ev_inf_pct = active_ev.get("annualized_inflation", 0.025) * 100.0
        st.caption(f"**Category:** {active_ev['category']} | **Precedent:** {active_ev['historical_precedent']} | **Macro Inflation:** {ev_inf_pct:.1f}% p.a.")
        st.info(f"📰 **Headline:** {active_ev['headline']}")
        st.write(active_ev['context_description'])

        # ── Macro Shock & Market Impact Metrics ──
        st.markdown("##### ⚡ Macro Shock Transmission & Market Impact")
        sec_shifts = active_ev.get("sector_impacts", {})
        if sec_shifts:
            sorted_secs = sorted(sec_shifts.items(), key=lambda x: x[1], reverse=True)
            best_sec = sorted_secs[0]
            worst_sec = sorted_secs[-1]
            cols = st.columns(3)
            with cols[0]:
                st.metric("Top Sector Catalyst", f"{best_sec[0][:14]}", f"{best_sec[1]*100:+.1f}%")
            with cols[1]:
                st.metric("Worst Sector Shock", f"{worst_sec[0][:14]}", f"{worst_sec[1]*100:+.1f}%")
            with cols[2]:
                inf_tag = "Elevated" if ev_inf_pct >= 4.0 else ("Subdued" if ev_inf_pct <= 2.0 else "Stable")
                st.metric("Macro CPI Inflation", f"{ev_inf_pct:.1f}% p.a.", inf_tag, delta_color="inverse" if ev_inf_pct >= 4.0 else "normal")

        # Quarterly Portfolio Impact Callout (when event is resolved in history)
        if not is_pending and len(portfolio.history) >= 2:
            prev_nav = portfolio.history[-2]["nav"]
            cur_q_nav = portfolio.history[-1]["nav"]
            nav_diff = cur_q_nav - prev_nav
            nav_diff_pct = (nav_diff / prev_nav) * 100.0 if prev_nav > 0 else 0.0
            divs_received = portfolio.history[-1].get("dividends_this_qtr", 0.0)
            
            p_color = "green" if nav_diff >= 0 else "red"
            st.markdown(
                f"💼 **Quarterly Portfolio Impact:** "
                f"NAV :{p_color}[**S${nav_diff:+,.2f} ({nav_diff_pct:+.2f}%)**] | "
                f"Income (Divs & Interest): **+S${divs_received:,.2f}**"
            )

        with st.expander("🔍 View All Sector & Asset Transmission Shocks"):
            sec_items = [f"**{s}:** {chg*100:+.1f}%" for s, chg in active_ev.get("sector_impacts", {}).items()]
            ast_items = [f"**{a}:** {chg*100:+.1f}%" for a, chg in active_ev.get("asset_impacts", {}).items()]
            if sec_items:
                st.markdown("**Sectors:** " + " • ".join(sec_items))
            if ast_items:
                st.markdown("**Key Assets:** " + " • ".join(ast_items))

        with st.expander("📖 Timeless Investor Principle"):
            st.markdown(f"*{active_ev['investor_wisdom_quote']}*")

        if is_seasonal and st.session_state.event_phase == "PLANNING":
            st.warning("⏳ **Planning Window Active:** You can strategically rebalance your portfolio at the Trading Desk *before* this forecast impacts the market!")
        elif st.session_state.event_phase == "SHOCKED":
            st.error("🚨 **Sudden Market Shock Active:** Circuit breakers triggered! Selling is frozen to prevent pre-crash front-running. Advance the quarter to absorb the shock and test your portfolio's diversification resilience.")
        elif st.session_state.event_phase == "RESOLVED" and not is_playing:
            st.success("✅ **Market Shock Absorbed:** Prices have adjusted to this macro event. Use the Trading Desk below or click 'Next Quarter' / 'Play Simulation' to proceed.")
    else:
        st.info(
            "### 🛫 Flight Simulator Ready: Quarter Q0\n\n"
            "Your initial institutional portfolio of **S$100,000.00** is deployed across 7 diversified asset classes with 30% liquid cash reserves.\n\n"
            "**How to Play:**\n"
            "- Click **▶️ Play Simulation** to watch your portfolio navigate 30 years (120 Quarters) of macroeconomic cycles.\n"
            "- Or click **➡️ Next Quarter** / **🎲 Draw Event** to advance quarter-by-quarter manually.\n"
            "- Watch how different market shocks (rate hikes, pandemics, commodity surges, AI booms) impact each asset class and benchmark!"
        )

    # ── AI Mentor Panel (Phase 2 - Causal Shock Analysis) ──
    st.divider()
    mentor = st.session_state.get("mentor")
    mentor_debrief = st.session_state.get("mentor_debrief")
    last_ev = st.session_state.get("last_resolved_event")

    if mentor:
        provider_label = f"🤖 AI Mentor — *{mentor.provider_name}*"
        st.markdown(f"#### {provider_label}")

        # Display debrief if user requested it
        if mentor_debrief:
            with st.chat_message("assistant"):
                st.markdown(mentor_debrief.text)

            if mentor_debrief.has_citations:
                with st.expander("📚 Source Citations"):
                    for c in mentor_debrief.citations:
                        if c:
                            st.caption(f"— {c.get('source', 'Unknown source')}")
            st.caption(f"Tokens: {mentor_debrief.tokens_used} | Model: {mentor_debrief.model}")

        # Focused on-demand action: Explain shock & causal transmission with live streaming
        if last_ev:
            button_label = "🔄 Re-analyze Market Shock" if mentor_debrief else "🔍 Explain Market Shock & Causal Transmission"
            if st.button(button_label, width="stretch"):
                try:
                    new_nav = portfolio.get_nav(current_prices)
                    prev_nav = portfolio.history[-2]["nav"] if len(portfolio.history) >= 2 else 100000.0
                    nav_change_pct = ((new_nav - prev_nav) / prev_nav) * 100.0
                    breakdown = portfolio.get_holdings_breakdown(current_prices, assets_dict)
                    aw_return = ((benchmarks.nav_all_weather - 100000.0) / 100000.0) * 100.0
                    user_return = ((new_nav - 100000.0) / 100000.0) * 100.0
                    real_ret = benchmarks.get_real_return_pct(user_return)

                    p_state = {
                        "nav": new_nav,
                        "nav_change_pct": nav_change_pct,
                        "cash": portfolio.cash,
                        "cash_pct": (portfolio.cash / new_nav * 100.0) if new_nav > 0 else 0,
                        "holdings": breakdown,
                        "alpha_aw": user_return - aw_return,
                        "nominal_return_pct": user_return,
                        "real_return_pct": real_ret,
                        "cpi_hurdle": benchmarks.cpi_hurdle,
                    }

                    stream, citations, provider, model = mentor.post_event_debrief_stream(
                        quarter=portfolio.current_quarter,
                        event=last_ev,
                        price_impacts=st.session_state.get("last_price_impacts", {}),
                        portfolio_state=p_state,
                    )

                    with st.chat_message("assistant"):
                        full_text = st.write_stream(stream)

                    if citations:
                        with st.expander("📚 Source Citations"):
                            for c in citations:
                                if c:
                                    st.caption(f"— {c.get('source', 'Unknown source')}")
                    st.caption(f"Model: {model} | Provider: {provider}")

                    st.session_state.mentor_debrief = MentorResponse(
                        text=full_text,
                        citations=citations,
                        provider=provider,
                        model=model,
                        tokens_used=len(full_text.split()),
                    )
                except Exception as e:
                    st.error(f"Mentor unavailable: {e}")
        else:
            st.caption("ℹ️ Advance through a quarter with a market event to unlock causal shock analysis.")
    else:
        # Graceful degradation
        with st.expander("🤖 AI Mentor (Not Configured)"):
            st.info(
                "Configure an LLM provider to enable the AI Mentor.\n\n"
                "1. Copy `.env.example` to `.env`\n"
                "2. Set `LLM_PROVIDER=gemini` and add your `GEMINI_API_KEY`\n"
                "3. Get a free key at [aistudio.google.com](https://aistudio.google.com/apikey)"
            )

# ── 6. Continuous Simulation Runner (Play / Pause / Fast Forward Loop) ──
if st.session_state.get("is_playing", False):
    if portfolio.current_quarter >= 120:
        st.session_state.is_playing = False
        st.session_state.is_fast = False
        st.balloons()
        st.toast("🎉 Completed full 30-Year Career Horizon (120 Quarters)!")
        st.rerun()
    else:
        delay = 0.20 if st.session_state.get("is_fast", False) else 0.80
        time.sleep(delay)
        step_simulation_quarter()
        st.rerun()

