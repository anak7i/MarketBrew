#!/usr/bin/env python3
"""
测试多种快速数据源
"""

import pandas as pd
import requests
import json
from datetime import datetime, timedelta

def test_tushare():
    """测试Tushare数据源"""
    try:
        import tushare as ts
        # 免费版本可以获取基础数据
        df = ts.get_stock_basics()
        print(f"✅ Tushare可用: {len(df)} 只股票")
        return True
    except:
        print("❌ Tushare不可用")
        return False

def test_yfinance():
    """测试Yahoo Finance"""
    try:
        import yfinance as yf
        # 测试获取中国股票
        ticker = yf.Ticker("000001.SZ")
        hist = ticker.history(period="5d")
        if not hist.empty:
            print(f"✅ Yahoo Finance可用")
            return True
    except:
        pass
    print("❌ Yahoo Finance不可用")
    return False

def test_free_apis():
    """测试免费API"""
    apis = [
        "新浪财经API",
        "腾讯财经API", 
        "网易财经API",
        "百度股市通API"
    ]
    
    # 测试新浪财经接口
    try:
        url = "http://hq.sinajs.cn/list=sz000001"
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and len(response.text) > 50:
            print("✅ 新浪财经API可用")
            return "sina"
    except:
        pass
    
    # 测试腾讯财经
    try:
        url = "http://qt.gtimg.cn/q=sz000001"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print("✅ 腾讯财经API可用")
            return "qq"
    except:
        pass
    
    print("❌ 免费API均不可用")
    return None

def test_local_generation():
    """测试本地数据生成"""
    print("💡 本地数据生成方案:")
    print("   - 基于现有143只股票数据")
    print("   - 使用统计模型生成相似股票数据")
    print("   - 保持数据的真实性和相关性")
    return True

if __name__ == "__main__":
    print("🔍 测试快速数据源...")
    print("=" * 40)
    
    test_tushare()
    test_yfinance() 
    test_free_apis()
    test_local_generation()
    
    print("\n💡 推荐方案:")
    print("1. 使用现有143只股票数据立即开始")
    print("2. 尝试安装tushare获取更多数据")
    print("3. 使用免费API补充数据")
    print("4. 本地生成相似股票数据")