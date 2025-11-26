#!/usr/bin/env python3
"""
验证增强版技术分析功能
展示完整的技术分析结果，验证所有功能是否正常工作
"""

import requests
import json
from enhanced_technical_analyzer import EnhancedTechnicalAnalyzer

def test_enhanced_technical_analyzer():
    """测试增强版技术分析器"""
    print("🔍 测试增强版技术分析器")
    print("="*50)
    
    analyzer = EnhancedTechnicalAnalyzer()
    
    # 获取分析报告
    report = analyzer.generate_analysis_report()
    print(report)
    
    return analyzer.analyze_technical_signal()

def test_market_temperature_api():
    """测试市场温度计API"""
    print("\n🌡️ 测试市场温度计API")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:5015/api/market-temperature")
        if response.status_code == 200:
            data = response.json()
            
            print("✅ API响应正常")
            print(f"🌡️ 市场温度: {data['data']['temperature_score']}分 - {data['data']['temperature_level']}")
            
            print("\n📊 增强技术分析结果:")
            enhanced = data['data']['enhanced_analysis']
            print(f"  • 综合信号: {enhanced['signal']}")
            print(f"  • 信号强度: {enhanced['strength']}%")
            print(f"  • 连续突破: {enhanced['consecutive_days']}天")
            print(f"  • 放量突破: {'是' if enhanced['volume_breakout'] else '否'}")
            print(f"  • 均线向上: {'是' if enhanced['ma_trend_up'] else '否'}")
            print(f"  • 回踩不破: {'是' if enhanced['pullback_hold'] else '否'}")
            
            print("\n📈 沪深300数据:")
            hs300 = data['data']['hs300']
            print(f"  • 最新价格: {hs300['price']:.2f}")
            print(f"  • 涨跌幅: {hs300['change']:+.2f}%")
            print(f"  • MA20: {hs300['ma20']:.2f} (距离: {hs300['vs_ma20']:+.2f}%)")
            print(f"  • MA30: {hs300['ma30']:.2f} (距离: {hs300['vs_ma30']:+.2f}%)")
            print(f"  • 基础信号: {hs300['signal']}")
            
            print("\n🔥 升温因素:")
            for source in data['data']['heat_sources']:
                print(f"  • {source}")
            
            print("\n❄️ 降温因素:")
            for source in data['data']['cool_sources']:
                print(f"  • {source}")
            
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")

def validate_technical_conditions():
    """验证技术条件"""
    print("\n🔬 验证技术条件")
    print("="*50)
    
    analyzer = EnhancedTechnicalAnalyzer()
    signal = analyzer.analyze_technical_signal()
    
    print("📋 技术条件检查:")
    print(f"  1. 指数 > MA20 & MA30: {'✅' if signal.above_ma else '❌'}")
    print(f"  2. MA20、MA30向上: {'✅' if signal.ma_trend_up else '❌'}")
    print(f"  3. 连续突破天数: {signal.consecutive_days}天 {'✅' if signal.consecutive_days >= 2 else '❌'}")
    print(f"  4. 放量突破: {'✅' if signal.volume_breakout else '❌'}")
    print(f"  5. 回踩不破: {'✅' if signal.pullback_hold else '❌'}")
    
    print(f"\n📊 综合评分: {signal.signal_strength:.1f}/100")
    print(f"🎯 信号类型: {signal.signal_type}")
    
    # 判断是否满足强势突破条件
    strong_conditions_met = (
        signal.above_ma and 
        signal.ma_trend_up and 
        signal.consecutive_days >= 2
    )
    
    print(f"\n🚀 强势突破条件: {'✅ 满足' if strong_conditions_met else '❌ 未满足'}")
    
    if strong_conditions_met:
        print("💡 建议: 可考虑积极布局")
        if signal.volume_breakout:
            print("💡 加分项: 放量突破确认，信号更强")
    else:
        print("💡 建议: 等待更多确认信号")
    
    return signal

def main():
    """主函数"""
    print("🚀 增强版技术分析验证系统")
    print("="*60)
    
    # 1. 测试独立的技术分析器
    signal = test_enhanced_technical_analyzer()
    
    # 2. 测试市场温度计API
    test_market_temperature_api()
    
    # 3. 验证技术条件
    validate_technical_conditions()
    
    print(f"\n✅ 验证完成！")
    print(f"📊 当前市场状态: {signal.signal_type} (强度: {signal.signal_strength:.1f}%)")
    print(f"🌐 访问仪表板: http://localhost:5015/dashboard")

if __name__ == "__main__":
    main()