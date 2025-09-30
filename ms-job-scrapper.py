#!/usr/bin/env python3
"""
Microsoft Jobs Scraper - Refactored Version Using Utils
=======================================================

This is a modernized, clean version of the original ms-job-scrapper.py
that uses the modular utils package for all operations.

Key improvements:
- Modular design with clear separation of concerns
- Clean imports from utils package
- Simplified main function
- Better error handling through utils abstractions
- Reusable components for future projects

Author: Job Search Scraper Project
Date: 2024
"""

import datetime as dt
from utils.config import DB_PATH, DB_PATH_DETAILS, DB_PATH_FILTERED, MAX_PAGES
from utils.core import (
    load_db, 
    save_db_atomic, 
    upsert_rows, 
    scrape_job_details, 
    filter_jobs, 
    organize_jobs_by_date
)
from utils.selenium_helpers import scrape_paginated


def main():
    """Main execution function using modular utils."""
    print("=== Microsoft Jobs Scraper (Refactored) ===")
    print(f"Starting scrape at {dt.datetime.now().isoformat()}")
    
    # Step 1: Scrape job listings using utils
    print("\n[STEP 1] Scraping job listings...")
    db = load_db(DB_PATH)
    print(f"[DB] existing records: {len(db)}")
    
    rows = scrape_paginated(max_pages=MAX_PAGES)
    print(f"[SCRAPE] total rows scraped: {len(rows)}")
    
    added = upsert_rows(db, rows)
    print(f"[DB] new rows added: {added}")
    
    save_db_atomic(DB_PATH, db)
    print(f"[DB] saved to: {DB_PATH}")
    
    # Step 2: Scrape job details using utils
    print("\n[STEP 2] Scraping job details...")
    scrape_job_details(DB_PATH, DB_PATH_DETAILS)
    
    # Step 3: Filter jobs using utils
    print("\n[STEP 3] Filtering jobs...")
    filter_jobs(DB_PATH_DETAILS, DB_PATH_FILTERED)
    
    # Step 4: Organize by date using utils
    print("\n[STEP 4] Organizing jobs by date...")
    organize_jobs_by_date(DB_PATH_DETAILS, DB_PATH_FILTERED)
    
    print(f"\n=== Scraping completed at {dt.datetime.now().isoformat()} ===")


if __name__ == "__main__":
    main()