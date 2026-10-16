"""
MarketSense — Knowledge Loader

Loads curated investor wisdom JSON files into ChromaDB for RAG retrieval.
Handles initial ingestion and incremental updates.
"""
import json
import os
from pathlib import Path

# Disable ChromaDB telemetry to avoid grpc DLL issues on some Windows systems
os.environ.setdefault("CHROMA_ANONYMIZED_TELEMETRY", "FALSE")
import chromadb

from config import KNOWLEDGE_DIR, CHROMA_DIR


COLLECTION_NAME = "investor_wisdom"


def _load_json_chunks(knowledge_dir: Path) -> list[dict]:
    """Load all wisdom chunks from JSON files in the knowledge directory."""
    all_chunks = []

    if not knowledge_dir.exists():
        return all_chunks

    for json_file in sorted(knowledge_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                chunks = json.load(f)
            if isinstance(chunks, list):
                all_chunks.extend(chunks)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {json_file.name}: {e}")

    return all_chunks


def _build_metadata(chunk: dict) -> dict:
    """
    Convert a wisdom chunk's metadata into ChromaDB-compatible format.
    ChromaDB supports str, int, float, bool, and lists of strings.
    """
    app_events = chunk.get("applicable_events", [])
    if isinstance(app_events, str):
        app_events = [e.strip() for e in app_events.split(",") if e.strip()]

    tags = chunk.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    assets = chunk.get("asset_class_relevance", [])
    if isinstance(assets, str):
        assets = [a.strip() for a in assets.split(",") if a.strip()]

    return {
        "source": chunk.get("source", ""),
        "author": chunk.get("author", ""),
        "tags": tags,
        "applicable_events": app_events,
        "market_cycle": chunk.get("market_cycle", ""),
        "asset_class_relevance": assets,
    }


def load_knowledge(
    knowledge_dir: Path | None = None,
    chroma_dir: Path | None = None,
    force_reload: bool = False,
) -> chromadb.Collection:
    """
    Load the investor wisdom corpus into ChromaDB.

    Args:
        knowledge_dir: Path to the knowledge JSON files. Defaults to config.
        chroma_dir: Path for ChromaDB persistent storage. Defaults to config.
        force_reload: If True, delete and recreate the collection.

    Returns:
        The ChromaDB collection, ready for querying.
    """
    knowledge_dir = knowledge_dir or KNOWLEDGE_DIR
    chroma_dir = chroma_dir or CHROMA_DIR

    # Initialize ChromaDB with persistent storage
    client = chromadb.PersistentClient(path=str(chroma_dir))

    # Check if collection already exists and is populated
    existing_collections = [c.name for c in client.list_collections()]

    if COLLECTION_NAME in existing_collections:
        collection = client.get_collection(COLLECTION_NAME)
        if collection.count() > 0 and not force_reload:
            return collection
        # Force reload — delete and recreate
        client.delete_collection(COLLECTION_NAME)

    # Create fresh collection
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "MarketSense investor wisdom corpus for RAG"},
    )

    # Load all chunks from JSON files
    chunks = _load_json_chunks(knowledge_dir)

    if not chunks:
        print("Warning: No knowledge chunks found. RAG will have no context.")
        return collection

    # Batch insert into ChromaDB
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        chunk_id = chunk.get("id", "")
        text = chunk.get("text", "")

        if not chunk_id or not text:
            continue

        ids.append(chunk_id)
        documents.append(text)
        metadatas.append(_build_metadata(chunk))

    if ids:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

    print(f"Loaded {len(ids)} wisdom chunks into ChromaDB.")
    return collection
