# Meta Jobs Scraper Configuration Guide

## Overview
The Meta Jobs Scraper now uses a centralized configuration file (`utils/meta_config.py`) that makes it easy to customize the scraper's behavior without modifying the main script.

## Quick Start

1. **Clone the repository**
2. **Edit the configuration** in `utils/meta_config.py`
3. **Run the scraper**: `python first-meta-jobs-scrapper.py`

## Configuration File Location
```
utils/meta_config.py
```

## Key Configuration Sections

### 🌐 URLs and Paths
```python
BASE_URL = "https://www.metacareers.com/jobs/"
JOBS_LIST_URL = "https://www.metacareers.com/jobs?sort_by_new=true&offices[0]=North%20America"
OUTPUT_DIR = "meta-jobs"
JOB_IDS_FILE = "meta_job_ids.json"
JOB_DETAILS_FILE = "meta_job_details.json"
```

### ⚙️ Scraping Settings
```python
HEADLESS = True  # Set to False to see browser
MAX_PAGES = 999  # Set to specific number to limit pages
SCROLL_ROUNDS = 6  # Number of scrolls per page
DELAY_BETWEEN_PAGES = 7  # Seconds between pages
DELAY_BETWEEN_JOBS = 2  # Seconds between job details
```

### 🎯 CSS Selectors
```python
JOB_DETAIL_CLASSES = {
    "main_container": "_8muv _ar_h",
    "title_location_container": "_a6jl _armv",
    "title_class": "_army",
    "location_class": "_ar_e",
    # ... more selectors
}
```

## Environment Variables Override

You can override key settings using environment variables without editing the config file:

```bash
# Run with visible browser
HEADFUL=1 python first-meta-jobs-scrapper.py

# Limit to 10 pages
MAX_PAGES=10 python first-meta-jobs-scrapper.py

# More aggressive scrolling
SCROLL_ROUNDS=10 python first-meta-jobs-scrapper.py

# Custom output path
OUT=my-custom-folder/jobs.json python first-meta-jobs-scrapper.py
```

## Windows PowerShell Examples
```powershell
# Run with visible browser
$env:HEADFUL="1"; python first-meta-jobs-scrapper.py

# Limit to 5 pages with more scrolling
$env:MAX_PAGES="5"; $env:SCROLL_ROUNDS="8"; python first-meta-jobs-scrapper.py
```

## Common Customizations

### 1. Change Target Location
Edit `JOBS_LIST_URL` in config file:
```python
JOBS_LIST_URL = "https://www.metacareers.com/jobs?sort_by_new=true&offices[0]=Europe"
```

### 2. Adjust Scraping Speed
```python
DELAY_BETWEEN_PAGES = 10  # Slower, more respectful
SCROLL_ROUNDS = 10        # More thorough scrolling
```

### 3. Change Output Directory
```python
OUTPUT_DIR = "my-meta-jobs"
```

### 4. Debug Mode (Visible Browser)
```python
HEADLESS = False  # or use HEADFUL=1 environment variable
```

### 5. Limit Pages for Testing
```python
MAX_PAGES = 3  # Only scrape first 3 pages
```

## CSS Selector Updates

If Meta changes their website structure, update the CSS selectors in the config:

```python
JOB_DETAIL_CLASSES = {
    "main_container": "new-main-class",
    "title_class": "new-title-class",
    # ... update as needed
}
```

## File Structure After Running
```
meta-jobs/
├── meta_job_ids.json      # Job IDs found
└── meta_job_details.json  # Full job details
```

## Troubleshooting

### No Jobs Found
1. Check if `JOBS_LIST_URL` is correct
2. Increase `ELEMENT_WAIT_TIMEOUT` if pages load slowly
3. Set `HEADLESS = False` to see what's happening

### Missing Job Details
1. Update CSS selectors in `JOB_DETAIL_CLASSES`
2. Increase `REACT_RENDER_DELAY` for slow-loading pages

### Rate Limiting
1. Increase `DELAY_BETWEEN_PAGES`
2. Increase `DELAY_BETWEEN_JOBS`

## Contributing

When contributing, please:
1. Update the config file instead of hardcoding values
2. Document any new configuration options
3. Test with both default and custom config values