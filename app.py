"""Vercel FastAPI entrypoint.

The production app lives in api.main. Keeping this tiny root-level module lets
Vercel detect the FastAPI `app` instance without moving the existing API code.
"""

from api.main import app
