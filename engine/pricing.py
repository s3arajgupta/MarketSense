"""
MarketSense AI Deterministic Financial Pricing Engine
Implements mathematically grounded pricing models combining:
- Macro shock inputs from crisis cards
- Sector sensitivities (Beta, Debt-to-Equity, Cash Resilience, Cap Size)
- Stochastic noise bounds (no unconstrained LLM price hallucinations)
"""
import random
from typing import Dict, List, Any, Optional

CAP_SIZE_MULTIPLIERS = {
    "Large": 1.00,
    "Mid": 1.15,
    "Small": 1.35,
    "N/A": 1.00
}

def calculate_new_prices(
    current_prices: Dict[str, float],
    event: Dict[str, Any],
    assets: List[Dict[str, Any]],
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculates updated asset prices after an event shock.
    Returns:
        {
            'new_prices': {asset_id: new_price},
            'pct_changes': {asset_id: pct_change},
            'sector_changes': {sector_name: avg_pct_change}
        }
    """
    if seed is not None:
        random.seed(seed)

    sector_impacts = event.get("sector_impacts", {})
    asset_impacts = event.get("asset_impacts", {})

    new_prices = {}
    pct_changes = {}
    sector_sums = {}
    sector_counts = {}

    for asset in assets:
        a_id = asset["id"]
        cur_price = current_prices.get(a_id, asset.get("base_price", 100.0))
        a_class = asset["asset_class"]
        sector = asset["sector"]
        market_cap = asset.get("market_cap", "N/A")
        beta = asset.get("beta", 1.0)
        debt_ratio = asset.get("debt_ratio", 0.0)
        cash_resilience = asset.get("cash_resilience", 1.0)

        # Baseline microscopic noise (+/- 0.5%)
        noise = random.uniform(-0.005, 0.005)

        if a_class == "Equities":
            base_sector_shift = sector_impacts.get(sector, 0.0)
            cap_mult = CAP_SIZE_MULTIPLIERS.get(market_cap, 1.0)

            if base_sector_shift < 0:
                # Debt amplifies downturn; Cash buffers it
                debt_penalty = max(0.0, debt_ratio - 0.40) * 0.35
                cash_buffer = cash_resilience * 0.20
                multiplier = 1.0 + debt_penalty - cash_buffer
                pct_change = (beta * base_sector_shift * cap_mult * multiplier) + noise
            else:
                # Growth upside; cash enables expansion
                multiplier = 1.0 + (cash_resilience * 0.10)
                pct_change = (beta * base_sector_shift * cap_mult * multiplier) + noise

        elif a_class == "Commodities":
            base_shift = asset_impacts.get(a_id, 0.0)
            pct_change = base_shift + noise

        elif a_class == "Fixed Income":
            base_shift = asset_impacts.get(a_id, 0.0)
            pct_change = base_shift + (noise * 0.2)

        elif a_class == "Cash Equivalents":
            # Cash principal does not decline; maintains floor
            pct_change = max(0.0, asset_impacts.get(a_id, 0.01) + (noise * 0.1))

        elif a_class == "Digital Assets":
            base_shift = asset_impacts.get(a_id, 0.0)
            pct_change = (base_shift * beta) + (noise * 2.0)

        else:
            pct_change = noise

        # Safety bound: max single-quarter drop capped at -85%
        pct_change = max(-0.85, pct_change)

        new_price = max(0.01, cur_price * (1.0 + pct_change))
        new_prices[a_id] = round(new_price, 2)
        pct_changes[a_id] = round(pct_change, 4)

        # Accumulate sector statistics
        sector_sums[sector] = sector_sums.get(sector, 0.0) + pct_change
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    sector_changes = {
        sec: round(sector_sums[sec] / sector_counts[sec], 4)
        for sec in sector_sums
    }

    return {
        "new_prices": new_prices,
        "pct_changes": pct_changes,
        "sector_changes": sector_changes
    }
