"""
MarketSense AI Passive Parallel Benchmark Tracker
Tracks three institutional reference portfolios alongside the trainee:
1. 100% Equity Benchmark (Unhedged pure equity market)
2. Traditional 60/40 Portfolio (60% Equities, 40% Sovereign Bonds)
3. Ray Dalio All-Weather Portfolio (Risk Parity across Equities, Long Bonds, Short Bonds, Gold, Commodities)
"""
from typing import Dict, List, Any

class BenchmarkTracker:
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        
        # Portfolio values
        self.nav_100_equity = initial_capital
        self.nav_60_40 = initial_capital
        self.nav_all_weather = initial_capital

        # History log
        self.history = [{
            "quarter": 0,
            "100_equity": initial_capital,
            "60_40": initial_capital,
            "all_weather": initial_capital
        }]

    def update(
        self,
        pct_changes: Dict[str, float],
        assets: List[Dict[str, Any]],
        quarter: int
    ) -> Dict[str, float]:
        """
        Updates benchmark NAVs based on quarterly asset price movements.
        """
        equity_changes = [
            pct_changes.get(a["id"], 0.0)
            for a in assets if a["asset_class"] == "Equities"
        ]
        avg_equity_return = sum(equity_changes) / len(equity_changes) if equity_changes else 0.0

        tbill_return = pct_changes.get("FI_TBILL_SHORT", 0.01)
        long_bond_return = pct_changes.get("FI_BOND_LONG", 0.0)
        gold_return = pct_changes.get("COMM_GOLD", 0.0)
        energy_return = pct_changes.get("EQ_NRG_LC", 0.0)

        # 1. 100% Equity Benchmark
        self.nav_100_equity *= (1.0 + avg_equity_return)

        # 2. Traditional 60/40 (60% Equities, 20% Short T-Bills, 20% Long Bonds)
        ret_60_40 = (0.60 * avg_equity_return) + (0.20 * tbill_return) + (0.20 * long_bond_return)
        self.nav_60_40 *= (1.0 + ret_60_40)

        # 3. Ray Dalio All-Weather (30% Equities, 40% Long Bonds, 15% Short T-Bills, 7.5% Gold, 7.5% Commodities)
        ret_all_weather = (
            (0.30 * avg_equity_return) +
            (0.40 * long_bond_return) +
            (0.15 * tbill_return) +
            (0.075 * gold_return) +
            (0.075 * energy_return)
        )
        self.nav_all_weather *= (1.0 + ret_all_weather)

        record = {
            "quarter": quarter,
            "100_equity": round(self.nav_100_equity, 2),
            "60_40": round(self.nav_60_40, 2),
            "all_weather": round(self.nav_all_weather, 2)
        }
        self.history.append(record)
        return record

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history
