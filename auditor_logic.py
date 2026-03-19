import requests
from bs4 import BeautifulSoup
import time
import asyncio
from playwright.async_api import async_playwright

class FiisualAuditor:
    def __init__(self, url):
        self.url = url
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        self.report = []
        self.load_time = 0
        self.screenshot_path = "mobile_test.png"

    def _log(self, block, item, severity, status, detail=""):
        self.report.append({"區塊": block, "檢測項目": item, "嚴重程度": severity, "狀態": "✅ 通過" if status else "❌ 待修復", "備註": detail})

    async def run_full_audit(self):
        # --- Block 1 & 2: SEO & Accessibility (靜態檢查) ---
        res = requests.get(self.url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # SEO 邏輯
        h1s = soup.find_all('h1')
        self._log("SEO", "H1 存在", "Critical", len(h1s) > 0)
        self._log("SEO", "H1 唯一性", "High", len(h1s) == 1, f"偵測到 {len(h1s)} 個")
        
        # A11y 邏輯
        self._log("A11y", "html lang 設定", "Critical", soup.find('html').has_attr('lang'))
        self._log("A11y", "圖片 alt 屬性", "Medium", all(img.has_attr('alt') for img in soup.find_all('img')))

        # --- Block 3 & 4: Page Speed & Viewport (動態檢查) ---
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # 模擬 iPhone 15 規格
            context = await browser.new_context(viewport={'width': 393, 'height': 852}, is_mobile=True)
            page = await context.new_page()
            
            start_time = time.time()
            await page.goto(self.url, wait_until="networkidle")
            self.load_time = time.time() - start_time
            
            # Page Speed 判定
            self._log("Speed", "載入時間 < 3秒", "Medium", self.load_time < 3, f"{self.load_time:.2f}s")
            
            # Viewport 截圖
            await page.screenshot(path=self.screenshot_path, full_page=False)
            self._log("View", "手機版渲染完成", "High", True, "請查看下方截圖")
            
            await browser.close()
        
        return self.report