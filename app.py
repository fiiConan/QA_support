import streamlit as st
import asyncio
from auditor_logic import FiisualAuditor
import pandas as pd
import os

# 檢查是否在 Streamlit Cloud 環境中 (這段建議放在 app.py 最上方)
if not os.path.exists("/home/adminuser/.cache/ms-playwright"):
    os.system("playwright install chromium")
st.set_page_config(page_title="Fiisual QA Support", layout="wide")
st.title("🎯 Fiisual 網頁品質自動化檢測")

url = st.text_input("請輸入網址 (URL):", placeholder="https://tw.fiisual.com/blog")

if st.button("執行檢測"):
    if not url.startswith("http"):
        st.error("請輸入完整的網址 (包含 http:// 或 https://)")
    else:
        auditor = FiisualAuditor(url)
        with st.spinner("正在執行跨裝置檢測與 SEO 審計..."):
            # 執行非同步邏輯
            report_data = asyncio.run(auditor.run_full_audit())
            
            # 顯示結果
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("📋 檢測報告")
                df = pd.DataFrame(report_data)
                # 根據狀態給顏色
                st.dataframe(df.style.applymap(lambda x: 'color: red' if x == '❌ 待修復' else '', subset=['狀態']), use_container_width=True)
            
            with col2:
                st.subheader("📱 手機版畫面")
                st.image(auditor.screenshot_path)