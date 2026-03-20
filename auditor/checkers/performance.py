import time


def log_result(report, block, item, severity, status, detail=""):
    report.append({
        "區塊": block,
        "檢測項目": item,
        "嚴重程度": severity,
        "狀態": "✅ 通過" if status else "❌ 待修復",
        "備註": detail
    })


async def run_performance_checks(browser, url, report):
    context = await browser.new_context(
        viewport={"width": 393, "height": 852},
        is_mobile=True
    )
    page = await context.new_page()

    try:
        start = time.time()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        load_time = time.time() - start

        log_result(
            report,
            "Page Speed",
            "載入時間小於 3 秒",
            "medium",
            load_time < 3,
            f"{load_time:.2f}s"
        )

        images_info = await page.evaluate("""
        () => {
            return [...document.images].map(img => ({
                src: img.currentSrc || img.src || "",
                naturalWidth: img.naturalWidth || 0,
                naturalHeight: img.naturalHeight || 0
            }));
        }
        """)

        oversized = []
        for img in images_info:
            if img["naturalWidth"] > 3000 or img["naturalHeight"] > 3000:
                oversized.append(img["src"])

        log_result(
            report,
            "Page Speed",
            "圖片大小合理（未過大）",
            "medium",
            len(oversized) == 0,
            f"過大圖片數量: {len(oversized)}"
        )

    except Exception as e:
        log_result(report, "Page Speed", "載入時間小於 3 秒", "medium", False, str(e))
        log_result(report, "Page Speed", "圖片大小合理（未過大）", "medium", False, str(e))
    finally:
        await context.close()