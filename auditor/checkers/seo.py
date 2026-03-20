import requests
from urllib.parse import urljoin, urlparse

from checkers.helpers import log_result, describe_element, describe_context


def is_heading_order_valid(soup):
    headings = soup.find_all(["h1", "h2", "h3"])
    if not headings:
        return False, "未找到 H1-H3"

    levels = []
    for h in headings:
        try:
            levels.append((h, int(h.name[1])))
        except Exception:
            continue

    if not levels:
        return False, "未找到有效 heading"

    prev_level = levels[0][1]
    for tag, current_level in levels[1:]:
        if current_level - prev_level > 1:
            return False, f"發現跳階：H{prev_level} -> H{current_level}（{tag.get_text(strip=True)[:30]}）"
        prev_level = current_level

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
            fake_candidates.append(f"{text[:30]}；位置：{describe_context(tag)}")

    return len(fake_candidates) == 0, fake_candidates


def check_og_image_accessible(soup, headers):
    og_image = soup.find("meta", attrs={"property": "og:image"})
    if not og_image or not og_image.get("content", "").strip():
        return False, "找不到 og:image"

    url = og_image.get("content", "").strip()
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        return response.status_code == 200, f"status={response.status_code}；{url}"
    except Exception as e:
        return False, str(e)


def check_http_status(response, report):
    ok = response.status_code == 200
    log_result(report, "SEO", "HTTP Status Code 為 200", "critical", ok, f"status={response.status_code}")


def check_canonical(soup, page_url, report):
    canonical_tags = soup.find_all("link", attrs={"rel": "canonical"})
    if not canonical_tags:
        log_result(report, "SEO", "Canonical 存在", "critical", False, issues=["頁面未找到 canonical"])
        log_result(report, "SEO", "Canonical 格式正確", "medium", None, "未找到 canonical")
        return

    href = canonical_tags[0].get("href", "").strip()
    parsed = urlparse(href)
    is_absolute = bool(parsed.scheme and parsed.netloc)
    same_domain = parsed.netloc == urlparse(page_url).netloc if is_absolute else False

    log_result(report, "SEO", "Canonical 存在", "critical", True, href)
    log_result(
        report,
        "SEO",
        "Canonical 格式正確",
        "medium",
        is_absolute and same_domain,
        f"canonical={href}",
        [] if (is_absolute and same_domain) else [f"canonical 可能不正確：{href}"]
    )


def check_robots_meta(soup, report):
    robots = soup.find("meta", attrs={"name": "robots"})
    if robots is None or not robots.get("content", "").strip():
        log_result(report, "SEO", "Meta Robots 存在", "high", False, issues=["頁面未找到 robots meta"])
        log_result(report, "SEO", "Meta Robots 未阻擋索引", "critical", None, "未找到 robots meta")
        return

    content = robots.get("content", "").strip().lower()
    blocks_index = "noindex" in content
    blocks_follow = "nofollow" in content

    log_result(report, "SEO", "Meta Robots 存在", "high", True, content)
    log_result(
        report,
        "SEO",
        "Meta Robots 未阻擋索引",
        "critical",
        not blocks_index and not blocks_follow,
        content,
        [f"robots 設定為：{content}"] if (blocks_index or blocks_follow) else []
    )


def check_sitemap(base_url, headers, report):
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    try:
        response = requests.get(sitemap_url, headers=headers, timeout=10, allow_redirects=True)
        content_type = response.headers.get("Content-Type", "")
        ok = response.status_code == 200 and ("xml" in content_type.lower() or response.text.strip().startswith("<?xml"))
        log_result(report, "SEO", "sitemap.xml 可存取", "high", ok, f"status={response.status_code}；{sitemap_url}")
    except Exception as e:
        log_result(report, "SEO", "sitemap.xml 可存取", "high", False, str(e))


def check_robots_txt(base_url, headers, report):
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = requests.get(robots_url, headers=headers, timeout=10, allow_redirects=True)
        ok = response.status_code == 200
        detail = f"status={response.status_code}；{robots_url}"

        if ok and "disallow: /" in response.text.lower():
            log_result(report, "SEO", "robots.txt 可存取", "high", True, detail)
            log_result(report, "SEO", "robots.txt 未全站封鎖", "critical", False, "發現 Disallow: /", ["robots.txt 含有 Disallow: /"])
        else:
            log_result(report, "SEO", "robots.txt 可存取", "high", ok, detail)
            log_result(report, "SEO", "robots.txt 未全站封鎖", "critical", True if ok else None, "")
    except Exception as e:
        log_result(report, "SEO", "robots.txt 可存取", "high", False, str(e))
        log_result(report, "SEO", "robots.txt 未全站封鎖", "critical", None, str(e))


def check_structured_data(soup, report):
    schema_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    ok = len(schema_tags) > 0
    log_result(report, "SEO", "Structured Data（JSON-LD）存在", "high", ok, f"找到 {len(schema_tags)} 個")


def check_internal_links(soup, page_url, report):
    parsed_page = urlparse(page_url)
    domain = parsed_page.netloc

    links = soup.find_all("a", href=True)
    internal_links = []
    empty_anchor_issues = []

    for a in links:
        href = a.get("href", "").strip()
        if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
            continue

        full_url = urljoin(page_url, href)
        parsed = urlparse(full_url)

        if parsed.netloc == domain:
            internal_links.append(full_url)
            anchor_text = a.get_text(strip=True)
            aria_label = a.get("aria-label", "").strip()
            title_attr = a.get("title", "").strip()
            if not (anchor_text or aria_label or title_attr):
                empty_anchor_issues.append(
                    f"{describe_element(a)}；位置：{describe_context(a)}"
                )

    log_result(
        report,
        "SEO",
        "存在內部連結",
        "medium",
        len(internal_links) > 0,
        f"internal link 數量: {len(internal_links)}"
    )

    log_result(
        report,
        "SEO",
        "內部連結有可讀 anchor text",
        "medium",
        len(empty_anchor_issues) == 0,
        f"空白 anchor 數量: {len(empty_anchor_issues)}",
        empty_anchor_issues
    )


