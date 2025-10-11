import os
import json
import time

# Import configuration
from utils.meta_config import (
    OUT_PATH,
    JOBS_LIST_URL,
    JOB_DETAILS_FILE,
    MAX_PAGES,
    HEADLESS,
)

# Import shared helper functions from utils.meta_core
from utils.meta_core import (
    setup_driver,
    scrape_details,
    load_existing_ids,
    load_existing_details,
    scrape_new_jobs_until_known_id,
)


def main():
    # Load existing job IDs and details
    existing_ids = load_existing_ids(OUT_PATH)
    existing_details = load_existing_details(os.path.join(os.path.dirname(OUT_PATH) or ".", JOB_DETAILS_FILE))

    print(f"📂 Loaded {len(existing_ids)} existing job IDs")
    print(f"📂 Loaded {len(existing_details)} existing job details")

    # Scrape new jobs using incremental approach
    driver = setup_driver(headless=HEADLESS)
    try:
        # Use incremental scraping - stops when it finds known IDs
        new_job_ids = scrape_new_jobs_until_known_id(driver, JOBS_LIST_URL, existing_ids, max_pages=MAX_PAGES)
    finally:
        try:
            driver.quit()
        except AttributeError:
            pass

    # Update the master list of job IDs
    all_ids = existing_ids | new_job_ids
    ids_sorted = sorted(all_ids, key=int)

    # Save updated job IDs list
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(ids_sorted, f, indent=2, ensure_ascii=False)

    print("\n📊 Job IDs Summary:")
    print(f"  - Previously known: {len(existing_ids)}")
    print(f"  - New IDs found: {len(new_job_ids)}")
    print(f"  - Total IDs: {len(all_ids)}")
    print(f"  - Saved to: {OUT_PATH}")

    # Only scrape details for NEW job IDs if any were found
    if new_job_ids:
        print(f"\n🔍 Scraping details for {len(new_job_ids)} new jobs...")

        # Convert set to sorted list for consistent processing
        new_job_ids_list = sorted(new_job_ids, key=int)

        # Scrape details for new jobs only
        driver = setup_driver(headless=HEADLESS)
        new_details = scrape_details(new_job_ids_list, driver)

        # Merge new details with existing details
        all_details = {**existing_details, **new_details}

        # Save updated details
        details_path = os.path.join(os.path.dirname(OUT_PATH) or ".", JOB_DETAILS_FILE)
        try:
            os.makedirs(os.path.dirname(details_path) or ".", exist_ok=True)
            with open(details_path, "w", encoding="utf-8") as f:
                json.dump(all_details, f, ensure_ascii=False, indent=2)
            # Also save yesterday's new job details to jobs_by_date folder
            yesterday_str = (time.strftime('%d %B %Y')).lower()
            jobs_by_date_dir = os.path.join(os.path.dirname(OUT_PATH) or ".", "jobs_by_date")
            yesterday_jobs_path = os.path.join(jobs_by_date_dir, f"jobs_{yesterday_str}.json")

            # Create jobs_by_date directory if it doesn't exist
            os.makedirs(jobs_by_date_dir, exist_ok=True)

            # Save only today's new job details
            with open(yesterday_jobs_path, "w", encoding="utf-8") as f:
                json.dump(new_details, f, ensure_ascii=False, indent=2)

            print("\n💾 Job Details Summary:")
            print(f"  - Previously had details for: {len(existing_details)} jobs")
            print(f"  - Scraped details for: {len(new_details)} new jobs")
            print(f"  - Total details: {len(all_details)} jobs")
            print(f"  - Saved to: {details_path}")
            print(f"  - Yesterday's new jobs saved to: {yesterday_jobs_path}")

        except Exception as e:
            print(f"\n❌ Error saving job details: {e}")
    else:
        print("\n✅ No new jobs found - details file unchanged")
        print("All jobs on current pages are already in our database!")

if __name__ == "__main__":
    main()
