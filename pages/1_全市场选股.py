"""全市场选股 — Streamlit 页面."""

import streamlit as st
import akshare as ak
import pandas as pd
import time

st.set_page_config(page_title="全市场选股器", layout="wide")
st.title("📊 全市场选股器")
st.write("拖动左侧滑块设置筛选条件，点击下方按钮开始选股。")

st.sidebar.header("筛选条件")
min_amount = st.sidebar.slider("最小成交额（亿）", 0.5, 20.0, 5.0)
min_change = st.sidebar.slider("最小涨幅（%）", -10.0, 10.0, 2.0)
max_change = st.sidebar.slider("最大涨幅（%）", -10.0, 10.0, 9.8)
min_turnover = st.sidebar.slider("最小换手率（%）", 0.0, 20.0, 2.0)
max_turnover = st.sidebar.slider("最大换手率（%）", 0.0, 50.0, 20.0)


def fetch_data(max_retries=3):
    """获取数据，带自动重试和备用源"""
    for attempt in range(1, max_retries + 1):
        try:
            return ak.stock_zh_a_spot_em()
        except Exception:
            if attempt == max_retries:
                st.warning("东财接口超时，正在切换到新浪备用数据源...")
                return ak.stock_zh_a_spot()
            time.sleep(5)
    return None


if st.button("🚀 开始全市场筛选"):
    with st.spinner("正在获取全市场数据，请稍候（可能需要10-30秒）..."):
        try:
            df = fetch_data()
            if df is None:
                st.error("无法获取数据，请稍后再试。")
            else:
                df["成交额"] = pd.to_numeric(df["成交额"], errors="coerce")
                df["涨跌幅"] = pd.to_numeric(df["涨跌幅"], errors="coerce")
                df["换手率"] = pd.to_numeric(df["换手率"], errors="coerce")

                selected = df[
                    (df["成交额"] > min_amount * 1e8)
                    & (df["涨跌幅"] > min_change)
                    & (df["涨跌幅"] < max_change)
                    & (df["换手率"] > min_turnover)
                    & (df["换手率"] < max_turnover)
                ].copy()

                if "名称" in selected.columns:
                    selected = selected[~selected["名称"].str.contains("ST|退", na=False)]
                if "成交额" in selected.columns:
                    selected = selected.sort_values("成交额", ascending=False)

                st.success(f"筛选完成，共选出 {len(selected)} 只股票")
                st.dataframe(selected, use_container_width=True)

                csv = selected.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "📥 下载候选股票列表 (CSV)",
                    data=csv,
                    file_name="candidates_detail.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"获取或筛选数据失败：{e}")
            st.info("建议：稍等片刻后重试；或者检查网络代理设置。")