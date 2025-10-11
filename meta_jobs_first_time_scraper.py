"""Scrapes job IDs and details from Meta jobs and saves them to JSON files."""

import os
import json

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
    scrape_multiple_pages,
    scrape_details,
    load_existing_ids,
)

def main():
    driver = setup_driver(headless=HEADLESS)
    try:
        # Use the new pagination function to scrape multiple pages
        found_ids = scrape_multiple_pages(driver, JOBS_LIST_URL, max_pages=MAX_PAGES)
    finally:
        try:
            driver.quit()
        except AttributeError:
            pass

    # Merge con JSON existente y guardar
    existing_ids = load_existing_ids(OUT_PATH)
    merged = existing_ids | found_ids
    new_count = len(merged) - len(existing_ids)

    ids_sorted = sorted(merged, key=int)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(ids_sorted, f, indent=2, ensure_ascii=False)

    print(f"Found {len(found_ids)} IDs this run.")
    print(f"Existing file had {len(existing_ids)} IDs.")
    print(f"Added {new_count} new IDs. Saved {len(ids_sorted)} total to {OUT_PATH}.")

    # ---- Load job IDs correctly (don’t overwrite) ----
    with open(OUT_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        job_ids = [str(k) for k in raw.keys()]
    elif isinstance(raw, list):
        job_ids = [str(x) for x in raw]
    else:
        raise ValueError("OUT_PATH must contain a list of IDs or a dict keyed by IDs.")

    driver = setup_driver(headless=HEADLESS)

    results = scrape_details(job_ids, driver)

    # Optional: write results next to your OUT_PATH
    out_dir = os.path.dirname(OUT_PATH) or "."
    details_path = JOB_DETAILS_FILE
    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(details_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(results)} jobs to {details_path}")
    except (OSError, IOError) as e:
        print(f"\n[Warn] Could not save results: {e}")

if __name__ == "__main__":
    main()