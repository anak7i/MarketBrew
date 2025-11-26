#!/usr/bin/env python3
"""
检查所有股票的名称映射覆盖率
"""

import glob
import os
from unified_decision_engine import UnifiedDecisionEngine

def check_stock_names():
    engine = UnifiedDecisionEngine()
    
    # 获取所有A股代码
    all_stocks = engine.get_all_stocks()
    
    print(f"📊 总共有 {len(all_stocks)} 只A股数据")
    print("🔍 检查股票名称映射覆盖情况...\n")
    
    # 检查名称映射
    missing_names = []
    covered_names = []
    
    for symbol in all_stocks[:50]:  # 先检查前50只
        name = engine.get_stock_name(symbol)
        if name.startswith('股票'):
            missing_names.append(symbol)
            print(f"❌ {symbol}: {name}")
        else:
            covered_names.append(symbol)
            print(f"✅ {symbol}: {name}")
    
    print(f"\n📈 统计结果 (前50只):")
    print(f"✅ 有名称: {len(covered_names)} 只")
    print(f"❌ 无名称: {len(missing_names)} 只") 
    print(f"📊 覆盖率: {len(covered_names)/(len(covered_names)+len(missing_names))*100:.1f}%")
    
    if missing_names:
        print(f"\n🔍 缺失名称的股票代码:")
        print(missing_names[:20])  # 显示前20个
        
        print(f"\n💡 这些股票需要添加到 get_stock_name() 函数中")
        
    return missing_names, covered_names

if __name__ == "__main__":
    check_stock_names()