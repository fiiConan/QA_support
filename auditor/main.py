import streamlit as st
import asyncio
import os
import json
from core import FiisualAuditor

st.set_page_config(page_title="Fiisual Auditor", layout="wide")

st.title("Fiisual Website Auditor")

url = st.text_input("輸入網站 URL", placeholder="https://example.com")

run_btn = st.button("開始檢查")

if run_btn and url:
    st.info("檢查進行中，請稍候...")

    auditor = FiisualAuditor(url=url)

    with st.spinner("Running audit..."):
        report = asyncio.run(auditor.run_full_audit())
        report_path = auditor.save_report()

    st.success("稽核完成！")

    # ===== 結果表格 =====
    st.subheader("檢測結果")
    st.dataframe(report, use_container_width=True)

    # ===== 分類顯示 =====
    st.subheader("📂 分類檢視")
    grouped = {}
    for item in report:
        grouped.setdefault(item["區塊"], []).append(item)

    for block, items in grouped.items():
        with st.expander(block):
            for i in items:
                st.write(f"**{i['檢測項目']}** - {i['狀態']} ({i['嚴重程度']})")
                if i["備註"]:
                    st.caption(i["備註"])

    # ===== 截圖顯示 =====
    st.subheader("📸 Viewport Screenshots")

    if os.path.exists("outputs"):
        images = [f for f in os.listdir("outputs") if f.endswith(".png")]
        cols = st.columns(3)

        for i, img in enumerate(images):
            with cols[i % 3]:
                st.image(f"outputs/{img}", caption=img)

    # ===== JSON 下載 =====
    st.subheader("⬇️ 下載報告")

    with open(report_path, "r", encoding="utf-8") as f:
        st.download_button(
            label="下載 JSON 報告",
            data=f,
            file_name="audit_report.json",
            mime="application/json"
        )