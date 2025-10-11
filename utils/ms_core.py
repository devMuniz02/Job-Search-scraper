
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

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

# ==================== CONFIGURATION ====================
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
    """Normalize whitespace in string."""
    return re.sub(r"\s+", " ", (s or "")).strip()

def sleep_a_bit():
    """Sleep for a random duration between requests."""
    time.sleep(random.uniform(*SLEEP_BETWEEN))
    time.sleep(random.uniform(*SLEEP_BETWEEN))

def parse_date(date_str):
    """Parse various date formats, fallback to max date if missing."""
    if not date_str:
        return dt.datetime.max
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%b %d, %Y."):
        try:
            return dt.datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return dt.datetime.max

# ==================== PERSISTENCE ====================

def load_db(path: str) -> list:
    """Load JSON database file containing a list of job IDs."""
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
    except Exception:
        return []

def load_db_atomic(path: str) -> dict:
    """Load JSON database file."""
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
    except Exception:
        return {}

def save_db_atomic(path: str, data):
    """Atomically save data (list, set, or dict) to JSON file."""
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
    """Insert or update rows in database, return count of new additions."""
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
    """Upsert a single record into database."""
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
    """Launch Chrome browser with appropriate options."""
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

    # Reduce logging/noise from Chrome/Chromedriver
    opts.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)

    service_kwargs = {}
    try:
        # Windows: null device
        service_kwargs['log_path'] = 'NUL'
    except Exception:
        # Fallback: let Service decide
        pass

    if LOCAL_CHROMEDRIVER:
        return webdriver.Chrome(service=Service(LOCAL_CHROMEDRIVER, **service_kwargs), options=opts)
    return webdriver.Chrome(options=opts, service=Service(**service_kwargs))

# ==================== JOB LISTING SCRAPER ====================

def with_page(url: str, page: int) -> str:
    """Modify URL to set specific page number."""
    parts = list(urlparse(url))
    q = parse_qs(parts[4], keep_blank_values=True)
    q["pg"] = [str(page)]
    parts[4] = urlencode(q, doseq=True)
    return urlunparse(parts)

def find_cards(driver):
    """Find job listing cards on the page."""
    return driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')

def title_from_card(card):
    """Extract job title from card element."""
    try:
        h2 = card.find_element(By.CSS_SELECTOR, "h2")
        t = (h2.text or "").strip()
        if t:
            return t
    except Exception:
        pass
    txt = (card.text or "").strip()
    return txt.splitlines()[0].strip() if txt else None

def job_id_from_card(card):
    """Extract job ID from card element."""
    aria = card.get_attribute("aria-label") or ""
    m = JOB_ID_FROM_ARIA.search(aria)
    if m:
        return m.group(1)
    try:
        outer = card._parent.execute_script("return arguments[0].outerHTML;", card)
    except Exception:
        outer = ""
    m2 = JOB_ID_FROM_ARIA.search(outer or "")
    return int(m2.group(1)) if m2 else None

def link_from_card(card, job_id):
    """Extract job URL from card element."""
    try:
        a = card.find_element(By.CSS_SELECTOR, 'a[href*="/global/en/job/"]')
        href = a.get_attribute("href")
        if href:
            return href
    except Exception:
        pass
    return f"https://jobs.careers.microsoft.com/global/en/job/{job_id}/" if job_id else None

def parse_date_posted_from_detail(html_text):
    """Extract date posted from job detail page HTML."""
    soup = BeautifulSoup(html_text, "html.parser")

    # Try JSON-LD first
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = tag.string or ""
        try:
            data = json.loads(raw)
        except Exception:
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
    """Try to click the Next pagination button."""
    selectors = [
        (By.CSS_SELECTOR, 'button[aria-label*="Next"]:not([disabled]):not([aria-disabled="true"])'),
        (By.XPATH, "//button[(contains(., 'Next') or contains(@aria-label, 'Next')) and not(@disabled) and not(@aria-disabled='true')]"),
        (By.XPATH, "//a[(contains(., 'Next') or contains(@aria-label, 'Next')) and not(contains(@class,'disabled'))]"),
    ]
    for by, sel in selectors:
        try:
            btn = driver.find_element(by, sel)
            if not btn.is_displayed():
                continue
            if btn.get_attribute("disabled") or btn.get_attribute("aria-disabled") == "true":
                continue
            btn.click()
            return True
        except Exception:
            continue
    return False

