"""
MarketSense — Centralized Configuration
Loads settings from .env file with sensible defaults.
"""
import os
from pathlib import Path

# Try to load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # python-dotenv not installed — rely on environment variables


# ── LLM Provider ──
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

# ── Gemini API ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# ── Ollama ──
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# ── Paths ──
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
CHROMA_DIR = BASE_DIR / "chroma_db"

# ── RAG Settings ──
RAG_TOP_K = 5           # Number of chunks to retrieve
RAG_CONTEXT_CHUNKS = 3  # Number of chunks to inject into prompt

# ── Game Defaults ──
STARTING_CAPITAL = 100_000
CURRENCY = "SGD"
CASH_INTEREST_RATE = 0.038  # 3.8% p.a.


def is_llm_configured() -> bool:
    """Check if an LLM provider is properly configured."""
    if LLM_PROVIDER == "gemini":
        return bool(GEMINI_API_KEY) and GEMINI_API_KEY != "your-api-key-here"
    elif LLM_PROVIDER == "ollama":
        return True  # Ollama availability checked at runtime
    return False
