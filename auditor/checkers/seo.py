import requests


def log_result(report, block, item, severity, status, detail=""):
    report.append({
        "區塊": block,
        "檢測項目": item,
        "嚴重程度": severity,
        "狀態": "✅ 通過" if status else "❌ 待修復",
        "備註": detail
    })


def is_heading_order_valid(soup):
    headings = soup.find_all(["h1", "h2", "h3"])
    if not headings:
        return False, "未找到 H1-H3"

    levels = []
    for h in headings:
        try:
            levels.append(int(h.name[1]))
        except Exception:
            continue

    if not levels:
        return False, "未找到有效 heading"

    prev = levels[0]
    for level in levels[1:]:
        if level - prev > 1:
            return False, f"發現跳階：H{prev} -> H{level}"
        prev = level

    return True, "heading 階層正常"


def has_fake_heading_div(soup):
    fake_candidates = []

    for tag in soup.find_all(["div", "span", "p"]):
        classes = " ".join(tag.get("class", [])) if tag.get("class") else ""
        style = tag.get("style", "") or ""
        text = tag.get_text(strip=True)

        if not text:
            continue

        if (
            "title" in classes.lower()
            or "heading" in classes.lower()
            or "font-size" in style.lower()
            or "font-weight" in style.lower()
        ):
            fake_candidates.append(text[:50])

    return len(fake_candidates) == 0, f"疑似偽標籤數量: {len(fake_candidates)}"


def check_og_image_accessible(soup):
    og_image = soup.find("meta", attrs={"property": "og:image"})
    if not og_image or not og_image.get("content", "").strip():
        return False, "找不到 og:image"

    url = og_image.get("content", "").strip()
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return response.status_code == 200, f"status={response.status_code}"
    except Exception as e:
        return False, str(e)


def run_seo_checks(soup, report):
    h1s = soup.find_all("h1")
    h2s = soup.find_all("h2")
    h3s = soup.find_all("h3")
    headings = h1s + h2s + h3s

    # H1 存在
    log_result(report, "SEO", "H1 存在", "critical", len(h1s) > 0)

    # H1 只有一個
    log_result(report, "SEO", "H1 只有一個", "high", len(h1s) == 1, f"偵測到 {len(h1s)} 個")

    # 不使用 div 做偽標籤
    ok_fake_heading, fake_detail = has_fake_heading_div(soup)
    log_result(report, "SEO", "不使用 div 做偽標籤", "high", ok_fake_heading, fake_detail)

    # H1-H3 階層順序正確
    order_ok, order_detail = is_heading_order_valid(soup)
    log_result(report, "SEO", "H1 - H3 階層順序正確（不跳階）", "medium", order_ok, order_detail)

    # heading 標籤內容不可為空
    heading_non_empty = len(headings) > 0 and all(h.get_text(strip=True) for h in headings)
    log_result(report, "SEO", "heading 標籤內容不可為空", "high", heading_non_empty)

    # Title 存在
    title_tag = soup.find("title")
    title_exists = title_tag is not None and bool(title_tag.get_text(strip=True))
    log_result(report, "SEO", "Title 存在", "critical", title_exists)

    # Title 唯一（不為預設值）
    title_tags = soup.find_all("title")
    title_text = title_tag.get_text(strip=True).lower() if title_tag else ""
    default_like = title_text in {"home", "index", "untitled", "document"}
    title_unique_ok = len(title_tags) == 1 and title_exists and not default_like
    log_result(
        report,
        "SEO",
        "Title 唯一（不為預設值）",
        "critical",
        title_unique_ok,
        f"偵測到 {len(title_tags)} 個；title='{title_text}'"
    )

    # Meta Description 存在
    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_desc_exists = meta_desc is not None and bool(meta_desc.get("content", "").strip())
    log_result(report, "SEO", "Meta Description 存在", "high", meta_desc_exists)

    # Meta Description 長度合理
    meta_len = len(meta_desc.get("content", "").strip()) if meta_desc_exists else 0
    meta_len_ok = 50 <= meta_len <= 160
    log_result(report, "SEO", "Meta Description 長度合理", "low", meta_len_ok, f"長度 {meta_len}")

    # OG title 存在
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_title_ok = og_title is not None and bool(og_title.get("content", "").strip())
    log_result(report, "SEO", "OG title 存在", "medium", og_title_ok)

    # OG Description 存在
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_desc_ok = og_desc is not None and bool(og_desc.get("content", "").strip())
    log_result(report, "SEO", "OG Description 存在", "medium", og_desc_ok)

    # OG Image 存在且可存取（Http 200）
    og_image_ok, og_image_detail = check_og_image_accessible(soup)
    log_result(report, "SEO", "OG Image 存在且可存取（Http 200）", "medium", og_image_ok, og_image_detail)

    # <img> 圖片皆有 alt 屬性
    imgs = soup.find_all("img")
    all_alt = all(img.has_attr("alt") for img in imgs)
    log_result(report, "SEO", "<img> 圖片皆有 alt 屬性", "medium", all_alt, f"共 {len(imgs)} 張圖")

    # 頁面有足夠文字內容
    body_text = soup.get_text(separator=" ", strip=True)
    text_len = len(body_text)
    enough_content = text_len >= 300
    log_result(report, "SEO", "頁面有足夠文字內容", "low", enough_content, f"文字長度 {text_len}")