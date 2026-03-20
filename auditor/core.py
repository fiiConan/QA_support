import os
import json
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from checkers.seo import run_seo_checks
from checkers.accessibility import run_accessibility_checks
from checkers.performance import run_performance_checks
from checkers.viewport import run_viewport_checks


class FiisualAuditor:
    def __init__(self, url: str, output_dir: str = "outputs"):
        self.url = url
        self.output_dir = output_dir
        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }
        self.report = []
        self.response = None

    def fetch_soup(self):
        self.response = requests.get(self.url, headers=self.headers, timeout=15, allow_redirects=True)
        self.response.raise_for_status()
        return BeautifulSoup(self.response.text, "lxml")

    def run_static_checks(self):
        soup = self.fetch_soup()
        run_seo_checks(
            soup=soup,
            report=self.report,
            page_url=self.url,
            response=self.response,
            headers=self.headers
        )
        run_accessibility_checks(soup, self.report)

    async def run_dynamic_checks(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                await run_performance_checks(browser, self.url, self.report)
                await run_viewport_checks(
                    playwright=p,
                    browser=browser,
                    url=self.url,
                    report=self.report,
                    output_dir=self.output_dir
                )
            finally:
                await browser.close()

    async def run_full_audit(self):
        os.makedirs(self.output_dir, exist_ok=True)
        self.run_static_checks()
        await self.run_dynamic_checks()
        return self.report

    def save_report(self, filename="audit_report.json"):
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        return path