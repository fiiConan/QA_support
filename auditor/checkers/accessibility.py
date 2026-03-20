from checkers.helpers import log_result, describe_element, describe_context


def has_accessible_name(tag):
    text_ok = bool(tag.get_text(strip=True))
    aria_ok = bool(tag.get("aria-label", "").strip())
    title_ok = bool(tag.get("title", "").strip())
    img_alt_ok = False

    img = tag.find("img")
    if img is not None:
        img_alt_ok = bool(img.get("alt", "").strip())

    return text_ok or aria_ok or title_ok or img_alt_ok


def describe_input_issue(inp):
    input_type = inp.get("type", "text")
    name = inp.get("name", "").strip()
    placeholder = inp.get("placeholder", "").strip()
    input_id = inp.get("id", "").strip()

    parts = [f"輸入欄位 type={input_type}"]

    if name:
        parts.append(f"name={name}")
    if input_id:
        parts.append(f"id={input_id}")
    if placeholder:
        parts.append(f"placeholder={placeholder}")

    desc = "；".join(parts)
    return f"{desc}；缺少對應 label；位置：{describe_context(inp)}"


def run_accessibility_checks(soup, report, page_url=""):
    html_tag = soup.find("html")
    html_lang_ok = (
        html_tag is not None
        and html_tag.has_attr("lang")
        and bool(html_tag.get("lang", "").strip())
    )
    log_result(report, "Accessibility", "html lang 設定", "critical", html_lang_ok)

    main_ok = soup.find("main") is not None
    log_result(report, "Accessibility", "<main> 標籤", "high", main_ok)

    interactive_tags = soup.find_all(["button", "a"])
    bad_interactive = []

    for tag in interactive_tags:
        if not has_accessible_name(tag):
            bad_interactive.append(
                f"{describe_element(tag, page_url)}；位置：{describe_context(tag)}"
            )

    log_result(
        report,
        "Accessibility",
        "<button> & <a> 標籤有 aria-label",
        "critical",
        len(bad_interactive) == 0,
        f"未通過數量: {len(bad_interactive)}",
        bad_interactive
    )

    inputs = soup.find_all("input")
    bad_inputs = []

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
            bad_inputs.append(describe_input_issue(inp))

    log_result(
        report,
        "Accessibility",
        "<input> 標籤有對應的 label",
        "critical",
        len(bad_inputs) == 0,
        f"未通過 {len(bad_inputs)} 個",
        bad_inputs
    )