def wait_for_new_page(driver, prev_ids, timeout=12) -> bool:
    """Wait for page to change after clicking Next."""
    t0 = time.time()
    last_count = len(prev_ids)
    while time.time() - t0 < timeout:
        time.sleep(0.8)
        cards = find_cards(driver)
        for c in cards:
            try:
                c._parent = driver
            except Exception:
                pass
        curr_ids = set()
        for c in cards:
            jid = job_id_from_card(c)
            if jid:
                curr_ids.add(jid)
        if len(cards) != last_count or (curr_ids - prev_ids):
            return True
    return False

def scrape_paginated(max_pages=MAX_PAGES, seen_global_ids=None) -> List[Dict[str, Any]]:
    """Scrape job listings from multiple pages."""
    driver = launch_chrome()
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    wait = WebDriverWait(driver, WAIT_PER_PAGE)

    # Start at page 1
    driver.get(SEARCH_URL)
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"]')))
    except Exception:
        pass

    new_ids = []
    seen_global_ids = set(seen_global_ids) or set()
    current_page = 1
    page_already_seen = False

    while current_page <= max_pages:
        cards = find_cards(driver)
        for c in cards:
            try:
                c._parent = driver
            except Exception:
                pass

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
                except Exception:
                    pass
        else:
            next_url = with_page(SEARCH_URL, current_page + 1)
            driver.get(next_url)
            try:
                WebDriverWait(driver, WAIT_PER_PAGE).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"]'))
                )
            except Exception:
                pass

        time.sleep(DELAY_AFTER_NEXT)
        current_page += 1

    driver.quit()
    return new_ids, seen_global_ids

# ==================== DETAIL SCRAPER ====================

def extract_pay_ranges(text: str) -> List[Dict[str, str]]:
    """Extract pay ranges from text."""
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
    """Extract job locations from JSON-LD structured data."""
    out = []
    soup = BeautifulSoup(html_text, "html.parser")
    for tag in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except Exception:
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
    """Convert HTML to block text preserving bullet points."""
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
    """Find pattern span in text."""
    m = pattern.search(text, start_at)
    return (m.start(), m.end()) if m else (None, None)

def slice_between(text: str, start_pat: re.Pattern, end_pats: tuple, start_offset_to_content=True) -> str:
    """Extract text between patterns."""
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
    """Split qualifications text into required, preferred, and other sections."""
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
    """Safely extract text from element."""
    try:
        return norm(el.text)
    except Exception:
        return None

def parse_detail_page(url: str, driver: webdriver.Chrome) -> Dict[str, Any]:
    """Parse a job detail page and extract structured information."""
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
    except Exception:
        pass

    # Extract field values
    def value_for(label: str) -> str | None:
        try:
            lab = panel.find_element(By.XPATH, f".//*[normalize-space()='{label}' or normalize-space()='{label}:']")
        except Exception:
            return None
        for rel in ["./following-sibling::*[normalize-space()][1]", "following::*[normalize-space()][1]"]:
            try:
                node = lab.find_element(By.XPATH, rel)
                val = safe_text(node)
                if val:
                    return val
            except Exception:
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
            except Exception:
                break
            tg = sib.tag_name.lower()
            if tg in ("h2", "h3"):
                break
            frag.append(sib.get_attribute("outerHTML"))
        q_html = "".join(frag)
    except Exception:
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
    """Scrape detailed information for all jobs in the input database."""
    
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
                except Exception as e:
                    print(f"   ! attempt {attempt} failed: {e}")
                    if "chrome" in str(e).lower() or "session" in str(e).lower():
                        try:
                            drv.quit()
                        except:
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
    """Convert any field to searchable text."""
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
    """Extract job ID from record."""
    if rec.get("job_id"):
        return str(rec["job_id"])
    m = re.search(r"/job/(\d+)", rec.get("url") or key or "")
    return m.group(1) if m else (rec.get("url") or key or "UNKNOWN")

def iter_scannable_fields(rec: Dict[str, Any]):
    """Iterate over fields that should be scanned."""
    for f in SCANNABLE_FIELDS:
        if f in rec:
            yield f

def kw_boundary_search(blob: str, kw: str) -> bool:
    """Search for keyword with word boundaries."""
    return re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", blob, re.I) is not None

def materialize_field_keywords(per_field: Dict[str, List[str]], available_fields: List[str]) -> Dict[str, List[str]]:
    """Merge wildcard keywords into specific fields."""
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
    """Filter jobs based on defined rules."""
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
    """Remove jobs older than 10 days from the database."""
    
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
            except Exception as e:
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
    """Remove jobs from the main jobs database using job IDs from details cleanup."""

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
    """Remove job files older than 10 days from ms-jobs/jobs_by_date/."""

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
    """Organize filtered Python jobs by date posted."""
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
            except Exception:
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
