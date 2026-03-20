from bs4 import Tag


def build_status_text(status):
    status_map = {
        True: "✅ 通過",
        False: "❌ 待修復",
        None: "⏭ 未執行",
    }
    return status_map.get(status, "⏭ 未執行")


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


def describe_element(tag: Tag):
    if tag is None:
        return "未知元素"

    tag_name = tag.name or "未知標籤"
    text = safe_text(tag.get_text(" ", strip=True))
    element_id = tag.get("id", "")
    classes = " ".join(tag.get("class", [])) if tag.get("class") else ""

    if tag_name == "img":
        src = tag.get("src", "") or tag.get("data-src", "") or "未知圖片"
        alt = tag.get("alt", "")
        return f"圖片：{src}；alt={'有值' if alt.strip() else '缺少'}"

    if tag_name == "a":
        href = tag.get("href", "") or "無 href"
        if text:
            return f"連結：{text}（{href}）"
        return f"連結：{href}（無可讀文字）"

    if tag_name == "button":
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

    desc = f"<{tag_name}>"
    if text:
        desc += f" 內容：{text}"
    if element_id:
        desc += f" id={element_id}"
    if classes:
        desc += f" class={classes}"
    return desc


def describe_context(tag: Tag):
    if tag is None:
        return "未知區塊"

    parent = tag.parent if hasattr(tag, "parent") else None
    while parent and getattr(parent, "name", None) not in {"section", "article", "main", "header", "footer", "nav", "div", "form"}:
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

    return "頁面區塊未命名"