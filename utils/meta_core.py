"""
meta_core.py

Utility functions for scraping job listings and details from Meta Careers.
"""

import datetime as dt
import glob
import re
import json
import time
from pathlib import Path
from urllib.parse import urljoin
from typing import Dict, List, Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import os
import contextlib
import subprocess
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from bs4 import BeautifulSoup

# Import only required configuration from utils.meta_config
from utils.meta_config import (
    HEADLESS_OPTIONS,
    CHROME_OPTIONS,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    USER_AGENT,
    PAGE_LOAD_TIMEOUT,
    COOKIE_XPATHS,
    COOKIE_WAIT_TIMEOUT,
    SCROLL_PAUSE,
    SCROLL_ROUNDS,
    WHITESPACE_PATTERN,
    MAX_PREVIEW_ITEMS,
    MAX_PREVIEW_CHARS,
    JOB_LINKS_XPATH,
    JOB_ID_PATTERN,
    ELEMENT_WAIT_TIMEOUT,
    DELAY_BETWEEN_PAGES,
    DELAY_BETWEEN_JOBS,
    BASE_URL,
    REACT_RENDER_DELAY,
    JOB_DETAIL_CLASSES,
)

def setup_driver(headless: bool = True):
    """Create and return a configured Selenium Chrome WebDriver.

    This applies headless and other chrome options defined in the
    project's configuration and sets a page load timeout.

    Args:
        headless: If True, enable headless/browserless options from config.

    Returns:
        A configured instance of selenium.webdriver.Chrome.
    """
    opts = ChromeOptions()
    if headless:
        for option in HEADLESS_OPTIONS:
            opts.add_argument(option)
    
    # Add standard Chrome options from config
    for option in CHROME_OPTIONS:
        opts.add_argument(option)
    
    opts.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
    opts.add_argument(f"--user-agent={USER_AGENT}")
    # Reduce noisy logs
    opts.add_argument("--disable-logging")
    opts.add_argument("--log-level=3")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    # Configure Service to send logs to the null device and avoid creating a
    # visible child console on Windows.
    service_kwargs = {'log_path': os.devnull}
    if os.name == 'nt':
        service_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    # Create the driver while suppressing stdout/stderr so Chrome/Chromedriver
    # noisy messages don't appear in the user's terminal.
    with open(os.devnull, 'w', encoding='utf-8', errors='ignore') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            d = webdriver.Chrome(options=opts, service=Service(**service_kwargs))
    d.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return d


def accept_cookies_if_present(driver):
    """Attempt to accept cookie dialogs using configured XPATHs.

    Iterates over `COOKIE_XPATHS` and clicks the first clickable
    element found. Ignores timeouts and stale element errors so
    the caller can continue if no cookie banner is present.

    Args:
        driver: Selenium WebDriver instance already pointed at a page.
    """
    for xp in COOKIE_XPATHS:
        try:
            btn = WebDriverWait(driver, COOKIE_WAIT_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, xp)))
            btn.click()
            time.sleep(0.5)
            break
        except (TimeoutException, StaleElementReferenceException):
            pass


def scroll_infinite(driver, pause_s: float = SCROLL_PAUSE, rounds: int = SCROLL_ROUNDS):
    """Scroll the page to the bottom multiple times to trigger lazy loading.

    Performs `rounds` iterations of scrolling to the document bottom and
    waits `pause_s` seconds between iterations. Stops early if the
    document height does not change between rounds.

    Args:
        driver: Selenium WebDriver instance.
        pause_s: Seconds to wait between scroll rounds.
        rounds: Maximum number of scroll rounds to attempt.
    """
    last_h = driver.execute_script("return document.body.scrollHeight")
    for _ in range(rounds):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_s)
        h = driver.execute_script("return document.body.scrollHeight")
        if h == last_h:
            break
        last_h = h


def load_existing_ids(path: str) -> set:
    """Load existing job IDs from a JSON file and return as a set of strings.

    The function tolerates missing files and malformed JSON and only returns
    numeric-like IDs (strings made of digits). This is used to compare
    previously scraped job IDs when doing incremental scrapes.

    Args:
        path: Path to a JSON file containing a list or iterable of IDs.

    Returns:
        A set of numeric string IDs found in the file, or an empty set.
    """
    p = Path(path)
    if not p.exists():
        os.makedirs(p.parent, exist_ok=True)
        return set()
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Ensure they're numeric strings
        return {str(x) for x in data if isinstance(x, (str, int)) and str(x).isdigit()}
    except (OSError, json.JSONDecodeError):
        return set()


