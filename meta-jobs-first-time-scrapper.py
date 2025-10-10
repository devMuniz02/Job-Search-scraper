import os
import re
import json
import time
from pathlib import Path
from urllib.parse import urljoin
from typing import Dict, List, Any

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

def scrape_multiple_pages(driver, base_url: str, max_pages: int = 999) -> set:
    """
    Scrape job IDs from ALL available pages.
    Automatically stops when no more jobs are found.
    Returns a set of all unique job ID strings found.
    """
    all_found_ids = set()
    page_num = 1
    
    while page_num <= max_pages:
        # Construct URL for current page
        if page_num == 1:
            # First page doesn't have page parameter
            page_url = base_url
        else:
            # Pages 2+ use &page=2, &page=3, etc.
            page_url = f"{base_url}&page={page_num}"
        
        page_ids = scrape_jobs_from_page(driver, page_url)
        
        # If no IDs found on this page, we've reached the end
        if not page_ids:
            print(f"No job IDs found on page {page_num}. Reached end of available pages.")
            break
            
        all_found_ids.update(page_ids)
        print(f"Page {page_num}: Found {len(page_ids)} jobs (Total so far: {len(all_found_ids)})")
        
        # Add delay between pages to be respectful
        time.sleep(DELAY_BETWEEN_PAGES)
        page_num += 1
    
    print(f"Finished scraping. Total unique job IDs found across {page_num - 1} pages: {len(all_found_ids)}")
    return all_found_ids

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
                "responsibilities": responsibilities,  # (typo fixed)
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
    driver = setup_driver(headless=HEADLESS)
    try:
        # Use the new pagination function to scrape multiple pages
        found_ids = scrape_multiple_pages(driver, JOBS_LIST_URL, max_pages=MAX_PAGES)
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # Merge con JSON existente y guardar
    existing_ids = load_existing_ids(OUT_PATH)
    merged = existing_ids | found_ids
    new_count = len(merged) - len(existing_ids)

    ids_sorted = sorted(merged, key=lambda x: int(x))
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
    details_path = os.path.join(out_dir, JOB_DETAILS_FILE)
    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(details_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\nSaved {len(results)} jobs to {details_path}")
    except Exception as e:
        print(f"\n[Warn] Could not save results: {e}")

if __name__ == "__main__":
    main()