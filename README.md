# Microsoft & Meta Jobs Scraper

A comprehensive Python web scraper for extracting job listings from both Microsoft Careers and Meta Careers websites with advanced filtering, data processing, incremental scraping, and automated daily collection via GitHub Actions.

## 🌟 Features

### 🏢 **Microsoft Jobs Scraper**
- **✅ Modular Architecture**: Clean 55-line main script using utils package
- **🔄 Automated Job Scraping**: Extract job listings from Microsoft careers page
- **🎯 Intelligent Filtering**: Filter jobs based on visa requirements, experience level, technologies
- **📊 Data Processing**: Parse job details, salary ranges, locations, and qualifications
- **📅 Date Organization**: Automatically organize scraped jobs by posting date

### 🌐 **Meta Jobs Scraper**
- **⚡ Incremental Scraping**: Smart detection to only scrape new jobs since last run
- **🔄 Daily Automation**: Automated daily collection via GitHub Actions
- **� Daily Tracking**: Save each day's new jobs to separate dated files
- **�🛡️ Duplicate Prevention**: Stops scraping when previously known jobs are encountered
- **🎯 Efficient Processing**: Only scrapes details for newly discovered jobs

### 🤖 **Shared Features**
- **🛡️ Robust Error Handling**: Retry mechanisms and graceful failure handling
- **🤖 Headless Browser Support**: Selenium automation with Chrome headless mode
- **🧪 Comprehensive Testing**: Complete test suite for all utility functions
- **⚡ Enhanced Performance**: Improved timing and wait mechanisms for reliable scraping
- **🚀 GitHub Actions**: Automated daily scraping with comprehensive reporting

## 📁 Project Structure

```
Job-Search-scrapper/
├── 🏢 Microsoft Jobs Scraper
│   ├── ms-job-scrapper.py          # 🎯 Main MS scraper script (refactored modular version)
│   └── old-ms-job-scrapper.py      # 📦 Original monolithic version (backup)
├── 🌐 Meta Jobs Scraper  
│   ├── meta-jobs-daily-scraper.py  # 🔄 Daily incremental Meta scraper
│   ├── temp-meta-jobs-incremental-scraper.py # 🧪 Development version
│   └── temp-meta-job-scrapper.ipynb # 📝 Jupyter notebook for experimentation
├── 🧪 Testing & Development
│   ├── test_utils.py              # 🧪 Comprehensive test suite for utils
│   ├── test_content_comparison.py # 🔍 Content comparison tests
│   ├── example_scraper.py         # � Example implementation
│   └── remove_ids.ipynb           # 🧹 Data cleanup utilities
├── ⚙️ Configuration & Setup
│   ├── requirements.txt           # 📋 Python dependencies
│   ├── CONFIG_GUIDE.md            # ⚙️ Configuration guide
│   ├── README.md                  # 📖 Main project documentation (this file)
│   ├── README_UTILS.md            # 🔧 Utils package detailed documentation
│   └── LICENSE                    # � MIT License
├── 🤖 Automation
│   └── .github/workflows/
│       └── daily-scraper.yml      # 🚀 GitHub Actions daily automation
├── utils/                         # 🛠️ Modular utilities package
│   ├── __init__.py               # Package initialization
│   ├── core.py                   # Core utility functions (677 lines)
│   ├── selenium_helpers.py       # Browser automation utilities (216 lines)
│   ├── config.py                 # MS Jobs configuration constants (140 lines)
│   ├── meta_config.py            # Meta Jobs configuration constants
│   ├── patterns.py               # Regex patterns (20 lines)
│   └── README.md                 # Utils package documentation
├── 📂 Microsoft Jobs Data
│   └── ms-jobs/                  # 📂 Output directory for MS job data
│       ├── jobs_ms.json          # Raw job listings
│       ├── jobs_ms_details.json  # Detailed job information
│       ├── jobs_ms_avoid_hits_by_field.json # Filtered jobs by rules
│       ├── jobs_ms_avoid_hits.json # Legacy filtered jobs format
│       └── jobs_by_date/         # Jobs organized by posting date
│           ├── jobs_01_october_2025.json
│           ├── jobs_02_october_2025.json
│           └── jobs_03_october_2025.json
└── 📂 Meta Jobs Data
    └── meta-jobs/                # 📂 Output directory for Meta job data
        ├── meta_job_ids.json     # All Meta job IDs (incremental)
        ├── meta_job_details.json # All Meta job details
        └── jobs_by_date/         # Daily new jobs
            ├── jobs_01_october_2025.json
            ├── jobs_02_october_2025.json
            └── jobs_03_october_2025.json
```

