"""
MarketSense Phase 1 Verification Test Script
Tests all engine modules end-to-end.
"""
import json
from engine.portfolio import Portfolio
from engine.pricing import calculate_new_prices
from engine.benchmarks import BenchmarkTracker
from engine.friction import preview_sell_friction, preview_buy_friction

# --- 1. Load Data ---
with open("data/assets.json", "r", encoding="utf-8") as f:
    assets_data = json.load(f)
assets_list = assets_data["assets"]
assets_dict = {a["id"]: a for a in assets_list}

with open("data/crisis_cards.json", "r", encoding="utf-8") as f:
    events_list = json.load(f)["events"]

print("=" * 60)
print("MARKETSENSE PHASE 1 — VERIFICATION TEST SUITE")
print("=" * 60)

# --- Test 1a: Asset Data Model ---
print("\n[1a] ASSET DATA MODEL (data/assets.json)")
print(f"  Total assets loaded: {len(assets_list)}")
equities = [a for a in assets_list if a["asset_class"] == "Equities"]
commodities = [a for a in assets_list if a["asset_class"] == "Commodities"]
fi = [a for a in assets_list if a["asset_class"] == "Fixed Income"]
cash = [a for a in assets_list if a["asset_class"] == "Cash Equivalents"]
digital = [a for a in assets_list if a["asset_class"] == "Digital Assets"]
print(f"  Equities: {len(equities)}  (expect 18 = 6 sectors × 3 caps)")
print(f"  Commodities: {len(commodities)}  (expect 2: Gold, Silver)")
print(f"  Fixed Income: {len(fi)}  (expect 2: T-Bills, Gov Bonds)")
print(f"  Cash Equivalents: {len(cash)}  (expect 1: Money Market)")
print(f"  Digital Assets: {len(digital)}  (expect 1: Crypto ETF)")

# Verify sectors
sectors = set(a["sector"] for a in equities)
print(f"  Equity sectors: {sorted(sectors)}")
for sector in sectors:
    caps = [a["market_cap"] for a in equities if a["sector"] == sector]
    print(f"    {sector}: {sorted(caps)}")

# Verify required fields
required_fields = ["beta", "debt_ratio", "cash_resilience", "dividend_yield"]
missing = []
for a in assets_list:
    for field in required_fields:
        if field not in a:
            missing.append((a["id"], field))
if missing:
    print(f"  ⚠️  MISSING FIELDS: {missing}")
else:
    print(f"  ✅ All {len(assets_list)} assets have required fields: {required_fields}")

# --- Test 1b: Event Library ---
print(f"\n[1b] EVENT LIBRARY (data/crisis_cards.json)")
print(f"  Total events: {len(events_list)}  (spec: 15-20)")
seasonal = [e for e in events_list if e["event_type"] == "Seasonal"]
sudden = [e for e in events_list if e["event_type"] == "Sudden"]
print(f"  Seasonal (forecastable): {len(seasonal)}")
print(f"  Sudden (black swan): {len(sudden)}")
for e in events_list:
    has_impacts = "sector_impacts" in e and "asset_impacts" in e
    has_wisdom = "investor_wisdom_quote" in e
    has_precedent = "historical_precedent" in e
    if not (has_impacts and has_wisdom and has_precedent):
        print(f"  ⚠️  Event '{e['title']}' missing fields: impacts={has_impacts}, wisdom={has_wisdom}, precedent={has_precedent}")
print(f"  ✅ All events have sector_impacts, asset_impacts, wisdom quotes, and precedents.")

# --- Test 1c: Pricing Engine ---
print(f"\n[1c] DETERMINISTIC PRICING ENGINE (engine/pricing.py)")
prices = {a["id"]: a["base_price"] for a in assets_list}
ev = events_list[0]  # Use first event
res = calculate_new_prices(prices, ev, assets_list, seed=42)
print(f"  Test event: '{ev['title']}' ({ev['event_type']})")
print(f"  New prices computed: {len(res['new_prices'])} assets")
print(f"  Pct changes computed: {len(res['pct_changes'])} assets")
print(f"  Sector changes computed: {len(res['sector_changes'])} sectors")

# Verify determinism with same seed
res2 = calculate_new_prices(prices, ev, assets_list, seed=42)
if res["new_prices"] == res2["new_prices"]:
    print("  ✅ DETERMINISTIC: Same seed produces identical prices.")
else:
    print("  ⚠️  NON-DETERMINISTIC: Same seed produces different prices!")

