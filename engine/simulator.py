"""
MarketSense AI — Multi-Quarter Time Travel & Batch Simulation Engine
Simulates multi-year / multi-decade forward trajectories in milliseconds.
"""
from typing import Dict, List, Any, Optional
from engine.portfolio import Portfolio
from engine.benchmarks import BenchmarkTracker
from engine.pricing import calculate_new_prices


def simulate_multi_quarters(
    portfolio: Portfolio,
    benchmarks: BenchmarkTracker,
    current_prices: Dict[str, float],
    events_list: List[Dict[str, Any]],
    assets_list: List[Dict[str, Any]],
    quarters_to_advance: int,
    start_event_idx: int = 0,
    rebalance_annually: bool = False,
    target_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Executes an instantaneous forward warp across N quarters.
    Handles macro price shocks, dividend compounding, tax holding periods,
    benchmarks, and cumulative CPI purchasing power hurdles.
    """
    total_events = len(events_list)
    curr_p = dict(current_prices)
    last_calc_res = None
    rebalance_count = 0

    for i in range(quarters_to_advance):
        ev_idx = (start_event_idx + i) % total_events
        ev = events_list[ev_idx]

        calc_res = calculate_new_prices(curr_p, ev, assets_list)
        curr_p = calc_res["new_prices"]
        last_calc_res = calc_res

        ev_inflation = ev.get("annualized_inflation", 0.025)
        benchmarks.update(
            calc_res["pct_changes"],
            assets_list,
            portfolio.current_quarter + 1,
            annualized_inflation=ev_inflation,
        )

        portfolio.advance_quarter(
            curr_p,
            assets_list,
            ev.get("title", ev.get("name", "Market Event")),
        )

        # Annual institutional rebalancing at every 4th quarter (Q4, Q8, Q12...)
        if rebalance_annually and target_weights and (portfolio.current_quarter % 4 == 0):
            portfolio.rebalance(target_weights, curr_p)
            rebalance_count += 1

    final_nav = portfolio.get_nav(curr_p)
    total_return_pct = ((final_nav - portfolio.initial_cash) / portfolio.initial_cash) * 100.0
    real_return_pct = benchmarks.get_real_return_pct(total_return_pct)

    last_event = events_list[(start_event_idx + quarters_to_advance - 1) % total_events]

    return {
        "quarters_advanced": quarters_to_advance,
        "years_advanced": round(quarters_to_advance / 4.0, 1),
        "new_event_queue_idx": start_event_idx + quarters_to_advance,
        "final_prices": curr_p,
        "last_event": last_event,
        "last_pct_changes": last_calc_res["pct_changes"] if last_calc_res else {},
        "last_sector_changes": last_calc_res["sector_changes"] if last_calc_res else {},
        "final_nav": final_nav,
        "total_return_pct": round(total_return_pct, 2),
        "real_return_pct": round(real_return_pct, 2),
        "max_drawdown_portfolio": portfolio.get_max_drawdown(),
        "max_drawdowns_benchmarks": benchmarks.get_max_drawdowns(),
        "rebalances_performed": rebalance_count,
        "cpi_hurdle": benchmarks.cpi_hurdle,
        "cum_cpi_pct": benchmarks.get_history()[-1].get("cumulative_cpi_pct", 0.0),
    }
