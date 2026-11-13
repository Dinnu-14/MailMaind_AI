"""Vercel Serverless Function Entrypoint for MailMind AI API."""
import os
import sys

# Ensure root and backend directories are in Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, ".."))
backend_dir = os.path.join(root_dir, "backend")

for p in (root_dir, backend_dir):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app

# Vercel's Python runtime requires an ASGI/WSGI app named 'app'
__all__ = ["app"]

