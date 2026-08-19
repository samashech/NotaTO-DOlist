from contextvars import ContextVar

gemini_key_ctx = ContextVar("gemini_key", default=None)
