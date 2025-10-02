"""
Core utility functions for Microsoft Jobs Scraper

This module contains reusable utility functions organized by category
for better maintainability and reusability.
"""

import os
import re
import json
import time
import tempfile
import datetime as dt
from typing import Dict, Any, List, Tuple, Optional, Union
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Import patterns from the patterns module
from .patterns import USD_RANGE, PAY_START, REQ_RE, PREF_RE, OTHER_RE, ISO_DATE_RE

# ==================== STRING UTILITIES ====================

def norm(s: Union[str, None]) -> str:
    """Normalize whitespace in string."""
    return re.sub(r"\s+", " ", (s or "")).strip()


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


def kw_boundary_search(blob: str, kw: str) -> bool:
    """Search for keyword with word boundaries."""
    return re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", blob, re.I) is not None


# ==================== DATE UTILITIES ====================

def parse_date(date_str: Optional[str]) -> dt.datetime:
    """Parse various date formats, fallback to max date if missing."""
    if not date_str:
        return dt.datetime.max
    for fmt in ("%b %d, %Y", "%Y-%m-%d", "%b %d, %Y."):
        try:
            return dt.datetime.strptime(date_str.strip(), fmt)
        except Exception:
            continue
    return dt.datetime.max


def parse_date_posted_from_detail(html_text: str) -> Optional[str]:
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


# ==================== FILE/DATABASE UTILITIES ====================

def load_db(path: str) -> dict:
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


def save_db_atomic(path: str, data: dict) -> None:
    """Atomically save data to JSON file."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="jobs_", suffix=".json", 
                                   dir=os.path.dirname(os.path.abspath(path)))
    os.close(fd)
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


# ==================== URL UTILITIES ====================

def with_page(url: str, page: int) -> str:
    """Modify URL to set specific page number."""
    parts = list(urlparse(url))
    q = parse_qs(parts[4], keep_blank_values=True)
    q["pg"] = [str(page)]
    parts[4] = urlencode(q, doseq=True)
    return urlunparse(parts)


# ==================== HTML/TEXT PROCESSING UTILITIES ====================

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


def safe_text(el) -> Optional[str]:
    """Safely extract text from HTML element."""
    if el is None:
        return None
    return norm(el.get_text(" ", strip=True)) if hasattr(el, 'get_text') else None


# ==================== TEXT PATTERN UTILITIES ====================

def find_span(text: str, pattern: re.Pattern, start_at: int = 0) -> Tuple[Optional[int], Optional[int]]:
    """Find pattern span in text."""
    m = pattern.search(text, start_at)
    return (m.start(), m.end()) if m else (None, None)


def slice_between(text: str, start_pat: re.Pattern, end_pats: tuple, start_offset_to_content: bool = True) -> str:
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


def split_qualifications(qual_text: str) -> Tuple[str, str, str]:
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
    
    return required_text, preferred_text, other_text


# ==================== JOB PROCESSING UTILITIES ====================

def get_job_id(key: str, rec: Dict[str, Any]) -> str:
    """Extract job ID from record."""
    if rec.get("job_id"):
        return str(rec["job_id"])
    m = re.search(r"/job/(\d+)", rec.get("url") or key or "")
    return m.group(1) if m else (rec.get("url") or key or "UNKNOWN")


def materialize_field_keywords(per_field: Dict[str, List[str]], available_fields: List[str]) -> Dict[str, List[str]]:
    """Merge wildcard keywords into specific fields."""
    result = {}
    wild = per_field.get("*", [])
    for f in available_fields:
        kws = set(wild)
        if f in per_field:
            kws.update(per_field[f])
        if kws:
            result[f] = sorted(kws)
    return result


# ==================== TIMING UTILITIES ====================

def sleep_a_bit(sleep_range: Tuple[float, float] = (3.0, 6.0)) -> None:
    """Sleep for a random duration between requests."""
    import random
    time.sleep(random.uniform(*sleep_range))


# ==================== DETAIL PAGE PARSING ====================

def safe_text(el) -> str | None:
    """Safely extract text from a WebElement."""
    try:
        return norm(el.text)
    except Exception:
        return None


def parse_detail_page(url: str, driver) -> Dict[str, Any]:
    """Parse a job detail page and extract structured information."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from .config import LABELS
    import time
    import re
    
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


