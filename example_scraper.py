#!/usr/bin/env python3
"""
Example: Microsoft Jobs Scraper Using Utils

This script demonstrates how to use the extracted utility modules
to build a job scraper with better code organization.
"""

import requests
from typing import List, Dict, Any

# Import utilities from our utils package
from utils import (
    load_db, save_db_atomic, upsert_rows, parse_date_posted_from_detail,
    sleep_a_bit, extract_pay_ranges, extract_locations_jsonld,
    launch_chrome, find_cards, title_from_card, job_id_from_card,
    link_from_card, click_next_if_possible, wait_for_new_page,
    wait_for_elements, SEARCH_URL, DB_PATH, MAX_PAGES, PAGE_LOAD_TIMEOUT,
    USER_AGENT, HTTP_TIMEOUT
)


def fetch_job_details(url: str) -> Dict[str, Any]:
    """Fetch detailed job information from a job URL."""
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    
    try:
        response = session.get(url, timeout=HTTP_TIMEOUT, allow_redirects=True)
        date_posted = parse_date_posted_from_detail(response.text)
        pay_ranges = extract_pay_ranges(response.text)
        locations = extract_locations_jsonld(response.text)
        
        return {
            "date_posted": date_posted,
            "pay_ranges": pay_ranges,
            "locations": locations,
            "final_url": response.url
        }
    except Exception as e:
        print(f"Error fetching details for {url}: {e}")
        return {}


def scrape_job_listings(max_pages: int = 3) -> List[Dict[str, Any]]:
    """
    Scrape job listings using the utility functions.
    
    This is a simplified example demonstrating the modular approach.
    """
    driver = launch_chrome()
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    
    try:
        # Navigate to the search page
        driver.get(SEARCH_URL)
        
        # Wait for job cards to load
        if not wait_for_elements(driver, 'div[role="listitem"]'):
            print("No job cards found on the page")
            return []
        
        all_jobs = []
        current_page = 1
        
        while current_page <= max_pages:
            print(f"Scraping page {current_page}...")
            
            # Find all job cards on current page
            cards = find_cards(driver)
            print(f"Found {len(cards)} job cards")
            
            page_ids = set()
            
            for card in cards:
                # Extract basic job information
                job_id = job_id_from_card(card)
                title = title_from_card(card)
                url = link_from_card(card, job_id)
                
                if job_id:
                    page_ids.add(job_id)
                
                if url:
                    # Fetch additional details
                    details = fetch_job_details(url)
                    sleep_a_bit()  # Be respectful with requests
                    
                    job_data = {
                        "job_id": job_id,
                        "title": title,
                        "url": url,
                        **details
                    }
                    all_jobs.append(job_data)
            
            # Try to navigate to next page
            if current_page < max_pages:
                clicked = click_next_if_possible(driver)
                if clicked:
                    # Wait for page to change
                    if not wait_for_new_page(driver, page_ids):
                        print("Failed to load next page")
                        break
                else:
                    print("No next page button found")
                    break
            
            current_page += 1
        
        return all_jobs
    
    finally:
        driver.quit()


def save_jobs_to_database(jobs: List[Dict[str, Any]]) -> None:
    """Save scraped jobs to the database using utility functions."""
    # Load existing database
    db = load_db(DB_PATH)
    
    # Add new jobs
    added_count = upsert_rows(db, jobs)
    
    # Save back to database
    save_db_atomic(DB_PATH, db)
    
    print(f"Added {added_count} new jobs to database")
    print(f"Total jobs in database: {len(db)}")


def main():
    """Main execution function demonstrating the modular approach."""
    print("Starting Microsoft Jobs Scraper with Utils...")
    print("="*50)
    
    try:
        # Scrape job listings
        jobs = scrape_job_listings(max_pages=2)  # Limited to 2 pages for demo
        
        if jobs:
            print(f"\nSuccessfully scraped {len(jobs)} jobs")
            
            # Show sample job data
            sample_job = jobs[0]
            print(f"\nSample job:")
            print(f"  Title: {sample_job.get('title')}")
            print(f"  Job ID: {sample_job.get('job_id')}")
            print(f"  Date Posted: {sample_job.get('date_posted')}")
            print(f"  Locations: {sample_job.get('locations', [])}")
            print(f"  Pay Ranges: {len(sample_job.get('pay_ranges', []))} found")
            
            # Save to database
            save_jobs_to_database(jobs)
            
        else:
            print("No jobs found")
    
    except Exception as e:
        print(f"Error during scraping: {e}")
        return 1
    
    print("\nScraping completed successfully!")
    return 0


if __name__ == "__main__":
    exit(main())