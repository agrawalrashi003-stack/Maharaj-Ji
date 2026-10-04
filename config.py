import os
from dotenv import load_dotenv

load_dotenv(override=True)


# ==========================================
# API KEYS
# ==========================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GNANI_API_KEY = os.getenv("GNANI_API_KEY")


# ==========================================
# MODELS
# ==========================================

GEMINI_MODEL = "gemini-3.6-flash"

LIVE_MODEL = "gemini-3.8-live"


# ==========================================
# AGENT
# ==========================================

AGENT_NAME = "Maharaj Ji"


# ==========================================
# FLASK
# ==========================================

FLASK_ENV = os.getenv(
    "FLASK_ENV",
    "development"
)


# ==========================================
# VALIDATION
# ==========================================

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing from .env"
    )