### 🔄 **Refactoring Achievement**
- **Original**: 1,200+ lines monolithic script
- **Refactored**: 55-line clean main script + modular utils
- **Code Reduction**: 94% reduction in main file complexity
- **Functionality**: 100% identical results between versions

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Chrome browser (for Selenium automation)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/devMuniz02/Job-Search-scrapper.git
   cd Job-Search-scrapper
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests to verify installation**
   ```bash
   python test_utils.py
   ```

### Basic Usage

#### **🏢 Microsoft Jobs Scraper**
```bash
# Recommended: Use the refactored modular version
python ms-job-scrapper.py

# Backup: Use the original monolithic version
python old-ms-job-scrapper.py
```

#### **🌐 Meta Jobs Scraper (Incremental)**
```bash
# Run daily incremental scraping (recommended)
python meta-jobs-daily-scraper.py

# Run development version
python temp-meta-jobs-incremental-scraper.py
```

#### **🤖 Automated Daily Collection**
The project includes GitHub Actions automation that runs both scrapers daily:
- **Schedule**: 7:00 AM UTC daily
- **Manual trigger**: Available via GitHub Actions interface
- **Output**: Comprehensive reports and artifact uploads
- **Auto-commit**: Results automatically committed to repository

#### **Backup: Use the Original Version**
```bash
python old-ms-job-scrapper.py
```
*Original monolithic version kept as backup*

#### **Custom Implementation: Use Utils Package**
```python
# Microsoft Jobs - Custom implementation
from utils import (
    launch_chrome, find_cards, title_from_card,
    load_db, save_db_atomic, extract_pay_ranges,
    SEARCH_URL, MAX_PAGES
)

# Meta Jobs - Custom implementation  
from utils.meta_config import *

# Your custom scraping logic here
driver = launch_chrome()
driver.get(SEARCH_URL)
cards = find_cards(driver)
# ... process cards
```

## 📊 Configuration

### Microsoft Jobs Settings
Edit `utils/config.py` to customize:

```python
MAX_PAGES = 10                    # Maximum pages to scrape
PAGE_LOAD_TIMEOUT = 60           # Page load timeout (seconds)
SLEEP_BETWEEN = (0.6, 1.2)      # Delay between requests
```

### Meta Jobs Settings
Edit `utils/meta_config.py` to customize:

```python
MAX_PAGES = 999                   # Maximum pages for incremental scraping
HEADLESS = True                   # Run browser in headless mode
DELAY_BETWEEN_PAGES = 2           # Delay between pages (seconds)
DELAY_BETWEEN_JOBS = 1            # Delay between job detail scraping
```

### Filtering Rules (Microsoft Only)
Customize job filtering in `utils/config.py`:

```python
AVOID_RULES = {
    "visa_sponsorship_block": {
        "title": ["no sponsorship", "no visa"],
        "other_requirements_text": ["citizens only", "green card"]
    },
    "senior_only": {
        "required_qualifications_text": ["6+ years", "10+ years"]
    },
    # Add your own rules...
}
```

## 🛠️ Utils Package

The project features a modular utils package with the following components:

