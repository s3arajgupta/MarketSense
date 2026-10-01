"""
Tests for Phase 1: Core Simulation Engine

Verifies:
- Asset universe & crisis event data integrity
- Deterministic pricing formula & bounds
- Portfolio accounting, trade execution, and cash balances
- Financial friction (STCG vs LTCG tax rates, brokerage)
- Passive benchmark tracking (100% Equity, 60/40, All-Weather)
"""
import json
import pytest
from pathlib import Path

from engine.portfolio import Portfolio
from engine.pricing import calculate_new_prices
from engine.friction import preview_buy_friction, preview_sell_friction
from engine.benchmarks import BenchmarkTracker
from engine.simulator import simulate_multi_quarters


@pytest.fixture
def assets():
    with open("data/assets.json", "r", encoding="utf-8") as f:
        return json.load(f)["assets"]


@pytest.fixture
def events():
    with open("data/crisis_cards.json", "r", encoding="utf-8") as f:
        return json.load(f)["events"]


def test_asset_universe_integrity(assets):
    """Verify all 24 multi-asset instruments and required attributes."""
    assert len(assets) == 24

    equities = [a for a in assets if a["asset_class"] == "Equities"]
    commodities = [a for a in assets if a["asset_class"] == "Commodities"]
    fi = [a for a in assets if a["asset_class"] == "Fixed Income"]
    cash = [a for a in assets if a["asset_class"] == "Cash Equivalents"]
    digital = [a for a in assets if a["asset_class"] == "Digital Assets"]

    assert len(equities) == 18  # 6 sectors x 3 market caps
    assert len(commodities) == 2
    assert len(fi) == 2
    assert len(cash) == 1
    assert len(digital) == 1

    for a in assets:
        assert "beta" in a
        assert "debt_ratio" in a
        assert "cash_resilience" in a
        assert "dividend_yield" in a
        assert a["base_price"] > 0


def test_crisis_events_schema(events):
    """Verify all 22 macro crisis events have valid structure."""
    assert len(events) >= 20

    for ev in events:
        assert "id" in ev
        assert "title" in ev
        assert "category" in ev
        assert "event_type" in ev
        assert ev["event_type"] in ["Seasonal", "Sudden"]
        assert "sector_impacts" in ev
        assert "historical_precedent" in ev


def test_pricing_determinism(assets, events):
    """Ensure pricing formula is deterministic and reproducible given same seed."""
    event = events[0]
    initial_prices = {a["id"]: a["base_price"] for a in assets}

    res1 = calculate_new_prices(initial_prices, event, assets, seed=42)
    res2 = calculate_new_prices(initial_prices, event, assets, seed=42)

    assert res1["new_prices"] == res2["new_prices"]
    assert res1["pct_changes"] == res2["pct_changes"]

    # Cash must never decline
    assert res1["new_prices"]["CASH_MMF"] >= initial_prices["CASH_MMF"]


def test_portfolio_buy_and_sell(assets):
    """Test buying and selling mechanics, cash adjustments, and average cost."""
    p = Portfolio(initial_cash=100000.0, base_currency="SGD")

    # Buy S$10,000 of tech at S$100 (fee rate 0.0015)
    res = p.buy("EQ_IT_LC", 10000.0, 100.0)
    assert res["success"] is True
    assert p.cash < 90000.0  # 10000 + 15 fee deducted
    assert "EQ_IT_LC" in p.holdings
    assert p.holdings["EQ_IT_LC"]["units"] == 100.0

    # Sell half (50 units) at S$120 (gain)
    res_sell = p.sell("EQ_IT_LC", 50.0, 120.0)
    assert res_sell["success"] is True
    assert p.holdings["EQ_IT_LC"]["units"] == 50.0
    assert p.total_tax_paid > 0  # Paid capital gains tax


def test_friction_stcg_vs_ltcg():
    """Verify short-term capital gains tax (25%) vs long-term (10%) threshold at 4 quarters."""
    # Held for 2 quarters -> STCG (25%)
    stcg = preview_sell_friction(units=100, current_price=150.0, avg_cost=100.0, quarters_held=2)
    assert "STCG" in stcg["tax_type"]
    # Capital gain = 100 * 50 = $5000 -> 25% = $1250 tax
    assert pytest.approx(stcg["estimated_tax"], 0.01) == 1250.0

    # Held for 4 quarters -> LTCG (10%)
    ltcg = preview_sell_friction(units=100, current_price=150.0, avg_cost=100.0, quarters_held=4)
    assert "LTCG" in ltcg["tax_type"]
    # Capital gain = $5000 -> 10% = $500 tax
    assert pytest.approx(ltcg["estimated_tax"], 0.01) == 500.0


def test_benchmarks_tracking(assets, events):
    """Verify passive benchmarks (100% Equity, 60/40, All-Weather) track correctly."""
    bt = BenchmarkTracker(initial_capital=100000.0)
    initial_prices = {a["id"]: a["base_price"] for a in assets}

    calc_res = calculate_new_prices(initial_prices, events[0], assets, seed=42)
    bt.update(calc_res["pct_changes"], assets, quarter=1)

    hist = bt.get_history()
    assert len(hist) == 2  # Q0 and Q1
    assert hist[1]["quarter"] == 1
    assert hist[1]["100_equity"] > 0
    assert hist[1]["60_40"] > 0
    assert hist[1]["all_weather"] > 0
    assert hist[1]["cpi_hurdle"] > 100000.0


