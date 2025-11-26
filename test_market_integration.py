#!/usr/bin/env python3
"""
测试大盘数据集成功能
验证市场指数服务和批量决策引擎的协同工作
"""

import sys
import time
import requests
from datetime import datetime
from batch_optimized_decision_engine import BatchOptimizedDecisionEngine

def test_market_index_service():
    """测试市场指数服务"""
    print("=== 测试市场指数服务 ===")
    
    base_url = "http://localhost:5008"
    
    # 测试服务健康状态
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 市场指数服务运行正常")
        else:
            print("❌ 市场指数服务异常")
            return False
    except Exception as e:
        print(f"❌ 无法连接市场指数服务: {e}")
        print("💡 请先启动市场指数服务: python market_index_service.py")
        return False
    
    # 测试主要指数数据
    try:
        response = requests.get(f"{base_url}/api/main-indices", timeout=5)
        if response.status_code == 200:
            data = response.json()
            indices = data.get('indices', {})
            print(f"📊 获取到 {len(indices)} 个主要指数数据:")
            for symbol, idx_data in indices.items():
                name = idx_data.get('name', symbol)
                current_value = idx_data.get('current_value', 0)
                change_pct = idx_data.get('change_percent', 0)
                print(f"   {name}: {current_value:.2f} ({change_pct:+.2f}%)")
        else:
            print("❌ 获取主要指数数据失败")
    except Exception as e:
        print(f"❌ 主要指数数据请求失败: {e}")
    
    # 测试市场摘要
    try:
        response = requests.get(f"{base_url}/api/market-summary", timeout=5)
        if response.status_code == 200:
            data = response.json()
            market_summary = data.get('market_summary', '')
            print(f"📈 市场环境摘要:")
            print(f"   {market_summary}")
        else:
            print("❌ 获取市场摘要失败")
    except Exception as e:
        print(f"❌ 市场摘要请求失败: {e}")
    
    return True

def test_batch_engine_with_market_context():
    """测试集成大盘数据的批量决策引擎"""
    print("\n=== 测试批量决策引擎 + 大盘数据集成 ===")
    
    # 创建引擎实例
    engine = BatchOptimizedDecisionEngine()
    
    # 测试市场环境获取
    print("🔄 测试市场环境数据获取...")
    market_context = engine.get_market_context()
    
    if market_context and "数据获取异常" not in market_context:
        print(f"✅ 成功获取市场环境: {market_context[:100]}...")
    else:
        print(f"⚠️  市场环境数据: {market_context}")
    
    # 测试小批量股票分析（包含大盘背景）
    print("\n🔄 测试批量股票分析（包含大盘背景）...")
    test_symbols = ["000001", "000002", "000977"]  # 测试股票
    
    start_time = time.time()
    results = engine.analyze_batch_stocks(test_symbols)
    elapsed = time.time() - start_time
    
    print(f"📊 分析结果 ({elapsed:.1f}秒):")
    
    for result in results:
        symbol = result.get('symbol', 'Unknown')
        name = result.get('name', 'Unknown')
        decision = result.get('decision', 'Unknown')
        strength = result.get('strength', 'Unknown')
        reason = result.get('reason', 'Unknown')
        price = result.get('price', 0)
        
        print(f"   {symbol} ({name}): {decision} ({strength})")
        print(f"     价格: ¥{price:.2f} | 理由: {reason}")
        print(f"     完整分析: {result.get('full_analysis', '')[:150]}...")
        print()
    
    return len(results) > 0

def test_prompt_enhancement():
    """测试提示词增强效果"""
    print("\n=== 测试提示词增强效果 ===")
    
    engine = BatchOptimizedDecisionEngine()
    
    # 模拟股票数据
    symbol = "000977"
    name = "浪潮信息"
    price_data = {
        'current_price': 59.99,
        'change_percent': 2.5,
        'volume': 320000
    }
    tech_data = {
        'trend': '温和上升',
        'ma5': 58.5,
        'signal_strength': 'mild_bullish',
        'price_position': 2.8
    }
    volume_data = {
        'avg_volume': 250000
    }
    
    # 生成增强后的提示词
    prompt = engine.build_efficient_prompt(symbol, name, price_data, tech_data, volume_data)
    
    print("📝 增强后的分析提示词:")
    print("-" * 50)
    print(prompt)
    print("-" * 50)
    
    # 检查是否包含大盘信息
    if "市场环境" in prompt or "大盘" in prompt:
        print("✅ 提示词成功集成大盘环境信息")
        return True
    else:
        print("❌ 提示词缺少大盘环境信息")
        return False

def performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    
    engine = BatchOptimizedDecisionEngine()
    
    # 测试不同数量股票的处理时间
    test_batches = [
        (["000001", "000002"], "2股"),
        (["000001", "000002", "000977", "300750", "600519"], "5股"),
        (["000001", "000002", "000977", "300750", "600519", 
          "000858", "002415", "600036", "300059", "002594"], "10股")
    ]
    
    for symbols, desc in test_batches:
        print(f"\n🔄 测试 {desc} 批量分析...")
        start_time = time.time()
        
        # 预加载市场数据（模拟真实场景）
        market_context = engine.get_market_context()
        
        results = engine.analyze_batch_stocks(symbols)
        elapsed = time.time() - start_time
        
        avg_time = elapsed / len(symbols) if symbols else 0
        print(f"⏱️  {desc} 用时: {elapsed:.1f}秒 (平均 {avg_time:.2f}秒/股)")
        print(f"📊 成功分析: {len(results)}/{len(symbols)} 只股票")
        
        if len(symbols) == 10:
            # 外推到443股的预计时间
            estimated_443 = avg_time * 443
            print(f"🎯 预计443股用时: {estimated_443/60:.1f}分钟")

def main():
    """主测试函数"""
    print("🚀 AlphaBloom 大盘数据集成测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 测试市场指数服务
    market_service_ok = test_market_index_service()
    
    if not market_service_ok:
        print("\n❌ 市场指数服务测试失败，无法继续后续测试")
        print("💡 解决方案: 请先启动市场指数服务")
        print("   cd /Users/aaron/Marketbrew")
        print("   python market_index_service.py")
        return
    
    # 测试批量引擎集成
    batch_engine_ok = test_batch_engine_with_market_context()
    
    # 测试提示词增强
    prompt_enhancement_ok = test_prompt_enhancement()
    
    # 性能测试
    if batch_engine_ok:
        performance_test()
    
    # 测试总结
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"✅ 市场指数服务: {'通过' if market_service_ok else '失败'}")
    print(f"✅ 批量引擎集成: {'通过' if batch_engine_ok else '失败'}")
    print(f"✅ 提示词增强: {'通过' if prompt_enhancement_ok else '失败'}")
    
    if market_service_ok and batch_engine_ok and prompt_enhancement_ok:
        print("\n🎉 所有测试通过！AlphaBloom 大盘数据集成功能正常")
        print("💡 建议: 可以开始使用增强版批量分析功能")
    else:
        print("\n⚠️  部分测试失败，请检查相关服务和配置")

if __name__ == "__main__":
    main()