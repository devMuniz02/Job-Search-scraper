
import os
import re
import json
import time
import tempfile
import datetime as dt
import requests
import glob
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict, Any, List
from collections import defaultdict
import random
import contextlib
import subprocess

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException,
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    JavascriptException,
    InvalidElementStateException,
)

# ==================== CONFIGURATION ====================

from utils.ms_config import (
    LOCAL_CHROMEDRIVER,
    SLEEP_BETWEEN,
    MAX_PAGES,
    PAGE_LOAD_TIMEOUT,
    WAIT_PER_PAGE,
    SEARCH_URL,
    DELAY_AFTER_NEXT,
    LABELS,
    RESTART_EVERY,
    MAX_RETRIES,
    SCANNABLE_FIELDS,
    AVOID_RULES
)

# ==================== REGEX PATTERNS ====================

JOB_ID_FROM_ARIA = re.compile(r"Job item\s+(\d+)")
ISO_DATE_RE = re.compile(r"(20\d{2})-(\d{2})-(\d{2})")
USD_RANGE = re.compile(r"USD\s*\$\s*[\d,]+\s*-\s*\$\s*[\d,]+", re.I)
PAY_START = re.compile(
    r"(typical\s+base\s+pay\s+range|base\s+pay\s+range\s+for\s+this\s+role|benefits\s+and\s+pay\s+information|USD\s*\$\s*[\d,]+\s*-\s*\$\s*[\d,]+)",
    re.I
)
REQ_RE = re.compile(r"\bRequired\s+Qualifications\b", re.I)
PREF_RE = re.compile(r"\bPreferred\s+Qualifications\b", re.I)
OTHER_RE = re.compile(r"\bOther\s+Requirements?\b", re.I)

# ==================== UTILITIES ====================

def norm(s: str | None) -> str:
    """Normalize whitespace in a string.

    Collapses runs of whitespace (spaces, newlines, tabs) into a single space
    and trims leading/trailing whitespace. Accepts None and returns an empty
    string in that case.

    Args:
        s: Input string or None.

    Returns:
        Normalized string with collapsed whitespace.
    """
    return re.sub(r"\s+", " ", (s or "")).strip()

def sleep_a_bit():
    """Pause execution for a short, random duration to avoid hammering servers.

    The function sleeps twice with durations drawn from the configured
    `SLEEP_BETWEEN` range to create a small randomized delay between
    requests or page fetches.
    """
    time.sleep(random.uniform(*SLEEP_BETWEEN))
    time.sleep(random.uniform(*SLEEP_BETWEEN))

def parse_date(date_str):
    """Parse a date string into a datetime object.

    Tries a few common formats used in job postings. If parsing fails or the
    input is falsy, returns datetime.max to indicate an unknown/future date
    which sorts after real dates.

    Args:
        date_str: String containing a date to parse.

    Returns:
        datetime.datetime instance parsed from the string or datetime.max.
    """
    if not date_str:
        return dt.datetime.max
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%b %d, %Y."):
        try:
            return dt.datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return dt.datetime.max

# ==================== PERSISTENCE ====================

def load_db(path: str) -> list:
    """Load a JSON database file and return a list of job IDs or keys.

    The function supports files that contain either a list or a dict. If the
    file contains a dict, its keys are returned as the list of IDs. On error
    an empty list is returned.

    Args:
        path: Path to JSON file.

    Returns:
        A list of job IDs (possibly empty).
    """
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        # If it's a dict, return its keys as a list
        if isinstance(data, dict):
            return list(data.keys())
        return []
    except (json.JSONDecodeError, OSError):
        return []

