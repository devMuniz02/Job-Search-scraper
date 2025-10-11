#!/usr/bin/env python3
"""
Microsoft Jobs Scraper
Automated script for scraping Microsoft job postings, extracting details, 
filtering by criteria, and organizing by date.

Usage: python ms-job-scrapper.py
"""

import datetime as dt
from utils.ms_core import (
    scrape_paginated,
    scrape_job_details,
    filter_jobs,
    organize_jobs_by_date,
    cleanup_old_jobs,
    cleanup_main_jobs_db,
    cleanup_old_job_files,
    load_db,
    save_db_atomic,
    DB_PATH, DB_PATH_DETAILS, DB_PATH_FILTERED, FOLDER, FILTERS, DAYS_TO_KEEP, MAX_PAGES
)

def main():
    """Main execution function."""

    print("Paths:", DB_PATH, DB_PATH_DETAILS, DB_PATH_FILTERED)
    print("=== Microsoft Jobs Scraper ===")
    print(f"Starting scrape at {dt.datetime.now().isoformat()}")
    
    # Step 1: Scrape job listings
    print("\n[STEP 1] Scraping job listings...")
    previous_job_ids = load_db(DB_PATH)
    print(f"[DB] existing records: {len(previous_job_ids)}")

    new_job_ids, all_job_ids = scrape_paginated(max_pages=MAX_PAGES, seen_global_ids=previous_job_ids)
    print(f"[SCRAPE] total rows scraped: {len(new_job_ids)}")
    print(f"[SCRAPE] sample rows: {new_job_ids}")
    print(f"[SCRAPE] total unique job ids: {len(all_job_ids)}")

    save_db_atomic(DB_PATH, all_job_ids)
    print(f"[DB] saved to: {DB_PATH}")
    
    # Step 2: Scrape job details
    print("\n[STEP 2] Scraping job details...")
    scrape_job_details(new_job_ids, DB_PATH_DETAILS)
    
    # # Step 3: Filter jobs
    if FILTERS is None:
        print("\n[STEP 3] No filters defined, skipping filtering step.")
        # Step 4: Organize by date
        print("\n[STEP 4] Organizing jobs by date...")
        organize_jobs_by_date(FOLDER, DB_PATH_DETAILS)

    else:
        print("\n[STEP 3] Filtering jobs...")
        filter_jobs(DB_PATH_DETAILS, DB_PATH_FILTERED)
    
        # Step 4: Organize by date
        print("\n[STEP 4] Organizing jobs by date...")
        organize_jobs_by_date(FOLDER, DB_PATH_DETAILS, DB_PATH_FILTERED)

    # Step 5: Cleanup old jobs from details DB and main jobs DB
    print(f"\n[STEP 5] Cleaning up old jobs from details and main DB up to {DAYS_TO_KEEP} days old...")
    
    old_job_ids = cleanup_old_jobs(DB_PATH_DETAILS, days=DAYS_TO_KEEP)
    print(f"Total old jobs removed from details DB: {len(old_job_ids)}")
    
    removed_count = cleanup_main_jobs_db(DB_PATH, old_job_ids)
    print(f"Total old jobs removed from main DB: {removed_count}")
    
    files_removed = cleanup_old_job_files(FOLDER)
    print(f"Total files removed in jobs by date: {files_removed}")

    print(f"\n=== Scraping completed at {dt.datetime.now().isoformat()} ===")

if __name__ == "__main__":
    main()