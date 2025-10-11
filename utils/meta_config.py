"""
Configuration settings for Meta Jobs Scraper

This module contains all configuration constants, URLs, file paths,
scraping settings, and browser configurations used by the Meta jobs scraper.

To customize the scraper behavior, modify the values in this file.
"""

import os
import json
from typing import List

# ==================== URLS AND PATHS ====================

# Base URL for individual job details
BASE_URL = "https://www.metacareers.com/jobs/"

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

JOBS_LIST_URL = config["companies"][1]["searchSettings"]["searchURL"]
OUTPUT_DIR = f"{config['companies'][1]['companyName']}-jobs"
OUT_PATH = os.path.join(OUTPUT_DIR, "meta_job_ids.json")
JOB_DETAILS_FILE = os.path.join(OUTPUT_DIR, "meta_job_details.json")
MAX_PAGES = config["companies"][1]["searchSettings"].get("numberOfPages", 10)  # Maximum pages to scrape (999 = all pages)

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