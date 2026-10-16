"""
MarketSense — RAG Engine

Hybrid retrieval engine: tag-based pre-filtering + semantic similarity search.
Retrieves the most relevant investor wisdom chunks given the current game context.
"""
from dataclasses import dataclass
import os

os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "FALSE")
import chromadb

from config import RAG_TOP_K, RAG_CONTEXT_CHUNKS
from intelligence.knowledge_loader import load_knowledge


@dataclass
class RetrievedChunk:
    """A single retrieved wisdom chunk with metadata."""
    id: str
    text: str
    source: str
    author: str
    relevance_score: float
    market_cycle: str
    tags: list[str]

    def format_citation(self) -> str:
        """Format as a readable citation for prompt injection."""
        return f'"{self.text}"\n  \u2014 {self.source}'


class RAGEngine:
    """
    Hybrid retrieval engine for investor wisdom.

    Strategy:
    1. Tag-based pre-filter (by event ID, market cycle, asset class)
    2. Semantic similarity search within filtered results
    3. Return top-K chunks with citations for prompt injection
    """

    def __init__(self, collection: chromadb.Collection | None = None):
        """
        Initialize the RAG engine.

        Args:
            collection: Pre-loaded ChromaDB collection. If None, loads from disk.
        """
        self._collection = collection

    @property
    def collection(self) -> chromadb.Collection:
        """Lazy-load the collection."""
        if self._collection is None:
            self._collection = load_knowledge()
        return self._collection

    @property
    def corpus_size(self) -> int:
        """Number of chunks in the knowledge corpus."""
        return self.collection.count()

    def retrieve(
        self,
        query: str,
        event_id: str | None = None,
        market_cycle: str | None = None,
        asset_classes: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """
        Retrieve relevant wisdom chunks using hybrid search.

        Args:
            query: Natural language query describing the current situation.
            event_id: Current event ID for tag-based pre-filtering.
            market_cycle: Current market cycle phase for filtering.
            asset_classes: Relevant asset classes for filtering.
            top_k: Number of chunks to retrieve. Defaults to config.

        Returns:
            List of RetrievedChunk objects, sorted by relevance.
        """
        top_k = top_k or RAG_TOP_K

        # Build ChromaDB where-filter for tag-based pre-filtering
        where_filters = self._build_where_filter(event_id, market_cycle, asset_classes)

        # Try filtered search first
        results = self._search(query, top_k, where_filters)

        # If filtered search returns too few results, fall back to unfiltered
        if len(results) < RAG_CONTEXT_CHUNKS and where_filters:
            unfiltered_results = self._search(query, top_k, where_filter=None)
            # Merge: prioritize filtered results, then fill with unfiltered
            seen_ids = {r.id for r in results}
            for chunk in unfiltered_results:
                if chunk.id not in seen_ids:
                    results.append(chunk)
                    seen_ids.add(chunk.id)
                if len(results) >= top_k:
                    break

        return results[:top_k]

    def retrieve_twin_precedents(
        self,
        event_id: str,
        query: str = "",
        top_k: int = 1,
    ) -> list[RetrievedChunk]:
        """
        Retrieve historical twin precedent case studies for a specific crisis event.

        Args:
            event_id: Crisis event ID (e.g., 'EVENT_MONETARY_HIKE')
            query: Optional semantic context string.
            top_k: Number of twin precedent chunks to retrieve.

        Returns:
            List of RetrievedChunk objects matching the twin precedent.
        """
        search_query = query or f"historical twin precedent comparative metric {event_id}"
        where_filter = {"applicable_events": {"$contains": event_id}}
        results = self._search(search_query, top_k * 2, where_filter)

        # Prioritize chunks with twin_precedent tag or historical source
        precedents = [r for r in results if "twin_precedent" in r.tags or "Historical" in r.source]
        if not precedents:
            precedents = results

        return precedents[:top_k]

    def get_context_for_prompt(
        self,
        query: str,
        event_id: str | None = None,
        market_cycle: str | None = None,
        asset_classes: list[str] | None = None,
    ) -> str:
        """
        Retrieve chunks and format them as a prompt-ready context block.

        Returns a formatted string ready to inject into the system prompt,
        with numbered citations including grounded investor wisdom and
        historical twin precedents.
        """
        chunks = self.retrieve(
            query=query,
            event_id=event_id,
            market_cycle=market_cycle,
            asset_classes=asset_classes,
            top_k=RAG_CONTEXT_CHUNKS,
        )

        twin_chunks = []
        if event_id:
            twin_chunks = self.retrieve_twin_precedents(event_id, query=query, top_k=1)

        seen_ids = set()
        all_chunks = []
        for chunk in twin_chunks + chunks:
            if chunk.id not in seen_ids:
                seen_ids.add(chunk.id)
                all_chunks.append(chunk)

        if not all_chunks:
            return "No relevant investor wisdom found for this scenario."

        lines = ["RELEVANT INVESTOR WISDOM & HISTORICAL PRECEDENTS (cite these in your analysis):"]
        for i, chunk in enumerate(all_chunks[:RAG_CONTEXT_CHUNKS + 1], 1):
            lines.append(f"\n[{i}] {chunk.format_citation()}")

        return "\n".join(lines)

    def _search(
        self,
        query: str,
        top_k: int,
        where_filter: dict | None = None,
    ) -> list[RetrievedChunk]:
        """Execute a ChromaDB semantic search with optional where filter."""
        try:
            kwargs = {
                "query_texts": [query],
                "n_results": top_k,
            }
            if where_filter:
                kwargs["where"] = where_filter

            results = self.collection.query(**kwargs)
        except Exception:
            return []

        chunks = []
        if results and results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0

                raw_tags = metadata.get("tags", [])
                parsed_tags = raw_tags if isinstance(raw_tags, list) else [t for t in str(raw_tags).split(",") if t]

                chunks.append(RetrievedChunk(
                    id=chunk_id,
                    text=results["documents"][0][i],
                    source=metadata.get("source", "Unknown"),
                    author=metadata.get("author", "Unknown"),
                    relevance_score=1.0 - distance,  # Convert distance to similarity
                    market_cycle=metadata.get("market_cycle", ""),
                    tags=parsed_tags,
                ))

        return chunks

    def _build_where_filter(
        self,
        event_id: str | None,
        market_cycle: str | None,
        asset_classes: list[str] | None,
    ) -> dict | None:
        """
        Build a ChromaDB where-filter for tag-based pre-filtering.

        Uses $contains for string-in-comma-separated-list matching.
        Combines filters with $and when multiple criteria are provided.
        """
        conditions = []

        if event_id:
            conditions.append({
                "applicable_events": {"$contains": event_id}
            })

        if market_cycle:
            conditions.append({
                "market_cycle": {"$eq": market_cycle}
            })

        if not conditions:
            return None

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}
