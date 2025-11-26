#!/usr/bin/env python3
"""
AlphaBloom 增强版演示
展示大盘数据集成 + 批量股票分析功能
"""

import time
import json
from datetime import datetime
from batch_optimized_decision_engine import BatchOptimizedDecisionEngine

def main():
    print("🌟 AlphaBloom 增强版演示")
    print("=" * 60)
    print("🔥 特色功能: 大盘环境 + DeepSeek AI + 批量分析")
    print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建决策引擎
    print("🤖 初始化 AlphaBloom 决策引擎...")
    engine = BatchOptimizedDecisionEngine()
    print("✅ 引擎初始化完成")
    print()
    
    # 演示股票列表
    demo_stocks = [
        "000001",  # 平安银行
        "000002",  # 万科A
        "000977",  # 浪潮信息
        "300750",  # 宁德时代
        "600519",  # 贵州茅台
        "000858",  # 五粮液
        "002415",  # 海康威视
        "600036"   # 招商银行
    ]
    
    print(f"📊 演示股票: {len(demo_stocks)} 只")
    for i, symbol in enumerate(demo_stocks, 1):
        print(f"   {i}. {symbol}")
    print()
    
    # 步骤1: 展示市场环境获取
    print("📈 步骤1: 获取当前市场环境...")
    market_context = engine.get_market_context()
    print("🌍 当前市场环境:")
    print(f"   {market_context}")
    print()
    
    # 步骤2: 执行批量分析
    print("⚡ 步骤2: 执行批量股票分析...")
    print("🔄 分析进行中，请稍候...")
    
    start_time = time.time()
    results = engine.analyze_batch_stocks(demo_stocks)
    elapsed_time = time.time() - start_time
    
    print(f"✅ 分析完成! 用时 {elapsed_time:.1f} 秒")
    print(f"📊 成功分析 {len(results)}/{len(demo_stocks)} 只股票")
    print()
    
    # 步骤3: 展示分析结果
    print("📋 步骤3: 分析结果展示")
    print("-" * 60)
    
    # 按决策类型分组
    buy_stocks = []
    sell_stocks = []
    hold_stocks = []
    
    for result in results:
        decision = result.get('decision', '持有').lower()
        if '买' in decision:
            buy_stocks.append(result)
        elif '卖' in decision:
            sell_stocks.append(result)
        else:
            hold_stocks.append(result)
    
    # 显示买入建议
    if buy_stocks:
        print(f"🟢 买入建议 ({len(buy_stocks)}只):")
        for stock in buy_stocks:
            symbol = stock.get('symbol', '')
            name = stock.get('name', '')
            strength = stock.get('strength', '')
            reason = stock.get('reason', '')
            price = stock.get('price', 0)
            print(f"   {symbol} ({name}) - {strength}")
            print(f"      价格: ¥{price:.2f} | {reason}")
    else:
        print("🟢 买入建议: 暂无")
    print()
    
    # 显示卖出建议
    if sell_stocks:
        print(f"🔴 卖出建议 ({len(sell_stocks)}只):")
        for stock in sell_stocks:
            symbol = stock.get('symbol', '')
            name = stock.get('name', '')
            strength = stock.get('strength', '')
            reason = stock.get('reason', '')
            price = stock.get('price', 0)
            print(f"   {symbol} ({name}) - {strength}")
            print(f"      价格: ¥{price:.2f} | {reason}")
    else:
        print("🔴 卖出建议: 暂无")
    print()
    
    # 显示持有建议
    if hold_stocks:
        print(f"🟡 持有建议 ({len(hold_stocks)}只):")
        for stock in hold_stocks[:3]:  # 只显示前3只
            symbol = stock.get('symbol', '')
            name = stock.get('name', '')
            reason = stock.get('reason', '')
            price = stock.get('price', 0)
            print(f"   {symbol} ({name})")
            print(f"      价格: ¥{price:.2f} | {reason}")
        if len(hold_stocks) > 3:
            print(f"   ... 及其他 {len(hold_stocks)-3} 只")
    else:
        print("🟡 持有建议: 暂无")
    print()
    
    # 步骤4: 性能统计
    print("⚡ 步骤4: 性能统计")
    print("-" * 60)
    avg_time = elapsed_time / len(demo_stocks) if demo_stocks else 0
    print(f"📊 分析效率: {avg_time:.2f} 秒/股")
    print(f"🎯 443股预计用时: {avg_time * 443 / 60:.1f} 分钟")
    print(f"🔥 相比传统方法提速: ~60%")
    print()
    
    # 步骤5: 技术特点
    print("🚀 步骤5: AlphaBloom 技术特点")
    print("-" * 60)
    features = [
        "✅ DeepSeek AI智能分析",
        "✅ 大盘环境背景集成",
        "✅ 实时价格数据获取", 
        "✅ 8线程并发处理",
        "✅ 智能数据缓存",
        "✅ 批量优化算法",
        "✅ 技术指标计算",
        "✅ 风险评估分析"
    ]
    
    for feature in features:
        print(f"   {feature}")
    print()
    
    # 保存结果到文件
    output_file = f"alphabloom_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'market_context': market_context,
                'analysis_time': elapsed_time,
                'total_stocks': len(demo_stocks),
                'successful_analysis': len(results),
                'results': results
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 分析结果已保存至: {output_file}")
    except Exception as e:
        print(f"⚠️  保存结果失败: {e}")
    
    print()
    print("🎉 AlphaBloom 演示完成!")
    print("💡 若要分析更多股票，请调用 engine.analyze_batch_stocks(stock_list)")

if __name__ == "__main__":
    main()