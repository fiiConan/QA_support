from bs4 import Tag
from urllib.parse import urljoin
import re


def build_status_text(status):
    return {
        True: "✅ 通過",
        False: "❌ 待修復",
        None: "⏭ 未執行",
    }.get(status, "⏭ 未執行")


def log_result(report, block, item, severity, status, detail="", issues=None):
    report.append({
        "區塊": block,
        "檢測項目": item,
        "嚴重程度": severity,
        "狀態": build_status_text(status),
        "備註": detail,
        "問題列表": issues or []
    })


def safe_text(text, max_len=40):
    text = (text or "").strip()
    if not text:
        return ""
    return text[:max_len]


def extract_image_url(tag: Tag, page_url: str = ""):
    if tag is None:
        return ""

    candidates = [
        tag.get("src", ""),
        tag.get("data-src", ""),
        tag.get("data-lazy", ""),
        tag.get("data-original", ""),
        tag.get("data-image", ""),
        tag.get("data-fallback-src", ""),
    ]

    srcset = tag.get("srcset", "").strip()
    if srcset:
        first_srcset = srcset.split(",")[0].strip().split(" ")[0].strip()
        if first_srcset:
            candidates.append(first_srcset)

    for candidate in candidates:
        if candidate and candidate.strip():
            return urljoin(page_url, candidate.strip()) if page_url else candidate.strip()

    parent = tag.parent
    if parent and getattr(parent, "name", None) == "picture":
        source = parent.find("source")
        if source:
            source_srcset = source.get("srcset", "").strip()
            if source_srcset:
                first_source = source_srcset.split(",")[0].strip().split(" ")[0].strip()
                if first_source:
                    return urljoin(page_url, first_source) if page_url else first_source

    style = tag.get("style", "")
    if "background-image" in style:
        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
        if match:
            bg_url = match.group(1).strip()
            return urljoin(page_url, bg_url) if page_url else bg_url

    return ""


def describe_element(tag: Tag, page_url=""):
    if tag is None:
        return "未知元素"

    tag_name = tag.name or "未知標籤"

    if tag_name == "img":
        src = extract_image_url(tag, page_url) or "未知圖片"
        alt = tag.get("alt", "").strip()
        return f"圖片：{src}（{'有 alt' if alt else '缺少 alt'}）"

    if tag_name == "a":
        href = tag.get("href", "").strip() or "無 href"
        full_href = urljoin(page_url, href) if page_url and href != "無 href" else href
        text = safe_text(tag.get_text(" ", strip=True), 60)

        if text:
            return f"連結：{text}（{full_href}）"
        return f"連結：{full_href}（無可讀文字）"

    if tag_name == "button":
        text = safe_text(tag.get_text(" ", strip=True), 60)
        aria = tag.get("aria-label", "").strip()
        if text:
            return f"按鈕：{text}"
        if aria:
            return f"按鈕：aria-label={aria}"
        return "按鈕：無文字、無 aria-label"

    if tag_name == "input":
        input_type = tag.get("type", "text")
        name = tag.get("name", "")
        placeholder = tag.get("placeholder", "")
        desc = f"input[type={input_type}]"
        if name:
            desc += f" name={name}"
        if placeholder:
            desc += f" placeholder={placeholder}"
        return desc

    return f"<{tag_name}>"


def describe_context(tag: Tag):
    if tag is None:
        return "未知區塊"

    parent = tag.parent if hasattr(tag, "parent") else None
    while parent and getattr(parent, "name", None) not in {
        "section", "article", "main", "header", "footer", "nav", "div", "form"
    }:
        parent = parent.parent if hasattr(parent, "parent") else None

    if parent:
        text = safe_text(parent.get_text(" ", strip=True), 50)
        if text:
            return text

        parent_id = parent.get("id", "") if hasattr(parent, "get") else ""
        parent_class = " ".join(parent.get("class", [])) if hasattr(parent, "get") and parent.get("class") else ""

        if parent_id:
            return f"區塊 id={parent_id}"
        if parent_class:
            return f"區塊 class={parent_class}"

    return "頁面區塊"