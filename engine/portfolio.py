"""
MarketSense AI Portfolio State & Trade Management Engine
Handles:
- Multi-asset holdings & cash tracking in SGD
- Buy / Sell execution with friction hooks
- Quarterly dividend distribution & cash interest compounding
- Holding period tracking for STCG vs. LTCG classification
- NAV snapshots for historical benchmarking
"""
from typing import Dict, List, Any, Optional

class Portfolio:
    def __init__(self, initial_cash: float = 100000.0, base_currency: str = "SGD"):
        self.initial_cash = float(initial_cash)
        self.cash = float(initial_cash)
        self.base_currency = base_currency
        self.holdings: Dict[str, Dict[str, Any]] = {}
        self.current_quarter = 0
        self.history: List[Dict[str, Any]] = []
        self.total_tax_paid = 0.0
        self.total_brokerage_paid = 0.0
        self.total_dividends_earned = 0.0

    def get_nav(self, current_prices: Dict[str, float]) -> float:
        """Calculates total Net Asset Value (Cash + Market Value of all holdings)."""
        holdings_val = sum(
            h["units"] * current_prices.get(a_id, h["avg_cost"])
            for a_id, h in self.holdings.items()
            if h["units"] > 0
        )
        return round(self.cash + holdings_val, 2)

    def get_holdings_breakdown(
        self, current_prices: Dict[str, float], assets_meta: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Returns structured ledger rows for UI display."""
        total_nav = self.get_nav(current_prices)
        meta = assets_meta or {}
        breakdown = []

        # Cash row
        cash_weight = round((self.cash / total_nav) * 100.0, 2) if total_nav > 0 else 100.0
        breakdown.append({
            "asset_id": "CASH-SGD",
            "name": "Liquid Cash & SGD Money Market",
            "asset_class": "Cash Equivalents",
            "sector": "Cash Equivalents",
            "units": round(self.cash, 2),
            "avg_cost": 1.0,
            "current_price": 1.0,
            "market_value": round(self.cash, 2),
            "weight_pct": cash_weight,
            "unrealized_pnl": 0.0,
            "unrealized_pnl_pct": 0.0,
            "quarters_held": self.current_quarter,
            "tax_status": "N/A"
        })

        for a_id, h in self.holdings.items():
            if h["units"] <= 0:
                continue
            cur_price = current_prices.get(a_id, h["avg_cost"])
            mkt_val = round(h["units"] * cur_price, 2)
            cost_basis = round(h["units"] * h["avg_cost"], 2)
            pnl = round(mkt_val - cost_basis, 2)
            pnl_pct = round((pnl / cost_basis) * 100.0, 2) if cost_basis > 0 else 0.0
            weight = round((mkt_val / total_nav) * 100.0, 2) if total_nav > 0 else 0.0
            tax_status = "LTCG (10%)" if h["quarters_held"] >= 4 else "STCG (25%)"

            info = meta.get(a_id, {})
            breakdown.append({
                "asset_id": a_id,
                "name": info.get("name", a_id),
                "asset_class": info.get("asset_class", "Equities"),
                "sector": info.get("sector", "Other"),
                "units": round(h["units"], 4),
                "avg_cost": round(h["avg_cost"], 2),
                "current_price": round(cur_price, 2),
                "market_value": mkt_val,
                "weight_pct": weight,
                "unrealized_pnl": pnl,
                "unrealized_pnl_pct": pnl_pct,
                "quarters_held": h["quarters_held"],
                "tax_status": tax_status
            })

        return breakdown

    def buy(
        self, asset_id: str, amount_sgd: float, current_price: float, fee_rate: float = 0.0015
    ) -> Dict[str, Any]:
        """Executes a buy order funded from cash."""
        if amount_sgd <= 0:
            return {"success": False, "message": "Investment amount must be positive."}
        if current_price <= 0:
            return {"success": False, "message": "Invalid current price."}

        fee = amount_sgd * fee_rate
        total_required = amount_sgd + fee

        if total_required > self.cash:
            return {
                "success": False,
                "message": f"Insufficient cash. Required: S${total_required:,.2f}, Available: S${self.cash:,.2f}"
            }

        units_bought = amount_sgd / current_price
        self.cash -= total_required
        self.total_brokerage_paid += fee

        if asset_id in self.holdings and self.holdings[asset_id]["units"] > 0:
            existing = self.holdings[asset_id]
            total_units = existing["units"] + units_bought
            total_cost = (existing["units"] * existing["avg_cost"]) + amount_sgd
            existing["avg_cost"] = total_cost / total_units
            existing["units"] = total_units
        else:
            self.holdings[asset_id] = {
                "units": units_bought,
                "avg_cost": current_price,
                "quarters_held": 0
            }

        return {
            "success": True,
            "units_bought": units_bought,
            "amount_spent": amount_sgd,
            "fee_paid": fee,
            "remaining_cash": self.cash
        }

    def sell(
        self,
        asset_id: str,
        units_to_sell: float,
        current_price: float,
        fee_rate: float = 0.0015,
        stcg_rate: float = 0.25,
        ltcg_rate: float = 0.10
    ) -> Dict[str, Any]:
        """Executes a sell order, applying capital gains tax and brokerage fees."""
        if asset_id not in self.holdings or self.holdings[asset_id]["units"] <= 0:
            return {"success": False, "message": "Position not held."}

        existing = self.holdings[asset_id]
        if units_to_sell > existing["units"]:
            units_to_sell = existing["units"]

        gross_proceeds = units_to_sell * current_price
        cost_basis = units_to_sell * existing["avg_cost"]
        realized_gain = gross_proceeds - cost_basis

        brokerage_fee = gross_proceeds * fee_rate
        tax = 0.0

        if realized_gain > 0:
            tax_rate = ltcg_rate if existing["quarters_held"] >= 4 else stcg_rate
            tax = realized_gain * tax_rate

        net_proceeds = gross_proceeds - brokerage_fee - tax
        self.cash += net_proceeds
        self.total_tax_paid += tax
        self.total_brokerage_paid += brokerage_fee

        existing["units"] -= units_to_sell
        if existing["units"] <= 0.00001:
            del self.holdings[asset_id]

        return {
            "success": True,
            "units_sold": units_to_sell,
            "gross_proceeds": round(gross_proceeds, 2),
            "realized_gain": round(realized_gain, 2),
            "tax_paid": round(tax, 2),
            "fee_paid": round(brokerage_fee, 2),
            "net_proceeds": round(net_proceeds, 2),
            "remaining_cash": round(self.cash, 2)
        }

    def advance_quarter(
        self,
        current_prices: Dict[str, float],
        assets_list: List[Dict[str, Any]],
        event_title: str = "Market Quarter"
    ) -> Dict[str, Any]:
        """
        Advances the quarter:
        - Accrues quarterly cash money market interest (3.8% p.a. / 4)
        - Accrues quarterly equity/bond dividends
        - Increments holding period count for all positions
        - Appends historical snapshot
        """
        self.current_quarter += 1

        # 1. Cash interest
        quarterly_cash_rate = 0.038 / 4.0
        cash_interest = self.cash * quarterly_cash_rate
        self.cash += cash_interest

        # 2. Dividends
        meta_dict = {a["id"]: a for a in assets_list}
        quarterly_dividends = 0.0

        for a_id, h in self.holdings.items():
            if h["units"] <= 0:
                continue
            cur_price = current_prices.get(a_id, h["avg_cost"])
            ann_yield = meta_dict.get(a_id, {}).get("dividend_yield", 0.0)
            quarterly_div = h["units"] * cur_price * (ann_yield / 4.0)
            quarterly_dividends += quarterly_div
            h["quarters_held"] += 1

        self.cash += quarterly_dividends
        self.total_dividends_earned += (cash_interest + quarterly_dividends)

        # 3. Snapshot for charts
        nav = self.get_nav(current_prices)
        snapshot = {
            "quarter": self.current_quarter,
            "nav": nav,
            "cash": round(self.cash, 2),
            "event_title": event_title,
            "total_return_pct": round(((nav - self.initial_cash) / self.initial_cash) * 100.0, 2),
            "dividends_this_qtr": round(cash_interest + quarterly_dividends, 2)
        }
        self.history.append(snapshot)

        return snapshot
