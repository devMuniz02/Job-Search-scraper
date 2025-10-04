import os
import re
import json
import time
from pathlib import Path
from urllib.parse import urljoin
from typing import Dict, List, Any
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from bs4 import BeautifulSoup

# Import configuration
from utils.meta_config import *

def setup_driver(headless: bool = True):
    opts = ChromeOptions()
    if headless:
        for option in HEADLESS_OPTIONS:
            opts.add_argument(option)
    
    # Add standard Chrome options from config
    for option in CHROME_OPTIONS:
        opts.add_argument(option)
    
    opts.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
    opts.add_argument(f"--user-agent={USER_AGENT}")
    
    d = webdriver.Chrome(options=opts)
    d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return d

def accept_cookies_if_present(driver):
    for xp in COOKIE_XPATHS:
        try:
            btn = WebDriverWait(driver, COOKIE_WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, xp)))
            btn.click()
            time.sleep(0.5)
            break
        except Exception:
            pass

def scroll_infinite(driver, pause_s: float = SCROLL_PAUSE, rounds: int = SCROLL_ROUNDS):
    last_h = driver.execute_script("return document.body.scrollHeight")
    for _ in range(rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_s)
        h = driver.execute_script("return document.body.scrollHeight")
        if h == last_h:
            break
        last_h = h

def load_existing_ids(path: str) -> set:
    """Carga IDs existentes del JSON si existe; devuelve set de strings numéricas."""
    p = Path(path)
    if not p.exists():
        return set()
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Asegura que sean strings numéricas
        return {str(x) for x in data if isinstance(x, (str, int)) and str(x).isdigit()}
    except Exception:
        # Si el archivo está corrupto o con formato inesperado, ignóralo
        return set()

def load_existing_details(path: str) -> Dict[str, Any]:
    """Load existing job details from JSON file."""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def clean(s: str) -> str:
    return re.sub(WHITESPACE_PATTERN, " ", s or "").strip()

def extract_from_div(soup: BeautifulSoup, class_name: str) -> Dict[str, List[str]]:
    container = soup.find("div", class_=class_name)
    if not container:
        return {}
    class_groups: Dict[str, List[str]] = {}
    for tag in container.find_all(True):
        txt = clean(tag.get_text(" "))
        if not txt:
            continue
        tag_class = tag.get("class", [])
        class_str = " ".join(tag_class) if tag_class else "no-class"
        class_groups.setdefault(class_str, []).append(txt)
    return class_groups

def preview_items(items: Dict[str, List[str]], label: str, max_items: int = MAX_PREVIEW_ITEMS, max_chars: int = MAX_PREVIEW_CHARS):
    print(f"\n[Preview] {label}: found {len(items)} class groups")
    for i, (cls, texts) in enumerate(items.items()):
        if i >= max_items:
            print("... (more omitted)")
            break
        joined = " | ".join(texts[:3])
        if len(joined) > max_chars:
            joined = joined[:max_chars].rstrip() + "..."
        print(f"  [{i}] <{cls}> → {joined}")

def safe_pick(items: Dict[str, List[str]], key: str, idx: int = 0, label: str = "") -> str:
    """
    Try to pick items[key][idx]; if missing, preview available keys and return "".
    """
    try:
        return items[key][idx]
    except Exception:
        print(f"\n[Warn] Could not find key='{key}' idx={idx} in {label}.")
        preview_items(items, label=label)
        return ""

def scrape_jobs_from_page(driver, page_url: str) -> set:
    """
    Scrape job IDs from a single page.
    Returns a set of job ID strings.
    """
    found_ids = set()
    try:
        print(f"Scraping page: {page_url}")
        driver.get(page_url)
        accept_cookies_if_present(driver)

        # Espera a que aparezcan enlaces con "/jobs"
        try:
            WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, JOB_LINKS_XPATH))
            )
        except TimeoutException:
            print("No job links found on this page")
            return found_ids

        # Carga contenido con scroll
        scroll_infinite(driver)

        # Toma todos los <a> con '/jobs' y extrae IDs numéricos
        anchors = driver.find_elements(By.XPATH, JOB_LINKS_XPATH)
        for a in anchors:
            try:
                href = a.get_attribute("href") or ""
                if not href or "?page=" in href:
                    continue
                href = href if href.startswith("http") else urljoin("https://www.metacareers.com", href)
                m = re.search(JOB_ID_PATTERN, href)
                if m:
                    found_ids.add(m.group(1))
            except StaleElementReferenceException:
                continue
        
        print(f"Found {len(found_ids)} job IDs on this page")
        return found_ids
    
    except Exception as e:
        print(f"Error scraping page {page_url}: {e}")
        return found_ids

