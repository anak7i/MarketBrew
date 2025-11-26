#!/usr/bin/env python3
"""
展示数据增强前后的对比
Before: 只有基础价格数据
After: 完整的财务+技术+宏观+行业+情绪数据
"""

import requests
import json
import time

def show_old_vs_new_data():
    """展示新旧数据格式对比"""
    print("🔄 MarketBrew 数据增强效果对比")
    print("=" * 60)
    
    # 1. 旧版本数据（仅基础价格）
    print("\n📊 【旧版本】基础价格数据:")
    print("-" * 30)
    old_data = {
        "symbol": "600519",
        "name": "贵州茅台", 
        "current_price": 1433.33,
        "change_percent": -0.13,
        "volume": 18861
    }
    
    for key, value in old_data.items():
        print(f"   {key}: {value}")
    
    print(f"\n📝 旧版本分析输入给DeepSeek的数据量: ~{len(str(old_data))} 字符")
    print("   ❌ 缺少PE/PB/ROE等关键财务指标")
    print("   ❌ 没有行业对比和宏观环境")
    print("   ❌ 无法进行深度估值分析")
    
    # 2. 新版本数据（完整增强数据）
    print("\n\n📈 【新版本】完整增强数据:")
    print("-" * 30)
    
    try:
        # 获取综合增强数据
        response = requests.get("http://localhost:5006/api/comprehensive/600519", timeout=15)
        
        if response.status_code == 200:
            new_data = response.json()
            
            print(f"✅ 数据获取成功!")
            print(f"   数据质量: {new_data.get('data_quality', {}).get('level', '未知')} ({new_data.get('data_quality', {}).get('overall_score', 0):.1f}分)")
            
            # 显示各模块数据摘要
            modules = [
                ("💰 基础信息", "basic_info", ["current_price", "change_percent", "volume"]),
                ("📊 财务指标", "financial_metrics", ["pe_ratio", "pb_ratio", "roe", "revenue_growth"]),
                ("📈 技术指标", "technical_indicators", ["ma5", "ma20", "rsi", "macd_trend"]),
                ("🏭 行业对比", "industry_comparison", ["sector", "industry_pe", "policy_support"]),
                ("🌍 宏观环境", "macro_environment", ["gdp_growth", "cpi", "shanghai_index"]),
                ("🎭 个股情绪", "stock_sentiment", ["main_net_inflow", "institutional_action"]),
                ("📊 市场情绪", "market_sentiment", ["sentiment_level", "fear_greed_index"])
            ]
            
            total_chars = 0
            
            for module_name, module_key, sample_fields in modules:
                module_data = new_data.get(module_key, {})
                
                if module_data and not isinstance(module_data, str):
                    print(f"\n   {module_name}:")
                    
                    for field in sample_fields:
                        if field in module_data:
                            value = module_data[field]
                            if isinstance(value, float):
                                print(f"      {field}: {value:.2f}")
                            else:
                                print(f"      {field}: {value}")
                    
                    module_chars = len(str(module_data))
                    total_chars += module_chars
                    print(f"      → 数据量: {module_chars} 字符")
                else:
                    print(f"\n   {module_name}: ❌ 数据缺失")
            
            print(f"\n📝 新版本分析输入给DeepSeek的数据量: ~{total_chars} 字符")
            print(f"   📈 数据增强倍数: {total_chars // len(str(old_data))}x")
            
            print(f"\n🎯 关键改进:")
            print(f"   ✅ 真实PE估值: {new_data.get('financial_metrics', {}).get('pe_ratio', 0):.1f}倍")
            print(f"   ✅ 行业对比: {new_data.get('industry_comparison', {}).get('sector', '未知')}行业 (行业PE: {new_data.get('industry_comparison', {}).get('industry_pe', 0):.1f}倍)")
            print(f"   ✅ 宏观环境: GDP{new_data.get('macro_environment', {}).get('gdp_growth', 0):.1f}% CPI{new_data.get('macro_environment', {}).get('cpi', 0):.1f}%")
            print(f"   ✅ 市场情绪: {new_data.get('market_sentiment', {}).get('sentiment_level', '中性')}({new_data.get('market_sentiment', {}).get('overall_sentiment_score', 50):.0f}分)")
            print(f"   ✅ 资金流向: 主力净流入{new_data.get('stock_sentiment', {}).get('main_net_inflow', 0):+.2f}万元")
            
        else:
            print(f"❌ 数据获取失败: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 数据获取异常: {e}")

def compare_analysis_capability():
    """对比分析能力"""
    print("\n\n🤖 分析能力对比:")
    print("=" * 60)
    
    print("\n📉 【旧版本】基于基础数据的分析局限:")
    print("   ❌ 只能进行技术面分析（基于价格走势）")
    print("   ❌ 无法判断估值是否合理") 
    print("   ❌ 不了解公司基本面状况")
    print("   ❌ 缺乏行业和宏观背景")
    print("   ❌ 分析结论缺乏数据支撑")
    print("   ❌ 投资建议信心度低")
    
    print("\n📈 【新版本】基于综合数据的分析优势:")
    print("   ✅ 基本面分析: PE/PB/ROE深度估值")
    print("   ✅ 技术面分析: 多指标确认趋势")
    print("   ✅ 行业对比: 相对估值和竞争地位")
    print("   ✅ 宏观分析: 经济环境和政策影响")
    print("   ✅ 情绪分析: 资金流向和市场预期")
    print("   ✅ 综合决策: 多维度数据融合分析")
    print("   ✅ 专业建议: 基金经理级别的投资策略")

def show_prompt_enhancement():
    """展示prompt增强效果"""
    print("\n\n💬 DeepSeek分析Prompt对比:")
    print("=" * 60)
    
    print("\n📉 【旧版本】简单Prompt (约200字):")
    print("   '分析股票600519贵州茅台，当前价格1433.33元，涨跌幅-0.13%'")
    
    print("\n📈 【新版本】专业Prompt (约2000字):")
    print("   包含完整的:")
    print("   • 实时市场数据 (价格/成交量/换手率)")
    print("   • 真实财务指标 (PE/PB/ROE/增长率/毛利率)")
    print("   • 技术指标分析 (MA/RSI/MACD/支撑阻力)")
    print("   • 行业对比数据 (估值/增长/政策/趋势)")
    print("   • 宏观环境分析 (GDP/CPI/利率/指数)")
    print("   • 市场情绪数据 (资金流向/投资者行为)")
    print("   • 专业分析要求 (基金经理角色设定)")
    print("   • 结构化输出格式 (商业分析/估值/策略/风险)")

def main():
    """主演示流程"""
    show_old_vs_new_data()
    compare_analysis_capability()
    show_prompt_enhancement()
    
    print("\n\n🎉 总结:")
    print("=" * 60)
    print("📊 数据维度: 从1维扩展到7维")
    print("📈 数据量: 增加10-20倍")
    print("🎯 分析深度: 从表面到深度")
    print("💼 专业度: 从业余到专业")
    print("🔍 可信度: 从猜测到数据驱动")
    print("⚡ 实用性: 从参考到可执行")
    
    print("\n🚀 MarketBrew现在提供的是:")
    print("   真正的专业级股票分析服务!")

if __name__ == "__main__":
    main()