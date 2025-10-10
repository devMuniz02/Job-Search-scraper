
# Microsoft & Meta Jobs Scraper

A comprehensive Python web scraper for extracting job listings from both Microsoft Careers and Meta Careers websites with advanced filtering, data processing, incremental scraping, and automated daily collection via GitHub Actions.

## 📁 Project Structure
This repository contains scrapers and helper utilities for extracting job listings from Microsoft and Meta career sites. The tree below shows the current project layout and the most important files.

```
Job-Search-scrapper/
├── README.md                      # this file
├── LICENSE
├── config.json                    # runtime search configuration
├── requirements.txt               # Python dependencies
├── ms-jobs-daily-scrapper.py      # Microsoft daily scraper runner
├── meta-jobs-daily-scraper.py     # Meta daily incremental scraper runner
├── meta-jobs-first-time-scrapper.py # Meta full first-time scraper
├── Meta-jobs/                     # Meta-specific output and state
│   ├── meta_job_details.json
│   ├── meta_job_ids.json
│   └── jobs_by_date/
│       ├── jobs_"date".json
├── Microsoft-jobs/                # Microsoft-specific output and state
│   ├── ms_job_avoid_hits_by_field.json
│   ├── ms_job_avoid_hits.json
│   ├── ms_job_details.json
│   ├── ms_job_ids.json
│   └── jobs_by_date/
│       ├── jobs_"date".json
└── utils/                          # helper modules used by scrapers
  ├── __init__.py
  ├── config.py
  ├── core.py
  ├── meta_config.py
  ├── patterns.py
  ├── selenium_helpers.py
  └── README.md

```

Quick file purposes:

- `ms-jobs-daily-scrapper.py` — main runner to scrape Microsoft jobs incrementally each day.
- `meta-jobs-daily-scraper.py` — incremental daily runner for Meta jobs.
- `meta-jobs-first-time-scrapper.py` — full initial run for Meta to seed IDs/details.
- `config.json` — contains search URLs and scraping options (edit to change searches).
- `utils/` — shared utilities and Selenium helpers.

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

## 🚀 Quick Start — Fork & run (GitHub Actions)

If you want to run this repository from your own fork as a daily scraper via GitHub Actions, follow these steps. This covers forking, configuring `config.json`, enabling Actions in your fork, and notes about committing results back to your fork.

1) Fork the repository on GitHub

- Go to the original repo page and click the "Fork" button to create a copy under your account.

2) (Optional) Clone your fork locally and set upstream

```powershell
git clone https://github.com/<your-username>/Job-Search-scrapper.git
cd Job-Search-scrapper
git remote add upstream https://github.com/devMuniz02/Job-Search-scrapper.git
git fetch upstream
```

3) Edit `config.json` in your fork to configure the searches you want the Actions workflow to run. Update `searchURL`, `numberOfPages`, and any other company-specific settings. Example:

```json
{
  "companyName": "Microsoft",
  "searchSettings": {
    "searchURL": "https://jobs.careers.microsoft.com/global/en/search?lc=Mexico&l=en_us&pg=1&pgSz=20&o=Recent&flt=true",
    "numberOfPages": 5
  }
}
```

Notes:
- The GitHub Actions workflow runs using the code and files in your fork. Make sure `config.json` in the default branch of your fork contains the settings you want.
- If you want the workflow to run for multiple companies or multiple search URLs, you can modify `config.json` schema (or create multiple workflows) accordingly.

4) Enable GitHub Actions in your fork

- In your fork on GitHub, go to the "Actions" tab and enable workflows if prompted. If the repository already contains workflow files under `.github/workflows/`, they will be available in your fork.
- Inspect the workflow YAML(s) in `.github/workflows/` to confirm the schedule (cron), the runner used, and whether the workflow commits artifacts or JSON output back to the repository. Adjust as needed.