def load_db_atomic(path: str) -> dict:
    """Load a JSON database file into a dict in an atomic-friendly shape.

    If the file contains a dict it is returned unchanged. If it contains a
    list of records the function will convert it into a dict keyed by the
    `job_id` or `url` field of each record for easier lookups.

    Args:
        path: Path to a JSON file to load.

    Returns:
        A dict representing the database (possibly empty on error).
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
        # Convert list to dict keyed by job_id or url
        out = {}
        for row in data:
            key = (row.get("job_id") or row.get("url"))
            if key:
                out[str(key)] = row
        return out
    except (json.JSONDecodeError, OSError):
        return {}

def save_db_atomic(path: str, data):
    """Atomically save data to a JSON file.

    Writes data to a temporary file in the same directory and then renames it
    into place to avoid partial writes. Sets are converted to lists before
    serialization.

    Args:
        path: Destination file path.
        data: Data to serialize (list, set, or dict).
    """
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="jobs_", suffix=".json", 
                                   dir=os.path.dirname(os.path.abspath(path)))
    os.close(fd)
    # Convert set to list for JSON serialization
    if isinstance(data, set):
        data = list(data)
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)

def upsert_rows(db: dict, rows: list) -> int:
    """Insert or update multiple rows into an in-memory database dict.

    For each row the function uses `job_id` or `url` as the key. If the key
    did not exist it is added and counted as a new addition; otherwise select
    fields are updated.

    Args:
        db: Mapping to mutate.
        rows: Iterable of row dicts to upsert.

    Returns:
        Number of rows newly added to `db`.
    """
    added = 0
    for row in rows:
        key = str(row.get("job_id") or row.get("url"))
        if not key:
            continue
        if key not in db:
            db[key] = row
            added += 1
        else:
            old = db[key]
            for fld in ("name", "url", "date_posted"):
                if row.get(fld):
                    old[fld] = row[fld]
    return added

def upsert_record(rec: Dict[str, Any], db: Dict[str, Any]) -> None:
    """Insert or merge a single record into the `db` mapping.

    Existing keys are updated only with non-empty values from `rec` to avoid
    clobbering previously extracted fields with empty values.

    Args:
        rec: Record dict containing at least a `job_id` or `url` to key by.
        db: Mapping to update in-place.
    """
    key = str(rec.get("job_id") or rec.get("url"))
    if not key:
        return
    if key not in db:
        db[key] = rec
    else:
        for k, v in rec.items():
            if v not in (None, "", []):
                db[key][k] = v

# ==================== SELENIUM SETUP ====================

session = requests.Session()
session.headers.update({"User-Agent": "MS-Careers-Scraper/1.5 (+you@example.com)"})

def launch_chrome():
    """Create and return a configured Selenium Chrome WebDriver for scraping.

    Applies several flags to improve reliability in headless or server
    environments, reduces logging, and optionally uses a local chromedriver
    binary if configured.

    Returns:
        A selenium.webdriver.Chrome instance.
    """
    opts = ChromeOptions()
    # Headless and basic flags
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,2000")

    # Disable GPU and use software rasterizer to avoid GLES3/GLES2 errors on some virtualized
    # or GPU-less environments. Also disable features that may try to use hardware acceleration.
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-software-rasterizer")
    opts.add_argument("--disable-accelerated-2d-canvas")
    opts.add_argument("--disable-accelerated-jpeg-decoding")
    opts.add_argument("--disable-accelerated-mjpeg-decode")
    # Force use of SwiftShader (software GL) as a fallback when GPU is unavailable.
    opts.add_argument("--use-gl=swiftshader")
    # Additional flags to reduce logging/noise
    opts.add_argument("--disable-logging")
    opts.add_argument("--log-level=3")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")

    # Reduce logging/noise from Chrome/Chromedriver
    opts.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)

    # Ensure chromedriver logs go to the platform null device
    service_kwargs = {'log_path': os.devnull}
    # On Windows, prevent child console windows / stdout by using CREATE_NO_WINDOW
    if os.name == 'nt':
        service_kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    # Create the driver while suppressing stdout/stderr so chrome/chromedriver
    # messages like 'DevTools listening on ...' or GPU errors don't leak to
    # the user's terminal.
    # open devnull with explicit encoding to satisfy static checkers
    with open(os.devnull, 'w', encoding='utf-8', errors='ignore') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            if LOCAL_CHROMEDRIVER:
                return webdriver.Chrome(service=Service(LOCAL_CHROMEDRIVER, **service_kwargs), options=opts)
            return webdriver.Chrome(options=opts, service=Service(**service_kwargs))

# ==================== JOB LISTING SCRAPER ====================

def with_page(url: str, page: int) -> str:
    """Return a copy of `url` with the query parameter `pg` set to `page`.

    Useful for paginating search URLs where the site uses `pg` as the page
    number parameter.
    """
    parts = list(urlparse(url))
    q = parse_qs(parts[4], keep_blank_values=True)
    q["pg"] = [str(page)]
    parts[4] = urlencode(q, doseq=True)
    return urlunparse(parts)

def find_cards(driver):
    """Locate job listing card elements on the current page.

    Returns the list of found Selenium elements representing job cards.
    """
    return driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')

def title_from_card(card):
    """Extract a job title string from a job card element.

    Tries to use an <h2> element if present; otherwise falls back to splitting
    the card text and returning the first non-empty line.
    """
    try:
        h2 = card.find_element(By.CSS_SELECTOR, "h2")
        t = (h2.text or "").strip()
        if t:
            return t
    except NoSuchElementException:
        pass
    txt = (card.text or "").strip()
    return txt.splitlines()[0].strip() if txt else None

def job_id_from_card(card):
    """Extract a job id from a card element using aria-label or outerHTML.

    The function first attempts to parse the aria-label text, then falls
    back to examining the card's outerHTML. Returns an integer job id or
    None if not found.
    """
    aria = card.get_attribute("aria-label") or ""
    m = JOB_ID_FROM_ARIA.search(aria)
    if m:
        return m.group(1)
    try:
        outer = card.parent.execute_script("return arguments[0].outerHTML;", card)
    except WebDriverException:
        outer = ""
    m2 = JOB_ID_FROM_ARIA.search(outer or "")
    return int(m2.group(1)) if m2 else None

def link_from_card(card, job_id):
    """Return the job detail URL present on the card or a generated fallback.

    If the card contains an anchor with the expected job URL it is returned;
    otherwise a fallback URL is constructed using the provided `job_id`.
    """
    try:
        a = card.find_element(By.CSS_SELECTOR, 'a[href*="/global/en/job/"]')
        href = a.get_attribute("href")
        if href:
            return href
    except NoSuchElementException:
        pass
    return f"https://jobs.careers.microsoft.com/global/en/job/{job_id}/" if job_id else None

def parse_date_posted_from_detail(html_text):
    """Extract the job's posted date from HTML using JSON-LD or heuristics.

    The function checks JSON-LD blocks for JobPosting data first, then
    falls back to regex searching, and finally looks for the word "Today"
    to return today's date.

    Args:
        html_text: Full HTML text of a job detail page.

    Returns:
        ISO-formatted date string (YYYY-MM-DD) or None if not found.
    """
    soup = BeautifulSoup(html_text, "html.parser")

    # Try JSON-LD first
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or ""
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") in {"JobPosting", "Posting"}:
                dp = item.get("datePosted") or item.get("dateCreated") or item.get("dateModified")
                if dp:
                    m = ISO_DATE_RE.search(dp)
                    if m:
                        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Fallback to regex search
    m2 = ISO_DATE_RE.search(html_text)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"

    # Check for "Today"
    text = soup.get_text(" ", strip=True)
    if "Today" in text:
        return dt.date.today().isoformat()
    return None

def click_next_if_possible(driver) -> bool:
    """Attempt to click a visible, enabled pagination "Next" control.

    Tries several selectors to locate the Next button, ensures it is visible
    and not disabled, clicks it and returns True. Returns False if no
    suitable control is found.
    """
    selectors = [
        (By.CSS_SELECTOR, 'button[aria-label*="Next"]'),
        (By.XPATH, "//button[(contains(., 'Next') or contains(@aria-label, 'Next'))]"),
        (By.XPATH, "//a[(contains(., 'Next') or contains(@aria-label, 'Next'))]")
    ]

    for by, sel in selectors:
        try:
            # use find_elements to avoid raising when element is absent
            candidates = driver.find_elements(by, sel)
            if not candidates:
                continue
            for btn in candidates:
                try:
                    if not btn.is_displayed():
                        continue
                    if btn.get_attribute("disabled") or btn.get_attribute("aria-disabled") == "true":
                        continue
                    # Try a normal click first, fallback to JS click if needed
                    try:
                        btn.click()
                    except (ElementClickInterceptedException, InvalidElementStateException, WebDriverException):
                        try:
                            driver.execute_script("arguments[0].click();", btn)
                        except (JavascriptException, WebDriverException):
                            # If clicking this candidate failed, try next
                            continue
                    return True
                except (StaleElementReferenceException, WebDriverException):
                    # Element went stale or other webdriver issue - try next candidate
                    continue
        except (WebDriverException, JavascriptException):
            # Catch any unexpected errors for robustness and try the next selector
            continue
    return False

def wait_for_new_page(driver, prev_ids, timeout=12) -> bool:
    """Wait until the job listing cards change after navigating pagination.

    Polls the page until new card ids appear or the number of cards changes
    compared to `prev_ids`. Returns True if a change was detected within the
    timeout, otherwise False.
    """
    t0 = time.time()
    last_count = len(prev_ids)
    while time.time() - t0 < timeout:
        time.sleep(0.8)
        cards = find_cards(driver)
        # No need to set protected member _parent; pass driver as needed
        curr_ids = set()
        for c in cards:
            jid = job_id_from_card(c)
            if jid:
                curr_ids.add(jid)
        if len(cards) != last_count or (curr_ids - prev_ids):
            return True
    return False

def scrape_paginated(max_pages=MAX_PAGES, seen_global_ids=None) -> List[Dict[str, Any]]:
    """Scrape multiple pages of job listings from the configured SEARCH_URL.

    Navigates pagination using the site's controls when possible and falls
    back to constructing page URLs. Returns a tuple of (new_ids_list,
    seen_global_ids_set).
    """
    driver = launch_chrome()
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    wait = WebDriverWait(driver, WAIT_PER_PAGE)

    # Start at page 1
    driver.get(SEARCH_URL)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"]')))
    except TimeoutException:
        pass

    new_ids = []
    seen_global_ids = set(seen_global_ids) or set()
    current_page = 1
    page_already_seen = False

    while current_page <= max_pages:
        cards = find_cards(driver)

        print(f"[PAGE {current_page}] cards found: {len(cards)}")

        page_ids = set()
        for card in cards:
            jid = job_id_from_card(card)
            if jid:
                if jid in seen_global_ids:
                    page_already_seen = True
                    print(f"  - already seen job id {jid}, stopping pagination.")
                    break
                new_ids.append(jid)
                seen_global_ids.add(jid)

        # Check if we're done (fewer than 20 cards)
        if len(cards) < 20 or page_already_seen:
            break

        # Try to go to next page
        clicked = click_next_if_possible(driver)
        if clicked:
            changed = wait_for_new_page(driver, page_ids, timeout=12)
            if not changed:
                next_url = with_page(SEARCH_URL, current_page + 1)
                driver.get(next_url)
                try:
                    WebDriverWait(driver, WAIT_PER_PAGE).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"]'))
                    )
                except (TimeoutException, WebDriverException):
                    # Timeout waiting for elements or other webdriver error
                    pass
        else:
            next_url = with_page(SEARCH_URL, current_page + 1)
            driver.get(next_url)
            try:
                WebDriverWait(driver, WAIT_PER_PAGE).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"]'))
                )
            except (TimeoutException, WebDriverException):
                pass

        time.sleep(DELAY_AFTER_NEXT)
        current_page += 1

    driver.quit()
    return new_ids, seen_global_ids

# ==================== DETAIL SCRAPER ====================

def extract_pay_ranges(text: str) -> List[Dict[str, str]]:
    """Find USD pay ranges in free text and return them with a region hint.

    Scans `text` for patterns that look like USD pay ranges and returns a
    list of dicts each containing a `region` and the matched `range` string.
    Duplicates are removed preserving order.
    """
    spans = []
    for m in USD_RANGE.finditer(text):
        s, e = m.span()
        ctx = text[max(0, s-140): min(len(text), e+140)]
        region = "U.S."
        if re.search(r"San\s*Francisco\s*Bay|New\s*York\s*City", ctx, re.I):
            region = "SF Bay Area / NYC"
        spans.append({"region": region, "range": m.group(0)})
    
    # Remove duplicates
    uniq, seen = [], set()
    for r in spans:
        key = (r["region"], r["range"])
        if key not in seen:
            seen.add(key)
            uniq.append(r)
    return uniq

def extract_locations_jsonld(html_text: str) -> List[str]:
    """Extract location(s) from JSON-LD <script type="application/ld+json"> blocks.

    Returns a deduplicated list of human-readable location strings built from
    the JSON-LD `jobLocation` address fields when present.
    """
    out = []
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except (ValueError, TypeError, json.JSONDecodeError):
            # Skip invalid JSON-LD blocks
            continue
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and it.get("@type") in {"JobPosting", "Posting"}:
                jl = it.get("jobLocation")
                if isinstance(jl, dict):
                    jl = [jl]
                if isinstance(jl, list):
                    for loc in jl:
                        addr = (loc or {}).get("address", {})
                        parts = [addr.get("addressLocality"), addr.get("addressRegion"), addr.get("addressCountry")]
                        parts = [p for p in parts if p]
                        if parts:
                            out.append(", ".join(parts))
    return list(dict.fromkeys(out))

def block_text_from_html(html: str) -> str:
    """Convert arbitrary HTML into readable block text preserving bullets.

    Traverses the HTML and converts list items into lines starting with a
    bullet character and paragraphs/divs into separate lines. Consecutive
    duplicate lines are removed.
    """
    soup = BeautifulSoup(html, "html.parser")
    pieces = []
    for node in soup.descendants:
        if isinstance(node, NavigableString):
            continue
        if node.name in ("ul", "ol"):
            for li in node.select(":scope > li"):
                t = norm(li.get_text(" ", strip=True))
                if t:
                    pieces.append("• " + t)
        elif node.name in ("p", "div", "section"):
            t = norm(node.get_text(" ", strip=True))
            if t:
                pieces.append(t)
    
    # Remove consecutive duplicates
    out = []
    for p in pieces:
        if not out or p != out[-1]:
            out.append(p)
    return "\n".join(out)

def find_span(text: str, pattern: re.Pattern, start_at: int = 0):
    """Return the (start, end) span of `pattern` in `text` or (None, None).

    This small helper wraps re.search to return the numeric span or a pair
    of Nones when no match is found.
    """
    m = pattern.search(text, start_at)
    return (m.start(), m.end()) if m else (None, None)

def slice_between(text: str, start_pat: re.Pattern, end_pats: tuple, start_offset_to_content=True) -> str:
    """Extract and return the substring between `start_pat` and the nearest end pattern.

    Finds the first match of `start_pat` and then looks for the earliest
    match among `end_pats` after the start. If no end pattern is found the
    slice runs until the end of the text.
    """
    s0, s1 = find_span(text, start_pat)
    if s0 is None:
        return ""
    start = s1 if start_offset_to_content else s0
    ends = []
    for ep in end_pats:
        e0, _ = find_span(text, ep, start_at=start)
        if e0 is not None:
            ends.append(e0)
    stop = min(ends) if ends else len(text)
    return text[start:stop].strip()

def split_qualifications(qual_text: str):
    """Split a qualifications block into required, preferred and other texts.

    Uses configured regex patterns to locate section headers and returns a
    tuple of (required_text, preferred_text, other_text). Falls back to
    alternate heuristics if explicit headers can't be found.
    """
    q = qual_text
    pay_start_idx, _ = find_span(q, PAY_START)
    pay_enders = (PAY_START,) if pay_start_idx is not None else ()

    required_text = slice_between(q, REQ_RE, (OTHER_RE, PREF_RE))
    other_text = slice_between(q, OTHER_RE, (PREF_RE,))
    preferred_text = slice_between(q, PREF_RE, pay_enders)

    # Fallbacks
    if not required_text and REQ_RE.search(q):
        required_text = slice_between(q, REQ_RE, pay_enders)
    if not other_text and OTHER_RE.search(q):
        other_text = slice_between(q, OTHER_RE, pay_enders)
    if not preferred_text and PREF_RE.search(q):
        preferred_text = slice_between(q, PREF_RE, ())

    return required_text, preferred_text, other_text

def safe_text(el) -> str | None:
    """Safely extract normalized text from a Selenium element.

    Returns None when the element is not accessible or .text raises an
    exception.
    """
    try:
        return norm(el.text)
    except (AttributeError, StaleElementReferenceException, WebDriverException):
        # AttributeError if element doesn't have .text; StaleElementReference if DOM changed
        return None

def parse_detail_page(url: str, driver: webdriver.Chrome) -> Dict[str, Any]:
    """Load a job detail page and extract structured fields.

    The function navigates to `url`, waits for the page to render, and
    extracts fields such as title, locations, travel, qualifications and
    pay ranges using a combination of Selenium lookups and HTML parsing.

    Args:
        url: Full URL to the job detail page.
        driver: Selenium WebDriver used to load the page.

    Returns:
        A dict containing extracted fields including `job_id`, `title`,
        `date_posted`, `locations`, and qualification text blobs.
    """
    driver.get(url)
    WebDriverWait(driver, 35).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    time.sleep(0.7)

    # Find title by looking for "Date posted" anchor
    dp = WebDriverWait(driver, 25).until(
        EC.presence_of_element_located((By.XPATH, "//*[normalize-space()='Date posted']"))
    )
    title_el = dp.find_element(By.XPATH, "preceding::h1[1]")
    title = safe_text(title_el)

    # Find the panel containing both title and "Date posted"
    panel = title_el.find_element(By.XPATH, "ancestor::*[.//*[normalize-space()='Date posted']][1]")

    # Extract location
    location = None
    try:
        cand = panel.find_element(By.XPATH, ".//h1/following::*[normalize-space()][1]")
        txt = safe_text(cand)
        if txt and not any(x in txt for x in ("Apply", "Save", "Share job")):
            location = txt
    except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
        # Missing element or DOM/driver issue - leave location as None
        pass

    # Extract field values
    def value_for(label: str) -> str | None:
        try:
            lab = panel.find_element(By.XPATH, f".//*[normalize-space()='{label}' or normalize-space()='{label}:']")
        except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
            return None
        for rel in ["./following-sibling::*[normalize-space()][1]", "following::*[normalize-space()][1]"]:
            try:
                node = lab.find_element(By.XPATH, rel)
                val = safe_text(node)
                if val:
                    return val
            except (NoSuchElementException, StaleElementReferenceException, WebDriverException):
                # Try next relation if current one fails
                pass
        return None

    fields = {lab: value_for(lab) for lab in LABELS}

    # Extract qualifications HTML
    q_html = ""
    try:
        qh = panel.find_element(By.XPATH, ".//h2[normalize-space()='Qualifications'] | .//h3[normalize-space()='Qualifications']")
        frag, sib = [], qh
        for _ in range(160):
            try:
                sib = sib.find_element(By.XPATH, "following-sibling::*[1]")
            except NoSuchElementException:
                break
            tg = sib.tag_name.lower()
            if tg in ("h2", "h3"):
                break
            frag.append(sib.get_attribute("outerHTML"))
        q_html = "".join(frag)
    except NoSuchElementException:
        pass

    qualifications_text = block_text_from_html(q_html) if q_html else ""
    req_text, pref_text, other_text = split_qualifications(qualifications_text)
    pay_ranges = extract_pay_ranges(qualifications_text)

    # Fallback location extraction
    if not location:
        jl = extract_locations_jsonld(driver.page_source)
        if jl:
            location = " | ".join(jl)

    # Extract job ID
    m = re.search(r"/job/(\d+)", driver.current_url)
    job_id = fields.get("Job number") or (m.group(1) if m else None)

    return {
        "job_id": job_id,
        "title": title,
        "url": driver.current_url,
        "date_posted": fields.get("Date posted"),
        "locations": [location] if location else [],
        "travel": fields.get("Travel"),
        "required_qualifications_text": req_text,
        "other_requirements_text": other_text,
        "preferred_qualifications_text": pref_text,
        "qualifications_text": qualifications_text,
        "pay_ranges": pay_ranges,
    }

def scrape_job_details(job_ids, output_path: str):
    """Fetch and store detailed job records for a list of job IDs.

    Builds canonical job URLs for each job_id, skips already present
    entries in `output_path`, and periodically restarts the browser to
    reduce resource leaks. Saves progress atomically to the output file.

    Args:
        job_ids: Iterable of job IDs (or strings convertible to int).
        output_path: Path where job details will be saved as JSON.
    """
    
    # Build URLs
    urls = []
    seen = set()
    for job_id in job_ids:
        url = f"https://jobs.careers.microsoft.com/global/en/job/{int(job_id)}/"
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    details_db = load_db_atomic(output_path)
    
    drv = None
    processed = 0
    
    try:
        print(f"[DETAILS] processing {len(urls)} job pages…")
        for i, url in enumerate(urls, 1):
            key = re.search(r"/job/(\d+)", url)
            key = key.group(1) if key else url

            if key in details_db:
                print(f"[{i}/{len(urls)}] SKIP already saved: {key}")
                continue

            # Restart browser periodically
            if drv is None or (processed > 0 and processed % RESTART_EVERY == 0):
                if drv:
                    print(f"   - restarting browser after {RESTART_EVERY} jobs")
                    drv.quit()
                    time.sleep(2)
                drv = launch_chrome()

            print(f"[{i}/{len(urls)}] GET {url}")
            success = False

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    rec = parse_detail_page(url, drv)
                    upsert_record(rec, details_db)
                    processed += 1
                    success = True
                    break
                except (WebDriverException, TimeoutException, NoSuchElementException, requests.RequestException) as e:
                    print(f"   ! attempt {attempt} failed: {e}")
                    if "chrome" in str(e).lower() or "session" in str(e).lower():
                        try:
                            drv.quit()
                        except (WebDriverException, AttributeError):
                            # If quitting the driver fails, ignore and recreate
                            pass
                        time.sleep(2)
                        drv = launch_chrome()
                    time.sleep(1.0)

            if not success:
                print(f"   x failed all attempts: {url}")

            # Checkpoint save
            if processed and processed % 5 == 0:
                save_db_atomic(output_path, details_db)
                print(f"   - checkpoint saved ({processed} records)")

            sleep_a_bit()

    finally:
        save_db_atomic(output_path, details_db)
        if drv:
            drv.quit()

    print(f"[DONE] wrote {len(details_db)} records to {output_path}")

# ==================== JOB FILTERING ====================

def to_text(val: Any) -> str:
    """Convert a field value into lowercase searchable text.

    Handles lists, dicts and scalars, producing a normalized single string
    that can be used for keyword matching.
    """
    if val is None:
        return ""
    if isinstance(val, list):
        parts = []
        for x in val:
            if isinstance(x, dict):
                parts.append(json.dumps(x, ensure_ascii=False))
            else:
                parts.append(str(x))
        return norm(" | ".join(parts)).lower()
    if isinstance(val, dict):
        return norm(json.dumps(val, ensure_ascii=False)).lower()
    return norm(str(val)).lower()

def get_job_id(key: str, rec: Dict[str, Any]) -> str:
    """Return the canonical job id string for a record or key.

    Prefers `rec['job_id']` when present, otherwise attempts to parse an id
    from the `url` or falls back to returning the provided `key`.
    """
    if rec.get("job_id"):
        return str(rec["job_id"])
    m = re.search(r"/job/(\d+)", rec.get("url") or key or "")
    return m.group(1) if m else (rec.get("url") or key or "UNKNOWN")

def iter_scannable_fields(rec: Dict[str, Any]):
    """Yield the field names from `SCANNABLE_FIELDS` that exist in `rec`.

    This helper restricts scanning to the configured set of fields.
    """
    for f in SCANNABLE_FIELDS:
        if f in rec:
            yield f

def kw_boundary_search(blob: str, kw: str) -> bool:
    """Return True if `kw` appears in `blob` using word-boundary matching.

    Uses a regex that avoids matching substrings inside larger words.
    """
    return re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", blob, re.I) is not None

def materialize_field_keywords(per_field: Dict[str, List[str]], available_fields: List[str]) -> Dict[str, List[str]]:
    """Expand wildcard '*' keywords into specific available fields.

    Returns a mapping of field -> sorted keyword list for only the fields
    present in `available_fields`.
    """
    result = {}
    wild = per_field.get("*", [])
    for field in available_fields:
        kws = set(wild)
        if field in per_field:
            kws.update(per_field[field])
        if kws:
            result[field] = sorted(kws)
    return result

def filter_jobs(details_path: str, output_path: str):
    """Scan job detail records and produce buckets of hits based on rules.

    Loads the details database from `details_path`, checks each record using
    `AVOID_RULES`, and writes a JSON summary of hits to `output_path`.
    """
    details = load_db(details_path)
    hits_out = {}
    total = 0
    total_hits = 0

    for key, rec in details.items():
        total += 1
        job_id = get_job_id(key, rec)

        # Cache field text
        available_fields = list(iter_scannable_fields(rec))
        field_blob = {f: to_text(rec.get(f)) for f in available_fields}

        for cls, per_field in AVOID_RULES.items():
            field_kws = materialize_field_keywords(per_field, available_fields)
            if not field_kws:
                continue

            matched_fields = {}
            for field, kws in field_kws.items():
                blob = field_blob.get(field, "")
                if not blob:
                    continue
                found = [kw for kw in kws if kw_boundary_search(blob, kw)]
                if found:
                    matched_fields[field] = sorted(set(found))

            if matched_fields:
                bucket = hits_out.setdefault(cls, {"job_ids": [], "matches": {}})
                if job_id not in bucket["job_ids"]:
                    bucket["job_ids"].append(job_id)
                    total_hits += 1
                bucket["matches"][job_id] = matched_fields

    # Sort and clean up
    for cls, bucket in list(hits_out.items()):
        bucket["job_ids"] = sorted(bucket["job_ids"], key=lambda x: (len(str(x)), str(x)))
        if not bucket["job_ids"]:
            del hits_out[cls]

    save_db_atomic(output_path, hits_out)
    
    print(f"[FILTER] scanned {total} jobs from {details_path}")
    print(f"[FILTER] wrote hits to {output_path}")
    for cls in sorted(hits_out.keys()):
        print(f"  - {cls}: {len(hits_out[cls]['job_ids'])} job(s)")

    return hits_out

# ==================== JOB ORGANIZATION ====================

def cleanup_old_jobs(details_path: str, days: int = 10) -> list[str]:
    """Remove job detail records older than `days` from the database.

    Parses the `date_posted` field of each record and removes entries older
    than the cutoff. Returns the list of removed job ids for further
    cleanup in the main jobs DB.
    """
    
    cutoff_date = dt.date.today() - dt.timedelta(days=days)
    print(f"Removing jobs older than: {cutoff_date}")
    
    details_db = load_db_atomic(details_path)
    original_count = len(details_db)
    removed_count = 0
    
    # Find jobs to remove
    jobs_to_remove = []
    for job_id, job in details_db.items():
        date_posted = job.get('date_posted', 'unknown')
        
        if date_posted and date_posted != 'unknown':
            try:
                parsed_date = parse_date(date_posted)
                if parsed_date != dt.datetime.max:
                    job_date = parsed_date.date()
                    if job_date < cutoff_date:
                        jobs_to_remove.append(job_id)
            except (ValueError, TypeError) as e:
                # Log parsing errors but continue
                print(f"Error parsing date for job {job_id}: {e}")
    
    # Remove old jobs
    for job_id in jobs_to_remove:
        del details_db[job_id]
        removed_count += 1
    
    # Save updated database
    if removed_count > 0:
        save_db_atomic(details_path, details_db)
        print(f"Removed {removed_count} old jobs from {details_path}")
        print(f"Jobs remaining: {len(details_db)} (was {original_count})")
    else:
        print("No old jobs found to remove")
    
    # Return the list of removed job IDs for cleanup in main DB
    return jobs_to_remove

def cleanup_main_jobs_db(main_db_path: str, old_job_ids: list = None):
    """Remove a list of job IDs from the main jobs list and persist changes.

    Args:
        main_db_path: Path to the main jobs JSON (list) file.
        old_job_ids: Iterable of job id strings to remove. If None, nothing is done.

    Returns:
        Number of removed entries.
    """

    main_db_ids = set(load_db(main_db_path))
    original_count = len(main_db_ids)
    removed_count = 0
    
    if old_job_ids:
        print(f"Cleaning main jobs DB - removing {len(old_job_ids)} old job IDs")
        
        # Remove jobs by ID
        for job_id in old_job_ids:
            if job_id in main_db_ids:
                main_db_ids.remove(job_id)
                removed_count += 1
        
        # Save updated database
        if removed_count > 0:
            save_db_atomic(main_db_path, main_db_ids)
            print(f"Removed {removed_count} old jobs from {main_db_path}")
            print(f"Jobs remaining: {len(main_db_ids)} (was {original_count})")
        else:
            print("No matching old jobs found to remove from main DB")
    else:
        print("No old job IDs provided - skipping main DB cleanup")
    
    return removed_count

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

def organize_jobs_by_date(save_path: str, details_path: str, filtered_path: str = None):
    """Group filtered jobs by their posted date and write per-date JSON files.

    Uses `filtered_path` to restrict the set of jobs when provided and writes
    files into `{save_path}/jobs_by_date` with a filename-safe date token.
    """
    # Load data
    details_db = load_db_atomic(details_path)

    if filtered_path is None or not os.path.exists(filtered_path):
        print("[ORGANIZE] no filtered path provided or file does not exist, skipping filtering step.")
        wanted_jobs = set(details_db.keys())
    else:
        filtered_db = load_db(filtered_path)

        # Calculate wanted Python jobs
        python_jobs = set(filtered_db.get('knowledge_python', {}).get('job_ids', []))
        knowledge_fullstack = set(filtered_db.get('knowledge_fullstack', {}).get('job_ids', []))
        clearance_required = set(filtered_db.get('clearance_required', {}).get('job_ids', []))
        visa_sponsorship_block = set(filtered_db.get('visa_sponsorship_block', {}).get('job_ids', []))
        unwanted_positions = set(filtered_db.get('unwanted_positions', {}).get('job_ids', []))
        senior_only = set(filtered_db.get('senior_only', {}).get('job_ids', []))
        
        wanted_jobs = python_jobs - knowledge_fullstack - clearance_required - visa_sponsorship_block - unwanted_positions - senior_only
        
        print(f"Total Python jobs: {len(python_jobs)}")
        print(f"Total knowledge fullstack jobs: {len(knowledge_fullstack)}")
        print(f"Total wanted Python jobs: {len(wanted_jobs)}")

    # Group jobs by date
    jobs_by_date = defaultdict(list)

    for job_id in wanted_jobs:
        job = details_db.get(job_id, {})
        date_posted = job.get('date_posted', 'unknown')
        
        # Create filename-friendly date
        if date_posted and date_posted != 'unknown':
            try:
                parsed_date = parse_date(date_posted)
                if parsed_date != dt.datetime.max:
                    filename_date = parsed_date.strftime("%d_%B_%Y").lower()
                else:
                    filename_date = date_posted.replace("-", "_").replace(" ", "_").replace(",", "")
            except (ValueError, TypeError):
                filename_date = date_posted.replace("-", "_").replace(" ", "_").replace(",", "")
        else:
            filename_date = "unknown_date"
        
        jobs_by_date[filename_date].append({
            "job_id": job_id,
            "title": job.get('title'),
            "locations": job.get('locations'),
            "travel": job.get('travel'),
            "date_posted": date_posted,
            "url": job.get('url'),
            "required_qualifications_text": job.get('required_qualifications_text'),
            "preferred_qualifications_text": job.get('preferred_qualifications_text'),
            "other_requirements_text": job.get('other_requirements_text'),
            "pay_ranges": job.get('pay_ranges')
        })
    
    # Save files
    output_dir = f"{save_path}"
    output_dir = os.path.join(output_dir, "jobs_by_date")
    os.makedirs(output_dir, exist_ok=True)
    
    date_today = dt.date.today().strftime("%d_%B_%Y").lower()
    date_yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime("%d_%B_%Y").lower()
    files_created = 0
    jobs_saved = 0
    for date_str, jobs_list in jobs_by_date.items():
        filename = f"jobs_{date_str}.json"
        filepath = os.path.join(output_dir, filename)
        if os.path.exists(filepath) and date_str not in [date_today, date_yesterday]:  # If file path exists, append a suffix to avoid overwriting
            continue
        else:
            if date_str in [date_today, date_yesterday]:
                print(f"Overwriting file for date {date_str}: {filepath}")
            else:
                print(f"Creating new file for date {date_str}: {filepath}")

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(jobs_list, f, ensure_ascii=False, indent=2)
            
            print(f"Saved {len(jobs_list)} jobs to {filepath}")
            files_created += 1
            jobs_saved += len(jobs_list)

    print(f"Total files created/overwritten: {files_created}")
    print(f"Total jobs saved: {jobs_saved}")
