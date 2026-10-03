"""
MarketSense — AI Mentor Orchestrator

Coordinates RAG retrieval, prompt assembly, and LLM generation
to produce grounded, cited investment mentorship.

This is the main entry point for all AI Mentor interactions.
"""
from dataclasses import dataclass
from intelligence.llm_client import LLMClient, LLMResponse, create_llm_client
from intelligence.rag_engine import RAGEngine
from intelligence.prompts import (
    SYSTEM_PROMPT_BASE,
    POST_EVENT_DEBRIEF,
    PRE_TRADE_INSIGHT,
    PORTFOLIO_HEALTH_CHECK,
    CAREER_RETROSPECTIVE,
)


@dataclass
class MentorResponse:
    """Complete mentor response with text, citations, and metadata."""
    text: str
    citations: list[dict]  # List of {source, author, text} dicts
    provider: str
    model: str
    tokens_used: int

    @property
    def has_citations(self) -> bool:
        return len(self.citations) > 0


class AIMentor:
    """
    AI Mentor — the reasoning orchestrator.

    Workflow for each interaction:
    1. Gather game context (portfolio state, event, prices)
    2. Query RAG engine for relevant wisdom chunks
    3. Assemble prompt with context + wisdom + task instructions
    4. Send to LLM provider
    5. Return structured response with citations
    """

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        rag_engine: RAGEngine | None = None,
    ):
        """
        Initialize the AI Mentor.

        Args:
            llm_client: LLM provider. If None, creates from config.
            rag_engine: RAG engine. If None, creates with default collection.
        """
        self._llm = llm_client
        self._rag = rag_engine or RAGEngine()

    @property
    def llm(self) -> LLMClient:
        """Lazy-initialize the LLM client."""
        if self._llm is None:
            self._llm = create_llm_client()
        return self._llm

    @property
    def provider_name(self) -> str:
        """Human-readable LLM provider name for UI."""
        return self.llm.provider_name

    def post_event_debrief(
        self,
        quarter: int,
        event: dict,
        price_impacts: dict,
        portfolio_state: dict,
    ) -> MentorResponse:
        """
        Generate a post-event debrief explaining what happened and why.

        Args:
            quarter: Current quarter number.
            event: The crisis event dict from crisis_cards.json.
            price_impacts: Dict of {asset_name: pct_change} from pricing engine.
            portfolio_state: Dict with nav, cash, holdings, alpha, etc.
        """
        event_id = event.get("id", "")
        event_name = event.get("title", event.get("name", "Unknown Event"))
        event_type = event.get("event_type", event.get("type", "unknown"))

        # Format price impacts for prompt
        impacts_text = self._format_price_impacts(price_impacts)

        # Format top holdings
        top_holdings = self._format_top_holdings(portfolio_state.get("holdings", []))

        # Retrieve relevant wisdom
        query = f"{event_name} {event.get('context_description', '')} {event.get('headline', '')}"
        wisdom_context = self._rag.get_context_for_prompt(
            query=query,
            event_id=event_id,
        )
        citations = self._extract_citations_from_context(wisdom_context)

        # Extract inflation & real return metrics
        inflation_rate = event.get("annualized_inflation", 0.025) * 100.0
        cpi_hurdle = portfolio_state.get("cpi_hurdle", 100000.0)
        real_return = portfolio_state.get("real_return_pct", portfolio_state.get("nominal_return_pct", 0.0))
        nominal_return = portfolio_state.get("nominal_return_pct", portfolio_state.get("nav_change_pct", 0.0))

        # Assemble prompt
        user_prompt = POST_EVENT_DEBRIEF.format(
            quarter=quarter,
            event_name=event_name,
            event_type=event_type.replace("_", " ").title(),
            event_description=event.get("context_description", ""),
            historical_precedent=event.get("historical_precedent", "N/A"),
            inflation_annualized=inflation_rate,
            cpi_hurdle=cpi_hurdle,
            price_impacts=impacts_text,
            nav=portfolio_state.get("nav", 100000),
            nav_change=portfolio_state.get("nav_change_pct", 0),
            real_return=real_return,
            nominal_return=nominal_return,
            cash=portfolio_state.get("cash", 0),
            cash_pct=portfolio_state.get("cash_pct", 0),
            top_holdings=top_holdings,
            alpha=portfolio_state.get("alpha_aw", 0),
            wisdom_context=wisdom_context,
        )

        return self._generate(user_prompt, citations, max_tokens=2048)

    def post_event_debrief_stream(
        self,
        quarter: int,
        event: dict,
        price_impacts: dict,
        portfolio_state: dict,
    ):
        """
        Stream post-event debrief in real-time.

        Returns:
            tuple: (generator_of_text_chunks, citations, provider_name, model_name)
        """
        event_id = event.get("id", "")
        event_name = event.get("title", event.get("name", "Unknown Event"))
        event_type = event.get("event_type", event.get("type", "unknown"))

        impacts_text = self._format_price_impacts(price_impacts)
        top_holdings = self._format_top_holdings(portfolio_state.get("holdings", []))

        query = f"{event_name} {event.get('context_description', '')} {event.get('headline', '')}"
        wisdom_context = self._rag.get_context_for_prompt(
            query=query,
            event_id=event_id,
        )
        citations = self._extract_citations_from_context(wisdom_context)

        # Extract inflation & real return metrics
        inflation_rate = event.get("annualized_inflation", 0.025) * 100.0
        cpi_hurdle = portfolio_state.get("cpi_hurdle", 100000.0)
        real_return = portfolio_state.get("real_return_pct", portfolio_state.get("nominal_return_pct", 0.0))
        nominal_return = portfolio_state.get("nominal_return_pct", portfolio_state.get("nav_change_pct", 0.0))

        user_prompt = POST_EVENT_DEBRIEF.format(
            quarter=quarter,
            event_name=event_name,
            event_type=event_type.replace("_", " ").title(),
            event_description=event.get("context_description", ""),
            historical_precedent=event.get("historical_precedent", "N/A"),
            inflation_annualized=inflation_rate,
            cpi_hurdle=cpi_hurdle,
            price_impacts=impacts_text,
            nav=portfolio_state.get("nav", 100000),
            nav_change=portfolio_state.get("nav_change_pct", 0),
            real_return=real_return,
            nominal_return=nominal_return,
            cash=portfolio_state.get("cash", 0),
            cash_pct=portfolio_state.get("cash_pct", 0),
            top_holdings=top_holdings,
            alpha=portfolio_state.get("alpha_aw", 0),
            wisdom_context=wisdom_context,
        )

        stream = self.llm.generate_stream(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT_BASE,
            temperature=0.7,
            max_tokens=2048,
        )

        return stream, citations, self.llm.provider_name, getattr(self.llm, "_model", "gemini")

    def pre_trade_insight(
        self,
        quarter: int,
        event: dict | None,
        trade: dict,
        portfolio_state: dict,
    ) -> MentorResponse:
        """
        Generate pre-trade insight for a proposed buy/sell.

        Args:
            quarter: Current quarter number.
            event: Current active event (or None).
            trade: Dict with action, asset_name, sector, cap_size, amount, costs.
            portfolio_state: Current portfolio state.
        """
        event_name = (event.get("title") or event.get("name") or "No active event") if event else "No active event"
        event_type = (event.get("event_type") or event.get("type") or "none") if event else "none"
        event_id = event.get("id", "") if event else ""

        # Retrieve relevant wisdom
        query = f"{trade.get('action', '')} {trade.get('asset_name', '')} {event_name}"
        wisdom_context = self._rag.get_context_for_prompt(
            query=query,
            event_id=event_id if event_id else None,
        )
        citations = self._extract_citations_from_context(wisdom_context)

        user_prompt = PRE_TRADE_INSIGHT.format(
            quarter=quarter,
            event_name=event_name,
            event_type=event_type.replace("_", " ").title(),
            action=trade.get("action", "Trade"),
            asset_name=trade.get("asset_name", "Unknown"),
            asset_sector=trade.get("sector", "Unknown"),
            asset_cap_size=trade.get("cap_size", "Unknown"),
            amount=trade.get("amount", 0),
            tax_cost=trade.get("tax_cost", 0),
            brokerage_cost=trade.get("brokerage_cost", 0),
            nav=portfolio_state.get("nav", 100000),
            cash=portfolio_state.get("cash", 0),
            cash_pct=portfolio_state.get("cash_pct", 0),
            current_position=trade.get("current_position", "None"),
            wisdom_context=wisdom_context,
        )

        return self._generate(user_prompt, citations, max_tokens=512)

    def portfolio_health_check(
        self,
        quarter: int,
        portfolio_state: dict,
        benchmark_alphas: dict,
    ) -> MentorResponse:
        """
        Generate a comprehensive portfolio health check.

        Args:
            quarter: Current quarter number.
            portfolio_state: Full portfolio state with holdings breakdown.
            benchmark_alphas: Dict with alpha vs each benchmark.
        """
        # Retrieve wisdom about portfolio construction
        query = "portfolio construction diversification risk management allocation"
        wisdom_context = self._rag.get_context_for_prompt(query=query)
        citations = self._extract_citations_from_context(wisdom_context)

        holdings_text = self._format_holdings_breakdown(
            portfolio_state.get("holdings", [])
        )
        sector_text = self._format_sector_concentration(
            portfolio_state.get("sector_weights", {})
        )

        user_prompt = PORTFOLIO_HEALTH_CHECK.format(
            quarter=quarter,
            quarters_played=quarter,
            nav=portfolio_state.get("nav", 100000),
            total_return=portfolio_state.get("total_return_pct", 0),
            real_return=portfolio_state.get("real_return_pct", portfolio_state.get("total_return_pct", 0)),
            cpi_hurdle=portfolio_state.get("cpi_hurdle", 100000.0),
            cash=portfolio_state.get("cash", 0),
            cash_pct=portfolio_state.get("cash_pct", 0),
            total_friction=portfolio_state.get("total_friction", 0),
            holdings_breakdown=holdings_text,
            sector_concentration=sector_text,
            alpha_equity=benchmark_alphas.get("equity", 0),
            alpha_6040=benchmark_alphas.get("6040", 0),
            alpha_aw=benchmark_alphas.get("all_weather", 0),
            wisdom_context=wisdom_context,
        )

        return self._generate(user_prompt, citations, max_tokens=1024)

    def career_retrospective(
        self,
        quarters: int,
        scorecard: dict,
    ) -> MentorResponse:
        """Generate a multi-decade career retrospective evaluation."""
        user_prompt, citations = self._build_career_prompt(quarters, scorecard)
        return self._generate(user_prompt, citations, max_tokens=2048)

    def career_retrospective_stream(
        self,
        quarters: int,
        scorecard: dict,
    ):
        """Stream multi-decade career retrospective evaluation in real-time."""
        user_prompt, citations = self._build_career_prompt(quarters, scorecard)
        stream = self.llm.generate_stream(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT_BASE,
            temperature=0.7,
            max_tokens=2048,
        )
        return stream, citations, self.llm.provider_name, getattr(self.llm, "_model", "gemini")

    def _build_career_prompt(self, quarters: int, sc: dict):
        years = round(quarters / 4.0, 1)
        query = "long term compounding market cycles patient investor indexation staying the course drawdowns"
        wisdom_context = self._rag.get_context_for_prompt(query=query)
        citations = self._extract_citations_from_context(wisdom_context)

        user_prompt = CAREER_RETROSPECTIVE.format(
            years=years,
            quarters=quarters,
            initial_capital=sc.get("initial_capital", 100000.0),
            final_nav=sc.get("final_nav", 100000.0),
            nominal_return=sc.get("nominal_return_pct", 0.0),
            real_return=sc.get("real_return_pct", 0.0),
            max_dd=sc.get("max_drawdown_portfolio", 0.0),
            total_friction=sc.get("total_friction", 0.0),
            taxes=sc.get("taxes_paid", 0.0),
            fees=sc.get("fees_paid", 0.0),
            dividends=sc.get("dividends_earned", 0.0),
            aw_nav=sc.get("aw_nav", 100000.0),
            aw_return=sc.get("aw_return_pct", 0.0),
            aw_dd=sc.get("aw_dd", 0.0),
            b6040_nav=sc.get("b6040_nav", 100000.0),
            b6040_return=sc.get("b6040_return_pct", 0.0),
            b6040_dd=sc.get("b6040_dd", 0.0),
            eq_nav=sc.get("eq_nav", 100000.0),
            eq_return=sc.get("eq_return_pct", 0.0),
            eq_dd=sc.get("eq_dd", 0.0),
            cpi_hurdle=sc.get("cpi_hurdle", 100000.0),
            cpi_cum_pct=sc.get("cum_cpi_pct", 0.0),
            wisdom_context=wisdom_context,
        )
        return user_prompt, citations

    # ── Private Helpers ──

    def _generate(
        self,
        user_prompt: str,
        citations: list[dict],
        max_tokens: int = 2048,
    ) -> MentorResponse:
        """Send prompt to LLM and wrap response."""
        response: LLMResponse = self.llm.generate(
            user_prompt=user_prompt,
            system_prompt=SYSTEM_PROMPT_BASE,
            temperature=0.7,
            max_tokens=max_tokens,
        )

        return MentorResponse(
            text=response.text,
            citations=citations,
            provider=response.provider,
            model=response.model,
            tokens_used=response.total_tokens,
        )

    def _format_price_impacts(self, price_impacts: dict) -> str:
        """Format price changes for prompt."""
        if not price_impacts:
            return "No significant price changes."

        lines = []
        # Sort by absolute change
        sorted_impacts = sorted(
            price_impacts.items(), key=lambda x: abs(x[1]), reverse=True
        )
        for name, pct in sorted_impacts[:10]:  # Top 10 movers
            direction = "\u25b2" if pct >= 0 else "\u25bc"
            lines.append(f"  {direction} {name}: {pct:+.1f}%")

        return "\n".join(lines)

    def _format_top_holdings(self, holdings: list) -> str:
        """Format top holdings for prompt."""
        if not holdings:
            return "No holdings"

        top = sorted(holdings, key=lambda h: h.get("value", 0), reverse=True)[:5]
        return ", ".join(
            f"{h.get('name', '?')} (S${h.get('value', 0):,.0f})"
            for h in top
        )

    def _format_holdings_breakdown(self, holdings: list) -> str:
        """Format full holdings breakdown for health check."""
        if not holdings:
            return "No holdings."

        lines = []
        for h in sorted(holdings, key=lambda x: x.get("value", 0), reverse=True):
            lines.append(
                f"  - {h.get('name', '?')}: S${h.get('value', 0):,.0f} "
                f"({h.get('weight_pct', 0):.1f}%) "
                f"P&L: {h.get('pnl_pct', 0):+.1f}% "
                f"Held: {h.get('quarters_held', 0)}Q"
            )
        return "\n".join(lines)

    def _format_sector_concentration(self, sector_weights: dict) -> str:
        """Format sector weights for health check."""
        if not sector_weights:
            return "No sector data."

        lines = []
        for sector, weight in sorted(
            sector_weights.items(), key=lambda x: x[1], reverse=True
        ):
            bar = "\u2588" * int(weight / 5)  # Simple text bar chart
            lines.append(f"  {sector}: {weight:.1f}% {bar}")
        return "\n".join(lines)

    def _extract_citations_from_context(self, wisdom_context: str) -> list[dict]:
        """Extract structured citations from the formatted wisdom context."""
        citations = []
        if not wisdom_context or "No relevant" in wisdom_context:
            return citations

        # Parse the formatted context to extract source info
        # The RAG engine formats as: [N] "text" — Source
        lines = wisdom_context.split("\n")
        current_text = ""
        for line in lines:
            line = line.strip()
            if line.startswith("[") and "]" in line:
                # New citation
                if current_text:
                    citations.append(self._parse_citation(current_text))
                current_text = line
            elif current_text:
                current_text += " " + line

        if current_text:
            citations.append(self._parse_citation(current_text))

        return [c for c in citations if c]  # Filter None

    def _parse_citation(self, text: str) -> dict | None:
        """Parse a single citation string into a dict."""
        try:
            # Format: [N] "quote text" — Source Name
            if "\u2014" in text:
                parts = text.split("\u2014", 1)
                quote = parts[0].strip().lstrip("[0123456789] ").strip('" ')
                source = parts[1].strip()
                return {"text": quote, "source": source, "author": source.split(" \u2014 ")[0] if " \u2014 " in source else source}
        except (IndexError, ValueError):
            pass
        return None
