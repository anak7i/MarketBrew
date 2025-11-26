#!/usr/bin/env python3
"""
测试 MarketBrew 价格服务
"""

import requests
import json
import time

def test_single_stock(symbol="000001"):
    """测试获取单只股票"""
    print(f"\n📊 测试获取单只股票：{symbol}")
    try:
        response = requests.get(f"http://localhost:5002/api/stock/{symbol}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取 {symbol} 数据:")
            print(f"   股票名称: {data.get('name', 'N/A')}")
            print(f"   当前价格: ¥{data.get('current_price', 0)}")
            print(f"   开盘价格: ¥{data.get('open', 0)}")
            print(f"   涨跌幅: {data.get('change_percent', 0):.2f}%")
            print(f"   成交量: {data.get('volume', 0):,}手")
            print(f"   市场状态: {data.get('market_status', 'unknown')}")
            return True
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_multiple_stocks():
    """测试批量获取股票"""
    symbols = ["000001", "600519", "000858", "300750"]
    print(f"\n📊 测试批量获取股票：{symbols}")
    
    try:
        response = requests.post(
            "http://localhost:5002/api/stocks",
            json={"symbols": symbols},
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取 {len(data)} 只股票数据:")
            for symbol, stock_data in data.items():
                if not stock_data.get('error'):
                    print(f"   {symbol} {stock_data.get('name', 'N/A')}: ¥{stock_data.get('current_price', 0)} ({stock_data.get('change_percent', 0):+.2f}%)")
                else:
                    print(f"   {symbol}: 获取失败 - {stock_data.get('error')}")
            return True
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_market_status():
    """测试市场状态"""
    print(f"\n📊 测试市场状态")
    try:
        response = requests.get("http://localhost:5002/api/market/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 市场状态: {data.get('status', 'unknown')}")
            print(f"   时间戳: {data.get('timestamp', 'N/A')}")
            return True
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_health_check():
    """测试健康检查"""
    print(f"\n📊 测试服务健康状态")
    try:
        response = requests.get("http://localhost:5002/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 服务状态: {data.get('status', 'unknown')}")
            print(f"   服务名称: {data.get('service', 'N/A')}")
            return True
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    print("🧪 MarketBrew 价格服务测试")
    print("=" * 50)
    
    # 检查服务是否运行
    print("\n🔍 检查服务连接...")
    try:
        response = requests.get("http://localhost:5002/health", timeout=3)
        if response.status_code != 200:
            print("❌ 服务未运行或无法连接")
            print("请先运行: python3 price_service.py")
            return
    except:
        print("❌ 无法连接到价格服务 (http://localhost:5002)")
        print("请先运行: python3 price_service.py")
        return
    
    print("✅ 服务连接正常")
    
    # 运行测试
    tests = [
        test_health_check,
        test_market_status,
        test_single_stock,
        test_multiple_stocks
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # 避免请求过快
    
    print("\n" + "=" * 50)
    print(f"🧪 测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！价格服务工作正常")
    else:
        print("⚠️  部分测试失败，请检查服务状态")

if __name__ == "__main__":
    main()