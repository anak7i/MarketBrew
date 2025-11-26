#!/usr/bin/env python3
"""
快速分析 - 分析前20只股票生成样本数据
"""

from unified_decision_engine import UnifiedDecisionEngine
import json

def quick_analysis():
    engine = UnifiedDecisionEngine()
    
    print("🚀 快速分析前20只股票...")
    
    # 获取前20只股票
    all_stocks = engine.get_all_stocks()
    test_stocks = all_stocks[:20]
    
    print(f"📊 分析股票: {test_stocks}")
    
    results = []
    for i, symbol in enumerate(test_stocks, 1):
        print(f"🔍 [{i}/20] 分析 {symbol}...")
        
        try:
            result = engine.analyze_single_stock(symbol)
            if result:
                results.append(result)
                print(f"✅ {symbol}: {result['decision']} - {result['price']}")
            else:
                print(f"❌ {symbol}: 分析失败")
        except Exception as e:
            print(f"❌ {symbol}: {e}")
    
    # 生成决策数据
    if results:
        decision_data = engine.generate_decision_data(results)
        engine.save_decision_data(decision_data)
        
        print(f"\n📊 快速分析完成!")
        print(f"✅ 成功分析: {len(results)}只")
        print(f"📈 买入建议: {decision_data['summary']['buy_count']}只")
        print(f"📉 卖出建议: {decision_data['summary']['sell_count']}只") 
        print(f"📋 持有建议: {decision_data['summary']['hold_count']}只")
        print(f"💾 数据已保存到: decision_data/")
        
        return True
    else:
        print("❌ 没有成功的分析结果")
        return False

if __name__ == "__main__":
    quick_analysis()