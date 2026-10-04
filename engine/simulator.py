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


COUNTERFACTUAL_STRATEGIES = {
    "all_weather": {
        "name": "Ray Dalio All-Weather",
        "description": "30% Equities, 40% Long Bonds, 15% Short T-Bills, 7.5% Gold, 7.5% Commodities",
        "weights": {
            "EQ_IT_LC": 0.05,
            "EQ_BNK_LC": 0.05,
            "EQ_NRG_LC": 0.05,
            "EQ_FMCG_LC": 0.05,
            "EQ_HLT_LC": 0.05,
            "EQ_EST_LC": 0.05,
            "FI_BOND_LONG": 0.40,
            "FI_TBILL_SHORT": 0.15,
            "COMM_GOLD": 0.075,
            "COMM_SILVER": 0.075,
        },
    },
    "pure_cash": {
        "name": "100% Cash MMF",
        "description": "100% Liquid SGD Money Market Fund with quarterly cash interest accrual",
        "weights": {
            "CASH_MMF": 1.00,
        },
    },
    "gold_defense": {
        "name": "Precious Metals Defensive",
        "description": "35% Physical Gold, 15% Silver, 30% Sovereign T-Bills, 20% Cash MMF",
        "weights": {
            "COMM_GOLD": 0.35,
            "COMM_SILVER": 0.15,
            "FI_TBILL_SHORT": 0.30,
            "CASH_MMF": 0.20,
        },
    },
    "tech_aggressive": {
        "name": "Aggressive Tech & Innovation",
        "description": "50% Tech Large-Cap, 20% Tech Mid-Cap, 10% Crypto ETF, 20% Cash MMF",
        "weights": {
            "EQ_IT_LC": 0.50,
            "EQ_IT_MC": 0.20,
            "CRYPTO_BENCH": 0.10,
            "CASH_MMF": 0.20,
        },
    },
}


def compute_counterfactual(
    capital: float,
    event: Dict[str, Any],
    current_prices: Dict[str, float],
    assets_list: List[Dict[str, Any]],
    user_actual_return_pct: float,
    strategy: str = "all_weather",
    custom_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Computes deterministic counterfactual 'What-If' outcome under the active event shock.

    Answers: What would the trainee's portfolio NAV and return have been under
    an alternative institutional allocation strategy during the exact same macro shock?
    """
    if custom_weights:
        strat_name = "Custom Allocation"
        strat_desc = "User-defined counterfactual weights"
        weights = custom_weights
    else:
        cfg = COUNTERFACTUAL_STRATEGIES.get(strategy, COUNTERFACTUAL_STRATEGIES["all_weather"])
        strat_name = cfg["name"]
        strat_desc = cfg["description"]
        weights = cfg["weights"]

    calc_res = calculate_new_prices(current_prices, event, assets_list)
    pct_changes = calc_res["pct_changes"]

    # Normalize weights to sum to 1.0
    total_w = sum(weights.values()) if weights else 1.0
    normalized_weights = {k: v / total_w for k, v in weights.items()} if total_w > 0 else {}

    # Compute weighted return
    quarterly_returns = {}
    weighted_return = 0.0

    for aid, w in normalized_weights.items():
        if aid == "CASH_MMF":
            # Cash earns 3.8% p.a. / 4 quarterly = 0.95%
            ret = 0.038 / 4.0
        else:
            ret = pct_changes.get(aid, 0.0)
        quarterly_returns[aid] = round(ret * 100.0, 2)
        weighted_return += w * ret

    cf_return_pct = round(weighted_return * 100.0, 2)
    cf_nav = round(capital * (1.0 + weighted_return), 2)
    actual_nav = round(capital * (1.0 + user_actual_return_pct / 100.0), 2)
    diff_nav = round(actual_nav - cf_nav, 2)
    diff_return_pct = round(user_actual_return_pct - cf_return_pct, 2)

    if diff_return_pct > 0.05:
        verdict = f"Active Portfolio Outperformed by +{diff_return_pct:.2f}%"
        sentiment = "positive"
    elif diff_return_pct < -0.05:
        verdict = f"Counterfactual Outperformed by {abs(diff_return_pct):.2f}%"
        sentiment = "negative"
    else:
        verdict = "Parity (Comparable Return)"
        sentiment = "neutral"

    return {
        "strategy": strategy,
        "strategy_name": strat_name,
        "strategy_description": strat_desc,
        "weights": normalized_weights,
        "capital_base": round(capital, 2),
        "actual_nav": actual_nav,
        "actual_return_pct": round(user_actual_return_pct, 2),
        "counterfactual_nav": cf_nav,
        "counterfactual_return_pct": cf_return_pct,
        "diff_nav": diff_nav,
        "diff_return_pct": diff_return_pct,
        "verdict": verdict,
        "sentiment": sentiment,
        "asset_movements": quarterly_returns,
    }

