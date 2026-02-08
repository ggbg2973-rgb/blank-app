import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime

# 设置页面配置
st.set_page_config(page_title="我的基金跟踪器", layout="wide")

# --- 模拟数据库 (实际应用中可保存到 CSV 或 Database) ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# --- 辅助函数：获取基金实时数据 ---
def get_fund_info(code):
    try:
        # 使用天天基金的公开 API 接口
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        r = requests.get(url, timeout=5)
        # 格式化返回的 JSONP 数据
        content = r.text
        json_str = content[content.find('{'):content.rfind('}')+1]
        return json.loads(json_str)
    except:
        return None

# --- 侧边栏：搜索与添加 ---
st.sidebar.header("🔍 添加新交易记录")
search_code = st.sidebar.text_input("输入基金代码 (如: 000001)")

if search_code:
    data = get_fund_info(search_code)
    if data:
        st.sidebar.success(f"已找到: {data['name']}")
        buy_date = st.sidebar.date_input("买入日期")
        buy_price = st.sidebar.number_input("买入单位净值", min_value=0.01, step=0.0001)
        buy_amount = st.sidebar.number_input("买入金额 (元)", min_value=1.0, step=100.0)
        
        if st.sidebar.button("添加到记录"):
            new_record = {
                "代码": search_code,
                "名称": data['name'],
                "买入时间": buy_date.strftime("%Y-%m-%d"),
                "买入单价": buy_price,
                "投入金额": buy_amount,
                "当前净值": float(data['gsz']),
                "涨跌幅": data['gszzl'] + "%"
            }
            st.session_state.portfolio.append(new_record)
            st.toast("添加成功！")
    else:
        st.sidebar.error("未找到基金信息，请检查代码。")

# --- 主界面 ---
st.title("📈 个人基金实时跟踪分析")

if not st.session_state.portfolio:
    st.info("目前还没有记录，请在左侧搜索并添加你的第一笔基金买入记录吧！")
else:
    df = pd.DataFrame(st.session_state.portfolio)
    
    # 计算核心逻辑
    df['当前份额'] = df['投入金额'] / df['买入单价']
    df['当前市值'] = df['当前份额'] * df['当前净值']
    df['盈亏额'] = df['当前市值'] - df['投入金额']
    df['收益率'] = (df['盈亏额'] / df['投入金额']) * 100

    # --- 数据概览卡片 ---
    total_invest = df['投入金额'].sum()
    total_value = df['当前市值'].sum()
    total_profit = total_value - total_invest
    
    col1, col2, col3 = st.columns(3)
    col1.metric("总资产 (元)", f"{total_value:.2f}")
    col2.metric("总投入 (元)", f"{total_invest:.2f}")
    col3.metric("总盈亏 (元)", f"{total_profit:.2f}", f"{(total_profit/total_invest*100):.2f}%")

    # --- 资产占比与明细 ---
    st.subheader("📊 持仓明细与占比分析")
    
    tab1, tab2 = st.tabs(["持仓表格", "分布图表"])
    
    with tab1:
        st.dataframe(df[['代码', '名称', '买入时间', '投入金额', '当前市值', '盈亏额', '收益率']], use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            st.write("基金市值占比")
            st.pie_chart(data=df, values='当前市值', names='名称')
        with c2:
            st.write("基金盈亏对比")
            st.bar_chart(data=df, x='名称', y='盈亏额')

    if st.button("清空所有记录"):
        st.session_state.portfolio = []
        st.rerun()
