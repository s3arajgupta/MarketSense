"""
MarketSense AI - Portfolio Flight Simulator
Interactive Streamlit Application
"""
import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from engine.portfolio import Portfolio
from engine.pricing import calculate_new_prices
from engine.benchmarks import BenchmarkTracker
from engine.friction import preview_sell_friction, preview_buy_friction

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

# 3. Session State Initialization
if "initialized" not in st.session_state:
    reset_simulation()

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
    if st.button("🔄 Reset Portfolio (S$30k Cash + S$70k Holdings)", use_container_width=True):
        reset_simulation()
        st.rerun()
    st.caption("Resets cash to S$30,000 and restores the 7-asset balanced allocation.")

# 4. Top Status Header & Permanent Navigation Controls
cur_nav = portfolio.get_nav(current_prices)
total_return_pct = ((cur_nav - portfolio.initial_cash) / portfolio.initial_cash) * 100.0
alpha_vs_equity = total_return_pct - (((benchmarks.nav_100_equity - 100000.0) / 100000.0) * 100.0)

# Top Action Control Bar
top_c1, top_c2, top_c3, top_c4, top_c5, top_act1, top_act2 = st.columns([1.1, 1.3, 1.3, 1.2, 1.1, 1.5, 1.5])

top_c1.metric("Timeline", f"Quarter Q{portfolio.current_quarter + 1}", f"Year {(portfolio.current_quarter // 4) + 1}")
top_c2.metric("Portfolio NAV", f"S${cur_nav:,.2f}", f"{total_return_pct:+.2f}%")
top_c3.metric("Liquid Cash", f"S${portfolio.cash:,.2f}", f"{(portfolio.cash / cur_nav * 100.0):.1f}% Alloc")
top_c4.metric("Alpha vs S&P", f"{alpha_vs_equity:+.2f}%")
top_c5.metric("Friction Paid", f"S${(portfolio.total_tax_paid + portfolio.total_brokerage_paid):,.0f}", f"Tax: S${portfolio.total_tax_paid:,.0f}")

with top_act1:
    draw_disabled = st.session_state.active_event is not None
    if st.button("🎲 Draw Market Event", type="primary", use_container_width=True, disabled=draw_disabled):
        ev = events_list[st.session_state.event_queue_idx % len(events_list)]
        st.session_state.event_queue_idx += 1
        st.session_state.active_event = ev
        st.session_state.event_phase = "PLANNING" if ev.get("event_type") == "Seasonal" else "SHOCKED"
        st.rerun()

with top_act2:
    advance_disabled = st.session_state.active_event is None
    if st.button("➡️ Advance Quarter", use_container_width=True, disabled=advance_disabled):
        ev = st.session_state.active_event
        calc_res = calculate_new_prices(current_prices, ev, assets_list)
        st.session_state.current_prices = calc_res["new_prices"]
        st.session_state.last_pct_changes = calc_res["pct_changes"]
        st.session_state.last_sector_changes = calc_res["sector_changes"]

        benchmarks.update(calc_res["pct_changes"], assets_list, portfolio.current_quarter + 1)
        portfolio.advance_quarter(calc_res["new_prices"], assets_list, ev["title"])

        st.session_state.active_event = None
        st.session_state.event_phase = "READY_FOR_EVENT"
        st.rerun()

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

        fig.update_layout(
            template='plotly_dark',
            xaxis_title="Quarter",
            yaxis_title="Net Asset Value (SGD)",
            margin=dict(l=10, r=10, t=30, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

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
            use_container_width=True,
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
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Sector movements will populate after the first market shock is processed.")

# ----------------- RIGHT COLUMN: Command Desk & Market Events -----------------
with right_col:
    active_ev = st.session_state.active_event
    if active_ev:
        is_seasonal = active_ev.get("event_type") == "Seasonal"
        
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

        st.markdown(f"**:{badge_color}[{badge_type}]**")
        st.markdown(f"### {active_ev['title']}")
        st.caption(f"**Category:** {active_ev['category']} | **Precedent:** {active_ev['historical_precedent']}")
        st.info(f"📰 **Headline:** {active_ev['headline']}")
        st.write(active_ev['context_description'])

        with st.expander("📖 Timeless Investor Principle"):
            st.markdown(f"*{active_ev['investor_wisdom_quote']}*")

        if is_seasonal and st.session_state.event_phase == "PLANNING":
            st.warning("⏳ **Planning Window Active:** You can strategically rebalance your portfolio *before* this forecast impacts the market!")
    else:
        st.info("Click **'🎲 Draw Market Event'** at the top right to start the quarter simulation.")

    # Trading & Rebalancing Desk
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

        if st.button("Confirm Buy Order", type="primary", use_container_width=True):
            res = portfolio.buy(buy_asset_id, buy_amount, cur_p)
            if res["success"]:
                st.success(f"Bought {res['units_bought']:.2f} units of {assets_dict[buy_asset_id]['ticker']}!")
                st.rerun()
            else:
                st.error(res["message"])

    else:  # Sell
        held_ids = [aid for aid, h in portfolio.holdings.items() if h["units"] > 0]
        if held_ids:
            sell_asset_id = st.selectbox(
                "Select Position to Sell",
                options=held_ids,
                format_func=lambda x: f"[{assets_dict[x]['ticker']}] {assets_dict[x]['name']} ({portfolio.holdings[x]['units']:.2f} units held)"
            )
            pos = portfolio.holdings[sell_asset_id]
            cur_p = current_prices.get(sell_asset_id, pos["avg_cost"])
            units_to_sell = st.number_input("Units to Sell", min_value=0.001, max_value=float(pos["units"]), value=float(pos["units"]), step=1.0)

            f_prev = preview_sell_friction(units_to_sell, cur_p, pos["avg_cost"], pos["quarters_held"])
            
            st.markdown("##### ⚠️ Pre-Trade Friction Preview")
            f_col1, f_col2, f_col3 = st.columns(3)
            f_col1.metric("Gross Proceeds", f"S${f_prev['gross_proceeds']:,.2f}")
            f_col2.metric("Taxes & Fees", f"-S${f_prev['total_friction']:,.2f}", f_prev['tax_type'])
            f_col3.metric("Net Cash Added", f"S${f_prev['net_proceeds']:,.2f}")
            st.caption(f"💡 **Mentor Note:** {f_prev['mentor_tip']}")

            if st.button("Confirm Sell Order (Deduct Taxes & Fees)", type="primary", use_container_width=True):
                res = portfolio.sell(sell_asset_id, units_to_sell, cur_p)
                if res["success"]:
                    st.success(f"Sold {units_to_sell:.2f} units. Net S${res['net_proceeds']:,.2f} credited to cash.")
                    st.rerun()
                else:
                    st.error(res["message"])
        else:
            st.info("No open positions held. Use cash to buy assets first.")
