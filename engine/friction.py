"""
MarketSense AI Real-World Friction Calculator
Computes:
- Short-Term Capital Gains Tax (STCG: 25% if held < 4 quarters)
- Long-Term Capital Gains Tax (LTCG: 10% if held >= 4 quarters)
- Brokerage & Exchange Fees (0.15% per trade)
- Pre-trade friction drag analytics and mentor optimization tips
"""
from typing import Dict, Any

DEFAULT_BROKERAGE_FEE = 0.0015  # 0.15%
DEFAULT_STCG_RATE = 0.25        # 25%
DEFAULT_LTCG_RATE = 0.10        # 10%

def preview_sell_friction(
    units: float,
    current_price: float,
    avg_cost: float,
    quarters_held: int,
    fee_rate: float = DEFAULT_BROKERAGE_FEE,
    stcg_rate: float = DEFAULT_STCG_RATE,
    ltcg_rate: float = DEFAULT_LTCG_RATE
) -> Dict[str, Any]:
    """
    Computes exact friction breakdown before a sell order is executed.
    """
    gross_proceeds = units * current_price
    cost_basis = units * avg_cost
    realized_gain = gross_proceeds - cost_basis

    brokerage_fee = gross_proceeds * fee_rate
    tax = 0.0
    tax_type = "No Capital Gain"

    if realized_gain > 0:
        if quarters_held >= 4:
            tax_rate = ltcg_rate
            tax_type = f"LTCG ({int(ltcg_rate * 100)}%)"
        else:
            tax_rate = stcg_rate
            tax_type = f"STCG ({int(stcg_rate * 100)}%)"
        tax = realized_gain * tax_rate

    net_proceeds = gross_proceeds - brokerage_fee - tax
    total_friction = brokerage_fee + tax
    friction_pct = (total_friction / gross_proceeds * 100.0) if gross_proceeds > 0 else 0.0

    # Pedagogical Mentor Advice
    if realized_gain > 0 and quarters_held < 4:
        quarters_left = 4 - quarters_held
        mentor_tip = (
            f"Holding this asset for {quarters_left} more quarter(s) will qualify you for the "
            f"Long-Term Capital Gains discount (tax drops from 25% to 10%), saving you S${(realized_gain * (stcg_rate - ltcg_rate)):,.2f}."
        )
    elif realized_gain <= 0:
        mentor_tip = "Selling at a loss triggers zero capital gains tax, but locks in permanent capital destruction."
    else:
        mentor_tip = "Congratulations on holding for >= 1 year! You unlocked the discounted 10% LTCG rate."

    return {
        "gross_proceeds": round(gross_proceeds, 2),
        "cost_basis": round(cost_basis, 2),
        "realized_gain": round(realized_gain, 2),
        "tax_type": tax_type,
        "estimated_tax": round(tax, 2),
        "brokerage_fee": round(brokerage_fee, 2),
        "total_friction": round(total_friction, 2),
        "friction_pct": round(friction_pct, 2),
        "net_proceeds": round(net_proceeds, 2),
        "mentor_tip": mentor_tip
    }

def preview_buy_friction(amount_sgd: float, fee_rate: float = DEFAULT_BROKERAGE_FEE) -> Dict[str, Any]:
    """Computes brokerage fee for buy order."""
    fee = amount_sgd * fee_rate
    return {
        "amount_invested": round(amount_sgd, 2),
        "brokerage_fee": round(fee, 2),
        "total_cash_required": round(amount_sgd + fee, 2)
    }
