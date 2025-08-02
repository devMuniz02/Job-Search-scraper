class JobScraper:
    def __init__(self, url):
        self.url = url

    def fetch_jobs(self, url=None):
        import requests
        from bs4 import BeautifulSoup

        target_url = url if url is not None else self.url
        response = requests.get(target_url)
        if response.status_code != 200:
            raise Exception("Failed to load page")
        
        return self.parse_jobs(response.text)

    def parse_jobs(self, html):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        
        for job_element in soup.find_all('div', class_='job-listing'):
            title = job_element.find('h2').text.strip()
            company_elem = job_element.find('div', class_='company')
            company = company_elem.text.strip() if company_elem else ''
            location_div = job_element.find('div', class_='location')
            location = location_div.text.strip() if location_div else None
            jobs.append({
                'title': title,
                'company': company,
                'location': location
            })
        
        return jobs