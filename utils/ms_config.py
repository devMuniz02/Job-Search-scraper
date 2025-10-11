"""
Configuration settings for Microsoft Jobs Scraper

This module contains all configuration constants, URLs, file paths,
scraping settings, and filtering rules used by the scraper.
"""

from typing import Dict, List
import json

with open("config.json", encoding="utf-8") as f:
    config = json.load(f)

# URLs and paths
SEARCH_URL = config["companies"][0]["searchSettings"]["searchURL"]
FOLDER = f"{config['companies'][0]['companyName']}-jobs"
DB_PATH = f"{FOLDER}/ms_job_ids.json"
DB_PATH_DETAILS = f"{FOLDER}/ms_job_details.json"
DB_PATH_FILTERED = f"{FOLDER}/ms_jobs_avoid_hits_by_field.json"
DAYS_TO_KEEP = config["scrapingSettings"].get("daysToKeep", 10)

FILTERS = config["companies"][0].get("filters", None)

# Scraping settings
MAX_PAGES = config["companies"][0]["searchSettings"].get("numberOfPages", 10)
PAGE_LOAD_TIMEOUT = 60
WAIT_PER_PAGE = 25
DELAY_AFTER_NEXT = 1.2
SLEEP_BETWEEN = (2.0, 5.0)  # (min, max) delay between detail requests
MAX_RETRIES = 2
RESTART_EVERY = 10  # Restart browser every N jobs

# Optional: local chromedriver path
LOCAL_CHROMEDRIVER = ""

# Detail scraping labels
LABELS = [
    "Date posted", "Work site", "Role type", "Discipline",
    "Job number", "Travel", "Profession", "Employment type"
]

# Job filtering rules
AVOID_RULES: Dict[str, Dict[str, List[str]]] = {
    "visa_sponsorship_block": {
        "title": ["no sponsorship", "no visa"],
        "qualifications_text": ["without sponsorship"],
        "other_requirements_text": ["citizens only", "citizenship required", "citizenship is required", 
                                   "U.S. citizens", "US citizens", "green card", "permanent resident"],
    },
    "senior_only": {
        "title": ["principal only", "senior only"],
        "required_qualifications_text": ["6+ years", "10+ years", "12+ years"],
    },
    "clearance_required": {
        "other_requirements_text": ["security clearance", "public trust", "polygraph"],
    },
    "knowledge_fullstack": {
        "required_qualifications_text": ["HTML", "React", "Node.js", "REST", "Full Stack", "Full-Stack", 
                                        "Fullstack", "Front End", "Frontend", "Back End", "Backend", "API",
                                        "Angular", "Vue.js", "Django", "Flask", "Ruby on Rails", "PHP", 
                                        "http", "HTTP", "HTTPS", "https"],
    },
    "unwanted_languages": {
        "required_qualifications_text": ["java", "javascript", "c#", "c-sharp", "c plus plus", "c++", 
                                        "ruby", "php", "swift", "kotlin", "go ", "golang", "r ", 
                                        "perl", "scala", "haskell", "lua"],
    },
    "knowledge_python": {
        "*": ["python"],
    },
    "unwanted_positions": {
        "title": ["finance", "accounting", "recruiter", "recruitment", 
                  "salesforce", "sales force", "sales", "marketing", 
                  "legal", "attorney", "lawyer", "paralegal", "compliance",
                  "human resources", "hr ", "talent acquisition", "talent management",
                  "UX designer", "user experience", "graphic designer", "ui designer",
                  "technical writer", "content writer", "copywriter"],
        "required_qualifications_text": ["finance", "accounting", "recruiter", "recruitment",
                                        "salesforce", "sales force", "sales", "marketing",
                                        "legal", "attorney", "lawyer", "paralegal", "compliance",
                                        "human resources", "hr ", "talent acquisition", "talent management",
                                        "UX designer", "user experience", "graphic designer", "ui designer",
                                        "technical writer", "content writer", "copywriter"],
    }
}

SCANNABLE_FIELDS: List[str] = [
    "title", "locations", "travel", "qualifications_text",
    "required_qualifications_text", "preferred_qualifications_text",
    "other_requirements_text", "date_posted",
]
