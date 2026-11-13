"""
config.py — Centralized configuration for LLM-CV Pipeline.

Provides default paths and constants with environment variable override support.
"""
import json
import os


# Base paths (override with environment variables if needed)
# Everything is computed relative to the skill folder, so the skill works from
# any location (for example ~/.claude/skills/mallika-cv, a symlink to this repo).
SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SKILL_DIR

DEFAULT_BASE_FILES_DIR = os.getenv(
    "LLM_CV_BASE_FILES_DIR",
    os.path.join(SKILL_DIR, "okf", "base_files")
)

# Applications directory: where each application folder is saved. Lives
# outside the skill folder so your applications survive skill updates.
# Override with the LLM_CV_APPLICATIONS_DIR environment variable.
APPLICATIONS_DIR = os.getenv(
    "LLM_CV_APPLICATIONS_DIR",
    os.path.join(os.path.expanduser("~"), "Documents", "Mallika Applications")
)

# Optional Obsidian vault. Obsidian sync only runs when this folder exists.
OBSIDIAN_VAULT_DIR = os.getenv(
    "LLM_CV_OBSIDIAN_VAULT",
    os.path.join(os.path.expanduser("~"), "Documents", "Obsidian Vault")
)

# Application tracker CSV.
TRACKER_CSV = os.getenv(
    "LLM_CV_TRACKER_CSV",
    os.path.join(os.path.expanduser("~"), "Documents", "mallika_applications_tracker.csv")
)

# ─── Candidate profile (okf/profile.yaml) ─────────────────────────────────────
def _load_profile() -> dict:
    """Read okf/profile.yaml. Returns {} when the file or PyYAML is missing."""
    path = os.path.join(SKILL_DIR, "okf", "profile.yaml")
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except (ImportError, OSError, ValueError):
        return {}


PROFILE = _load_profile()


def _resolve(path: str):
    """Make a profile path absolute (relative paths are relative to the skill)."""
    if not path:
        return None
    return path if os.path.isabs(path) else os.path.join(SKILL_DIR, path)


# Used by renderers as fallback defaults and by step docs as reference values.
# The YAML `name`/`sender` fields always take precedence over these defaults.
CANDIDATE_NAME = os.getenv("LLM_CV_CANDIDATE_NAME", PROFILE.get("name", "Mallika Mujgule"))
CANDIDATE_FILE_PREFIX = PROFILE.get("file_prefix", "MALLIKA_MUJGULE")
CANDIDATE_TITLE = PROFILE.get("title", "Product Designer")
CANDIDATE_PHONE = os.getenv("LLM_CV_CANDIDATE_PHONE", PROFILE.get("phone", ""))
CANDIDATE_EMAIL = os.getenv("LLM_CV_CANDIDATE_EMAIL", PROFILE.get("email", ""))
CANDIDATE_LINKEDIN = PROFILE.get("linkedin", "")
CANDIDATE_PORTFOLIO = PROFILE.get("portfolio", "")
CANDIDATE_LOCATION = PROFILE.get("location", "Berlin, Germany")
CANDIDATE_WORK_AUTH = PROFILE.get("work_authorization", "")
CANDIDATE_AVAILABILITY = PROFILE.get("availability", "")
CANDIDATE_LANGUAGES = PROFILE.get("languages", [])
# Kept for renderers that still read a GitHub field; empty for a designer profile.
CANDIDATE_GITHUB = os.getenv("LLM_CV_CANDIDATE_GITHUB", "")

# Candidate photo (headshot): stamped onto the top-right of LaTeX-mode resumes.
# Empty value disables it. Override via env var or YAML contact_info.photo.
CANDIDATE_PHOTO = os.getenv("LLM_CV_CANDIDATE_PHOTO", _resolve(PROFILE.get("photo", "")) or "")

# Signature image for the cover letter. Empty falls back to the typed name.
CANDIDATE_SIGNATURE = os.getenv(
    "LLM_CV_CANDIDATE_SIGNATURE", _resolve(PROFILE.get("signature", "")) or ""
)

