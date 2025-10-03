"""
Configuration settings for Meta Jobs Scraper

This module contains all configuration constants, URLs, file paths,
scraping settings, and browser configurations used by the Meta jobs scraper.

To customize the scraper behavior, modify the values in this file.
"""

import os
from typing import List

# ==================== URLS AND PATHS ====================

# Base URL for individual job details
BASE_URL = "https://www.metacareers.com/jobs/"

# URL for job listings page
JOBS_LIST_URL = "https://www.metacareers.com/jobs?sort_by_new=true&offices[0]=North%20America"

# Output file paths
OUTPUT_DIR = "meta-jobs"
JOB_IDS_FILE = "meta_job_ids.json"
JOB_DETAILS_FILE = "meta_job_details.json"

# Full paths (can be overridden by environment variables)
OUT_PATH = os.getenv("OUT", f"{OUTPUT_DIR}/{JOB_IDS_FILE}")
DETAILS_PATH = f"{OUTPUT_DIR}/{JOB_DETAILS_FILE}"

# ==================== SCRAPING SETTINGS ====================

# Browser settings
HEADLESS = os.getenv("HEADFUL", "0") != "1"  # Set HEADFUL=1 to see browser
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# Browser window size
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900

# Page loading and timeouts
PAGE_LOAD_TIMEOUT = 60  # seconds
ELEMENT_WAIT_TIMEOUT = 20  # seconds for job links to appear
COOKIE_WAIT_TIMEOUT = 3  # seconds to wait for cookie buttons

# Scrolling settings
SCROLL_ROUNDS = int(os.getenv("SCROLL_ROUNDS", "6"))  # Number of scroll rounds per page
SCROLL_PAUSE = 1.0  # Seconds to pause between scrolls

# Pagination settings
MAX_PAGES = int(os.getenv("MAX_PAGES", "999"))  # Maximum pages to scrape (999 = all pages)

# Delays and rate limiting
DELAY_BETWEEN_PAGES = 7  # Seconds to wait between pages
DELAY_BETWEEN_JOBS = 2  # Seconds to wait between job detail requests
REACT_RENDER_DELAY = 5  # Seconds to wait for React to render job details

# ==================== CSS SELECTORS AND XPATHS ====================

# XPath selectors for cookie acceptance
COOKIE_XPATHS: List[str] = [
    "//button[contains(.,'Accept')]",
    "//button[contains(.,'Agree')]",
    "//button[contains(.,'Aceptar')]",
    "//*[@aria-label[contains(.,'Accept')]]"
]

# XPath for job links
JOB_LINKS_XPATH = "//a[contains(@href,'/jobs')]"

# CSS class names for job detail extraction
JOB_DETAIL_CLASSES = {
    "main_container": "_8muv _ar_h",
    "title_location_container": "_a6jl _armv",
    "title_class": "_army",
    "location_class": "_ar_e",
    "sections_class": "_h46 _8lfy _8lfy",  # Used for responsibilities, qualifications
    "compensation_class": "_1n-_ _6hy- _94t2"
}

# ==================== CHROME BROWSER OPTIONS ====================

CHROME_OPTIONS: List[str] = [
    "--no-sandbox",
    "--disable-gpu", 
    "--disable-dev-shm-usage",
    "--lang=en-US"
]

# Additional options for headless mode
HEADLESS_OPTIONS: List[str] = [
    "--headless=new"
]

# ==================== DATA EXTRACTION SETTINGS ====================

# Maximum length for preview text in debug output
MAX_PREVIEW_CHARS = 200
MAX_PREVIEW_ITEMS = 6

# Job detail field mapping
JOB_FIELDS = {
    "title": {"container": "title_location_container", "class": "title_class", "index": 0},
    "location": {"container": "title_location_container", "class": "location_class", "index": 0},
    "responsibilities": {"container": "main_container", "class": "sections_class", "index": 0},
    "minimum_qualifications": {"container": "main_container", "class": "sections_class", "index": 1},
    "preferred_qualifications": {"container": "main_container", "class": "sections_class", "index": 2},
    "compensation": {"container": "main_container", "class": "compensation_class", "index": 1}
}

# ==================== REGEX PATTERNS ====================

# Pattern to extract job IDs from URLs
JOB_ID_PATTERN = r"/jobs/(\d+)$"

# Pattern to clean whitespace
WHITESPACE_PATTERN = r"\s+"

# ==================== ENVIRONMENT VARIABLE DOCUMENTATION ====================

"""
Environment Variables that can be used to override settings:

- HEADFUL: Set to "1" to run browser in visible mode (default: headless)
- SCROLL_ROUNDS: Number of scroll rounds per page (default: 6)
- MAX_PAGES: Maximum pages to scrape, 999 means all (default: 999)
- OUT: Custom output path for job IDs file (default: meta-jobs/meta_job_ids.json)

Examples:
    HEADFUL=1 python first-meta-jobs-scrapper.py    # Run with visible browser
    MAX_PAGES=10 python first-meta-jobs-scrapper.py  # Limit to 10 pages
    SCROLL_ROUNDS=10 python first-meta-jobs-scrapper.py  # More scrolling per page
"""