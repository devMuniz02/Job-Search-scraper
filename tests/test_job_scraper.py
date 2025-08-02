import unittest
from unittest.mock import patch, MagicMock
from src.scraper.job_scraper import JobScraper

class TestJobScraper(unittest.TestCase):

    @patch('src.scraper.job_scraper.requests.get')
    def test_fetch_jobs(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><div class="job">Job 1</div></body></html>'
        mock_get.return_value = mock_response

        scraper = JobScraper('http://fakeurl.com')
        jobs = scraper.fetch_jobs()

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0], 'Job 1')

    def test_parse_jobs(self):
        html_content = '<html><body><div class="job">Job 1</div><div class="job">Job 2</div></body></html>'
        scraper = JobScraper('http://fakeurl.com')
        jobs = scraper.parse_jobs(html_content)

        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0], 'Job 1')
        self.assertEqual(jobs[1], 'Job 2')

if __name__ == '__main__':
    unittest.main()