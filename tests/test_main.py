import unittest
from unittest.mock import patch
from src.main import main

class TestMain(unittest.TestCase):

    @patch('src.scraper.job_scraper.JobScraper')
    def test_main_initialization(self, MockJobScraper):
        mock_scraper_instance = MockJobScraper.return_value
        main()
        MockJobScraper.assert_called_once()
        mock_scraper_instance.fetch_jobs.assert_called_once_with('http://example.com/jobs')

if __name__ == '__main__':
    unittest.main()