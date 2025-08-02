# main.py

from scraper.job_scraper import JobScraper

def main():
    url = "https://example.com/jobs"  # Replace with the actual job listing URL
    scraper = JobScraper(url)
    jobs = scraper.fetch_jobs()
    for job in jobs:
        print(job)

if __name__ == "__main__":
    main()