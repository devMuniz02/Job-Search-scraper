# Utils Package Documentation

The `utils` package provides a comprehensive set of utility functions for the Microsoft Jobs Scraper project. The package is organized into specialized modules for better maintainability and reusability.

## Package Structure

```
utils/
├── __init__.py              # Package initialization and exports
├── core.py                  # Core utility functions
├── selenium_helpers.py      # Selenium web automation utilities
├── config.py               # Configuration constants and settings
└── patterns.py             # Regex patterns
```

## Module Overview

### `utils.core` - Core Utilities

Contains general-purpose utility functions organized by category:

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

Selenium-specific functions for web scraping and browser automation:

**Browser Management:**
- `launch_chrome(local_chromedriver)` - Launch Chrome with optimal settings

**DOM Interaction:**
- `find_cards(driver)` - Find job listing cards
- `title_from_card(card)` - Extract job titles from cards
- `job_id_from_card(card)` - Extract job IDs from cards
- `link_from_card(card, job_id)` - Extract job URLs from cards

**Navigation:**
- `click_next_if_possible(driver)` - Click pagination next button
- `wait_for_new_page(driver, prev_ids, timeout)` - Wait for page changes
- `wait_for_elements(driver, css_selector, timeout)` - Wait for elements to load

**Page Processing:**
- `process_cards_on_page(driver)` - Process all job cards on current page

### `utils.config` - Configuration Management

Centralized configuration constants:

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

**Request Settings:**
- `USER_AGENT` - HTTP user agent string
- `HTTP_TIMEOUT` - HTTP request timeout

### `utils.patterns` - Regex Patterns

Compiled regex patterns used throughout the scraper:

- `JOB_ID_FROM_ARIA` - Extract job IDs from ARIA labels
- `ISO_DATE_RE` - ISO date format pattern
- `USD_RANGE` - USD salary range pattern
- `PAY_START` - Pay section start pattern
- `REQ_RE` - Required qualifications pattern
- `PREF_RE` - Preferred qualifications pattern
- `OTHER_RE` - Other requirements pattern

## Usage Examples

### Basic Import and Usage

```python
# Import specific functions
from utils import norm, parse_date, load_db, launch_chrome

# Import configuration
from utils import SEARCH_URL, MAX_PAGES, AVOID_RULES

# Import patterns
from utils import USD_RANGE, REQ_RE
```

### Complete Scraper Example

```python
from utils import (
    launch_chrome, find_cards, title_from_card,
    load_db, save_db_atomic, sleep_a_bit,
    SEARCH_URL, PAGE_LOAD_TIMEOUT
)

# Setup
driver = launch_chrome()
driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
db = load_db("jobs.json")

# Scrape
driver.get(SEARCH_URL)
cards = find_cards(driver)

for card in cards:
    title = title_from_card(card)
    print(f"Found job: {title}")
    sleep_a_bit()

# Save and cleanup
save_db_atomic("jobs.json", db)
driver.quit()
```

### Processing Utilities

```python
from utils import extract_pay_ranges, split_qualifications

# Extract salary information
text = "The salary range is USD $80,000 - $120,000"
ranges = extract_pay_ranges(text)
print(ranges)  # [{'region': 'U.S.', 'range': 'USD $80,000 - $120,000'}]

# Split job qualifications
qual_text = "Required Qualifications: Python experience. Preferred Qualifications: AWS knowledge."
req, pref, other = split_qualifications(qual_text)
```

## Installation and Setup

The utils package is automatically available when you're in the project directory:

```bash
# Activate virtual environment
C:/path/to/venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Test the package
python -c "from utils import norm; print('✓ Utils package working')"
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