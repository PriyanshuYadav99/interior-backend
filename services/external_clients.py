"""
External service client setup — Supabase (database) and Cloudinary (image
storage). Both are configured once at import time, exactly like they were
in the original app.py, just relocated so other modules (services, routes)
can import `supabase` without importing from app.py and risking a circular
import.

Note: this codebase previously also had `mongo_client = None` / `db = None`
left over from a removed MongoDB integration. Neither was ever read anywhere
in the codebase, so they were dropped as genuinely dead code, not moved.
"""

import logging
import cloudinary
from supabase import create_client, Client

from config.settings import (
    SUPABASE_URL,
    SUPABASE_KEY,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
)

logger = logging.getLogger(__name__)

# ── Supabase ──────────────────────────────────────────────────
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
logger.info("[SETUP] 📦 Using Supabase as primary database")

# ── Cloudinary ────────────────────────────────────────────────
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)
