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
        self.cpi_hurdle = initial_capital  # Purchasing power baseline

        # History log
        self.history = [{
            "quarter": 0,
            "100_equity": initial_capital,
            "60_40": initial_capital,
            "all_weather": initial_capital,
            "cpi_hurdle": initial_capital,
            "cumulative_cpi_pct": 0.0,
            "quarterly_cpi_annualized": 0.0,
        }]

    def update(
        self,
        pct_changes: Dict[str, float],
        assets: List[Dict[str, Any]],
        quarter: int,
        annualized_inflation: float = 0.025,
    ) -> Dict[str, float]:
        """
        Updates benchmark NAVs and the CPI hurdle based on quarterly asset price movements
        and macroeconomic inflation.
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

        # 4. CPI Inflation Hurdle (Compounded quarterly from annualized rate)
        quarterly_cpi = (1.0 + annualized_inflation) ** 0.25 - 1.0
        self.cpi_hurdle *= (1.0 + quarterly_cpi)
        cum_cpi_pct = ((self.cpi_hurdle - self.initial_capital) / self.initial_capital) * 100.0

        record = {
            "quarter": quarter,
            "100_equity": round(self.nav_100_equity, 2),
            "60_40": round(self.nav_60_40, 2),
            "all_weather": round(self.nav_all_weather, 2),
            "cpi_hurdle": round(self.cpi_hurdle, 2),
            "cumulative_cpi_pct": round(cum_cpi_pct, 2),
            "quarterly_cpi_annualized": round(annualized_inflation * 100.0, 1),
        }
        self.history.append(record)
        return record

    def get_real_return_pct(self, nominal_return_pct: float) -> float:
        """
        Calculates inflation-adjusted real return using the Fisher equation:
        Real Return = ((1 + Nominal Return) / (1 + Cumulative Inflation) - 1) * 100
        """
        cum_cpi_pct = ((self.cpi_hurdle - self.initial_capital) / self.initial_capital) * 100.0
        if cum_cpi_pct <= -100.0:
            return nominal_return_pct
        real_ret = ((1.0 + nominal_return_pct / 100.0) / (1.0 + cum_cpi_pct / 100.0) - 1.0) * 100.0
        return round(real_ret, 2)

    def get_max_drawdowns(self) -> Dict[str, float]:
        """Calculates maximum peak-to-trough drawdowns for all reference benchmarks."""
        benchmarks = ["100_equity", "60_40", "all_weather"]
        max_dds = {b: 0.0 for b in benchmarks}
        peaks = {b: self.initial_capital for b in benchmarks}

        for record in self.history:
            for b in benchmarks:
                val = record.get(b, self.initial_capital)
                if val > peaks[b]:
                    peaks[b] = val
                elif peaks[b] > 0:
                    dd = (peaks[b] - val) / peaks[b] * 100.0
                    if dd > max_dds[b]:
                        max_dds[b] = dd

        return {k: round(v, 2) for k, v in max_dds.items()}

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history
