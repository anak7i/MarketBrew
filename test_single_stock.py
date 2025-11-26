#!/usr/bin/env python3
"""
测试单只股票分析 - 检查数据读取是否正常
"""

from unified_decision_engine import UnifiedDecisionEngine
import json

def test_single_stock():
    engine = UnifiedDecisionEngine()
    
    # 测试000001平安银行
    print("🧪 测试股票数据读取...")
    
    try:
        # 直接读取数据文件查看结构
        with open('./data/daily_prices_000001.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        time_series = data.get('Time Series (Daily)', {})
        if time_series:
            latest_date = sorted(time_series.keys(), reverse=True)[0]
            latest_data = time_series[latest_date]
            
            print(f"📅 最新日期: {latest_date}")
            print(f"📊 数据字段: {list(latest_data.keys())}")
            
            # 检查价格字段
            price_fields = ['4. close', '4. sell price', '4. high', '4. low']
            for field in price_fields:
                if field in latest_data:
                    print(f"💰 {field}: {latest_data[field]}")
            
            print(f"📈 成交量: {latest_data.get('5. volume', 'N/A')}")
            
        print("\n🤖 测试AI分析...")
        result = engine.analyze_single_stock('000001')
        
        if result:
            print(f"✅ 分析成功!")
            print(f"🏷️ 股票: {result['symbol']} {result['name']}")
            print(f"💰 价格: ¥{result['price']} ({result['change_pct']:+.1f}%)")
            print(f"🎯 决策: {result['decision']} ({result['strength']})")
            print(f"📝 理由: {result['reason']}")
            print(f"📊 置信度: {result['confidence']}")
        else:
            print("❌ 分析失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_single_stock()