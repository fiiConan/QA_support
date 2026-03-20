def log_result(report, block, item, severity, status, detail=""):
    report.append({
        "區塊": block,
        "檢測項目": item,
        "嚴重程度": severity,
        "狀態": "✅ 通過" if status else "❌ 待修復",
        "備註": detail
    })


def has_accessible_name(tag):
    text_ok = bool(tag.get_text(strip=True))
    aria_ok = bool(tag.get("aria-label", "").strip())
    title_ok = bool(tag.get("title", "").strip())
    img_alt_ok = False

    img = tag.find("img")
    if img is not None:
        img_alt_ok = bool(img.get("alt", "").strip())

    return text_ok or aria_ok or title_ok or img_alt_ok


def run_accessibility_checks(soup, report):
    # html lang 設定
    html_tag = soup.find("html")
    html_lang_ok = (
        html_tag is not None
        and html_tag.has_attr("lang")
        and bool(html_tag.get("lang", "").strip())
    )
    log_result(report, "Accessibility", "html lang 設定", "critical", html_lang_ok)

    # <main> 標籤
    main_ok = soup.find("main") is not None
    log_result(report, "Accessibility", "<main> 標籤", "high", main_ok)

    # <button> & <a> 標籤有 aria-label / 可讀名稱
    interactive_tags = soup.find_all(["button", "a"])
    bad_interactive = []

    for tag in interactive_tags:
        if not has_accessible_name(tag):
            bad_interactive.append(tag.name)

    interactive_ok = len(bad_interactive) == 0
    log_result(
        report,
        "Accessibility",
        "<button> & <a> 標籤有 aria-label",
        "critical",
        interactive_ok,
        f"未通過數量: {len(bad_interactive)}"
    )

    # <input> 標籤有對應的 label
    inputs = soup.find_all("input")
    bad_inputs = 0

    for inp in inputs:
        input_type = inp.get("type", "text").lower()
        if input_type in {"hidden", "submit", "button", "reset", "image"}:
            continue

        input_id = inp.get("id")
        aria_label = inp.get("aria-label", "").strip()
        aria_labelledby = inp.get("aria-labelledby", "").strip()

        has_for_label = False
        if input_id:
            label = soup.find("label", attrs={"for": input_id})
            has_for_label = label is not None

        wrapped_label = inp.find_parent("label") is not None

        if not (has_for_label or wrapped_label or aria_label or aria_labelledby):
            bad_inputs += 1

    inputs_ok = bad_inputs == 0
    log_result(
        report,
        "Accessibility",
        "<input> 標籤有對應的 label",
        "critical",
        inputs_ok,
        f"未通過 {bad_inputs} 個"
    )