### Core Utilities (`utils.core`)
- **String Processing**: `norm()`, `to_text()`, `kw_boundary_search()`
- **Date Handling**: `parse_date()`, `parse_date_posted_from_detail()`
- **File Operations**: `load_db()`, `save_db_atomic()`, `upsert_rows()`
- **HTML Processing**: `extract_pay_ranges()`, `block_text_from_html()`
- **Pattern Matching**: `find_span()`, `slice_between()`, `split_qualifications()`

### Selenium Helpers (`utils.selenium_helpers`)
- **Browser Management**: `launch_chrome()`
- **DOM Interaction**: `find_cards()`, `title_from_card()`, `job_id_from_card()`
- **Navigation**: `click_next_if_possible()`, `wait_for_new_page()`

### Configuration (`utils.config` & `utils.meta_config`)
- **Microsoft**: URLs, paths, scraping settings, and filtering rules
- **Meta**: Job scraping configuration, CSS selectors, and incremental settings
- Request configurations and browser options

### Patterns (`utils.patterns`)
- Compiled regex patterns for job parsing
- Date, salary, and qualification patterns

## 📈 Usage Examples

### Basic Job Scraping - Microsoft
```python
from utils import launch_chrome, find_cards, SEARCH_URL

driver = launch_chrome()
driver.get(SEARCH_URL)
cards = find_cards(driver)

for card in cards:
    title = title_from_card(card)
    job_id = job_id_from_card(card)
    print(f"Found: {title} (ID: {job_id})")

driver.quit()
```

### Basic Job Scraping - Meta (Incremental)
```python
from utils.meta_config import *
import time

# Load existing IDs to implement incremental scraping
existing_ids = load_existing_ids("meta-jobs/meta_job_ids.json")

# Scrape new jobs until finding known IDs
driver = setup_driver(headless=True)
new_job_ids = scrape_new_jobs_until_known_id(
    driver, JOBS_LIST_URL, existing_ids, max_pages=10
)

print(f"Found {len(new_job_ids)} new jobs")
```

### Data Processing
```python
from utils import extract_pay_ranges, parse_date

# Extract salary information
text = "The salary range is USD $80,000 - $120,000"
ranges = extract_pay_ranges(text)
print(ranges)  # [{'region': 'U.S.', 'range': 'USD $80,000 - $120,000'}]

# Parse dates
date_obj = parse_date("Jan 15, 2024")
print(date_obj)  # 2024-01-15 00:00:00
```

### Database Operations
```python
from utils import load_db, save_db_atomic, upsert_rows

# Load existing data
jobs_db = load_db("ms-jobs/jobs_ms.json")

# Add new jobs
new_jobs = [
    {"job_id": "123", "title": "Software Engineer"},
    {"job_id": "456", "title": "Data Scientist"}
]
added_count = upsert_rows(jobs_db, new_jobs)

# Save atomically
save_db_atomic("ms-jobs/jobs_ms.json", jobs_db)
print(f"Added {added_count} new jobs")
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test all utilities
python test_utils.py

# Test specific functionality
python -c "from utils import norm; print(norm('  test  '))"
```

Expected output:
```
Running utility module tests...
==================================================
Testing string utilities...
✓ norm() working correctly
✓ to_text() working correctly
✓ kw_boundary_search() working correctly
...
✅ All tests passed! Utility modules are working correctly.
```

## 📋 Output Data

### Microsoft Jobs Output

#### `ms-jobs/jobs_ms.json`
Raw job listings with basic information:
```json
{
  "123456": {
    "job_id": "123456",
    "name": "Software Engineer",
    "url": "https://jobs.careers.microsoft.com/...",
    "date_posted": "2024-01-15"
  }
}
```

#### `ms-jobs/jobs_ms_details.json`
Detailed job information including qualifications, descriptions, and metadata.

#### `ms-jobs/jobs_ms_avoid_hits_by_field.json`
Filtered jobs based on the configured filtering rules.

#### `ms-jobs/jobs_by_date/`
Jobs organized by posting date for easier analysis.

### Meta Jobs Output

#### `meta-jobs/meta_job_ids.json`
Array of all Meta job IDs (incremental collection):
```json
["123456", "789012", "345678"]
```