def scrape_job_details(input_path: str, output_path: str):
    """Scrape detailed information for all jobs in the input database."""
    from .selenium_helpers import launch_chrome
    from .config import RESTART_EVERY, MAX_RETRIES
    import time
    import re
    
    # Load job index
    rows = list(load_db(input_path).values())
    
    # Build URLs
    urls = []
    seen = set()
    for row in rows:
        url = row.get("url")
        if not url and row.get("job_id"):
            url = f"https://jobs.careers.microsoft.com/global/en/job/{row['job_id']}/"
        if url and url not in seen:
            seen.add(url)
            urls.append(url)

    details_db = load_db(output_path)
    
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
    import json
    
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


def iter_scannable_fields(rec: Dict[str, Any]):
    """Iterate over fields that should be scanned."""
    from .config import SCANNABLE_FIELDS
    
    for f in SCANNABLE_FIELDS:
        if f in rec:
            yield f


def kw_boundary_search(blob: str, kw: str) -> bool:
    """Search for keyword with word boundaries."""
    import re
    
    return re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", blob, re.I) is not None


def filter_jobs(details_path: str, output_path: str):
    """Filter jobs based on defined rules."""
    from .config import AVOID_RULES
    
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
            for f, kws in field_kws.items():
                blob = field_blob.get(f, "")
                if not blob:
                    continue
                found = [kw for kw in kws if kw_boundary_search(blob, kw)]
                if found:
                    matched_fields[f] = sorted(set(found))

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

def organize_jobs_by_date(details_path: str, filtered_path: str):
    """Organize filtered Python jobs by date posted."""
    from collections import defaultdict
    import os
    import json
    import datetime as dt
    
    # Load data
    details_db = load_db(details_path)
    filtered_db = load_db(filtered_path)
    
    # Calculate wanted Python jobs
    python_jobs = set(filtered_db.get('knowledge_python', {}).get('job_ids', []))
    knowledge_fullstack = set(filtered_db.get('knowledge_fullstack', {}).get('job_ids', []))
    clearance_required = set(filtered_db.get('clearance_required', {}).get('job_ids', []))
    visa_sponsorship_block = set(filtered_db.get('visa_sponsorship_block', {}).get('job_ids', []))
    unwanted_positions = set(filtered_db.get('unwanted_positions', {}).get('job_ids', []))
    senior_only = set(filtered_db.get('senior_only', {}).get('job_ids', []))
    
    wanted_python_jobs = python_jobs - knowledge_fullstack - clearance_required - visa_sponsorship_block - unwanted_positions - senior_only
    
    print(f"Total Python jobs: {len(python_jobs)}")
    print(f"Total knowledge fullstack jobs: {len(knowledge_fullstack)}")
    print(f"Total wanted Python jobs: {len(wanted_python_jobs)}")
    
    # Group jobs by date
    jobs_by_date = defaultdict(list)
    
    for job_id in wanted_python_jobs:
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
            except:
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
    output_dir = "ms-jobs/jobs_by_date"
    os.makedirs(output_dir, exist_ok=True)
    
    files_created = 0
    files_updated = 0
    files_skipped = 0
    
    for date_str, jobs_list in jobs_by_date.items():
        filename = f"jobs_{date_str}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Prepare current content
        current_content = json.dumps(jobs_list, ensure_ascii=False, indent=2)
        
        # Check if file exists and compare content
        should_save = True
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                
                # Compare content
                if current_content == existing_content:
                    should_save = False
                    files_skipped += 1
                    print(f"Skipped {filename} - content unchanged ({len(jobs_list)} jobs)")
                else:
                    files_updated += 1
                    print(f"Updated {filename} - content changed ({len(jobs_list)} jobs)")
            except Exception as e:
                print(f"Error reading existing file {filepath}: {e}")
                # If we can't read the existing file, save anyway
                files_updated += 1
                print(f"Overwriting {filename} due to read error ({len(jobs_list)} jobs)")
        else:
            files_created += 1
            print(f"Created {filename} - new file ({len(jobs_list)} jobs)")
        
        # Save file only if needed
        if should_save:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(current_content)
    
    print(f"Summary: {files_created} files created, {files_updated} files updated, {files_skipped} files skipped")
    print(f"Total jobs processed: {sum(len(jobs) for jobs in jobs_by_date.values())}")