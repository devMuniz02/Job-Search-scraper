# Microsoft Jobs Scraper

A comprehensive Python web scraper for extracting job listings from Microsoft Careers website with advanced filtering, data processing, and modular utility architecture.

## 🌟 Features

- **✅ Modular Architecture**: Clean 55-line main script using utils package
- **🔄 Automated Job Scraping**: Extract job listings from Microsoft careers page
- **🎯 Intelligent Filtering**: Filter jobs based on visa requirements, experience level, technologies
- **📊 Data Processing**: Parse job details, salary ranges, locations, and qualifications
- **📅 Date Organization**: Automatically organize scraped jobs by posting date
- **🛡️ Robust Error Handling**: Retry mechanisms and graceful failure handling
- **🤖 Headless Browser Support**: Selenium automation with Chrome headless mode
- **🧪 Comprehensive Testing**: Complete test suite for all utility functions
- **⚡ Enhanced Performance**: Improved timing and wait mechanisms for reliable scraping

## 📁 Project Structure

```
Job-Search-scrapper/
├── ms-job-scrapper.py          # 🎯 Main scraper script (refactored modular version)
├── old-ms-job-scrapper.py      # 📦 Original monolithic version (backup)
├── test_utils.py              # 🧪 Comprehensive test suite for utils
├── scrapper.ipynb             # 📝 Jupyter notebook for experimentation
├── requirements.txt           # 📋 Python dependencies
├── README.md                  # 📖 Main project documentation (this file)
├── README_UTILS.md            # 🔧 Utils package detailed documentation
├── REFACTORING_ANALYSIS.md    # 📊 Refactoring analysis and comparison
├── utils/                     # 🛠️ Modular utilities package
│   ├── __init__.py           # Package initialization
│   ├── core.py               # Core utility functions (677 lines)
│   ├── selenium_helpers.py   # Browser automation utilities (216 lines)
│   ├── config.py             # Configuration constants (140 lines)
│   └── patterns.py           # Regex patterns (20 lines)
└── ms-jobs/                  # 📂 Output directory for scraped job data
    ├── jobs_ms.json          # Raw job listings
    ├── jobs_ms_details.json  # Detailed job information
    ├── jobs_ms_avoid_hits_by_field.json # Filtered jobs by rules
    ├── jobs_ms_avoid_hits.json # Legacy filtered jobs format
    └── jobs_by_date/         # Jobs organized by posting date
        ├── jobs_18_september_2025.json
        ├── jobs_23_september_2025.json
        ├── jobs_24_september_2025.json
        ├── jobs_25_september_2025.json
        ├── jobs_26_september_2025.json
        ├── jobs_27_september_2025.json
        └── jobs_29_september_2025.json
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

#### **Recommended: Use the Refactored Version**
```bash
python ms-job-scrapper.py
```
*This is the clean, modular version with identical functionality*

#### **Backup: Use the Original Version**
```bash
python old-ms-job-scrapper.py
```
*Original monolithic version kept as backup*

#### **Custom Implementation: Use Utils Package**
```python
from utils import (
    launch_chrome, find_cards, title_from_card,
    load_db, save_db_atomic, extract_pay_ranges,
    SEARCH_URL, MAX_PAGES
)

# Your custom scraping logic here
driver = launch_chrome()
driver.get(SEARCH_URL)
cards = find_cards(driver)
# ... process cards
```

## 📊 Configuration

### Scraping Settings
Edit `utils/config.py` to customize:

```python
MAX_PAGES = 10                    # Maximum pages to scrape
PAGE_LOAD_TIMEOUT = 60           # Page load timeout (seconds)
SLEEP_BETWEEN = (0.6, 1.2)      # Delay between requests
```

### Filtering Rules
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

### Configuration (`utils.config`)
- URLs, paths, and scraping settings
- Field definitions and filtering rules
- Request configurations

### Patterns (`utils.patterns`)
- Compiled regex patterns for job parsing
- Date, salary, and qualification patterns

## 📈 Usage Examples

### Basic Job Scraping
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

The scraper generates several data files:

### `jobs_ms.json`
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

### `jobs_ms_details.json`
Detailed job information including qualifications, descriptions, and metadata.

### `jobs_ms_avoid_hits_by_field.json`
Filtered jobs based on the configured filtering rules.

### `jobs_by_date/`
Jobs organized by posting date for easier analysis.

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

- [x] **Modular architecture refactoring** *(Completed September 2025)*
- [x] **Comprehensive test suite** *(Completed September 2025)*
- [x] **Enhanced timing and reliability** *(Completed September 2025)*
- [ ] Database integration (PostgreSQL, MongoDB)
- [ ] Web dashboard for job analytics
- [ ] Email notifications for new jobs
- [ ] Multi-company support (Google, Amazon, etc.)
- [ ] Machine learning job recommendation
- [ ] Docker containerization
- [ ] REST API interface

---

**Happy Job Hunting! 🎯**