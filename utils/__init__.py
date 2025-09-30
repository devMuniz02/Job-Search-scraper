"""
Microsoft Jobs Scraper Utils Package

A comprehensive utility package for job scraping operations.
This package provides modular utilities for web scraping, data processing,
and configuration management.
"""

from .core import (
    norm,
    parse_date,
    load_db,
    save_db_atomic,
    sleep_a_bit,
    extract_pay_ranges,
    block_text_from_html,
    to_text,
    get_job_id,
    materialize_field_keywords,
    kw_boundary_search,
    with_page,
    parse_date_posted_from_detail,
    upsert_rows,
    upsert_record,
    extract_locations_jsonld,
    find_span,
    slice_between,
    split_qualifications,
    safe_text
)

from .selenium_helpers import (
    launch_chrome,
    find_cards,
    title_from_card,
    job_id_from_card,
    link_from_card,
    click_next_if_possible,
    wait_for_new_page,
    wait_for_elements,
    process_cards_on_page
)

from .config import (
    SEARCH_URL,
    DB_PATH,
    DB_PATH_DETAILS,
    DB_PATH_FILTERED,
    MAX_PAGES,
    AVOID_RULES,
    SCANNABLE_FIELDS,
    LABELS,
    PAGE_LOAD_TIMEOUT,
    WAIT_PER_PAGE,
    DELAY_AFTER_NEXT,
    SLEEP_BETWEEN,
    MAX_RETRIES,
    RESTART_EVERY,
    LOCAL_CHROMEDRIVER,
    USER_AGENT,
    HTTP_TIMEOUT,
    CHROME_OPTIONS
)

from .patterns import (
    JOB_ID_FROM_ARIA,
    ISO_DATE_RE,
    USD_RANGE,
    PAY_START,
    REQ_RE,
    PREF_RE,
    OTHER_RE
)

__version__ = "1.0.0"
__author__ = "Job Search Scraper Team"

__all__ = [
    # Core utilities
    'norm',
    'parse_date',
    'load_db',
    'save_db_atomic',
    'sleep_a_bit',
    'extract_pay_ranges',
    'block_text_from_html',
    'to_text',
    'get_job_id',
    'materialize_field_keywords',
    'kw_boundary_search',
    'with_page',
    'parse_date_posted_from_detail',
    'upsert_rows',
    'upsert_record',
    'extract_locations_jsonld',
    'find_span',
    'slice_between',
    'split_qualifications',
    'safe_text',
    
    # Selenium utilities
    'launch_chrome',
    'find_cards',
    'title_from_card',
    'job_id_from_card',
    'link_from_card',
    'click_next_if_possible',
    'wait_for_new_page',
    'wait_for_elements',
    'process_cards_on_page',
    
    # Configuration
    'SEARCH_URL',
    'DB_PATH',
    'DB_PATH_DETAILS',
    'DB_PATH_FILTERED',
    'MAX_PAGES',
    'AVOID_RULES',
    'SCANNABLE_FIELDS',
    'LABELS',
    'PAGE_LOAD_TIMEOUT',
    'WAIT_PER_PAGE',
    'DELAY_AFTER_NEXT',
    'SLEEP_BETWEEN',
    'MAX_RETRIES',
    'RESTART_EVERY',
    'LOCAL_CHROMEDRIVER',
    'USER_AGENT',
    'HTTP_TIMEOUT',
    'CHROME_OPTIONS',
    
    # Patterns
    'JOB_ID_FROM_ARIA',
    'ISO_DATE_RE',
    'USD_RANGE',
    'PAY_START',
    'REQ_RE',
    'PREF_RE',
    'OTHER_RE'
]