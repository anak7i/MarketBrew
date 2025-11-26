#!/usr/bin/env python3
"""
测试MA20和MA30的5天前数据功能
展示均线的5天变化趋势分析
"""

import requests
import json
from datetime import datetime

def test_ma_5d_ago_api():
    """测试API中的5天前数据"""
    print("📊 测试MA20/MA30五天前数据功能")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:5015/api/market-temperature")
        if response.status_code == 200:
            data = response.json()
            hs300 = data['data']['hs300']
            
            print("✅ API响应正常，获取到5天前数据")
            print(f"📅 数据时间: {data['timestamp']}")
            
            print(f"\n📈 沪深300均线对比分析:")
            print(f"{'指标':<12} {'当前值':<12} {'5天前值':<12} {'变化':<12} {'趋势':<8}")
            print("-" * 60)
            
            # MA20分析
            ma20_current = hs300['ma20']
            ma20_5d_ago = hs300['ma20_5d_ago']
            ma20_change = ma20_current - ma20_5d_ago
            ma20_change_pct = (ma20_change / ma20_5d_ago * 100) if ma20_5d_ago > 0 else 0
            ma20_trend = "📈" if ma20_change > 0 else "📉" if ma20_change < 0 else "➡️"
            
            print(f"{'MA20':<12} {ma20_current:<12.2f} {ma20_5d_ago:<12.2f} {ma20_change:+8.2f} {ma20_trend}")
            print(f"{'MA20变化%':<12} {'':<12} {'':<12} {ma20_change_pct:+8.3f}% {'':<8}")
            
            # MA30分析
            ma30_current = hs300['ma30']
            ma30_5d_ago = hs300['ma30_5d_ago']
            ma30_change = ma30_current - ma30_5d_ago
            ma30_change_pct = (ma30_change / ma30_5d_ago * 100) if ma30_5d_ago > 0 else 0
            ma30_trend = "📈" if ma30_change > 0 else "📉" if ma30_change < 0 else "➡️"
            
            print(f"{'MA30':<12} {ma30_current:<12.2f} {ma30_5d_ago:<12.2f} {ma30_change:+8.2f} {ma30_trend}")
            print(f"{'MA30变化%':<12} {'':<12} {'':<12} {ma30_change_pct:+8.3f}% {'':<8}")
            
            print(f"\n🎯 当前价格分析:")
            current_price = hs300['price']
            print(f"  • 当前价格: {current_price:.2f}")
            print(f"  • 距离MA20: {hs300['vs_ma20']:+.2f}% ({'下方' if hs300['vs_ma20'] < 0 else '上方'})")
            print(f"  • 距离MA30: {hs300['vs_ma30']:+.2f}% ({'下方' if hs300['vs_ma30'] < 0 else '上方'})")
            
            print(f"\n📊 均线趋势分析:")
            if ma20_change > 0 and ma30_change > 0:
                trend_signal = "双线向上 🟢"
                strength = "强势"
            elif ma20_change > 0 or ma30_change > 0:
                trend_signal = "单线向上 🟡"
                strength = "中性"
            elif ma20_change < 0 and ma30_change < 0:
                trend_signal = "双线向下 🔴"
                strength = "弱势"
            else:
                trend_signal = "震荡整理 ⚪"
                strength = "观察"
            
            print(f"  • 5天趋势: {trend_signal}")
            print(f"  • 趋势强度: {strength}")
            print(f"  • MA20斜率: {ma20_change_pct:+.3f}% (5天)")
            print(f"  • MA30斜率: {ma30_change_pct:+.3f}% (5天)")
            
            # 技术建议
            print(f"\n💡 技术建议:")
            if ma20_change > 0 and ma30_change > 0 and current_price > ma20_current:
                print("  • 🟢 强势信号：双均线向上且价格在均线上方")
                print("  • 🎯 建议：可积极关注做多机会")
            elif ma20_change > 0 and ma30_change > 0:
                print("  • 🟡 温和信号：双均线向上但价格仍在均线下方")
                print("  • 🎯 建议：等待价格突破均线确认")
            elif current_price < ma20_current and ma20_change < 0:
                print("  • 🔴 弱势信号：价格在下行均线下方")
                print("  • 🎯 建议：保持观望，等待转机")
            else:
                print("  • ⚪ 震荡信号：趋势不明确")
                print("  • 🎯 建议：谨慎操作，控制仓位")
            
            # 验证功能完整性
            print(f"\n✅ 功能验证:")
            required_fields = ['ma20_5d_ago', 'ma30_5d_ago']
            for field in required_fields:
                if field in hs300:
                    print(f"  • {field}: ✅ 正常 ({hs300[field]:.2f})")
                else:
                    print(f"  • {field}: ❌ 缺失")
            
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def analyze_ma_trend_strength():
    """分析均线趋势强度"""
    print(f"\n🔍 均线趋势强度分析")
    print("="*50)
    
    try:
        response = requests.get("http://localhost:5015/api/market-temperature")
        data = response.json()['data']
        hs300 = data['hs300']
        
        # 计算均线强度指标
        ma20_strength = (hs300['ma20'] - hs300['ma20_5d_ago']) / hs300['ma20_5d_ago'] * 100
        ma30_strength = (hs300['ma30'] - hs300['ma30_5d_ago']) / hs300['ma30_5d_ago'] * 100
        
        print(f"MA20强度评分: {ma20_strength:.3f}%")
        print(f"MA30强度评分: {ma30_strength:.3f}%")
        
        # 综合评分
        combined_strength = (ma20_strength * 0.6 + ma30_strength * 0.4)
        print(f"综合强度评分: {combined_strength:.3f}%")
        
        # 强度等级
        if combined_strength > 0.1:
            grade = "A+ (非常强势)"
        elif combined_strength > 0.05:
            grade = "A (强势)"
        elif combined_strength > 0:
            grade = "B (温和向上)"
        elif combined_strength > -0.05:
            grade = "C (震荡)"
        elif combined_strength > -0.1:
            grade = "D (温和向下)"
        else:
            grade = "F (弱势)"
        
        print(f"趋势等级: {grade}")
        
        # 增强分析结果
        enhanced = data['enhanced_analysis']
        print(f"\n🔍 增强分析确认:")
        print(f"  • 综合信号: {enhanced['signal']}")
        print(f"  • 信号强度: {enhanced['strength']}%")
        print(f"  • 均线向上: {'是' if enhanced['ma_trend_up'] else '否'}")
        
    except Exception as e:
        print(f"❌ 分析失败: {e}")

def main():
    """主函数"""
    print("🚀 MA20/MA30五天前数据功能测试")
    print("="*60)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试API功能
    test_ma_5d_ago_api()
    
    # 分析趋势强度
    analyze_ma_trend_strength()
    
    print(f"\n🌐 访问仪表板查看可视化: http://localhost:5015/dashboard")
    print(f"✅ 测试完成！")

if __name__ == "__main__":
    main()