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


def _get_setting(key: str, default: str = "") -> str:
    """Reads setting from environment variable or Streamlit Community Cloud secrets."""
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return default


# ── LLM Provider ──
LLM_PROVIDER = _get_setting("LLM_PROVIDER", "gemini").lower()

# ── Gemini API ──
GEMINI_API_KEY = _get_setting("GEMINI_API_KEY", "")
GEMINI_MODEL = _get_setting("GEMINI_MODEL", "gemini-2.5-flash")

# ── Ollama ──
OLLAMA_MODEL = _get_setting("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = _get_setting("OLLAMA_HOST", "http://localhost:11434")

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
