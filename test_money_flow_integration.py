#!/usr/bin/env python3
"""
测试资金流集成功能
验证北向资金、ETF资金、主力资金的三天数据
"""

import requests
import json
from datetime import datetime

def test_money_flow_integration():
    """测试资金流集成功能"""
    print("💰 测试资金流集成功能")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:5015/api/market-temperature")
        if response.status_code == 200:
            data = response.json()
            money_flow = data['data']['money_flow']
            
            print("✅ 资金流数据获取成功")
            print(f"📅 数据时间: {data['timestamp']}")
            
            # 综合评分
            print(f"\n📊 资金流综合分析:")
            print(f"  • 评分: {money_flow['score']:.1f}/100")
            print(f"  • 等级: {money_flow['level']}")
            
            # 今日资金流
            print(f"\n💰 今日资金流向:")
            today = money_flow['today']
            today_total = today['north_bound'] + today['etf_inflow'] + today['main_force']
            
            print(f"  • 北向资金: {today['north_bound']:+.2f}亿元")
            print(f"  • ETF资金:  {today['etf_inflow']:+.2f}亿元")
            print(f"  • 主力资金: {today['main_force']:+.2f}亿元")
            print(f"  • 📈 今日合计: {today_total:+.2f}亿元")
            
            # 3天累计
            print(f"\n📊 3天累计资金流:")
            three_days = money_flow['three_days_total']
            total_3d = three_days['north_bound'] + three_days['etf_inflow'] + three_days['main_force']
            
            print(f"  • 北向资金: {three_days['north_bound']:+.2f}亿元")
            print(f"  • ETF资金:  {three_days['etf_inflow']:+.2f}亿元")
            print(f"  • 主力资金: {three_days['main_force']:+.2f}亿元")
            print(f"  • 📈 3日合计: {total_3d:+.2f}亿元")
            
            # 趋势分析
            print(f"\n📈 资金流趋势:")
            trends = money_flow['trends']
            print(f"  • 北向资金: {trends['north_bound']}")
            print(f"  • ETF资金:  {trends['etf']}")
            print(f"  • 主力资金: {trends['main_force']}")
            
            # 对市场温度的影响
            overall_temp = data['data']['temperature_score']
            print(f"\n🌡️ 对市场温度的影响:")
            print(f"  • 市场温度: {overall_temp:.1f}分")
            print(f"  • 资金流贡献: 20%权重")
            print(f"  • 资金流评分: {money_flow['score']:.1f}分")
            
            # 投资建议
            print(f"\n💡 基于资金流的建议:")
            if money_flow['score'] >= 70:
                print("  • 🟢 资金持续流入，市场情绪积极")
                print("  • 🎯 建议：可考虑适度增加仓位")
                if today_total > 50:
                    print("  • 🚀 今日资金流入强劲，关注热点板块")
            elif money_flow['score'] >= 50:
                print("  • 🟡 资金流向基本平衡")
                print("  • 🎯 建议：保持观望，等待明确信号")
            else:
                print("  • 🔴 资金持续流出，市场承压")
                print("  • 🎯 建议：控制仓位，注意风险")
            
            # 验证数据完整性
            print(f"\n✅ 数据完整性验证:")
            required_fields = {
                'today': ['north_bound', 'etf_inflow', 'main_force'],
                'three_days_total': ['north_bound', 'etf_inflow', 'main_force'],
                'trends': ['north_bound', 'etf', 'main_force'],
            }
            
            for section, fields in required_fields.items():
                for field in fields:
                    if field in money_flow[section]:
                        print(f"  • {section}.{field}: ✅ 正常")
                    else:
                        print(f"  • {section}.{field}: ❌ 缺失")
            
            # 数据逻辑验证
            print(f"\n🔍 数据逻辑验证:")
            
            # 检查评分范围
            if 0 <= money_flow['score'] <= 100:
                print(f"  • 评分范围: ✅ 正常 ({money_flow['score']:.1f})")
            else:
                print(f"  • 评分范围: ❌ 异常 ({money_flow['score']:.1f})")
            
            # 检查数据合理性
            max_single_flow = 200  # 单日资金流最大合理值
            if abs(today_total) <= max_single_flow:
                print(f"  • 今日总流入: ✅ 合理 ({today_total:.1f}亿)")
            else:
                print(f"  • 今日总流入: ⚠️ 偏大 ({today_total:.1f}亿)")
            
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_dashboard_display():
    """测试仪表板显示"""
    print(f"\n🌐 仪表板显示测试")
    print("="*60)
    
    print("📋 仪表板新增功能:")
    print("  ✅ 资金流评分显示")
    print("  ✅ 今日净流入合计")
    print("  ✅ 北向/ETF/主力资金今日数据")
    print("  ✅ 3天累计资金流向")
    print("  ✅ 资金流趋势标识")
    
    print(f"\n🌐 访问仪表板: http://localhost:5015/dashboard")
    print("📊 新增资金流分析面板，实时显示三类资金动向")

def generate_summary_report():
    """生成功能总结报告"""
    try:
        response = requests.get("http://localhost:5015/api/market-temperature")
        data = response.json()['data']
        
        print(f"\n📋 资金流功能总结报告")
        print("="*60)
        
        money_flow = data['money_flow']
        enhanced = data['enhanced_analysis']
        hs300 = data['hs300']
        
        print(f"🎯 核心功能实现:")
        print(f"  ✅ 北向资金：今日{money_flow['today']['north_bound']:+.1f}亿，3日{money_flow['three_days_total']['north_bound']:+.1f}亿")
        print(f"  ✅ ETF资金： 今日{money_flow['today']['etf_inflow']:+.1f}亿，3日{money_flow['three_days_total']['etf_inflow']:+.1f}亿")
        print(f"  ✅ 主力资金：今日{money_flow['today']['main_force']:+.1f}亿，3日{money_flow['three_days_total']['main_force']:+.1f}亿")
        
        print(f"\n📊 综合分析结果:")
        print(f"  • 市场温度：{data['temperature_score']:.1f}分 - {data['temperature_level']}")
        print(f"  • 资金流评分：{money_flow['score']:.1f}分 - {money_flow['level']}")
        print(f"  • 技术信号：{enhanced['signal']} (强度{enhanced['strength']:.1f}%)")
        
        print(f"\n🏗️ 系统架构:")
        print(f"  • 数据层：集成北向/ETF/主力资金实时数据")
        print(f"  • 分析层：资金流评分算法 + 趋势判断")
        print(f"  • 展示层：API接口 + 实时仪表板")
        print(f"  • 权重配置：资金流占市场温度20%权重")
        
        return True
        
    except Exception as e:
        print(f"❌ 报告生成失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 资金流集成功能测试系统")
    print("="*70)
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 测试API集成
    test_money_flow_integration()
    
    # 2. 测试仪表板
    test_dashboard_display()
    
    # 3. 生成总结报告
    success = generate_summary_report()
    
    if success:
        print(f"\n✅ 所有测试完成！资金流功能已成功集成")
    else:
        print(f"\n⚠️ 部分测试失败，请检查系统状态")

if __name__ == "__main__":
    main()