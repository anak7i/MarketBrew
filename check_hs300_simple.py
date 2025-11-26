#!/usr/bin/env python3
"""
沪深300指数数据排查工具 - 简化版
使用本地服务获取数据
"""

import requests
import json
import pandas as pd
from datetime import datetime
import yfinance as yf
import warnings
warnings.filterwarnings('ignore')

def get_hs300_from_yfinance():
    """使用yfinance获取沪深300数据"""
    try:
        print("🔍 正在通过yfinance获取沪深300指数数据...")
        
        # 沪深300指数代码
        ticker = "000300.SS"
        stock = yf.Ticker(ticker)
        
        # 获取历史数据（最近60天）
        hist = stock.history(period="60d")
        
        if hist.empty:
            return None
            
        # 计算移动平均线
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['MA30'] = hist['Close'].rolling(window=30).mean()
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA10'] = hist['Close'].rolling(window=10).mean()
        
        return hist
        
    except Exception as e:
        print(f"❌ yfinance获取失败: {e}")
        return None

def get_hs300_from_local_service():
    """尝试从本地服务获取数据"""
    try:
        print("🔍 正在从本地服务获取沪深300数据...")
        
        # 尝试连接本地实时价格服务
        url = "http://localhost:5002/price"
        params = {"symbol": "000300"}
        
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
            
    except Exception as e:
        print(f"❌ 本地服务获取失败: {e}")
        return None

def analyze_hs300_yf_data(data):
    """分析yfinance获取的沪深300数据"""
    if data is None or data.empty:
        return
    
    # 获取最新数据
    latest = data.iloc[-1]
    prev_day = data.iloc[-2] if len(data) >= 2 else None
    
    print("\n" + "="*60)
    print("📊 沪深300指数数据分析报告")
    print("="*60)
    
    # 基本信息
    print(f"📅 最新交易日期: {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"💰 最新收盘价: {latest['Close']:.2f}")
    print(f"📈 开盘价: {latest['Open']:.2f}")
    print(f"📊 最高价: {latest['High']:.2f}")
    print(f"📉 最低价: {latest['Low']:.2f}")
    print(f"📦 成交量: {latest['Volume']:,.0f}")
    
    # 涨跌情况
    if prev_day is not None:
        change = latest['Close'] - prev_day['Close']
        change_pct = (change / prev_day['Close']) * 100
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
    
    current_price = latest['Close']
    
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
    
    recent_data = data.tail(5)[['Close', 'MA20', 'MA30']].copy()
    recent_data.columns = ['收盘价', 'MA20', 'MA30']
    recent_data = recent_data.round(2)
    recent_data.index = recent_data.index.strftime('%Y-%m-%d')
    
    print(recent_data.to_string())

def main():
    """主函数"""
    print("🚀 启动沪深300数据排查...")
    
    # 首先尝试本地服务
    local_data = get_hs300_from_local_service()
    if local_data:
        print("✅ 从本地服务获取到数据")
        print(json.dumps(local_data, indent=2, ensure_ascii=False))
    
    # 使用yfinance获取数据
    data = get_hs300_from_yfinance()
    
    if data is not None:
        # 分析数据
        analyze_hs300_yf_data(data)
        print(f"\n✅ 数据排查完成！共获取 {len(data)} 条记录")
    else:
        print("❌ 数据获取失败，请检查网络连接或稍后重试")

if __name__ == "__main__":
    main()