def check_heading_presence(soup, report):
    h2s = soup.find_all("h2")
    h3s = soup.find_all("h3")

    log_result(report, "SEO", "H2 存在", "medium", len(h2s) > 0, f"偵測到 {len(h2s)} 個")
    log_result(report, "SEO", "H3 存在", "low", len(h3s) > 0, f"偵測到 {len(h3s)} 個")


def check_og_extended(soup, report):
    og_url = soup.find("meta", attrs={"property": "og:url"})
    og_type = soup.find("meta", attrs={"property": "og:type"})

    og_url_ok = og_url is not None and bool(og_url.get("content", "").strip())
    og_type_ok = og_type is not None and bool(og_type.get("content", "").strip())

    log_result(report, "SEO", "OG URL 存在", "low", og_url_ok)
    log_result(report, "SEO", "OG Type 存在", "low", og_type_ok)


def check_image_lazy_loading(soup, report):
    imgs = soup.find_all("img")
    if not imgs:
        log_result(report, "SEO", "圖片使用 lazy loading", "low", None, "頁面無圖片")
        return

    lazy_count = 0
    for img in imgs:
        if img.get("loading", "").strip().lower() == "lazy":
            lazy_count += 1

    ok = lazy_count > 0
    log_result(report, "SEO", "圖片使用 lazy loading", "low", ok, f"lazy={lazy_count} / total={len(imgs)}")


def check_img_alt(soup, report):
    imgs = soup.find_all("img")
    missing_alt = []

    for img in imgs:
        if not img.has_attr("alt") or not img.get("alt", "").strip():
            missing_alt.append(
                f"{describe_element(img)}；位置：{describe_context(img)}"
            )

    log_result(
        report,
        "SEO",
        "<img> 圖片皆有 alt 屬性",
        "medium",
        len(missing_alt) == 0,
        f"共 {len(imgs)} 張圖；缺少 alt 數量: {len(missing_alt)}",
        missing_alt
    )


def run_seo_checks(soup, report, page_url, response, headers):
    h1s = soup.find_all("h1")
    h2s = soup.find_all("h2")
    h3s = soup.find_all("h3")
    headings = h1s + h2s + h3s

    check_http_status(response, report)

    log_result(report, "SEO", "H1 存在", "critical", len(h1s) > 0)
    log_result(report, "SEO", "H1 只有一個", "high", len(h1s) == 1, f"偵測到 {len(h1s)} 個")

    ok_fake_heading, fake_issues = has_fake_heading_div(soup)
    log_result(
        report,
        "SEO",
        "不使用 div 做偽標籤",
        "high",
        ok_fake_heading,
        f"疑似偽標籤數量: {len(fake_issues)}",
        fake_issues
    )

    order_ok, order_detail = is_heading_order_valid(soup)
    log_result(report, "SEO", "H1 - H3 階層順序正確（不跳階）", "medium", order_ok, order_detail)

    empty_headings = []
    for h in headings:
        if not h.get_text(strip=True):
            empty_headings.append(f"{h.name} 空白；位置：{describe_context(h)}")

    log_result(
        report,
        "SEO",
        "heading 標籤內容不可為空",
        "high",
        len(empty_headings) == 0,
        f"空白 heading 數量: {len(empty_headings)}",
        empty_headings
    )

    title_tag = soup.find("title")
    title_exists = title_tag is not None and bool(title_tag.get_text(strip=True))
    log_result(report, "SEO", "Title 存在", "critical", title_exists)

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

    meta_desc = soup.find("meta", attrs={"name": "description"})
    meta_desc_exists = meta_desc is not None and bool(meta_desc.get("content", "").strip())
    log_result(report, "SEO", "Meta Description 存在", "high", meta_desc_exists)

    meta_len = len(meta_desc.get("content", "").strip()) if meta_desc_exists else 0
    meta_len_ok = 50 <= meta_len <= 160
    log_result(report, "SEO", "Meta Description 長度合理", "low", meta_len_ok, f"長度 {meta_len}")

    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_title_ok = og_title is not None and bool(og_title.get("content", "").strip())
    log_result(report, "SEO", "OG title 存在", "medium", og_title_ok)

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    og_desc_ok = og_desc is not None and bool(og_desc.get("content", "").strip())
    log_result(report, "SEO", "OG Description 存在", "medium", og_desc_ok)

    og_image_ok, og_image_detail = check_og_image_accessible(soup, headers)
    log_result(report, "SEO", "OG Image 存在且可存取（Http 200）", "medium", og_image_ok, og_image_detail)

    check_img_alt(soup, report)

    body_text = soup.get_text(separator=" ", strip=True)
    text_len = len(body_text)
    enough_content = text_len >= 300
    log_result(report, "SEO", "頁面有足夠文字內容", "low", enough_content, f"文字長度 {text_len}")

    check_canonical(soup, page_url, report)
    check_robots_meta(soup, report)
    check_sitemap(page_url, headers, report)
    check_robots_txt(page_url, headers, report)
    check_structured_data(soup, report)
    check_internal_links(soup, page_url, report)
    check_heading_presence(soup, report)
    check_og_extended(soup, report)
    check_image_lazy_loading(soup, report)