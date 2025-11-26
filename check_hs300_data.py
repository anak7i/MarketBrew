#!/usr/bin/env python3
"""
沪深300指数数据排查工具
获取最新价格、MA20、MA30数据
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def get_hs300_data():
    """获取沪深300指数数据"""
    try:
        print("🔍 正在获取沪深300指数数据...")
        
        # 获取最近60天的数据以计算MA30
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=80)).strftime('%Y%m%d')
        
        # 获取沪深300指数历史数据
        hs300_data = ak.index_zh_a_hist(symbol="000300", period="daily", start_date=start_date, end_date=end_date)
        
        if hs300_data.empty:
            print("❌ 无法获取沪深300数据")
            return None
            
        # 确保数据按日期排序
        hs300_data = hs300_data.sort_values('日期')
        
        # 计算移动平均线
        hs300_data['MA5'] = hs300_data['收盘'].rolling(window=5).mean()
        hs300_data['MA10'] = hs300_data['收盘'].rolling(window=10).mean()
        hs300_data['MA20'] = hs300_data['收盘'].rolling(window=20).mean()
        hs300_data['MA30'] = hs300_data['收盘'].rolling(window=30).mean()
        
        return hs300_data
        
    except Exception as e:
        print(f"❌ 获取数据失败: {e}")
        return None

def analyze_hs300_data(data):
    """分析沪深300数据"""
    if data is None or data.empty:
        return
    
    # 获取最新数据
    latest = data.iloc[-1]
    prev_day = data.iloc[-2] if len(data) >= 2 else None
    
    print("\n" + "="*60)
    print("📊 沪深300指数数据分析报告")
    print("="*60)
    
    # 基本信息
    print(f"📅 最新交易日期: {latest['日期']}")
    print(f"💰 最新收盘价: {latest['收盘']:.2f}")
    print(f"📈 开盘价: {latest['开盘']:.2f}")
    print(f"📊 最高价: {latest['最高']:.2f}")
    print(f"📉 最低价: {latest['最低']:.2f}")
    print(f"📦 成交量: {latest['成交量']:,.0f}")
    print(f"💵 成交额: {latest['成交额']:,.0f}")
    
    # 涨跌情况
    if prev_day is not None:
        change = latest['收盘'] - prev_day['收盘']
        change_pct = (change / prev_day['收盘']) * 100
        print(f"📊 日涨跌: {change:+.2f} ({change_pct:+.2f}%)")
    
    print("\n" + "-"*40)
    print("📈 移动平均线数据")
    print("-"*40)
    
    # 移动平均线
    print(f"📏 MA5:  {latest['MA5']:.2f}" if not pd.isna(latest['MA5']) else "📏 MA5:  数据不足")
    print(f"📏 MA10: {latest['MA10']:.2f}" if not pd.isna(latest['MA10']) else "📏 MA10: 数据不足")
    print(f"📏 MA20: {latest['MA20']:.2f}" if not pd.isna(latest['MA20']) else "📏 MA20: 数据不足")
    print(f"📏 MA30: {latest['MA30']:.2f}" if not pd.isna(latest['MA30']) else "📏 MA30: 数据不足")
    
    # 技术分析
    print("\n" + "-"*40)
    print("🔍 技术分析")
    print("-"*40)
    
    current_price = latest['收盘']
    
    if not pd.isna(latest['MA20']):
        ma20_diff = current_price - latest['MA20']
        ma20_pct = (ma20_diff / latest['MA20']) * 100
        ma20_status = "上方 📈" if ma20_diff > 0 else "下方 📉"
        print(f"🎯 相对MA20: {ma20_status} {abs(ma20_diff):.2f}点 ({ma20_pct:+.2f}%)")
    
    if not pd.isna(latest['MA30']):
        ma30_diff = current_price - latest['MA30']
        ma30_pct = (ma30_diff / latest['MA30']) * 100
        ma30_status = "上方 📈" if ma30_diff > 0 else "下方 📉"
        print(f"🎯 相对MA30: {ma30_status} {abs(ma30_diff):.2f}点 ({ma30_pct:+.2f}%)")
    
    # 均线排列
    print("\n💡 均线排列分析:")
    if not any(pd.isna([latest['MA5'], latest['MA10'], latest['MA20'], latest['MA30']])):
        ma_values = [latest['MA5'], latest['MA10'], latest['MA20'], latest['MA30']]
        ma_names = ['MA5', 'MA10', 'MA20', 'MA30']
        
        if ma_values == sorted(ma_values, reverse=True):
            print("✅ 多头排列 (MA5 > MA10 > MA20 > MA30)")
        elif ma_values == sorted(ma_values):
            print("❌ 空头排列 (MA5 < MA10 < MA20 < MA30)")
        else:
            print("⚠️  均线纠缠，方向不明")
    
    # 最近几日数据
    print("\n" + "-"*40)
    print("📋 最近5个交易日数据")
    print("-"*40)
    
    recent_data = data.tail(5)[['日期', '收盘', 'MA20', 'MA30']].copy()
    recent_data['收盘'] = recent_data['收盘'].round(2)
    recent_data['MA20'] = recent_data['MA20'].round(2)
    recent_data['MA30'] = recent_data['MA30'].round(2)
    
    print(recent_data.to_string(index=False))

def main():
    """主函数"""
    print("🚀 启动沪深300数据排查...")
    
    # 获取数据
    data = get_hs300_data()
    
    if data is not None:
        # 分析数据
        analyze_hs300_data(data)
        print(f"\n✅ 数据排查完成！共获取 {len(data)} 条记录")
    else:
        print("❌ 数据获取失败，请检查网络连接或稍后重试")

if __name__ == "__main__":
    main()