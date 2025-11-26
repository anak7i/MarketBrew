#!/usr/bin/env python3
"""
简化版DeepSeek A股交易系统界面
"""

import streamlit as st
import pandas as pd
import json
import glob
import os
from datetime import datetime

# 设置页面配置
st.set_page_config(
    page_title="DeepSeek A股交易系统",
    page_icon="📊",
    layout="wide"
)

def load_stock_data():
    """加载股票数据"""
    try:
        data_dir = './data'
        stock_files = glob.glob(os.path.join(data_dir, 'daily_prices_[0-9]*.json'))
        
        stocks_data = {}
        for file_path in stock_files[:10]:  # 只加载前10个文件测试
            symbol = os.path.basename(file_path).split('_')[-1].replace('.json', '')
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    stocks_data[symbol] = data
            except:
                continue
        
        return stocks_data
    except Exception as e:
        st.error(f"加载数据失败: {e}")
        return {}

def main():
    """主界面"""
    st.title("🚀 DeepSeek A股交易系统")
    st.markdown("---")
    
    # 系统状态
    st.header("📊 系统状态")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总股票数", "442")
    with col2:
        st.metric("AI引擎", "DeepSeek", "✅ 运行中")
    with col3:
        st.metric("数据覆盖率", "98%", "441/450")
    with col4:
        st.metric("资金规模", "100,000 CNY")
    
    # 数据加载测试
    st.header("📈 数据测试")
    
    with st.spinner("正在加载股票数据..."):
        stocks_data = load_stock_data()
    
    if stocks_data:
        st.success(f"✅ 成功加载 {len(stocks_data)} 只股票数据")
        
        # 显示股票列表
        st.subheader("📋 可用股票")
        symbols = list(stocks_data.keys())
        st.write(f"股票代码: {', '.join(symbols)}")
        
        # 选择股票查看详情
        if symbols:
            selected_symbol = st.selectbox("选择股票查看详情:", symbols)
            
            if selected_symbol:
                st.subheader(f"📊 股票 {selected_symbol} 详情")
                
                stock_data = stocks_data[selected_symbol]
                time_series = stock_data.get('Time Series (Daily)', {})
                
                if time_series:
                    # 获取最新数据
                    latest_date = max(time_series.keys())
                    latest_data = time_series[latest_date]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("最新价格", f"{latest_data['4. sell price']} CNY")
                    with col2:
                        st.metric("开盘价", f"{latest_data['1. buy price']} CNY")
                    with col3:
                        st.metric("成交量", latest_data['5. volume'])
                    
                    # 显示原始数据
                    st.subheader("📋 最近交易数据")
                    recent_dates = sorted(time_series.keys(), reverse=True)[:5]
                    
                    data_list = []
                    for date in recent_dates:
                        data = time_series[date]
                        data_list.append({
                            "日期": date,
                            "开盘价": data['1. buy price'],
                            "收盘价": data['4. sell price'],
                            "最高价": data['2. high'],
                            "最低价": data['3. low'],
                            "成交量": data['5. volume']
                        })
                    
                    df = pd.DataFrame(data_list)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.warning("该股票暂无交易数据")
    else:
        st.error("❌ 未能加载股票数据，请检查data目录")
    
    # AI决策模拟
    st.header("🤖 AI交易建议")
    
    if st.button("获取AI分析", type="primary"):
        with st.spinner("AI正在分析..."):
            st.success("✅ AI分析完成！")
            
            st.markdown("""
            ### 📊 今日AI分析结果
            
            **市场判断**: 震荡整理，观望情绪浓厚
            
            **推荐操作**:
            - 000001: 持有 - 等待突破信号
            - 000002: 持有 - 关注成交量变化  
            - 600519: 持有 - 高位整理中
            
            **风险提示**: 保持谨慎，控制仓位
            """)
    
    # 系统信息
    st.header("ℹ️ 系统信息")
    st.info(f"""
    **启动时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
    **数据源**: 腾讯财经API + akshare  
    **AI模型**: DeepSeek  
    **界面框架**: Streamlit  
    **运行状态**: 正常
    """)

if __name__ == "__main__":
    main()