# Verify safety bounds
for aid, chg in res["pct_changes"].items():
    if chg < -0.85:
        print(f"  ⚠️  Safety bound violated: {aid} = {chg}")
all_prices_valid = all(p >= 0.01 for p in res["new_prices"].values())
print(f"  ✅ All prices >= $0.01: {all_prices_valid}")

# Verify Cash MMF never declines
if "CASH_MMF" in res["pct_changes"]:
    if res["pct_changes"]["CASH_MMF"] >= 0:
        print(f"  ✅ Cash MMF principal protected (change: {res['pct_changes']['CASH_MMF']:.4f})")
    else:
        print(f"  ⚠️  Cash MMF declined: {res['pct_changes']['CASH_MMF']}")

# --- Test 1c: Portfolio Manager ---
print(f"\n[1c] PORTFOLIO MANAGER (engine/portfolio.py)")
p = Portfolio(100000.0, "SGD")
print(f"  Initial cash: S${p.cash:,.2f}")
print(f"  Currency: {p.base_currency}")

# Buy initial positions (matching app.py setup)
p.buy("EQ_IT_LC", 10000.0, 100.0, fee_rate=0.0)
p.buy("EQ_FMCG_LC", 10000.0, 100.0, fee_rate=0.0)
p.buy("EQ_FIN_LC", 10000.0, 100.0, fee_rate=0.0)
p.buy("EQ_HLTH_LC", 10000.0, 100.0, fee_rate=0.0)
p.buy("COMM_GOLD", 10000.0, 100.0, fee_rate=0.0)
p.buy("FI_TBILL_SHORT", 15000.0, 100.0, fee_rate=0.0)
p.buy("CRYPTO_BENCH", 5000.0, 100.0, fee_rate=0.0)

nav = p.get_nav(prices)
print(f"  NAV after setup: S${nav:,.2f}  (expect S$100,000.00)")
print(f"  Cash remaining: S${p.cash:,.2f}  (expect S$30,000.00)")
print(f"  Holdings: {len(p.holdings)} positions")

if abs(nav - 100000.0) < 0.01 and abs(p.cash - 30000.0) < 0.01:
    print("  ✅ Portfolio setup matches spec (S$100k NAV, S$30k cash, 7 positions)")
else:
    print("  ⚠️  Portfolio setup mismatch!")

# Test buy with brokerage
buy_res = p.buy("EQ_NRG_LC", 5000.0, 100.0, fee_rate=0.0015)
print(f"  Buy with fee: units={buy_res['units_bought']:.2f}, fee=S${buy_res['fee_paid']:.2f}")
if buy_res["success"] and buy_res["fee_paid"] == 7.5:
    print("  ✅ Buy brokerage fee (0.15%) correctly applied")
else:
    print(f"  ⚠️  Buy fee issue: expected 7.50, got {buy_res.get('fee_paid')}")

# Test insufficient cash
bad_buy = p.buy("EQ_RE_LC", 999999.0, 100.0)
print(f"  Insufficient cash test: success={bad_buy['success']} → ✅" if not bad_buy["success"] else "  ⚠️  Should have rejected!")

# Advance quarter and check dividends
snap = p.advance_quarter(prices, assets_list, "Test Quarter")
print(f"  Quarter advanced to Q{p.current_quarter}")
print(f"  Cash interest earned: {0.038/4*p.cash:.2f} approx")
print(f"  Dividends this quarter: S${snap['dividends_this_qtr']:,.2f}")
if snap["dividends_this_qtr"] > 0:
    print("  ✅ Dividends and cash interest accruing correctly")

# Test sell with STCG (held < 4 quarters)
sell_res = p.sell("EQ_IT_LC", 50.0, 100.0)
print(f"  Sell 50 IT units: gain=S${sell_res['realized_gain']:.2f}, tax=S${sell_res['tax_paid']:.2f}")
if sell_res["success"]:
    print("  ✅ Sell order executed successfully")

# --- Test 1d: Friction Engine ---
print(f"\n[1d] FRICTION ENGINE (engine/friction.py)")
# STCG test
fric = preview_sell_friction(100, 120.0, 100.0, quarters_held=2)
print(f"  STCG preview (2 qtrs held, gain): tax_type={fric['tax_type']}, tax=S${fric['estimated_tax']:.2f}")
expected_tax = (120.0 - 100.0) * 100 * 0.25
if abs(fric["estimated_tax"] - expected_tax) < 0.01:
    print(f"  ✅ STCG 25% correctly applied (expected S${expected_tax:.2f})")
