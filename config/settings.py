"""
Centralized environment configuration.

Every environment variable the backend reads is loaded here once, so the
rest of the codebase imports named constants instead of scattering
os.getenv() calls (and their default values) across many files. Every
default below matches exactly what each file previously used on its own,
so behavior is unchanged — this only removes duplication.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── AI / Image generation ────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ── Database (Supabase) ──────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# ── Image storage (Cloudinary) ───────────────────────────────
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

# ── Email ─────────────────────────────────────────────────────
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)

# ── WhatsApp / SMS (Twilio via Meta) ─────────────────────────
META_WHATSAPP_API_VERSION = os.getenv("META_WHATSAPP_API_VERSION")
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")

# ── Maps / location ───────────────────────────────────────────
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# ── News ────────────────────────────────────────────────────
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ── Frontend / misc ──────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5177/")
PORT = int(os.getenv("PORT", 5000))

# ── In-process cache tuning ──────────────────────────────────
CACHE_DURATION = 1800          # image cache TTL, seconds (30 minutes)
VERSION_CACHE_DURATION = 3600  # Replicate model-version cache TTL, seconds (1 hour)
