# Microsoft Jobs Scraper - Automated Edition

An automated Python script that scrapes Microsoft job postings, extracts detailed information, filters by criteria, and organizes results by date. Designed to run daily via GitHub Actions.

## 🚀 Features

- **Automated Daily Scraping**: Runs automatically every day at 2:00 AM UTC
- **Complete Job Details**: Extracts titles, locations, qualifications, pay ranges, and more
- **Smart Filtering**: Identifies Python jobs while filtering out unwanted positions
- **Date Organization**: Groups jobs by posting date for easy tracking
- **GitHub Integration**: Automatically commits results and provides detailed summaries

## 📁 Files Created

The scraper generates several files:

- `jobs_ms.json` - Basic job listings index
- `jobs_ms_details.json` - Detailed job information  
- `jobs_ms_avoid_hits_by_field.json` - Filtered job categories
- `jobs_by_date/` - Directory with Python jobs organized by date

## 🔧 Setup for GitHub Actions

1. **Push to GitHub**: Ensure your repository is on GitHub
2. **Enable Actions**: The workflow will automatically run daily
3. **Manual Trigger**: Go to Actions → "Daily Microsoft Jobs Scraper" → "Run workflow"

## 📊 What Gets Filtered

The scraper identifies and filters jobs based on:

- **Python Jobs**: ✅ Keeps jobs mentioning Python
- **Visa Sponsorship**: ❌ Removes jobs requiring citizenship/no sponsorship
- **Senior Only**: ❌ Removes jobs requiring 6+ years experience
- **Security Clearance**: ❌ Removes jobs requiring clearance
- **Full Stack**: ❌ Removes jobs requiring HTML/React/Angular/etc.
- **Unwanted Languages**: ❌ Removes Java/JavaScript/C#/etc. focused roles
- **Non-Technical**: ❌ Removes finance/sales/marketing/legal positions

## 🏃‍♂️ Local Usage

To run the scraper locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python ms-job-scrapper.py
```

## ⚙️ Configuration

Edit these variables in `ms-job-scrapper.py`:

- `MAX_PAGES`: Number of pages to scrape (default: 10)
- `SEARCH_URL`: Microsoft careers search URL with filters
- `AVOID_RULES`: Job filtering criteria
- `DELAY_AFTER_NEXT`: Delay between page requests

## 📈 GitHub Actions Workflow

The workflow (`daily-scraper.yml`):

1. **Installs** Python and Chrome
2. **Runs** the scraper
3. **Commits** results if there are changes
4. **Creates** a summary with statistics
5. **Uploads** artifacts for download
6. **Notifies** on failures

## 📋 Monitoring

Check the Actions tab for:
- ✅ Successful runs with job counts
- ❌ Failed runs with error details  
- 📊 Summary reports with statistics
- 💾 Downloadable result artifacts

## 🛠️ Troubleshooting

Common issues:

- **No jobs found**: Website structure may have changed
- **Chrome errors**: Browser compatibility issues
- **Rate limiting**: Too many requests, increase delays
- **Git push fails**: Check repository permissions

## 📝 Sample Output Structure

```
jobs_by_date/
├── jobs_26_september_2025.json
├── jobs_27_september_2025.json
└── jobs_29_september_2025.json
```

Each date file contains Python jobs with:
```json
{
  "job_id": "1234567",
  "title": "Software Engineer - Python",
  "locations": ["Seattle, WA", "Remote"],
  "date_posted": "Sep 29, 2025",
  "url": "https://...",
  "required_qualifications_text": "...",
  "pay_ranges": [{"region": "U.S.", "range": "USD $120,000 - $180,000"}]
}
```

## 🔄 Automation Schedule

- **Daily at 2:00 AM UTC** (adjust in workflow file)
- **Manual trigger** available in GitHub Actions
- **Results committed** automatically to repository
- **30-day artifact retention** for backup downloads

---

*Last updated: September 2025*