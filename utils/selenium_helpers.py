"""
Selenium utilities for Microsoft Jobs Scraper

This module contains Selenium-specific utility functions for web scraping,
browser automation, and DOM interaction.
"""

import re
import time
from typing import Optional, Set
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException

# Import the regex pattern from patterns module
from .patterns import JOB_ID_FROM_ARIA


# ==================== BROWSER SETUP ====================

def launch_chrome(local_chromedriver: str = "") -> webdriver.Chrome:
    """Launch Chrome browser with appropriate options."""
    opts = ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,2000")
    
    if local_chromedriver:
        from selenium.webdriver.chrome.service import Service
        return webdriver.Chrome(service=Service(local_chromedriver), options=opts)
    return webdriver.Chrome(options=opts)


# ==================== DOM INTERACTION ====================

def find_cards(driver: webdriver.Chrome):
    """Find job listing cards on the page."""
    return driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')


def title_from_card(card) -> Optional[str]:
    """Extract job title from card element."""
    try:
        h2 = card.find_element(By.CSS_SELECTOR, "h2")
        t = (h2.text or "").strip()
        if t:
            return t
    except (NoSuchElementException, WebDriverException):
        pass
    txt = (card.text or "").strip()
    return txt.splitlines()[0].strip() if txt else None


def job_id_from_card(card) -> Optional[str]:
    """Extract job ID from card element."""
    aria = card.get_attribute("aria-label") or ""
    m = JOB_ID_FROM_ARIA.search(aria)
    if m:
        return m.group(1)
    try:
        # Note: accessing _parent is needed for the original implementation
        # This is a known pattern in this specific scraper
        outer = card._parent.execute_script("return arguments[0].outerHTML;", card)  # pylint: disable=protected-access
    except (WebDriverException, AttributeError):
        outer = ""
    m2 = JOB_ID_FROM_ARIA.search(outer or "")
    return m2.group(1) if m2 else None


def link_from_card(card, job_id: Optional[str]) -> Optional[str]:
    """Extract job URL from card element."""
    try:
        a = card.find_element(By.CSS_SELECTOR, 'a[href*="/global/en/job/"]')
        href = a.get_attribute("href")
        if href:
            return href
    except (NoSuchElementException, WebDriverException):
        pass
    return f"https://jobs.careers.microsoft.com/global/en/job/{job_id}/" if job_id else None


# ==================== NAVIGATION UTILITIES ====================

def click_next_if_possible(driver: webdriver.Chrome) -> bool:
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
        except (NoSuchElementException, WebDriverException):
            continue
    return False


def wait_for_new_page(driver: webdriver.Chrome, prev_ids: Set[str], timeout: int = 12) -> bool:
    """Wait for page to change after clicking Next."""
    t0 = time.time()
    last_count = len(prev_ids)
    while time.time() - t0 < timeout:
        time.sleep(0.8)
        cards = find_cards(driver)
        for c in cards:
            try:
                # Note: accessing _parent is needed for the original implementation
                c._parent = driver  # pylint: disable=protected-access
            except (AttributeError, WebDriverException):
                pass
        curr_ids = set()
        for c in cards:
            jid = job_id_from_card(c)
            if jid:
                curr_ids.add(jid)
        if len(cards) != last_count or (curr_ids - prev_ids):
            return True
    return False


def wait_for_elements(driver: webdriver.Chrome, css_selector: str, timeout: int = 30) -> bool:
    """Wait for elements to be present on the page."""
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css_selector)))
        return True
    except TimeoutException:
        return False


# ==================== PAGE PROCESSING ====================

def process_cards_on_page(driver: webdriver.Chrome) -> list:
    """Process all job cards on current page and extract basic info."""
    cards = find_cards(driver)
    # Attach parent driver for later operations
    for c in cards:
        try:
            # Note: accessing _parent is needed for the original implementation
            c._parent = driver  # pylint: disable=protected-access
        except (AttributeError, WebDriverException):
            pass
    
    page_data = []
    for card in cards:
        job_id = job_id_from_card(card)
        title = title_from_card(card)
        url = link_from_card(card, job_id)
        
        page_data.append({
            "job_id": job_id,
            "title": title,
            "url": url
        })
    
    return page_data


# ==================== PAGINATION SCRAPING ====================

def scrape_paginated(max_pages: int) -> list:
    """Scrape job listings across multiple pages."""
    from .config import SEARCH_URL
    from .core import sleep_a_bit
    
    driver = launch_chrome()
    all_rows = []
    
    try:
        print(f"[SCRAPE] starting at {SEARCH_URL}")
        driver.get(SEARCH_URL)
        
        # Wait for page to properly load
        print("[SCRAPE] waiting for page to load...")
        WebDriverWait(driver, 10).until(
            lambda d: "Search Jobs" in d.title
        )
        
        # Wait for job listings to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="listitem"]'))
        )
        
        # Additional wait for JavaScript to complete
        time.sleep(3)
        
        page_num = 1
        while page_num <= max_pages:
            print(f"[PAGE {page_num}] processing cards...")
            
            # Process current page
            page_data = process_cards_on_page(driver)
            if not page_data:
                print(f"[PAGE {page_num}] no cards found, stopping")
                break
                
            all_rows.extend(page_data)
            print(f"[PAGE {page_num}] found {len(page_data)} jobs (total: {len(all_rows)})")
            
            # Try to go to next page
            if page_num < max_pages:
                if not click_next_if_possible(driver):
                    print(f"[PAGE {page_num}] no next button found, stopping")
                    break
                
                # Wait for next page to load
                sleep_a_bit((2.0, 3.0))  # Longer wait for page transitions
                
                # Wait for new cards to load after page change
                time.sleep(2)
            
            page_num += 1
            
    finally:
        driver.quit()
    
    print(f"[SCRAPE] completed with {len(all_rows)} total rows")
    return all_rows