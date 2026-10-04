"""
Tests for Phase 2: Intelligent Reasoning Layer

Verifies:
- Centralized configuration and defaults
- RAG knowledge loading and hybrid retrieval
- Citation extraction and formatting
- Prompt template rendering and constraints
- LLM client interface abstraction & provider factory
- Offline inference simulation using mock provider
"""
import pytest
from config import is_llm_configured, KNOWLEDGE_DIR
from intelligence.llm_client import LLMClient, LLMResponse, create_llm_client
from intelligence.rag_engine import RAGEngine
from intelligence.prompts import SYSTEM_PROMPT_BASE, POST_EVENT_DEBRIEF, CAREER_RETROSPECTIVE
from intelligence.mentor import AIMentor, MentorResponse


def test_config_defaults():
    """Verify configuration loads properly."""
    assert KNOWLEDGE_DIR.exists()
    assert is_llm_configured() in [True, False]


def test_rag_hybrid_retrieval():
    """Verify hybrid RAG retrieval returns grounded investor wisdom with metadata."""
    rag = RAGEngine()
    assert rag.corpus_size >= 25

    # Test event-specific retrieval
    chunks = rag.retrieve("emergency rate hike interest rate jump", event_id="emergency_rate_hike")
    assert len(chunks) > 0

    top = chunks[0]
    assert top.author != ""
    assert top.source != ""
    assert len(top.text) > 30

    citation = top.format_citation()
    assert top.source in citation


def test_prompt_template_formatting():
    """Verify prompt formatting safely injects game state without syntax issues."""
    formatted = POST_EVENT_DEBRIEF.format(
        quarter=2,
        event_name="Test Event",
        event_type="Sudden",
        event_description="Test Description",
        historical_precedent="2008 GFC",
        inflation_annualized=7.8,
        cpi_hurdle=102000.0,
        price_impacts="Tech: -10%",
        nav=95000.0,
        nav_change=-5.0,
        real_return=-6.8,
        nominal_return=-5.0,
        cash=25000.0,
        cash_pct=26.3,
        top_holdings="Tech Large Cap",
        alpha=-1.5,
        causal_path_context="[1] Rate Hike -> Borrowing Cost -> Discount Rate -> Tech",
        wisdom_context="[1] 'Margin of safety' — Benjamin Graham",
    )
    assert "Test Event" in formatted
    assert "Margin of safety" in formatted
    assert "7.8% annualized" in formatted
    assert "Borrowing Cost" in formatted
    assert "HARD RULES" in SYSTEM_PROMPT_BASE


class MockOfflineClient(LLMClient):
    """
    Simulated Offline / Local LLM provider.
    Verifies that the mentor orchestrator functions in fully air-gapped / offline environments.
    """
    def __init__(self):
        self.last_user_prompt = ""
        self.last_system_prompt = ""

    def generate(self, user_prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 1024) -> LLMResponse:
        self.last_user_prompt = user_prompt
        self.last_system_prompt = system_prompt
        return LLMResponse(
            text="### 📉 What Happened\nMarkets dropped.\n\n### 🔗 Causal Chain\nRate hike -> Selloff.\n\n### 📚 Wisdom\n'Cash is oxygen' — Dalio.\n\n### 💡 Your Portfolio\nDiversification protected your NAV.",
            model="offline-mock-7b",
            provider="offline-simulated",
            input_tokens=150,
            output_tokens=60,
        )

    def generate_stream(self, user_prompt: str, system_prompt: str = "", temperature: float = 0.7, max_tokens: int = 2048):
        self.last_user_prompt = user_prompt
        self.last_system_prompt = system_prompt
        for word in ["### 📉 What Happened\n", "Markets ", "dropped.\n\n", "### 📚 Wisdom\n", "'Cash is oxygen'"]:
            yield word

    def is_available(self) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "Offline-Simulated"


