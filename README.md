
# Microsoft & Meta Jobs Scraper

A comprehensive Python web scraper for extracting job listings from both Microsoft Careers and Meta Careers websites with advanced filtering, data processing, incremental scraping, and automated daily collection via GitHub Actions.

## 📁 Project Structure

```
Job-Search-scrapper/
├── 🏢 Microsoft Jobs Scraper
│   ├── ms-jobs-daily-scrapper.py   # 🎯 Daily MS scraper script (refactored modular version)
│   └── temp-ms.ipynb               # 🧪 Development / experimental notebook
├── 🌐 Meta Jobs Scraper
│   ├── meta-jobs-daily-scraper.py  # 🔄 Daily incremental Meta scraper
│   ├── meta-jobs-first-time-scrapper.py # 🧪 One-off / first-time scraper
│   └── temp-meta-job-scrapper.ipynb # 📝 Jupyter notebook for experimentation
├── ⚙️ Configuration & Setup
│   ├── requirements.txt           # 📋 Python dependencies
│   ├── CONFIG_GUIDE.md            # ⚙️ Configuration guide
│   ├── README.md                  # 📖 Main project documentation (this file)
│   ├── README_UTILS.md            # 🔧 Utils package detailed documentation
│   └── LICENSE                    # 📜 MIT License
├── 🤖 Automation
│   └── .github/workflows/
│       └── daily-scraper.yml      # 🚀 GitHub Actions daily automation
├── utils/                         # 🛠️ Modular utilities package
│   ├── __init__.py               # Package initialization
│   ├── core.py                   # Core utility functions
│   ├── selenium_helpers.py       # Browser automation utilities
│   ├── config.py                 # MS Jobs configuration constants
│   ├── meta_config.py            # Meta Jobs configuration constants
│   ├── patterns.py               # Regex patterns
│   └── README.md                 # Utils package documentation
├── 📂 Microsoft Jobs Data
│   └── Microsoft-jobs/           # 📂 Output directory for MS job data
│       ├── ms_job_ids.json       # Raw job IDs / listings (incremental)
│       ├── ms_job_details.json   # Detailed job information
│       ├── ms_job_avoid_hits_by_field.json # Filtered jobs by rules
│       └── jobs_by_date/         # Jobs organized by posting date
└── 📂 Meta Jobs Data
    └── Meta-jobs/                # 📂 Output directory for Meta job data
        ├── meta_job_ids.json     # All Meta job IDs (incremental)
        ├── meta_job_details.json # All Meta job details
        └── jobs_by_date/         # Daily new jobs
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Chrome browser (for Selenium automation)
- Virtual environment (recommended)

### Installation

1. Clone the repository

```bash
git clone https://github.com/devMuniz02/Job-Search-scrapper.git
cd Job-Search-scrapper
```

2. Create and activate a virtual environment

Windows (PowerShell):

```powershell
python -m venv venv; venv\Scripts\Activate
```

Linux / macOS:

```bash
python -m venv venv; source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

### Basic usage

- Run the Microsoft daily scraper:

```powershell
python ms-jobs-daily-scrapper.py
```

- Run the Meta daily incremental scraper:

```powershell
python meta-jobs-daily-scraper.py
```

- For a first-time full run of Meta:

```powershell
python meta-jobs-first-time-scrapper.py
```

### Automation (GitHub Actions)

The repository includes a workflow that runs the scrapers daily and uploads results as artifacts. The workflow also optionally commits updated JSON outputs back to the repository when changes are detected.

Key notes:
- Schedule: 7:00 AM UTC daily
- Artifacts: uploaded under the name `job-scraping-results-${{ github.run_number }}`
- Retention: 30 days (configurable in the workflow)

## � Configuring searches (edit `config.json`)

To target a specific search (department, location, remote, newest first, etc.) update the company's `searchURL` in `config.json` and optionally set `numberOfPages`.

Steps:
1. Open the company's careers page and apply the filters you want.
2. Set sorting to newest first (if available) and copy the resulting URL from the address bar.
3. Paste that URL as the `searchURL` value.

Example `config.json` snippet:

```json
{
  "companyName": "Microsoft",
  "searchSettings": {
    "searchURL": "https://jobs.careers.microsoft.com/global/en/search?lc=Mexico&l=en_us&pg=1&pgSz=20&o=Recent&flt=true",
    "numberOfPages": 5
  }
}
```

Troubleshooting tips:
- If the site doesn't update the address bar after applying filters, use the site's Search button or inspect the Network tab to capture the request URL.
- Encode spaces as `%20` or let the browser provide the encoded URL.
- Some sites require scrolling/lazy-loading; configuring query parameters is more reliable than scraping dynamically-loaded results.

Verification:
- After editing `config.json`, run the appropriate scraper to confirm it returns expected listings.
- Quick config print (PowerShell):

```powershell
python -c "import json,sys;print(json.load(open('config.json')))
```

If you want, paste a sample search URL and I can advise on the best `numberOfPages` to use.

- Run the Meta daily incremental scraper:

```powershell
python meta-jobs-daily-scraper.py
```

- For a first-time full run of Meta:

```powershell
python meta-jobs-first-time-scrapper.py
```

#### Automation (GitHub Actions)

The repository includes a workflow that runs the scrapers daily and uploads results as artifacts. The workflow also optionally commits updated JSON outputs back to the repository when changes are detected.

Key notes:
- Schedule: 7:00 AM UTC daily
- Artifacts: uploaded under the name `job-scraping-results-${{ github.run_number }}`
- Retention: 30 days (configurable in the workflow)

## 🔧 Configuring searches (edit `config.json`)

To target a specific search (department, location, remote, newest first, etc.) update the company's `searchURL` in `config.json` and optionally set `numberOfPages`.

Steps:
1. Open the company's careers page and apply the filters you want.
2. Set sorting to newest first (if available) and copy the resulting URL from the address bar.
3. Paste that URL as the `searchURL` value.

Example `config.json` snippet:

```json
{
  "companyName": "Microsoft",
  "searchSettings": {
    "searchURL": "https://jobs.careers.microsoft.com/global/en/search?lc=Mexico&l=en_us&pg=1&pgSz=20&o=Recent&flt=true",
    "numberOfPages": 5
  }
}
```

Troubleshooting tips:
- If the site doesn't update the address bar after applying filters, use the site's Search button or inspect the Network tab to capture the request URL.
- Encode spaces as `%20` or let the browser provide the encoded URL.
- Some sites require scrolling/lazy-loading; configuring query parameters is more reliable than scraping dynamically-loaded results.

Verification:
- After editing `config.json`, run the appropriate scraper to confirm it returns expected listings.
- Quick config print (PowerShell):

```powershell
python -c "import json,sys;print(json.load(open('config.json')))
```

If you want, paste a sample search URL and I can advise on the best `numberOfPages` to use.

