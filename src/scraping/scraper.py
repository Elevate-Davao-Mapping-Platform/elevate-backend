import time
from typing import List, Set
from urllib.parse import urljoin, urlparse

import pdfkit
import requests
import urllib3
from aws_lambda_powertools import Logger
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WebScraper:
    def __init__(self):
        self.url_list = [
            'https://www.mugna.tech',
            'https://www.ingenuity.ph',
            'https://ideasdavao.org',
        ]
        self.visited: Set[str] = set()
        self.html_pages: List[str] = []
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        self.logger = Logger()

    def is_valid_url(self, url: str, base_url: str) -> bool:
        """Check if the URL is valid and belongs to the base domain."""
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and parsed.netloc == urlparse(base_url).netloc

    def get_all_links(self, soup: BeautifulSoup, current_url: str, base_url: str) -> List[str]:
        """Extract all valid internal links from the page soup."""
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            href = urljoin(current_url, href)
            if self.is_valid_url(href, base_url):
                links.append(href)
        return links

    def scrape_page(self, url: str) -> str | None:
        """Scrape the content of a single page and return its HTML."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f'Error scraping {url}: {e}')
            return None

    def crawl(self) -> None:
        """
        Crawl multiple websites from the url_list.
        """
        for base_url in self.url_list:
            self.logger.info(f'Starting crawl for: {base_url}')
            # First, scrape the base URL
            self.scrape_single_url(base_url)

            time.sleep(1)

            # Then discover and scrape additional pages
            self.discover_additional_pages(base_url, base_url)

    def scrape_single_url(self, url: str) -> None:
        """Scrape a single URL without recursive crawling."""
        if url in self.visited:
            return

        self.visited.add(url)
        self.logger.info(f'Scraping priority URL: {url}')

        html_content = self.scrape_page(url)
        if html_content:
            self.html_pages.append(html_content)

    def discover_additional_pages(self, url: str, base_url: str) -> None:
        """Recursively discover and scrape additional pages."""
        if url in self.visited:
            return

        self.visited.add(url)
        self.logger.info(f'Discovering additional pages from: {url}')

        html_content = self.scrape_page(url)
        if html_content:
            self.html_pages.append(html_content)

            soup = BeautifulSoup(html_content, 'html.parser')
            links = self.get_all_links(soup, url, base_url)
            for link in links:
                if link not in self.visited:
                    time.sleep(1)  # Be polite between requests
                    self.discover_additional_pages(link, base_url)

    def save_pdf(self, output_path: str) -> None:
        """Convert the list of HTML pages into a single multipage PDF."""
        self.logger.info('Saving to PDF...')

        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None,
        }

        config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')

        all_text = []
        for html in self.html_pages:
            soup = BeautifulSoup(html, 'html.parser')
            text = '\n'.join(line.strip() for line in soup.get_text().split('\n') if line.strip())
            all_text.append(text)

        combined_text = (
            '<div style="page-break-after: always;">'
            + '</div><div style="page-break-after: always;">'.join(all_text)
            + '</div>'
        )

        full_html = f"""
        <html>
          <head>
            <meta charset='UTF-8'>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              div {{ white-space: pre-wrap; }}
            </style>
          </head>
          <body>{combined_text}</body>
        </html>
        """

        try:
            pdfkit.from_string(full_html, output_path, options=options, configuration=config)
            self.logger.info(f'Saved {output_path}')
        except Exception as e:
            self.logger.error(f'Error generating PDF: {e}')
