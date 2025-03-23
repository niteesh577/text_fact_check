import requests
from bs4 import BeautifulSoup
from typing import Optional
import trafilatura

class WebScraperTool:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def scrape(self, url: str) -> dict:
        try:
            # Download webpage
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            # Extract main content using trafilatura
            downloaded = trafilatura.fetch_url(url)
            main_content = trafilatura.extract(downloaded, include_comments=False)
            
            # Parse with BeautifulSoup for metadata
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract metadata
            metadata = {
                "title": soup.title.string if soup.title else "",
                "meta_description": soup.find("meta", {"name": "description"})["content"] if soup.find("meta", {"name": "description"}) else "",
                "publish_date": soup.find("meta", {"property": "article:published_time"})["content"] if soup.find("meta", {"property": "article:published_time"}) else None
            }
            
            return {
                "url": url,
                "content": main_content,
                "metadata": metadata,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "status": "failed"
            }