def test_offline_inference_simulation():
    """Simulate complete offline mentor debrief without calling any external APIs."""
    mock_client = MockOfflineClient()
    mentor = AIMentor(llm_client=mock_client)

    dummy_event = {
        "id": "emergency_rate_hike",
        "title": "Rate Hike Shock",
        "type": "Sudden",
        "context_description": "Rates surged 100bps.",
        "headline": "Central Bank Hikes Rates",
        "historical_precedent": "1994 Bond Massacre",
    }

    dummy_portfolio = {
        "nav": 95000.0,
        "nav_change_pct": -5.0,
        "cash": 30000.0,
        "cash_pct": 31.5,
        "holdings": [{"name": "Tech Large Cap", "value": 10000.0}],
        "alpha_aw": 0.5,
    }

    # Test offline static generation
    resp = mentor.post_event_debrief(
        quarter=1,
        event=dummy_event,
        price_impacts={"Tech Large Cap": -10.0},
        portfolio_state=dummy_portfolio,
    )
    assert isinstance(resp, MentorResponse)
    assert resp.provider == "offline-simulated"
    assert "What Happened" in resp.text
    assert resp.has_citations is True
    assert "Rate Hike Shock" in mock_client.last_user_prompt
    assert "Sudden" in mock_client.last_user_prompt

    # Test offline streaming generator with real crisis_cards.json schema (title + event_type)
    real_crisis_card = {
        "id": "EVENT_MONETARY_HIKE",
        "title": "Emergency 100bps Central Bank Rate Hike",
        "event_type": "Sudden",
        "context_description": "With core CPI reading above 7.8%...",
        "headline": "Central Bank Announces Emergency 100bps Policy Rate Hike",
        "historical_precedent": "1994 Fed Tightening Cycle",
        "annualized_inflation": 0.078,
    }
    stream, citations, provider, model = mentor.post_event_debrief_stream(
        quarter=1,
        event=real_crisis_card,
        price_impacts={"Tech Large Cap": -10.0},
        portfolio_state=dummy_portfolio,
    )
    chunks = list(stream)
    assert len(chunks) > 0
    assert provider == "Offline-Simulated" or "offline" in provider.lower()
    assert "Emergency 100bps Central Bank Rate Hike" in mock_client.last_user_prompt
    assert "Sudden" in mock_client.last_user_prompt
    assert "SYMBOLIC CAUSAL TRANSMISSION PATHS" in mock_client.last_user_prompt
    assert "Central Bank Policy Rate" in mock_client.last_user_prompt


def test_career_retrospective_simulation():
    """Verify career retrospective prompt formatting and mock offline execution."""
    mock_client = MockOfflineClient()
    mentor = AIMentor(llm_client=mock_client)

    scorecard = {
        "initial_capital": 100000.0,
        "final_nav": 350000.0,
        "nominal_return_pct": 250.0,
        "real_return_pct": 110.5,
        "max_drawdown_portfolio": 21.4,
        "total_friction": 4500.0,
        "taxes_paid": 3200.0,
        "fees_paid": 1300.0,
        "dividends_earned": 54000.0,
        "aw_nav": 310000.0,
        "aw_return_pct": 210.0,
        "aw_dd": 14.2,
        "b6040_nav": 290000.0,
        "b6040_return_pct": 190.0,
        "b6040_dd": 29.5,
        "eq_nav": 420000.0,
        "eq_return_pct": 320.0,
        "eq_dd": 48.9,
        "cpi_hurdle": 166000.0,
        "cum_cpi_pct": 66.0,
    }

    resp = mentor.career_retrospective(quarters=120, scorecard=scorecard)
    assert isinstance(resp, MentorResponse)
    assert resp.provider == "offline-simulated"
    assert len(resp.text) > 0

    stream, citations, provider, model = mentor.career_retrospective_stream(quarters=120, scorecard=scorecard)
    chunks = list(stream)
    assert len(chunks) > 0
