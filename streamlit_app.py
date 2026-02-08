import streamlit as st
import pandas as pd
import requests
import json

# 设置页面
st.set_page_config(page_title="我的基金看板", layout="wide")

# 初始化数据：如果不存在则尝试从浏览器环境恢复（Streamlit原生支持有限，这里强化逻辑）
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

# --- 侧边栏 ---
st.sidebar.header("🔍 基金管理")
search_code = st.sidebar.text_input("输入基金代码")

if search_code:
    data = get_fund_info(search_code)
    if data:
        st.sidebar.write(f"基金名称: {data['name']}")
        price = st.sidebar.number_input("买入单价", value=1.0, format="%.4f")
        money = st.sidebar.number_input("买入金额", value=100.0)
        if st.sidebar.button("确认添加记录"):
            st.session_state.portfolio.append({
                "名称": data['name'], 
                "投入金额": money, 
                "买入单价": price, 
                "当前净值": float(data['gsz'])
            })
            st.sidebar.success("添加成功！注意：刷新页面前请先看下方备份说明")

# --- 主界面 ---
st.title("📈 基金实时跟踪分析")

if st.session_state.portfolio:
    df = pd.DataFrame(st.session_state.portfolio)
    df['当前市值'] = (df['投入金额'] / df['买入单价']) * df['当前净值']
    df['盈亏'] = df['当前市值'] - df['投入金额']
    
    # 核心指标
    c1, c2 = st.columns(2)
    c1.metric("总资产", f"{df['当前市值'].sum():.2f}")
    c2.metric("总盈亏", f"{df['盈亏'].sum():.2f}")

    st.dataframe(df, use_container_width=True)
    
    # --- 增加备份功能：防止数据丢失 ---
    st.divider()
    st.subheader("💾 数据备份 (重要)")
    st.write("由于云端不保存个人数据，建议每次添加后点击下方按钮下载备份：")
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("下载数据备份 (CSV文件)", data=csv, file_name="my_funds.csv", mime='text/csv')
    
    # 增加上传功能：下次进来可以恢复
    uploaded_file = st.file_uploader("📂 上传之前的备份以恢复数据", type="csv")
    if uploaded_file is not None:
        st.session_state.portfolio = pd.read_csv(uploaded_file).to_dict('records')
        st.rerun()

    if st.button("🔥 清空所有数据"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("目前没有记录。请从左侧添加，或上传备份文件。")
