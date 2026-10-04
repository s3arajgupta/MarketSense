"""
Tests for Phase 3: Symbolic Macroeconomic Knowledge Graph & XAI Engine

Verifies:
- NetworkX DiGraph loading and schema integrity
- Coverage of all 22 crisis cards from crisis_cards.json
- Shortest weighted causal transmission path calculation and polarity
- Graceful handling of unreachable or non-existent nodes
- Formatted symbolic causal chains for prompt grounding
- Interactive Pyvis HTML generation
"""
import json
import pytest
from pathlib import Path

from intelligence.knowledge_graph import CausalKnowledgeGraph


@pytest.fixture
def kg():
    return CausalKnowledgeGraph()


@pytest.fixture
def events():
    with open("data/crisis_cards.json", "r", encoding="utf-8") as f:
        return json.load(f)["events"]


def test_causal_graph_integrity(kg):
    """Verify nodes, edges, categories, and attributes in NetworkX graph."""
    assert kg.node_count >= 30
    assert kg.edge_count >= 40

    categories = set()
    for node, data in kg.graph.nodes(data=True):
        assert "label" in data
        assert "category" in data
        assert "description" in data
        categories.add(data["category"])

    assert "driver" in categories
    assert "channel" in categories
    assert "sector" in categories
    assert "asset_class" in categories

    for u, v, data in kg.graph.edges(data=True):
        assert data["sign"] in (-1, 1)
        assert 0.0 < data["weight"] <= 1.0
        assert data["resistance"] > 0.0
        assert len(data.get("description", "")) > 0


def test_all_22_events_mapped(kg, events):
    """Verify every event in crisis_cards.json has a valid mapping in the knowledge graph."""
    assert len(events) == 22
    for ev in events:
        event_id = ev["id"]
        mapping = kg.get_event_mapping(event_id)
        assert mapping is not None, f"Event {event_id} missing in causal_graph.json event_mappings"
        assert "primary_driver" in mapping
        assert mapping["primary_driver"] in kg.graph.nodes, f"Primary driver {mapping['primary_driver']} not in graph"
        assert mapping["polarity"] in (-1, 1)


def test_shortest_causal_path_extraction(kg):
    """Verify shortest weighted transmission path and polarity calculation."""
    # Policy rate -> Tech sector
    chain = kg.extract_causal_chain("driver_policy_rate", "sector_it")
    assert chain is not None
    assert chain["source"] == "driver_policy_rate"
    assert chain["target"] == "sector_it"
    assert chain["length"] >= 3
    assert chain["cumulative_polarity"] == -1  # Rate hike -> Borrowing cost (+) -> Discount rate (+) -> Tech P/E multiple (-)
    assert chain["overall_impact"] == "Contractionary (-)"

    for step in chain["steps"]:
        assert "from_node" in step
        assert "to_node" in step
        assert "from_label" in step
        assert "to_label" in step
        assert len(step["description"]) > 0


def test_oil_shock_causal_path(kg):
    """Verify crude oil shock transmission to energy sector and inflation."""
    chain = kg.extract_causal_chain("driver_crude_oil", "sector_energy")
    assert chain is not None
    assert chain["cumulative_polarity"] == 1
    assert chain["overall_impact"] == "Expansionary (+)"


def test_unreachable_node_handling(kg):
    """Verify graceful handling when no path exists or node is unknown."""
    # Non-existent node
    assert kg.extract_causal_chain("driver_policy_rate", "fake_nonexistent_node") is None
    assert kg.extract_causal_chain("fake_node", "sector_it") is None


def test_event_paths_to_targets(kg):
    """Verify extraction of multiple transmission paths for an event."""
    paths = kg.get_event_paths_to_targets("EVENT_MONETARY_HIKE")
    assert len(paths) >= 5

    # Check top transmission targets
    targets = [p["target"] for p in paths]
    assert "sector_it" in targets or "asset_long_bond" in targets


def test_format_causal_path_for_prompt(kg):
    """Verify formatted ASCII transmission paths for AI Mentor prompt grounding."""
    prompt_str = kg.format_causal_path_for_prompt("EVENT_MONETARY_HIKE", max_paths=3)
    assert "GROUNDED SYMBOLIC CAUSAL TRANSMISSION PATHS" in prompt_str
    assert "Central Bank Policy Rate" in prompt_str
    assert "=> Result:" in prompt_str

    # Unmapped event fallback
    unmapped = kg.format_causal_path_for_prompt("EVENT_UNKNOWN_XYZ")
    assert "No verified" in unmapped


def test_pyvis_subgraph_html_generation(kg):
    """Verify interactive Pyvis HTML visualization generation."""
    html = kg.render_pyvis_subgraph_html("EVENT_MONETARY_HIKE")
    assert isinstance(html, str)
    assert len(html) > 5000
    assert "vis-network" in html or "network" in html
    assert "Central Bank Policy Rate" in html


def test_counterfactual_simulation(events):
    """Verify counterfactual What-If simulation engine."""
    from engine.simulator import compute_counterfactual, COUNTERFACTUAL_STRATEGIES

    with open("data/assets.json", "r", encoding="utf-8") as f:
        assets = json.load(f)["assets"]

    ev = events[0]  # Rate Hike
    initial_prices = {a["id"]: a["base_price"] for a in assets}

    # Simulate: User was 100% tech equities and lost -8%
    cf_res = compute_counterfactual(
        capital=100000.0,
        event=ev,
        current_prices=initial_prices,
        assets_list=assets,
        user_actual_return_pct=-8.0,
        strategy="pure_cash",
    )

    assert cf_res["capital_base"] == 100000.0
    assert cf_res["counterfactual_return_pct"] > 0.0  # Cash earned interest
    assert cf_res["counterfactual_nav"] > 100000.0
    assert cf_res["actual_nav"] == 92000.0
    assert cf_res["diff_return_pct"] < 0  # Counterfactual cash outperformed panic holding
    assert "Counterfactual Outperformed" in cf_res["verdict"]

    # Test All-Weather strategy
    cf_aw = compute_counterfactual(
        capital=100000.0,
        event=ev,
        current_prices=initial_prices,
        assets_list=assets,
        user_actual_return_pct=-2.0,
        strategy="all_weather",
    )
    assert "Ray Dalio All-Weather" in cf_aw["strategy_name"]
    assert len(cf_aw["weights"]) > 5


def test_twin_precedents_retrieval():
    """Verify RAG v2 historical twin precedents retrieval and prompt context injection."""
    from intelligence.rag_engine import RAGEngine

    rag = RAGEngine()
    assert rag.corpus_size >= 50

    # Test Volcker shock twin precedent for rate hike
    prec_hike = rag.retrieve_twin_precedents("EVENT_MONETARY_HIKE")
    assert len(prec_hike) > 0
    assert "Volcker" in prec_hike[0].text or "1980" in prec_hike[0].text
    assert "Historical Crisis Twin Precedents" in prec_hike[0].source

    # Test Oil shock twin precedent
    prec_oil = rag.retrieve_twin_precedents("EVENT_OIL_SHOCK")
    assert len(prec_oil) > 0
    assert "1973" in prec_oil[0].text or "OPEC" in prec_oil[0].text

    # Test prompt context includes both wisdom and twin precedents
    context = rag.get_context_for_prompt("Emergency Rate Hike", event_id="EVENT_MONETARY_HIKE")
    assert "RELEVANT INVESTOR WISDOM & HISTORICAL PRECEDENTS" in context
    assert "Volcker" in context or "1980" in context