def scrape_new_jobs_until_known_id(driver, base_url: str, existing_ids: set, max_pages: int = 999) -> set:
    """
    Scrape job IDs from pages until we find a previously known ID.
    This implements incremental scraping - only get new jobs since last run.
    Returns a set of new job ID strings.
    """
    new_found_ids = set()
    page_num = 1
    
    print(f"Starting incremental scraping. Looking for new jobs not in {len(existing_ids)} existing IDs...")
    
    while page_num <= max_pages:
        # Construct URL for current page
        if page_num == 1:
            page_url = base_url
        else:
            page_url = f"{base_url}&page={page_num}"
        
        page_ids = scrape_jobs_from_page(driver, page_url)
        
        # If no IDs found on this page, we've reached the end
        if not page_ids:
            print(f"No job IDs found on page {page_num}. Reached end of available pages.")
            break
        
        # Check if any of the page IDs are already known (intersection)
        known_ids_on_page = page_ids & existing_ids
        new_ids_on_page = page_ids - existing_ids
        
        print(f"Page {page_num}: Found {len(page_ids)} total jobs")
        print(f"  - New jobs: {len(new_ids_on_page)}")
        print(f"  - Known jobs: {len(known_ids_on_page)}")
        
        # Add new IDs to our collection
        new_found_ids.update(new_ids_on_page)
        
        # If we found known IDs, we've reached content we've seen before
        if known_ids_on_page:
            print(f"\n✅ Found {len(known_ids_on_page)} previously known job(s) on page {page_num}.")
            print("This indicates we've reached content from previous scraping runs.")
            print("Stopping incremental scraping here to avoid duplicates.")
            break
        
        # Add delay between pages to be respectful
        time.sleep(DELAY_BETWEEN_PAGES)
        page_num += 1
    
    print("\n🎯 Incremental scraping complete!")
    print(f"📊 Total NEW job IDs found: {len(new_found_ids)}")
    print(f"📄 Pages scraped: {page_num}")
    
    return new_found_ids

def scrape_details(list_of_job_ids: List[str], driver) -> Dict[str, Any]:
    results: Dict[str, Any] = {}
    try:
        for job in list_of_job_ids:
            time.sleep(DELAY_BETWEEN_JOBS)  # gentle pacing
            job_url = BASE_URL + job
            print(f"\n=== Job ID {job} ===\nURL: {job_url}\n")
            driver.get(job_url)
            time.sleep(REACT_RENDER_DELAY)  # allow React to render

            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract data using class names from config
            items_1 = extract_from_div(soup, JOB_DETAIL_CLASSES["main_container"])
            items_2 = extract_from_div(soup, JOB_DETAIL_CLASSES["title_location_container"])

            # Extract fields using config mapping
            title = safe_pick(items_2, JOB_DETAIL_CLASSES["title_class"], 0, label="title/location block")
            location = safe_pick(items_2, JOB_DETAIL_CLASSES["location_class"], 0, label="title/location block")

            # The three stacked sections:
            responsibilities = safe_pick(items_1, JOB_DETAIL_CLASSES["sections_class"], 0, label="sections")
            minimum_qualifications = safe_pick(items_1, JOB_DETAIL_CLASSES["sections_class"], 1, label="sections")
            preferred_qualifications = safe_pick(items_1, JOB_DETAIL_CLASSES["sections_class"], 2, label="sections")

            # Compensation
            compensation = safe_pick(items_1, JOB_DETAIL_CLASSES["compensation_class"], 1, label="compensation")

            print("--- Extracted Data ---")
            print("Title:", title)
            print("Location:", location)
            print("Responsibilities:", responsibilities[:MAX_PREVIEW_CHARS] + ("..." if len(responsibilities) > MAX_PREVIEW_CHARS else ""))
            print("Minimum Qualifications:", minimum_qualifications[:MAX_PREVIEW_CHARS] + ("..." if len(minimum_qualifications) > MAX_PREVIEW_CHARS else ""))
            print("Preferred Qualifications:", preferred_qualifications[:MAX_PREVIEW_CHARS] + ("..." if len(preferred_qualifications) > MAX_PREVIEW_CHARS else ""))
            print("Compensation:", compensation)

            results[job] = {
                "title": title,
                "URL": job_url,
                "location": location,
                "responsibilities": responsibilities,
                "minimum_qualifications": minimum_qualifications,
                "preferred_qualifications": preferred_qualifications,
                "compensation": compensation
            }
    except Exception as e:
        print("Error:", e)
    
    finally:
        driver.quit()
    
    return results

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
        except Exception:
            pass

    # Update the master list of job IDs
    all_ids = existing_ids | new_job_ids
    ids_sorted = sorted(all_ids, key=lambda x: int(x))
    
    # Save updated job IDs list
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(ids_sorted, f, indent=2, ensure_ascii=False)

    print(f"\n📊 Job IDs Summary:")
    print(f"  - Previously known: {len(existing_ids)}")
    print(f"  - New IDs found: {len(new_job_ids)}")
    print(f"  - Total IDs: {len(all_ids)}")
    print(f"  - Saved to: {OUT_PATH}")

    # Only scrape details for NEW job IDs if any were found
    if new_job_ids:
        print(f"\n🔍 Scraping details for {len(new_job_ids)} new jobs...")
        
        # Convert set to sorted list for consistent processing
        new_job_ids_list = sorted(list(new_job_ids), key=lambda x: int(x))
        
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
            yesterday_str = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).strftime("%d %B %Y").lower()
            jobs_by_date_dir = os.path.join(os.path.dirname(OUT_PATH) or ".", "jobs_by_date")
            yesterday_jobs_path = os.path.join(jobs_by_date_dir, f"jobs_{yesterday_str}.json")
            
            # Create jobs_by_date directory if it doesn't exist
            os.makedirs(jobs_by_date_dir, exist_ok=True)
            
            # Save only today's new job details
            with open(yesterday_jobs_path, "w", encoding="utf-8") as f:
                json.dump(new_details, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Job Details Summary:")
            print(f"  - Previously had details for: {len(existing_details)} jobs")
            print(f"  - Scraped details for: {len(new_details)} new jobs")
            print(f"  - Total details: {len(all_details)} jobs")
            print(f"  - Saved to: {details_path}")
            print(f"  - Yesterday's new jobs saved to: {yesterday_jobs_path}")

        except Exception as e:
            print(f"\n❌ Error saving job details: {e}")
    else:
        print(f"\n✅ No new jobs found - details file unchanged")
        print("All jobs on current pages are already in our database!")

if __name__ == "__main__":
    main()