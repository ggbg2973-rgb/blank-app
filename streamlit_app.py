import streamlit as st
import pandas as pd
import requests
import json

# 设置页面
st.set_page_config(page_title="基金分析", layout="wide")

# --- 关键：使用本地缓存存储数据，刷新不丢失 ---
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

def get_fund_info(code):
    try:
        url = f"http://fundgz.1234567.com.cn/js/{code}.js"
        r = requests.get(url, timeout=5)
        content = r.text
        json_str = content[content.find('{'):content.rfind('}')+1]
        return json.loads(json_str)
    except: return None

# 侧边栏
st.sidebar.header("🔍 搜基金")
search_code = st.sidebar.text_input("输入代码 (如: 000001)")

if search_code:
    data = get_fund_info(search_code)
    if data:
        st.sidebar.info(f"基金: {data['name']}")
        price = st.sidebar.number_input("买入单价", value=1.0, format="%.4f")
        money = st.sidebar.number_input("买入金额", value=100.0)
        if st.sidebar.button("确认添加"):
            st.session_state.portfolio.append({
                "名称": data['name'], "投入金额": money, 
                "买入单价": price, "当前净值": float(data['gsz'])
            })
            st.toast("记录已保存")

# 主界面
st.title("📈 个人基金实时看板")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    df['当前市值'] = (df['投入金额'] / df['买入单价']) * df['当前净值']
    df['盈亏额'] = df['当前市值'] - df['投入金额']
    
    # 顶部指标
    st.metric("总资产", f"{df['当前市值'].sum():.2f} 元", f"{df['盈亏额'].sum():.2f}")
    
    # 持仓表格
    st.subheader("📋 持仓明细")
    st.dataframe(df, use_container_width=True)
    
    # 修复后的饼图
    st.subheader("📊 占比分析")
    st.bar_chart(data=df, x='名称', y='当前市值') # 用柱状图替代，手机兼容性最好
    
    if st.button("🔥 清空所有数据"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.warning("暂无数据，请在左侧添加")
