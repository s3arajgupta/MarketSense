"""
MarketSense AI — Macroeconomic Causal Knowledge Graph & XAI Engine

Constructs a directed weighted knowledge graph using NetworkX.
Provides:
1. Shortest weighted causal transmission path extraction from macro shocks to sectors/assets.
2. Formatted symbolic chains for Socratic AI Mentor prompt grounding.
3. Interactive Pyvis physics-based graph rendering for Streamlit UI.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import networkx as nx

from config import DATA_DIR

DEFAULT_GRAPH_PATH = DATA_DIR / "knowledge" / "causal_graph.json"

CATEGORY_COLORS = {
    "driver": "#E63946",      # Crimson / Red
    "channel": "#F4A261",     # Warm Amber / Orange
    "sector": "#457B9D",      # Slate Blue
    "asset_class": "#2A9D8F",  # Teal / Emerald
}


class CausalKnowledgeGraph:
    """
    Symbolic macroeconomic knowledge graph representing cause-and-effect
    transmission channels across financial markets.
    """

    def __init__(self, json_path: Optional[Path] = None):
        self.json_path = Path(json_path) if json_path else DEFAULT_GRAPH_PATH
        self.graph = nx.DiGraph()
        self.event_mappings: Dict[str, Dict[str, Any]] = {}
        self._raw_data: Dict[str, Any] = {}
        self.load_graph()

    def load_graph(self) -> None:
        """Loads nodes, edges, and event mappings from JSON."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"Causal graph definition not found at: {self.json_path}")

        with open(self.json_path, "r", encoding="utf-8") as f:
            self._raw_data = json.load(f)

        self.graph.clear()

        # Ingest Nodes
        for node in self._raw_data.get("nodes", []):
            self.graph.add_node(
                node["id"],
                label=node.get("label", node["id"]),
                category=node.get("category", "general"),
                description=node.get("description", ""),
            )

        # Ingest Directed Edges with weights and polarity
        for edge in self._raw_data.get("edges", []):
            weight = float(edge.get("weight", 0.5))
            # Resistance distance for shortest path: stronger weight = shorter resistance
            resistance = round(1.05 - min(max(weight, 0.05), 1.0), 4)
            self.graph.add_edge(
                edge["source"],
                edge["target"],
                sign=int(edge.get("sign", 1)),
                weight=weight,
                resistance=resistance,
                description=edge.get("description", ""),
            )

        self.event_mappings = self._raw_data.get("event_mappings", {})

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def get_event_mapping(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves primary/secondary driver mapping for an event."""
        return self.event_mappings.get(event_id)

    def extract_causal_chain(
        self,
        source_node: str,
        target_node: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Extracts the shortest weighted causal path between source and target node.
        Computes cumulative transmission polarity and collects edge rationale.
        """
        if source_node not in self.graph or target_node not in self.graph:
            return None

        try:
            path = nx.shortest_path(
                self.graph,
                source=source_node,
                target=target_node,
                weight="resistance",
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

        # Build detailed step-by-step path trace
        steps = []
        cumulative_polarity = 1
        total_resistance = 0.0

        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            edge_data = self.graph.get_edge_data(u, v)
            sign = edge_data.get("sign", 1)
            weight = edge_data.get("weight", 1.0)
            resistance = edge_data.get("resistance", 0.1)

            cumulative_polarity *= sign
            total_resistance += resistance

            steps.append({
                "from_node": u,
                "from_label": self.graph.nodes[u].get("label", u),
                "to_node": v,
                "to_label": self.graph.nodes[v].get("label", v),
                "sign": sign,
                "weight": weight,
                "description": edge_data.get("description", ""),
            })

        return {
            "source": source_node,
            "target": target_node,
            "path_nodes": path,
            "steps": steps,
            "length": len(path),
            "cumulative_polarity": cumulative_polarity,
            "overall_impact": "Expansionary (+)" if cumulative_polarity > 0 else "Contractionary (-)",
            "total_resistance": round(total_resistance, 4),
        }

    def get_event_paths_to_targets(
        self,
        event_id: str,
        targets: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extracts all causal paths from an event's primary driver to target nodes
        (sectors and assets).
        """
        mapping = self.get_event_mapping(event_id)
        if not mapping:
            return []

        primary_driver = mapping.get("primary_driver")
        event_polarity = mapping.get("polarity", 1)

        if not primary_driver or primary_driver not in self.graph:
            return []

        if targets is None:
            # Default to all sectors and assets
            targets = [
                n for n, d in self.graph.nodes(data=True)
                if d.get("category") in ("sector", "asset_class")
            ]

        extracted_paths = []
        for target in targets:
            chain = self.extract_causal_chain(primary_driver, target)
            if chain:
                # Adjust final polarity with initial event polarity
                final_polarity = chain["cumulative_polarity"] * event_polarity
                chain["event_adjusted_polarity"] = final_polarity
                chain["event_adjusted_impact"] = (
                    "Expansionary (+)" if final_polarity > 0 else "Contractionary (-)"
                )
                chain["event_id"] = event_id
                extracted_paths.append(chain)

        # Sort paths by total resistance (strongest transmission first)
        extracted_paths.sort(key=lambda x: x["total_resistance"])
        return extracted_paths

    def format_causal_path_for_prompt(
        self,
        event_id: str,
        max_paths: int = 4,
    ) -> str:
        """
        Renders structured, concise causal paths for injection into AI Mentor prompts.
        Guarantees that the LLM grounds its explanation on auditable graph nodes.
        """
        paths = self.get_event_paths_to_targets(event_id)
        if not paths:
            return "No verified symbolic causal transmission path mapped for this event."

        lines = [
            "GROUNDED SYMBOLIC CAUSAL TRANSMISSION PATHS (NetworkX Knowledge Graph):",
            "Trace these exact verified nodes and mechanisms in your causal explanation:"
        ]

        for idx, p in enumerate(paths[:max_paths], 1):
            nodes_seq = []
            for step in p["steps"]:
                sign_str = "+" if step["sign"] > 0 else "-"
                nodes_seq.append(f"{step['from_label']} --({sign_str}{step['weight']:.2f})-->")
            nodes_seq.append(f"{self.graph.nodes[p['target']].get('label', p['target'])}")

            chain_str = " ".join(nodes_seq)
            impact_tag = p["event_adjusted_impact"]
            lines.append(f"[{idx}] {chain_str} => Result: {impact_tag}")

        return "\n".join(lines)

    def render_pyvis_subgraph_html(
        self,
        event_id: Optional[str] = None,
        height: str = "520px",
        width: str = "100%",
    ) -> str:
        """
        Generates interactive physics-based HTML visualization using Pyvis.
        Highlights the active event's causal paths in glowing green or red.
        """
        from pyvis.network import Network

        net = Network(
            height=height,
            width=width,
            directed=True,
            bgcolor="#0E1117",
            font_color="#FAFAFA",
        )

        # Configure physics for smooth organic clustering with spacious layout
        net.set_options("""
        {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -80,
              "centralGravity": 0.015,
              "springLength": 160,
              "springConstant": 0.06,
              "damping": 0.5
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "navigationButtons": true,
            "keyboard": true
          }
        }
        """)

        # Identify active path edges and root primary driver if event_id is supplied
        active_edges = {}
        active_nodes = set()
        primary_driver = None

        if event_id:
            mapping = self.get_event_mapping(event_id)
            if mapping:
                primary_driver = mapping.get("primary_driver")
                if primary_driver:
                    active_nodes.add(primary_driver)

            event_paths = self.get_event_paths_to_targets(event_id)
            for p in event_paths[:6]:  # Top transmission paths
                for step in p["steps"]:
                    u, v = step["from_node"], step["to_node"]
                    active_edges[(u, v)] = p["event_adjusted_polarity"]
                    active_nodes.add(u)
                    active_nodes.add(v)

        # Add Nodes to Pyvis with prominent size and typography hierarchy
        for node_id, data in self.graph.nodes(data=True):
            cat = data.get("category", "general")
            base_color = CATEGORY_COLORS.get(cat, "#888888")
            raw_label = data.get("label", node_id)

            if event_id:
                is_primary = (node_id == primary_driver)
                is_active = (node_id in active_nodes)

                if is_primary:
                    # Root shock node: biggest, glowing amber halo, extra-large bold label
                    node_size = 46
                    border_width = 5
                    border_color = "#F59E0B"
                    font_cfg = {
                        "size": 24,
                        "face": "system-ui, -apple-system, sans-serif",
                        "bold": True,
                        "color": "#FFFFFF",
                        "strokeWidth": 4,
                        "strokeColor": "#000000"
                    }
                    node_label = f"⚡ {raw_label}"
                    node_color = {"background": base_color, "border": border_color, "highlight": {"background": "#F59E0B", "border": "#FFFFFF"}}
                    shadow_cfg = {"enabled": True, "color": "rgba(245, 158, 11, 0.8)", "size": 18, "x": 0, "y": 0}
                elif is_active:
                    # Affected downstream node: prominent size, bright border, large bold label
                    node_size = 36
                    border_width = 4
                    border_color = "#FFFFFF"
                    font_cfg = {
                        "size": 20,
                        "face": "system-ui, -apple-system, sans-serif",
                        "bold": True,
                        "color": "#FFFFFF",
                        "strokeWidth": 3,
                        "strokeColor": "#000000"
                    }
                    node_label = raw_label
                    node_color = {"background": base_color, "border": border_color, "highlight": {"background": base_color, "border": "#FFD700"}}
                    shadow_cfg = {"enabled": True, "color": "rgba(255, 255, 255, 0.4)", "size": 12, "x": 0, "y": 0}
                else:
                    # Inactive background node: subdued, smaller, non-distracting
                    node_size = 15
                    border_width = 1
                    border_color = "#334155"
                    font_cfg = {
                        "size": 11,
                        "face": "system-ui, -apple-system, sans-serif",
                        "bold": False,
                        "color": "#64748B",
                        "strokeWidth": 1,
                        "strokeColor": "#0E1117"
                    }
                    node_label = raw_label
                    node_color = {"background": "#1E293B", "border": border_color, "highlight": {"background": base_color, "border": "#94A3B8"}}
                    shadow_cfg = {"enabled": False}
            else:
                # Overview mode (no event filter): balanced legible sizes
                node_size = 28
                border_width = 2
                border_color = "#E2E8F0"
                font_cfg = {
                    "size": 15,
                    "face": "system-ui, -apple-system, sans-serif",
                    "bold": True,
                    "color": "#FAFAFA",
                    "strokeWidth": 2,
                    "strokeColor": "#000000"
                }
                node_label = raw_label
                node_color = {"background": base_color, "border": border_color, "highlight": {"background": base_color, "border": "#FFD700"}}
                shadow_cfg = {"enabled": False}

            net.add_node(
                node_id,
                label=node_label,
                title=f"<b>{raw_label}</b><br>Category: {cat.upper()}<br>{data.get('description', '')}",
                color=node_color,
                size=node_size,
                borderWidth=border_width,
                font=font_cfg,
                shadow=shadow_cfg,
            )

        # Add Edges to Pyvis with distinct glowing transmission styles
        for u, v, data in self.graph.edges(data=True):
            sign = data.get("sign", 1)
            weight = data.get("weight", 0.5)
            desc = data.get("description", "")

            # Highlight active transmission paths
            if (u, v) in active_edges:
                pol = active_edges[(u, v)]
                edge_color = "#10B981" if pol > 0 else "#EF4444"  # Vibrant Emerald (+) or Rose Red (-)
                edge_width = 4.5
                edge_shadow = {"enabled": True, "color": edge_color, "size": 8}
            elif event_id:
                edge_color = "#1E293B"  # Muted background edge
                edge_width = 1.0
                edge_shadow = {"enabled": False}
            else:
                edge_color = "#3A3F4B"
                edge_width = 1.5
                edge_shadow = {"enabled": False}

            net.add_edge(
                u,
                v,
                value=weight,
                title=f"<b>Transmission Mechanism:</b><br>{desc}<br>Strength: {weight:.2f} | Polarity: {'+' if sign>0 else '-'}",
                color=edge_color,
                width=edge_width,
                arrows="to",
                shadow=edge_shadow,
            )

        # Generate HTML representation
        html = net.generate_html()
        return html
