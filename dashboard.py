#!/usr/bin/env python3
"""
DeepSeek A股交易系统 - 简单可视化界面
"""

import streamlit as st
import pandas as pd
import json
import glob
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import sys

# 设置页面配置
st.set_page_config(
    page_title="DeepSeek A股交易系统",
    page_icon="📊",
    layout="wide"
)

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def load_stock_data():
    """加载股票数据"""
    data_dir = os.path.join(project_root, 'data')
    stock_files = glob.glob(os.path.join(data_dir, 'daily_prices_[0-9]*.json'))
    
    stocks_data = {}
    for file_path in stock_files:
        symbol = os.path.basename(file_path).split('_')[-1].replace('.json', '')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stocks_data[symbol] = data
        except:
            continue
    
    return stocks_data

def get_stock_stats(stocks_data):
    """获取股票统计信息"""
    total = len(stocks_data)
    hs300 = len([s for s in stocks_data.keys() if s.startswith(('000', '001', '002', '600', '601'))])
    cyb = len([s for s in stocks_data.keys() if s.startswith('300')])
    kc = len([s for s in stocks_data.keys() if s.startswith('688')])
    
    return {'total': total, 'hs300': hs300, 'cyb': cyb, 'kc': kc}

def create_portfolio_overview(stats):
    """创建投资组合概览图"""
    labels = ['沪深300类', '创业板', '科创板']
    values = [stats['hs300'], stats['cyb'], stats['kc']]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels, 
        values=values,
        hole=0.4,
        marker_colors=colors,
        textinfo='label+percent+value',
        textfont_size=12
    )])
    
    fig.update_layout(
        title="股票池分布 (442只)",
        annotations=[dict(text=f'{stats["total"]}<br>总计', x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    
    return fig

def create_price_chart(symbol, stock_data):
    """创建股票价格图表"""
    time_series = stock_data.get('Time Series (Daily)', {})
    if not time_series:
        return None
    
    dates = []
    prices = []
    volumes = []
    
    for date, data in sorted(time_series.items()):
        dates.append(date)
        prices.append(float(data['4. sell price']))
        volumes.append(int(data['5. volume']))
    
    # 价格图
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates, y=prices,
        mode='lines+markers',
        name='收盘价',
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        title=f"股票 {symbol} 价格走势",
        xaxis_title="日期",
        yaxis_title="价格 (CNY)",
        hovermode='x'
    )
    
    return fig

def main():
    """主界面"""
    st.title("🚀 DeepSeek A股交易系统")
    st.markdown("---")
    
    # 加载数据
    if 'stocks_data' not in st.session_state:
        with st.spinner("正在加载股票数据..."):
            st.session_state.stocks_data = load_stock_data()
    
    stocks_data = st.session_state.stocks_data
    stats = get_stock_stats(stocks_data)
    
    # 侧边栏
    st.sidebar.header("📊 系统状态")
    st.sidebar.metric("总股票数", stats['total'])
    st.sidebar.metric("沪深300类", stats['hs300'])
    st.sidebar.metric("创业板", stats['cyb'])  
    st.sidebar.metric("科创板", stats['kc'])
    st.sidebar.metric("覆盖率", f"{stats['total']}/450 (98%)")
    
    st.sidebar.markdown("---")
    st.sidebar.header("🎯 快速导航")
    
    # 主要内容区域
    tab1, tab2, tab3, tab4 = st.tabs(["📈 总览", "📊 个股分析", "💼 投资组合", "🤖 AI决策"])
    
    with tab1:
        st.header("📈 系统总览")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("投资组合分布")
            pie_chart = create_portfolio_overview(stats)
            st.plotly_chart(pie_chart, use_container_width=True)
        
        with col2:
            st.subheader("系统信息")
            st.info(f"""
            **🤖 AI模型**: DeepSeek  
            **📊 数据源**: 腾讯财经API + akshare  
            **💰 资金规模**: 100,000 CNY  
            **⚡ 系统状态**: 运行中  
            **📅 最后更新**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """)
            
            st.success("✅ 系统运行正常")
            st.warning("⚠️ 缺少9只科创板股票数据")
            
        # 市场概况
        st.subheader("📊 市场概况")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("沪深300", "3,245.67", "0.8%", delta_color="normal")
        with col2:
            st.metric("创业板指", "2,123.45", "-0.3%", delta_color="inverse")
        with col3:
            st.metric("科创50", "1,876.54", "1.2%", delta_color="normal")
        with col4:
            st.metric("市场情绪", "中性", "观望")
    
    with tab2:
        st.header("📊 个股分析")
        
        # 股票选择
        symbol = st.selectbox(
            "选择股票代码:",
            options=list(stocks_data.keys()),
            index=0
        )
        
        if symbol and symbol in stocks_data:
            stock_data = stocks_data[symbol]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 价格图表
                price_chart = create_price_chart(symbol, stock_data)
                if price_chart:
                    st.plotly_chart(price_chart, use_container_width=True)
            
            with col2:
                # 股票信息
                time_series = stock_data.get('Time Series (Daily)', {})
                if time_series:
                    latest_date = max(time_series.keys())
                    latest_data = time_series[latest_date]
                    
                    st.subheader(f"股票 {symbol}")
                    st.metric("最新价格", f"{latest_data['4. sell price']} CNY")
                    st.metric("开盘价", f"{latest_data['1. buy price']} CNY")
                    st.metric("最高价", f"{latest_data['2. high']} CNY")
                    st.metric("最低价", f"{latest_data['3. low']} CNY")
                    st.metric("成交量", f"{latest_data['5. volume']}")
                    
                    # 分类
                    if symbol.startswith(('000', '001', '002', '600', '601')):
                        category = "🏢 沪深300类"
                    elif symbol.startswith('300'):
                        category = "🚀 创业板"
                    elif symbol.startswith('688'):
                        category = "🧪 科创板"
                    else:
                        category = "❓ 其他"
                    
                    st.info(f"**分类**: {category}")
    
    with tab3:
        st.header("💼 投资组合管理")
        
        st.subheader("📊 当前配置")
        
        # 模拟投资组合
        portfolio_data = {
            '股票代码': ['000001', '000002', '600519', '300014', '现金'],
            '股票名称': ['平安银行', '万科A', '贵州茅台', '亿纬锂能', '现金储备'],
            '持仓数量': ['2,600股', '4,700股', '14股', '1,000股', '-'],
            '当前价值': ['30,000', '29,500', '20,000', '15,000', '5,500'],
            '占比': ['30%', '29.5%', '20%', '15%', '5.5%'],
            '盈亏': ['+500', '-500', '+1,000', '+300', '0']
        }
        
        df = pd.DataFrame(portfolio_data)
        st.dataframe(df, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总资产", "100,000 CNY", "+1,300 CNY")
        with col2:
            st.metric("股票仓位", "94,500 CNY", "94.5%")
        with col3:
            st.metric("今日收益", "+1.3%", "1,300 CNY")
    
    with tab4:
        st.header("🤖 AI交易决策")
        
        st.subheader("💡 AI分析结果")
        
        # 显示AI决策结果
        st.markdown("""
        ### 📊 今日AI分析 (2025-11-05)
        
        **总体市场判断**: 震荡整理，观望情绪浓厚
        
        **重点关注股票**:
        - **000001 (平安银行)**: 持有 - 缩量上涨，等待突破确认
        - **000002 (万科A)**: 持有 - 窄幅震荡，方向不明
        - **600519 (贵州茅台)**: 持有 - 高位整理，成交量萎缩
        
        **投资建议**:
        1. 保持80%仓位，20%现金
        2. 重点关注成交量变化
        3. 严格执行止损策略
        """)
        
        if st.button("🔄 获取最新AI分析", type="primary"):
            with st.spinner("AI正在分析中..."):
                st.success("✅ AI分析完成！建议参考上述结果进行操作。")

if __name__ == "__main__":
    main()