#### `meta-jobs/meta_job_details.json`
Detailed job information for all Meta jobs:
```json
{
  "123456": {
    "title": "Software Engineer",
    "URL": "https://www.metacareers.com/jobs/123456",
    "location": "Menlo Park, CA",
    "responsibilities": "...",
    "minimum_qualifications": "...",
    "preferred_qualifications": "...",
    "compensation": "..."
  }
}
```

#### `meta-jobs/jobs_by_date/`
Daily collections of new jobs only:
```json
{
  "123456": { /* job details for jobs found on this specific date */ }
}
```

## ⚙️ Advanced Configuration

### Custom Chrome Options
```python
from utils.selenium_helpers import launch_chrome

# Use local chromedriver
driver = launch_chrome(local_chromedriver="/path/to/chromedriver")
```

### Custom Filtering Rules
```python
from utils import materialize_field_keywords

# Define custom filter rules
custom_rules = {
    "python_jobs": {
        "title": ["python"],
        "required_qualifications_text": ["python", "django", "flask"]
    }
}

# Process rules
available_fields = ["title", "required_qualifications_text"]
processed_rules = materialize_field_keywords(custom_rules["python_jobs"], available_fields)
```

## 🔧 Troubleshooting

### Common Issues

1. **Chrome driver issues**
   - Ensure Chrome browser is installed
   - Update Chrome to the latest version
   - Selenium Manager will auto-download chromedriver

2. **Import errors**
   - Activate virtual environment: `venv\Scripts\activate`
   - Install dependencies: `pip install -r requirements.txt`

3. **Permission errors**
   - Run with appropriate permissions
   - Check file system access to output directory

4. **Network timeouts**
   - Increase timeout settings in `utils/config.py`
   - Check internet connection

### Debug Mode
Enable verbose logging by modifying the scripts to include debug output.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make your changes
4. Run tests (`python test_utils.py`)
5. Commit your changes (`git commit -am 'Add new feature'`)
6. Push to the branch (`git push origin feature/new-feature`)
7. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Selenium** for browser automation
- **Beautiful Soup** for HTML parsing
- **Requests** for HTTP operations
- **Microsoft Careers** for the job data source

## 📞 Support

For issues, questions, or contributions:

- Open an issue on [GitHub Issues](https://github.com/devMuniz02/Job-Search-scrapper/issues)
- Check the [Utils Documentation](README_UTILS.md) for detailed API reference
- Review the [test suite](test_utils.py) for usage examples

## 📈 Roadmap

### ✅ Completed Features
- [x] **Microsoft Jobs**: Modular architecture refactoring *(Completed September 2025)*
- [x] **Microsoft Jobs**: Comprehensive test suite *(Completed September 2025)*
- [x] **Microsoft Jobs**: Enhanced timing and reliability *(Completed September 2025)*
- [x] **Meta Jobs**: Incremental scraping system *(Completed October 2025)*
- [x] **Meta Jobs**: Daily automated collection *(Completed October 2025)*
- [x] **Automation**: GitHub Actions daily workflow *(Completed October 2025)*
- [x] **Data Organization**: Daily job tracking by date *(Completed October 2025)*

### 🚀 Upcoming Features
- [ ] **Multi-Company Expansion**: Google, Amazon, Apple job scrapers
- [ ] **Database Integration**: PostgreSQL, MongoDB support
- [ ] **Web Dashboard**: Job analytics and visualization interface
- [ ] **Email Notifications**: Alerts for new jobs matching criteria
- [ ] **Machine Learning**: Job recommendation system
- [ ] **Docker Support**: Containerization for easy deployment
- [ ] **REST API**: Interface for programmatic access
- [ ] **Advanced Filtering**: ML-based job relevance scoring
- [ ] **Real-time Updates**: WebSocket-based live job updates
- [ ] **Mobile App**: React Native app for job browsing

---

**Happy Job Hunting! 🎯**