def load_existing_details(path: str) -> Dict[str, Any]:
    """Load existing job details from a JSON file.

    If the file is missing or contains invalid JSON an empty dict is returned.

    Args:
        path: Path to the JSON file with job detail records.

    Returns:
        A dict parsed from the file or an empty dict on error.
    """
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def clean(s: str) -> str:
    """Normalize whitespace and trim a string.

    Replaces runs of whitespace (including newlines and tabs) with a single
    space according to `WHITESPACE_PATTERN` from the configuration and strips
    leading/trailing whitespace. Accepts None safely.

    Args:
        s: Input string (or None).

    Returns:
        A cleaned string with normalized internal whitespace.
    """
    return re.sub(WHITESPACE_PATTERN, " ", s or "").strip()


def extract_from_div(soup: BeautifulSoup, class_name: str) -> Dict[str, List[str]]:
    """Extract text grouped by element classes from a DIV with `class_name`.

    Finds the first <div> with the provided class name and iterates its child
    tags collecting cleaned text grouped by the tag's class attribute. Useful
    for exploring the structure of job detail pages where sections share a
    container class.

    Args:
        soup: BeautifulSoup-parsed document.
        class_name: Class name of the container div to search for.

    Returns:
        A mapping of class-string -> list of texts extracted from elements.
    """
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
    """Pretty-print a compact preview of extracted class groups and texts.

    This helper prints up to `max_items` of the keys in `items` and a short
    preview of the text found for each key (truncated to `max_chars`). It is
    primarily used for debugging and understanding HTML structure during
    scraping.

    Args:
        items: Mapping of class-name -> list of extracted texts.
        label: Label used in the printed header.
        max_items: Maximum number of groups to show.
        max_chars: Maximum characters to display per group preview.
    """
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
    except (KeyError, IndexError, TypeError):
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

        # Wait for job links to appear
        try:
            WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, JOB_LINKS_XPATH))
            )
        except TimeoutException:
            print("No job links found on this page")
            return found_ids

        # Load content with scrolling
        scroll_infinite(driver)

        # Take all <a> with '/jobs' and extract numeric IDs
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
    
    except (TimeoutException, StaleElementReferenceException) as e:
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
    """Fetch job detail pages for a list of job IDs and extract structured fields.

    For each job ID the function builds the job URL (using `BASE_URL`), loads
    the page with Selenium, waits briefly for React to render, then uses
    BeautifulSoup and helper functions to extract fields such as title,
    location, qualifications and compensation.

    Args:
        list_of_job_ids: Iterable of job id strings to fetch.
        driver: Selenium WebDriver instance used to load pages.

    Returns:
        A dict mapping job_id -> extracted fields (title, URL, location, etc.).
    """
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

            results[job] = {
                "title": title,
                "URL": job_url,
                "location": location,
                "responsibilities": responsibilities,
                "minimum_qualifications": minimum_qualifications,
                "preferred_qualifications": preferred_qualifications,
                "compensation": compensation
            }
    except (TimeoutException, StaleElementReferenceException, json.JSONDecodeError) as e:
        print("Error:", e)
    return results

def cleanup_old_job_files(save_path: str) -> int:
    """Delete per-day job files older than 10 days from the jobs_by_date dir.

    The function expects files named like `jobs_dd_month_yyyy.json` and removes
    those older than the cutoff date.
    """

    cutoff_date = dt.date.today() - dt.timedelta(days=10)
    output_dir = f"{save_path}"
    output_dir = os.path.join(output_dir, "jobs_by_date")
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(output_dir):
        return 0
    
    # Find all job files
    pattern = os.path.join(output_dir, "jobs_*.json")
    job_files = glob.glob(pattern)
    
    files_removed = 0
    
    for filepath in job_files:
        filename = os.path.basename(filepath)
        
        # Extract date from filename (jobs_dd_month_yyyy.json)
        try:
            # Remove 'jobs_' prefix and '.json' suffix
            date_part = filename[5:-5]  # Remove 'jobs_' and '.json'
            
            # Parse the date format: dd_month_yyyy
            parts = date_part.split('_')
            if len(parts) >= 3:
                day = int(parts[0])
                month_name = parts[1]
                year = int(parts[2])
                
                # Convert month name to number
                month_names = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                
                month = month_names.get(month_name.lower())
                if month:
                    file_date = dt.date(year, month, day)
                    
                    if file_date < cutoff_date:
                        os.remove(filepath)
                        files_removed += 1
                        print(f"Removed old file: {filename} (date: {file_date})")
        except (ValueError, IndexError, KeyError) as e:
            print(f"Could not parse date from filename {filename}: {e}")
            continue
    
    if files_removed > 0:
        print(f"Removed {files_removed} old job files")
    else:
        print("No old job files found to remove")
    
    return files_removed
