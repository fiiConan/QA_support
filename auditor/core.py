import os
import json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

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

    async def fetch_rendered_page(self, browser):
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            is_mobile=False,
            user_agent=self.headers["User-Agent"],
        )
        page = await context.new_page()

        try:
            response = None

            try:
                response = await page.goto(
                    self.url,
                    wait_until="domcontentloaded",
                    timeout=30000
                )
            except PlaywrightTimeoutError:
                # 至少保留頁面現況，不直接炸掉
                pass

            # 額外等一下讓前端 JS render
            await page.wait_for_timeout(3000)

            html = await page.content()
            final_url = page.url
            status_code = response.status if response else 200

            return {
                "html": html,
                "final_url": final_url,
                "status_code": status_code,
            }
        finally:
            await context.close()

    async def run_full_audit(self):
        os.makedirs(self.output_dir, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                rendered = await self.fetch_rendered_page(browser)
                soup = BeautifulSoup(rendered["html"], "lxml")

                run_seo_checks(
                    soup=soup,
                    report=self.report,
                    page_url=rendered["final_url"],
                    status_code=rendered["status_code"],
                    headers=self.headers,
                )

                run_accessibility_checks(
                    soup,
                    self.report,
                    rendered["final_url"]
                )

                await run_performance_checks(browser, self.url, self.report)

                await run_viewport_checks(
                    playwright=p,
                    browser=browser,
                    url=self.url,
                    report=self.report,
                    output_dir=self.output_dir
                )

                return self.report

            finally:
                await browser.close()

    def save_report(self, filename="audit_report.json"):
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        return path