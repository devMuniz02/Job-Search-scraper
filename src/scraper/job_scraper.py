class JobScraper:
    def __init__(self, url):
        self.url = url

    def fetch_jobs(self):
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(self.url)
        if response.status_code != 200:
            raise Exception("Failed to load page")
        
        return self.parse_jobs(response.text)

    def parse_jobs(self, html):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        
        for job_element in soup.find_all('div', class_='job-listing'):
            title = job_element.find('h2').text.strip()
            company = job_element.find('div', class_='company').text.strip()
            location = job_element.find('div', class_='location').text.strip()
            jobs.append({
                'title': title,
                'company': company,
                'location': location
            })
        
        return jobs