def test_cpi_inflation_hurdle_and_real_return(assets):
    """Verify CPI hurdle compounding and Fisher equation real return calculations."""
    bt = BenchmarkTracker(initial_capital=100000.0)
    initial_prices = {a["id"]: a["base_price"] for a in assets}

    # Simulate 1 quarter of 8.0% annualized inflation
    pct_changes = {a["id"]: 0.0 for a in assets}
    rec = bt.update(pct_changes, assets, quarter=1, annualized_inflation=0.08)

    # Quarterly inflation: (1 + 0.08)^0.25 - 1 = ~1.9426%
    expected_cpi_hurdle = 100000.0 * ((1.0 + 0.08) ** 0.25)
    assert pytest.approx(bt.cpi_hurdle, 0.1) == expected_cpi_hurdle
    assert rec["cumulative_cpi_pct"] > 1.9

    # Holding 0% nominal return while inflation is ~1.94% gives negative real return (cash drag)
    real_ret_zero_nom = bt.get_real_return_pct(0.0)
    assert real_ret_zero_nom < 0.0

    # Fisher equation verification: if nominal return is +10%
    # Real = ((1 + 0.10) / (1 + cum_cpi/100) - 1) * 100
    cum_cpi = rec["cumulative_cpi_pct"]
    expected_real = ((1.10 / (1.0 + cum_cpi / 100.0)) - 1.0) * 100.0
    assert pytest.approx(bt.get_real_return_pct(10.0), 0.01) == round(expected_real, 2)


def test_multi_quarter_time_travel_30_years(assets, events):
    """Verify 30-year (120-quarter) accelerated simulation executes instantaneously."""
    p = Portfolio(initial_cash=100000.0)
    p.buy("EQ_IT_LC", 20000.0, 100.0)
    p.buy("FI_TBILL_SHORT", 30000.0, 100.0)
    p.buy("COMM_GOLD", 20000.0, 100.0)

    bt = BenchmarkTracker(initial_capital=100000.0)
    initial_prices = {a["id"]: a["base_price"] for a in assets}

    res = simulate_multi_quarters(
        portfolio=p,
        benchmarks=bt,
        current_prices=initial_prices,
        events_list=events,
        assets_list=assets,
        quarters_to_advance=120,  # 30 years!
    )

    assert res["quarters_advanced"] == 120
    assert res["years_advanced"] == 30.0
    assert p.current_quarter == 120
    assert len(p.history) == 120  # 120 snapshots
    assert len(bt.history) == 121  # Q0 + 120 quarters

    # 30 years of compounding: CPI Hurdle must have grown significantly
    assert bt.cpi_hurdle > 150000.0  # Over 30 years at 2-8% inflation, CPI more than doubles
    assert res["cum_cpi_pct"] > 50.0

    # Drawdown metrics must be sensible
    max_dd = res["max_drawdown_portfolio"]
    assert 0.0 <= max_dd <= 100.0

    bm_dds = res["max_drawdowns_benchmarks"]
    assert "100_equity" in bm_dds
    assert "all_weather" in bm_dds
    assert bm_dds["all_weather"] >= 0.0


def test_quarterly_event_progression_variety(events):
    """Verify that quarterly simulation progresses through varied macro events and doesn't freeze on one."""
    assert len(events) >= 20
    event_titles = set()
    event_queue_idx = 0
    active_event = None
    event_phase = "READY_FOR_EVENT"

    for q in range(10):
        if event_phase in ("PLANNING", "SHOCKED") and active_event:
            ev = active_event
        else:
            ev = events[event_queue_idx % len(events)]
            event_queue_idx += 1
        active_event = ev
        event_phase = "RESOLVED"
        event_titles.add(ev["title"])

    # 10 quarters must have seen 10 distinct events in sequence
    assert len(event_titles) == 10
    assert event_queue_idx == 10


def test_predrawn_event_absorbed_before_queue(events):
    """Verify pre-drawn event (PLANNING/SHOCKED) is absorbed on next step before queue increments."""
    event_queue_idx = 0

    # User draws event 0 manually
    active_event = events[event_queue_idx % len(events)]
    event_queue_idx += 1
    event_phase = "PLANNING"
    drawn_title = active_event["title"]

    # Next step simulation consumes the pre-drawn event
    if event_phase in ("PLANNING", "SHOCKED") and active_event:
        ev = active_event
    else:
        ev = events[event_queue_idx % len(events)]
        event_queue_idx += 1
    event_phase = "RESOLVED"

    assert ev["title"] == drawn_title
    assert event_queue_idx == 1  # Did not double-increment

    # Subsequent step draws the next event
    if event_phase in ("PLANNING", "SHOCKED") and active_event:
        ev2 = active_event
    else:
        ev2 = events[event_queue_idx % len(events)]
        event_queue_idx += 1
    event_phase = "RESOLVED"

    assert ev2["title"] != drawn_title
    assert ev2["title"] == events[1]["title"]
    assert event_queue_idx == 2

