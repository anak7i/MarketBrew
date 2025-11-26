#!/usr/bin/env python3
"""
生成干净的决策数据 - 修复所有问题后重新分析
"""

from unified_decision_engine import UnifiedDecisionEngine
import json

def generate_clean_data():
    engine = UnifiedDecisionEngine()
    
    print("🧹 生成修复后的决策数据...")
    
    # 选择一些典型的A股进行测试
    test_stocks = [
        '000001',  # 平安银行
        '000002',  # 万科A  
        '600519',  # 贵州茅台
        '300750',  # 宁德时代
        '600036',  # 招商银行
        '000858',  # 五粮液
        '002594',  # 比亚迪
        '000568',  # 泸州老窖
        '002415',  # 海康威视
        '601318',  # 中国平安
    ]
    
    results = []
    
    for i, symbol in enumerate(test_stocks, 1):
        print(f"🔍 [{i}/{len(test_stocks)}] 分析 {symbol}...")
        
        try:
            result = engine.analyze_single_stock(symbol)
            if result:
                results.append(result)
                print(f"✅ {result['symbol']} {result['name']}: {result['decision']} - ¥{result['price']} ({result['reason'][:30]}...)")
            else:
                print(f"❌ {symbol}: 分析失败或数据异常")
        except Exception as e:
            print(f"❌ {symbol}: 异常 - {e}")
    
    # 生成决策数据
    if results:
        decision_data = engine.generate_decision_data(results)
        engine.save_decision_data(decision_data)
        
        print(f"\n📊 清洁数据生成完成!")
        print(f"✅ 成功分析: {len(results)}只股票")
        print(f"📈 买入建议: {decision_data['summary']['buy_count']}只")
        print(f"📉 卖出建议: {decision_data['summary']['sell_count']}只") 
        print(f"📋 持有建议: {decision_data['summary']['hold_count']}只")
        print(f"📝 市场分析: {decision_data['summary']['market_analysis']}")
        print(f"⚠️ 风险评级: {decision_data['summary']['risk_level']}")
        print(f"💾 数据已保存到: decision_data/latest_decision.json")
        
        # 显示一些样例
        print(f"\n📋 决策样例:")
        for category, stocks in decision_data['decisions'].items():
            if stocks:
                print(f"  {category.upper()}:")
                for stock in stocks[:3]:  # 显示前3只
                    print(f"    {stock['symbol']} {stock['name']}: ¥{stock['price']} - {stock['reason'][:50]}...")
        
        return True
    else:
        print("❌ 没有成功的分析结果")
        return False

if __name__ == "__main__":
    generate_clean_data()