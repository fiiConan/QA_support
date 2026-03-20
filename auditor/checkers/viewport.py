import os


def log_result(report, block, item, severity, status, detail=""):
    status_map = {
        True: "✅ 通過",
        False: "❌ 待修復",
        None: "⏭ 未執行",
    }

    report.append({
        "區塊": block,
        "檢測項目": item,
        "嚴重程度": severity,
        "狀態": status_map.get(status, "⏭ 未執行"),
        "備註": detail
    })


VIEWPORTS = {
    "Desktop": {"width": 1440, "height": 900, "is_mobile": False},
    "Tablet": {"width": 768, "height": 1024, "is_mobile": True},
    "Mobile": {"width": 393, "height": 852, "is_mobile": True},
}


BROWSER_TARGETS = [
    {
        "label": "Chrome",
        "engine": "chromium",
        "launch_kwargs": {},
        "context_kwargs": {
            "viewport": {"width": 1440, "height": 900},
            "is_mobile": False,
        },
    },
    {
        "label": "Safari",
        "engine": "webkit",
        "launch_kwargs": {},
        "context_kwargs": {
            "viewport": {"width": 1440, "height": 900},
            "is_mobile": False,
        },
        "note": "以 Playwright WebKit 模擬 Safari",
    },
    {
        "label": "Edge",
        "engine": "chromium",
        "launch_kwargs": {"channel": "msedge"},
        "context_kwargs": {
            "viewport": {"width": 1440, "height": 900},
            "is_mobile": False,
        },
        "note": "需本機已安裝 Microsoft Edge",
    },
    {
        "label": "Android",
        "engine": "chromium",
        "launch_kwargs": {},
        "device": "Pixel 5",
        "note": "以 Playwright 裝置模擬 Android Chrome",
    },
]


async def run_single_viewport_check(browser, url, device_name, config, report, output_dir):
    context = await browser.new_context(
        viewport={"width": config["width"], "height": config["height"]},
        is_mobile=config["is_mobile"]
    )
    page = await context.new_page()

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)

        screenshot_path = os.path.join(
            output_dir,
            f"{device_name.lower()}_chromium.png"
        )
        await page.screenshot(path=screenshot_path, full_page=False)

        log_result(
            report,
            "Viewport",
            f"{device_name} 正常顯示",
            "high",
            True,
            screenshot_path
        )

        horizontal_scroll = await page.evaluate(
            "() => document.documentElement.scrollWidth > window.innerWidth"
        )
        log_result(
            report,
            "Viewport",
            f"{device_name} 無橫向捲動",
            "high",
            not horizontal_scroll,
            "偵測到內容溢出" if horizontal_scroll else ""
        )

    except Exception as e:
        log_result(report, "Viewport", f"{device_name} 正常顯示", "high", False, str(e))
        log_result(report, "Viewport", f"{device_name} 無橫向捲動", "high", False, str(e))
    finally:
        await context.close()


async def run_browser_checks(playwright, url, report, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)

    for target in BROWSER_TARGETS:
        label = target["label"]
        engine_name = target["engine"]
        launch_kwargs = target.get("launch_kwargs", {})
        note = target.get("note", "")

        browser = None
        context = None

        try:
            engine = getattr(playwright, engine_name)
            browser = await engine.launch(headless=True, **launch_kwargs)

            if "device" in target:
                device_name = target["device"]
                device_config = playwright.devices[device_name]
                context = await browser.new_context(**device_config)
            else:
                context = await browser.new_context(**target.get("context_kwargs", {}))

            page = await context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)

            screenshot_path = os.path.join(output_dir, f"browser_{label.lower()}.png")
            await page.screenshot(path=screenshot_path, full_page=False)

            horizontal_scroll = await page.evaluate(
                "() => document.documentElement.scrollWidth > window.innerWidth"
            )

            log_result(
                report,
                "Viewport",
                f"{label} 瀏覽器正常顯示",
                "high",
                True,
                f"{screenshot_path}" + (f"；{note}" if note else "")
            )

            log_result(
                report,
                "Viewport",
                f"{label} 無橫向捲動",
                "high",
                not horizontal_scroll,
                ("偵測到內容溢出；" if horizontal_scroll else "") + note
            )

        except Exception as e:
            error_text = str(e)

            if label in {"Edge"}:
                log_result(
                    report,
                    "Viewport",
                    f"{label} 瀏覽器正常顯示",
                    "high",
                    None,
                    f"未執行：{error_text}"
                )
                log_result(
                    report,
                    "Viewport",
                    f"{label} 無橫向捲動",
                    "high",
                    None,
                    f"未執行：{error_text}"
                )
            else:
                log_result(
                    report,
                    "Viewport",
                    f"{label} 瀏覽器正常顯示",
                    "high",
                    False,
                    error_text
                )
                log_result(
                    report,
                    "Viewport",
                    f"{label} 無橫向捲動",
                    "high",
                    False,
                    error_text
                )
        finally:
            if context:
                await context.close()
            if browser:
                await browser.close()


async def run_viewport_checks(playwright, browser, url, report, output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)

    for device_name, config in VIEWPORTS.items():
        await run_single_viewport_check(
            browser=browser,
            url=url,
            device_name=device_name,
            config=config,
            report=report,
            output_dir=output_dir
        )

    await run_browser_checks(
        playwright=playwright,
        url=url,
        report=report,
        output_dir=output_dir
    )