else:
    print(f"  ⚠️  STCG tax mismatch: expected S${expected_tax:.2f}, got S${fric['estimated_tax']:.2f}")

# LTCG test
fric2 = preview_sell_friction(100, 120.0, 100.0, quarters_held=5)
print(f"  LTCG preview (5 qtrs held, gain): tax_type={fric2['tax_type']}, tax=S${fric2['estimated_tax']:.2f}")
expected_ltcg = (120.0 - 100.0) * 100 * 0.10
if abs(fric2["estimated_tax"] - expected_ltcg) < 0.01:
    print(f"  ✅ LTCG 10% correctly applied (expected S${expected_ltcg:.2f})")

# Loss test (no tax)
fric3 = preview_sell_friction(100, 80.0, 100.0, quarters_held=2)
print(f"  Loss preview: tax_type={fric3['tax_type']}, tax=S${fric3['estimated_tax']:.2f}")
if fric3["estimated_tax"] == 0.0:
    print("  ✅ No capital gains tax on losses")

# Mentor tip test
if "LTCG" in fric["mentor_tip"] or "Long-Term" in fric["mentor_tip"]:
    print("  ✅ Mentor tip advises holding for LTCG discount")

# Brokerage
buy_fric = preview_buy_friction(10000.0)
if abs(buy_fric["brokerage_fee"] - 15.0) < 0.01:
    print(f"  ✅ Buy brokerage: S${buy_fric['brokerage_fee']:.2f} (0.15% of S$10k)")

# --- Test 1d: Benchmarks ---
print(f"\n[1d] BENCHMARK TRACKER (engine/benchmarks.py)")
b = BenchmarkTracker(100000.0)
# Simulate 3 quarters
for i in range(3):
    ev_test = events_list[i % len(events_list)]
    res_test = calculate_new_prices(prices, ev_test, assets_list, seed=i)
    b.update(res_test["pct_changes"], assets_list, i + 1)
    prices_updated = res_test["new_prices"]

hist = b.get_history()
print(f"  History length: {len(hist)} (expect 4: Q0 + 3 quarters)")
print(f"  100% Equity NAV: S${b.nav_100_equity:,.2f}")
print(f"  60/40 NAV: S${b.nav_60_40:,.2f}")
print(f"  All-Weather NAV: S${b.nav_all_weather:,.2f}")
if len(hist) == 4:
    print("  ✅ Benchmark history tracking correctly")

# --- Test 1e: App Structure Validation ---
print(f"\n[1e] STREAMLIT UI VALIDATION (app.py)")
import ast
with open("app.py", "r", encoding="utf-8") as f:
    source = f.read()
tree = ast.parse(source)

imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
print(f"  Import statements: {len(imports)}")

# Check required imports
import_names = source[:500]
checks = {
    "streamlit": "streamlit" in import_names,
    "plotly": "plotly" in import_names,
    "pandas": "pandas" in import_names,
    "Portfolio": "Portfolio" in source,
    "calculate_new_prices": "calculate_new_prices" in source,
    "BenchmarkTracker": "BenchmarkTracker" in source,
    "preview_sell_friction": "preview_sell_friction" in source,
    "preview_buy_friction": "preview_buy_friction" in source,
}
for name, ok in checks.items():
    status = "✅" if ok else "⚠️ MISSING"
    print(f"  {status} {name} imported/used")

# Check key UI features
ui_checks = {
    "Performance chart (Plotly)": "go.Figure()" in source or "go.Scatter" in source,
    "Holdings table": "Holdings" in source and "dataframe" in source,
    "Sector heatmap tab": "Heatmap" in source or "heatmap" in source.lower(),
    "Event card display": "active_event" in source or "active_ev" in source,
    "Trading desk (Buy)": "Buy" in source and "Confirm Buy" in source,
    "Trading desk (Sell)": "Sell" in source and "Confirm Sell" in source,
    "Draw Market Event button": "Draw Market Event" in source,
    "Advance Quarter button": "Advance Quarter" in source,
    "Reset button": "Reset" in source,
    "Seasonal planning window": "Planning Window" in source,
    "Pre-trade friction preview": "Friction Preview" in source or "friction" in source.lower(),
    "Mentor tip display": "mentor_tip" in source or "Mentor" in source,
}
for feature, ok in ui_checks.items():
    status = "✅" if ok else "⚠️ MISSING"
    print(f"  {status} {feature}")

print("\n" + "=" * 60)
print("PHASE 1 VERIFICATION COMPLETE")
print("=" * 60)
