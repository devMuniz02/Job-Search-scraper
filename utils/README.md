# Utils Package Documentation

The `utils` package provides a comprehensive set of utility functions for the Microsoft & Meta Jobs Scraper project. The package is organized into specialized modules for better maintainability and reusability across both scraping systems.

## Package Structure

```
utils/
├── __init__.py              # Package initialization and exports
├── core.py                  # Core utility functions (677 lines)
├── selenium_helpers.py      # Selenium web automation utilities (216 lines)
├── config.py               # Microsoft Jobs configuration constants (140 lines)
├── meta_config.py          # Meta Jobs configuration constants & settings
├── patterns.py             # Regex patterns (20 lines)
└── README.md               # This documentation file
```

## Module Overview

### `utils.core` - Core Utilities

Contains general-purpose utility functions used by both Microsoft and Meta scrapers, organized by category:

**String Processing:**
- `norm(s)` - Normalize whitespace in strings
- `to_text(val)` - Convert any value to searchable text
- `kw_boundary_search(blob, kw)` - Search for keywords with word boundaries

**Date Handling:**
- `parse_date(date_str)` - Parse various date formats
- `parse_date_posted_from_detail(html_text)` - Extract job posting dates from HTML

**File & Database Operations:**
- `load_db(path)` - Load JSON database files
- `save_db_atomic(path, data)` - Atomically save data to JSON
- `upsert_rows(db, rows)` - Insert or update database rows
- `upsert_record(rec, db)` - Insert or update single records

**HTML & Text Processing:**
- `extract_pay_ranges(text)` - Extract salary ranges from text
- `extract_locations_jsonld(html_text)` - Extract locations from JSON-LD data
- `block_text_from_html(html)` - Convert HTML to formatted text
- `safe_text(el)` - Safely extract text from HTML elements

**Pattern Processing:**
- `find_span(text, pattern, start_at)` - Find pattern positions in text
- `slice_between(text, start_pat, end_pats)` - Extract text between patterns
- `split_qualifications(qual_text)` - Split job qualifications into sections

**Job Processing:**
- `get_job_id(key, rec)` - Extract job IDs from records
- `materialize_field_keywords(per_field, available_fields)` - Process filter keywords

**URL Utilities:**
- `with_page(url, page)` - Modify URLs to set page numbers

**Timing:**
- `sleep_a_bit(sleep_range)` - Random delay between requests

### `utils.selenium_helpers` - Selenium Automation

Selenium-specific functions for web scraping and browser automation used by both Microsoft and Meta scrapers:

**Browser Management:**
- `launch_chrome(local_chromedriver)` - Launch Chrome with optimal settings

**DOM Interaction:**
- `find_cards(driver)` - Find job listing cards (Microsoft-specific)
- `title_from_card(card)` - Extract job titles from cards (Microsoft-specific)
- `job_id_from_card(card)` - Extract job IDs from cards (Microsoft-specific)
- `link_from_card(card, job_id)` - Extract job URLs from cards (Microsoft-specific)

**Navigation:**
- `click_next_if_possible(driver)` - Click pagination next button
- `wait_for_new_page(driver, prev_ids, timeout)` - Wait for page changes
- `wait_for_elements(driver, css_selector, timeout)` - Wait for elements to load

**Page Processing:**
- `process_cards_on_page(driver)` - Process all job cards on current page (Microsoft-specific)

### `utils.config` - Microsoft Jobs Configuration

Centralized configuration constants for Microsoft Jobs scraper:

**URLs & Paths:**
- `SEARCH_URL` - Microsoft jobs search URL
- `DB_PATH`, `DB_PATH_DETAILS`, `DB_PATH_FILTERED` - Database file paths

**Scraping Settings:**
- `MAX_PAGES` - Maximum pages to scrape
- `PAGE_LOAD_TIMEOUT` - Page load timeout
- `WAIT_PER_PAGE` - Wait time per page
- `SLEEP_BETWEEN` - Sleep range between requests

**Field Definitions:**
- `LABELS` - Job detail field labels
- `SCANNABLE_FIELDS` - Fields to scan during filtering

**Filtering Rules:**
- `AVOID_RULES` - Job filtering criteria

**Filtering Rules:**
- `AVOID_RULES` - Job filtering criteria

**Request Settings:**
- Chrome options and user agent configurations

### `utils.meta_config` - Meta Jobs Configuration

Specialized configuration for Meta Jobs incremental scraper:

**URLs & Paths:**
- `BASE_URL` - Meta job details base URL
- `JOBS_LIST_URL` - Meta jobs listing page URL  
- `OUT_PATH`, `DETAILS_PATH` - Output file paths

**Scraping Settings:**
- `MAX_PAGES` - Maximum pages for incremental scraping
- `HEADLESS` - Browser headless mode setting
- `DELAY_BETWEEN_PAGES` - Delay between page scraping
- `DELAY_BETWEEN_JOBS` - Delay between job detail scraping
- `REACT_RENDER_DELAY` - Wait time for React rendering

**CSS Selectors & XPaths:**
- `JOB_LINKS_XPATH` - XPath for job links
- `JOB_ID_PATTERN` - Regex pattern for job ID extraction
- `JOB_DETAIL_CLASSES` - CSS classes for job detail extraction
- `COOKIE_XPATHS` - Cookie consent button selectors

