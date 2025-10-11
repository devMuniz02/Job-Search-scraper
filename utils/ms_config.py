"""
Configuration settings for Microsoft Jobs Scraper

This module contains all configuration constants, URLs, file paths,
scraping settings, and filtering rules used by the scraper.
"""

from typing import Dict, List, Tuple

# ==================== SCRAPING SETTINGS ====================

PAGE_LOAD_TIMEOUT = 60
WAIT_PER_PAGE = 25
DELAY_AFTER_NEXT = 1.2
SLEEP_BETWEEN: Tuple[float, float] = (0.6, 1.2)  # (min, max) delay between detail requests
MAX_RETRIES = 2
RESTART_EVERY = 10  # Restart browser every N jobs

# Optional: local chromedriver path
LOCAL_CHROMEDRIVER = ""

# ==================== FIELD DEFINITIONS ====================

# Detail scraping labels
LABELS: List[str] = [
    "Date posted", "Work site", "Role type", "Discipline",
    "Job number", "Travel", "Profession", "Employment type"
]

# Fields that should be scanned during filtering
SCANNABLE_FIELDS: List[str] = [
    "title", "locations", "travel", "qualifications_text",
    "required_qualifications_text", "preferred_qualifications_text",
    "other_requirements_text", "date_posted",
]

# ==================== JOB FILTERING RULES ====================

AVOID_RULES: Dict[str, Dict[str, List[str]]] = {
    "visa_sponsorship_block": {
        "title": ["no sponsorship", "no visa"],
        "qualifications_text": ["without sponsorship"],
        "other_requirements_text": [
            "citizens only", "citizenship required", "citizenship is required", 
            "U.S. citizens", "US citizens", "green card", "permanent resident"
        ],
    },
    "senior_only": {
        "title": ["principal only", "senior only"],
        "required_qualifications_text": ["6+ years", "10+ years", "12+ years"],
    },
    "clearance_required": {
        "other_requirements_text": ["security clearance", "public trust", "polygraph"],
    },
    "knowledge_fullstack": {
        "required_qualifications_text": [
            "HTML", "React", "Node.js", "REST", "Full Stack", "Full-Stack", 
            "Fullstack", "Front End", "Frontend", "Back End", "Backend", "API",
            "Angular", "Vue.js", "Django", "Flask", "Ruby on Rails", "PHP", 
            "http", "HTTP", "HTTPS", "https"
        ],
    },
    "unwanted_languages": {
        "required_qualifications_text": [
            "java", "javascript", "c#", "c-sharp", "c plus plus", "c++", 
            "ruby", "php", "swift", "kotlin", "go ", "golang", "r ", 
            "perl", "scala", "haskell", "lua"
        ],
    },
    "knowledge_python": {
        "*": ["python"],
    },
    "unwanted_positions": {
        "title": [
            "finance", "accounting", "recruiter", "recruitment", 
            "salesforce", "sales force", "sales", "marketing", 
            "legal", "attorney", "lawyer", "paralegal", "compliance",
            "human resources", "hr ", "talent acquisition", "talent management",
            "UX designer", "user experience", "graphic designer", "ui designer",
            "technical writer", "content writer", "copywriter"
        ],
        "required_qualifications_text": [
            "finance", "accounting", "recruiter", "recruitment",
            "salesforce", "sales force", "sales", "marketing",
            "legal", "attorney", "lawyer", "paralegal", "compliance",
            "human resources", "hr ", "talent acquisition", "talent management",
            "UX designer", "user experience", "graphic designer", "ui designer",
            "technical writer", "content writer", "copywriter"
        ],
    }
}

# ==================== REQUEST SETTINGS ====================

# User agent for HTTP requests
USER_AGENT = "MS-Careers-Scraper/1.5 (+you@example.com)"

# Timeout settings
HTTP_TIMEOUT = 25

# ==================== CHROME OPTIONS ====================

CHROME_OPTIONS = [
    "--headless=new",
    "--disable-gpu", 
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--window-size=1400,2000"
]

# ==================== DETAIL PAGE EXTRACTION ====================

# Field extraction labels
LABELS = [
    "Date posted",
    "Job number",
    "Work site",
    "Employment type",
    "Role type",
    "Team",
    "Discipline",
    "Profession",
    "Up to",
    "Career stage",
    "Travel"
]

# Browser control settings
RESTART_EVERY = 20
MAX_RETRIES = 3

# ==================== PROJECT-LEVEL DEFAULTS (from top-level config.json) ====
# These are convenience defaults so utils can reference common project paths.
import json
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
_cfg_path = _root / "config.json"

SEARCH_URL = ""
DB_PATH = "ms-jobs/ms_job_ids.json"
DB_PATH_DETAILS = "ms-jobs/ms_job_details.json"
DB_PATH_FILTERED = "ms-jobs/ms_jobs_avoid_hits_by_field.json"
MAX_PAGES = 10

try:
    if _cfg_path.exists():
        with open(_cfg_path, "r", encoding="utf-8") as _f:
            _c = json.load(_f)
        companies = _c.get("companies") or []
        if companies:
            c0 = companies[0]
            SEARCH_URL = c0.get("searchSettings", {}).get("searchURL", SEARCH_URL)
            MAX_PAGES = c0.get("searchSettings", {}).get("numberOfPages", MAX_PAGES)
            folder = f"{c0.get('companyName','ms')}-jobs"
            DB_PATH = f"{folder}/ms_job_ids.json"
            DB_PATH_DETAILS = f"{folder}/ms_job_details.json"
            DB_PATH_FILTERED = f"{folder}/ms_jobs_avoid_hits_by_field.json"
except (OSError, json.JSONDecodeError):
    # If reading config fails, fall back to defaults defined above
    pass
