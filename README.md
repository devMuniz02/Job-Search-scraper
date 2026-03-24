[![ArXiv](https://img.shields.io/badge/ArXiv-2512.16841-B31B1B?logo=arxiv&logoColor=white)](https://arxiv.org/abs/2512.16841)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-devmuniz-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/devmuniz)
[![GitHub Profile](https://img.shields.io/badge/GitHub-devMuniz02-181717?logo=github&logoColor=white)](https://github.com/devMuniz02)
[![Portfolio](https://img.shields.io/badge/Portfolio-devmuniz02.github.io-0F172A?logo=googlechrome&logoColor=white)](https://devmuniz02.github.io/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-manu02-FFD21E?logoColor=black)](https://huggingface.co/manu02)

# Microsoft & Meta Jobs Scraper

A comprehensive Python web scraper for extracting job listings from both Microsoft Careers and Meta Careers websites with advanced filtering, data processing, incremental scraping, and automated daily collection via GitHub Actions.

``` Job-Search-scrapper/ ├── README.md # this file ├── LICENSE ├── config.json # runtime search configuration ├── requirements.txt # Python dependencies ├── ms-jobs-daily-scrapper.py # Microsoft daily scraper runner ├── meta-jobs-daily-scraper.py # Meta daily incremental scraper runner ├── meta-jobs-first-time-scrapper.py # Meta full first-time scraper ├── Meta-jobs/ # Meta-specific output and state │ ├── meta_job_details.json │ ├── meta_job_ids.json │ └── jobs_by_date/ │ ├── jobs_"date".json ├── Microsoft-jobs/ # Microsoft-specific output and state │ ├── ms_job_avoid_hits_by_field.json │ ├── ms_job_avoid_hits.json │ ├── ms_job_details.json │ ├── ms_job_ids.json │ └── jobs_by_date/ │ ├── jobs_"date".json └── utils/ # helper modules used by scrapers ├── __init__.py ├── meta_config.py ├── ms_config.py ├── ms_core.py ├── selenium_helpers.py └── README.md

## Overview

This is the scrapper i use to find jobs that fit my description

## Repository Structure

| Path | Description |
| --- | --- |
| `assets/` | Images, figures, or other supporting media used by the project. |
| `Meta-jobs/` | Top-level project directory containing repository-specific resources. |
| `Microsoft-jobs/` | Top-level project directory containing repository-specific resources. |
| `utils/` | Reusable helper modules and shared utility functions. |
| `.gitignore` | Top-level file included in the repository. |
| `config.json` | Top-level file included in the repository. |
| `LICENSE` | Repository license information. |
| `meta_jobs_daily_scraper.py` | Top-level file included in the repository. |
| `meta_jobs_first_time_scraper.py` | Top-level file included in the repository. |
| `ms_jobs_daily_scraper.py` | Top-level file included in the repository. |

## Getting Started

1. Clone the repository.

   ```bash
   git clone https://github.com/devMuniz02/Job-Search-scraper.git
   cd Job-Search-scraper
   ```

2. Prepare the local environment.

Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Run or inspect the project entry point.

Use the project-specific scripts or notebooks in the repository root to run the workflow.

## Project Structure

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
    ├── meta_config.py
    ├── ms_config.py
    ├── ms_core.py
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

## Configuring searches edit configjson

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
For more specialized configurations modify the utils/**CompanyName**_config.py file

## Quick Start  Fork  run GitHub Actions

If you want to run this repository from your own fork as a daily scraper via GitHub Actions, follow these steps. This covers forking, configuring `config.json`, enabling Actions in your fork, and notes about committing results back to your fork.

1) Fork the repository on GitHub

- Go to the original repo page and click the "Fork" button to create a copy under your account.


2) Edit `config.json` in your fork to configure the searches you want the Actions workflow to run. Update `searchURL`, `numberOfPages`, and any other company-specific settings. Example:

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

3) Enable GitHub Actions in your fork

- In your fork on GitHub, go to the "Actions" tab and enable workflows if prompted. If the repository already contains workflow files under `.github/workflows/`, they will be available in your fork.
- Inspect the workflow YAML(s) in `.github/workflows/` to confirm the schedule (cron), the runner used, and whether the workflow commits artifacts or JSON output back to the repository. Adjust as needed.
