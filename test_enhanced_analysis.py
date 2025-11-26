#!/usr/bin/env python3
"""
测试增强的DeepSeek分析功能
"""

import requests
import json
import time

def test_stock_analysis():
    """测试个股AI分析"""
    print("🧪 测试增强的个股AI分析...")
    
    test_data = {
        "stocks": [
            {
                "symbol": "000001",
                "name": "平安银行",
                "current_price": 11.55,
                "change_percent": 0.35,
                "volume": 734851,
                "market_status": "closed"
            }
        ]
    }
    
    try:
        response = requests.post(
            "http://localhost:5001/api/langchain/stock-analysis",
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API调用成功!")
            print(f"📊 分析结果长度: {len(result['results'][0]['analysis'])} 字符")
            
            analysis = result['results'][0]['analysis']
            print("\n📈 分析内容预览:")
            print("=" * 60)
            print(analysis[:500] + "..." if len(analysis) > 500 else analysis)
            print("=" * 60)
            
            # 检查是否包含详细分析要素
            key_elements = [
                "综合评分", "投资建议", "目标价格", "基本面分析", 
                "技术面分析", "估值分析", "风险提示"
            ]
            
            found_elements = [elem for elem in key_elements if elem in analysis]
            print(f"\n📋 包含的关键要素 ({len(found_elements)}/{len(key_elements)}):")
            for elem in found_elements:
                print(f"  ✅ {elem}")
            
            missing_elements = [elem for elem in key_elements if elem not in analysis]
            if missing_elements:
                print("❌ 缺失的要素:")
                for elem in missing_elements:
                    print(f"  ❌ {elem}")
            
            return True
            
        else:
            print(f"❌ API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_market_analysis():
    """测试市场分析"""
    print("\n🧪 测试增强的市场AI分析...")
    
    test_data = {
        "market_status": "closed",
        "stocks": [
            {"symbol": "000001", "name": "平安银行"},
            {"symbol": "600519", "name": "贵州茅台"},
            {"symbol": "000858", "name": "五粮液"}
        ],
        "market_trend": "震荡",
        "liquidity": "适中",
        "policy_news": "政策面相对平稳"
    }
    
    try:
        response = requests.post(
            "http://localhost:5001/api/langchain/market-analysis",
            json=test_data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 市场分析API调用成功!")
            
            analysis = result.get('market_analysis', '')
            print(f"📊 分析结果长度: {len(analysis)} 字符")
            print("\n📈 市场分析预览:")
            print("=" * 60)
            print(analysis[:400] + "..." if len(analysis) > 400 else analysis)
            print("=" * 60)
            
            return True
            
        else:
            print(f"❌ 市场分析API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 市场分析请求异常: {e}")
        return False

def test_price_service():
    """测试价格服务"""
    print("\n🧪 测试价格服务...")
    
    try:
        # 测试单只股票
        response = requests.get("http://localhost:5002/api/stock/000001", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 价格服务正常: {data['symbol']} {data['name']} ¥{data['current_price']}")
            return True
        else:
            print(f"❌ 价格服务异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 价格服务连接失败: {e}")
        return False

def main():
    print("🚀 MarketBrew 增强分析系统测试")
    print("=" * 60)
    
    # 检查服务状态
    services_ok = True
    
    # 测试价格服务
    if not test_price_service():
        services_ok = False
        print("⚠️  请先启动价格服务: python3 price_service.py")
    
    # 测试个股分析
    if not test_stock_analysis():
        services_ok = False
        print("⚠️  个股AI分析服务异常")
    
    # 测试市场分析
    if not test_market_analysis():
        services_ok = False
        print("⚠️  市场AI分析服务异常")
    
    print("\n" + "=" * 60)
    if services_ok:
        print("🎉 所有测试通过! 增强分析系统工作正常")
        print("📱 现在可以在前端页面生成详细的AI分析报告")
    else:
        print("⚠️  部分服务异常，请检查服务状态")
        print("💡 即使AI服务异常，系统也会降级到传统分析")

if __name__ == "__main__":
    main()