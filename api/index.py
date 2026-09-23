"""
Vercel Serverless Function Entry Point for UniVault.
Exposes the WSGI Flask `app` object to the @vercel/python runtime.
"""

import os
import sys

# Add project root directory to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set VERCEL environment variable flag
os.environ["VERCEL"] = "1"

from app import app

# Vercel's WSGI adapter expects 'app' or 'handler'
handler = app
