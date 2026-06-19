"""
Backward-compatibility shim — app.config is preserved so that any external
references still work. New code should import from app.core.config.
"""
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL  # noqa: F401