# Diversity audit thresholds
DIVERSITY_VENDOR_CLUSTER_THRESHOLD = int(os.getenv("LLM_CV_DIVERSITY_VENDOR_THRESHOLD", "3"))
DIVERSITY_REFERRAL_RATE_MIN = float(os.getenv("LLM_CV_DIVERSITY_REFERRAL_MIN", "0.20"))
DIVERSITY_LOOKBACK_DAYS = int(os.getenv("LLM_CV_DIVERSITY_LOOKBACK_DAYS", "14"))


# ─── Candidate city table ─────────────────────────────────────────────────────
# Home base: Berlin. Every job location resolves to it unless you add more home
# cities to okf/profile.yaml and extend the table below.
CANDIDATE_CITIES = {
    "Berlin": (52.52, 13.40),
}

JOB_LOCATION_TO_CANDIDATE_CITY = {
    "Berlin": "Berlin, Germany",
    "Potsdam": "Berlin, Germany",
    "Remote": "Berlin, Germany",
    "Home Office": "Berlin, Germany",
    "Home-Office": "Berlin, Germany",
    "Deutschland": "Berlin, Germany",
    "Germany": "Berlin, Germany",
    "Nationwide": "Berlin, Germany",
}


def nearest_candidate_city(job_location: str) -> str:
    """Look up the nearest candidate city for a job location string.

    Uses the static JOB_LOCATION_TO_CANDIDATE_CITY table first, then falls back
    to a persistent location cache (okf/.location_cache.json) for locations
    previously resolved via web search. Returns None if the location is not
    found in either the table or the cache (caller should fall back to web
    search and then call cache_location_result() to store the answer).
    Normalizes input by stripping whitespace and trying case-insensitive match.
    """
    if not job_location:
        return None
    loc = job_location.strip()
    # Try exact match first
    if loc in JOB_LOCATION_TO_CANDIDATE_CITY:
        return JOB_LOCATION_TO_CANDIDATE_CITY[loc]
    # Try case-insensitive match
    loc_lower = loc.lower()
    for key, value in JOB_LOCATION_TO_CANDIDATE_CITY.items():
        if key.lower() == loc_lower:
            return value
    # Try substring match (e.g., "Munich, Germany" contains "Munich")
    for key, value in JOB_LOCATION_TO_CANDIDATE_CITY.items():
        if key.lower() in loc_lower:
            return value
    # Check the location cache (for locations previously resolved via web search)
    cached = _lookup_location_cache(loc)
    if cached:
        return cached
    # Single home city: any other location resolves to it.
    return CANDIDATE_LOCATION


# ─── Location web search cache ────────────────────────────────────────────────
# Caches results of web searches for job locations not in the static table.
# Geography doesn't change, so cache entries are permanent.

_LOCATION_CACHE_PATH = os.path.join(SKILL_DIR, "okf", ".location_cache.json")


def _load_location_cache() -> dict:
    """Load the location cache from disk."""
    try:
        if os.path.exists(_LOCATION_CACHE_PATH):
            with open(_LOCATION_CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _save_location_cache(cache: dict) -> None:
    """Save the location cache to disk."""
    try:
        os.makedirs(os.path.dirname(_LOCATION_CACHE_PATH), exist_ok=True)
        with open(_LOCATION_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _lookup_location_cache(job_location: str) -> str | None:
    """Check the location cache for a previously resolved location.

    Tries exact, case-insensitive, and substring matches (same strategy as
    the static table).
    """
    cache = _load_location_cache()
    if not cache:
        return None
    loc = job_location.strip()
    if loc in cache:
        return cache[loc]
    loc_lower = loc.lower()
    for key, value in cache.items():
        if key.lower() == loc_lower:
            return value
    for key, value in cache.items():
        if key.lower() in loc_lower:
            return value
    return None


def cache_location_result(job_location: str, nearest_city: str) -> None:
    """Store a web-search-resolved location in the persistent cache.

    Called by the pipeline after a web search resolves a location that wasn't
    in the static table. Future runs with the same location will hit the cache
    instead of doing another web search.
    """
    if not job_location or not nearest_city:
        return
    cache = _load_location_cache()
    cache[job_location.strip()] = nearest_city.strip()
    _save_location_cache(cache)