**Browser Configuration:**
- `CHROME_OPTIONS` - Chrome browser options
- `HEADLESS_OPTIONS` - Additional options for headless mode
- `WINDOW_WIDTH`, `WINDOW_HEIGHT` - Browser window dimensions

### `utils.patterns` - Regex Patterns

Compiled regex patterns for job parsing (shared between scrapers):

- `JOB_ID_FROM_ARIA` - Extract job IDs from ARIA labels
- `ISO_DATE_RE` - ISO date format pattern
- `USD_RANGE` - USD salary range pattern
- `PAY_START` - Pay section start pattern
- `REQ_RE` - Required qualifications pattern
- `PREF_RE` - Preferred qualifications pattern
- `OTHER_RE` - Other requirements pattern

## Usage Examples

### Microsoft Jobs Scraper Usage

```python
# Import Microsoft-specific utilities
from utils import (
    launch_chrome, find_cards, title_from_card,
    load_db, save_db_atomic, sleep_a_bit,
    SEARCH_URL, MAX_PAGES, AVOID_RULES
)

# Setup Microsoft scraper
driver = launch_chrome()
driver.get(SEARCH_URL)
cards = find_cards(driver)

for card in cards:
    title = title_from_card(card)
    print(f"Found Microsoft job: {title}")
    
driver.quit()
```

### Meta Jobs Scraper Usage

```python
# Import Meta-specific configuration
from utils.meta_config import *

# Setup Meta incremental scraper
existing_ids = load_existing_ids(OUT_PATH)
driver = setup_driver(headless=HEADLESS)

# Scrape new jobs until known IDs found
new_job_ids = scrape_new_jobs_until_known_id(
    driver, JOBS_LIST_URL, existing_ids, max_pages=MAX_PAGES
)

print(f"Found {len(new_job_ids)} new Meta jobs")
```

### Shared Processing Utilities

```python
from utils import extract_pay_ranges, split_qualifications, parse_date

# Extract salary information (works for both companies)
text = "The salary range is USD $80,000 - $120,000"
ranges = extract_pay_ranges(text)
print(ranges)  # [{'region': 'U.S.', 'range': 'USD $80,000 - $120,000'}]

# Split job qualifications (Microsoft-specific)
qual_text = "Required Qualifications: Python experience. Preferred Qualifications: AWS knowledge."
req, pref, other = split_qualifications(qual_text)

# Parse dates (shared utility)
date_obj = parse_date("Jan 15, 2024")
print(date_obj)  # 2024-01-15 00:00:00
```

## Installation and Setup

The utils package is automatically available when you're in the project directory:

```bash
# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac  
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test Microsoft utils
python -c "from utils import norm; print('✓ Microsoft utils working')"

# Test Meta utils  
python -c "from utils.meta_config import BASE_URL; print('✓ Meta utils working')"
```

## Testing

Run the comprehensive test suite:

```bash
python test_utils.py
```

The test suite validates:
- String processing functions
- Date parsing utilities  
- File operations
- HTML processing
- URL manipulation
- Pattern matching
- Configuration loading
- Cross-scraper compatibility

## Configuration Files Comparison

| Feature | `utils/config.py` (Microsoft) | `utils/meta_config.py` (Meta) |
|---------|-------------------------------|-------------------------------|
| **Purpose** | Microsoft Jobs scraper config | Meta Jobs incremental scraper |
| **Filtering** | Advanced rule-based filtering | No filtering (collect all) |
| **Scraping Mode** | Full pagination | Incremental (stop at known IDs) |
| **Data Organization** | By posting date + filtering | By discovery date |
| **Main URL** | Microsoft Careers | Meta Careers |
| **Complexity** | High (140+ lines) | Medium (130+ lines) |

## Architecture Benefits

### 🎯 **Modular Design**
- **Shared Core**: Common utilities work for both scrapers
- **Specialized Config**: Company-specific settings isolated
- **Reusable Components**: Browser automation shared across projects

### ⚡ **Performance**
- **Smart Caching**: Incremental Meta scraping reduces redundant work
- **Optimized Timing**: Different delay strategies per company
- **Resource Management**: Proper browser lifecycle management

### 🛡️ **Maintainability**  
- **Single Source of Truth**: Centralized configuration
- **Easy Testing**: Comprehensive test coverage
- **Clear Separation**: Company-specific vs shared functionality

## Benefits of the Package Structure

1. **Organized Imports**: Clean, logical import structure
2. **Modular Design**: Each module has a specific purpose
3. **Easy Testing**: Individual modules can be tested in isolation
4. **Documentation**: Clear separation of functionality
5. **Extensibility**: Easy to add new utilities to appropriate modules
6. **Reusability**: Can be imported into any Python project
7. **Maintainability**: Changes are localized to specific modules

## Future Enhancements

The modular structure enables easy additions:

- `utils.filters` - Advanced job filtering logic
- `utils.analyzers` - Data analysis and reporting  
- `utils.exporters` - Export to various formats (CSV, Excel, etc.)
- `utils.schedulers` - Automated scraping schedules
- `utils.notifications` - Email/Slack notifications
- `utils.database` - Database integration (PostgreSQL, MongoDB)

## Migration from Old Structure

If you have existing code using the old imports:

```python
# Old way
from utils import norm
from selenium_utils import launch_chrome  
from config import SEARCH_URL

# New way (all from utils package)
from utils import norm, launch_chrome, SEARCH_URL
```

All functions are now available through the main `utils` package import for convenience.