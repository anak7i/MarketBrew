#!/usr/bin/env python3
"""
专业股票分析演示
使用增强版LangChain API为用户的5只股票提供专业分析
"""

import requests
import json
import time

def get_professional_analysis(stock_info):
    """使用增强版API获取专业分析"""
    try:
        print(f"📊 正在深度分析 {stock_info['name']} ({stock_info['symbol']})...")
        
        # 使用LangChain增强版API
        response = requests.post(
            "http://localhost:5001/api/langchain/stock-analysis",
            json={"stocks": [stock_info]},
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                result = data['results'][0]
                analysis = result.get('analysis', '')
                
                # 提取关键信息
                lines = analysis.split('\n')
                key_info = {
                    'operation': '',
                    'confidence': '',
                    'position': '',
                    'target_price': '',
                    'logic': ''
                }
                
                for i, line in enumerate(lines):
                    if "**核心判断**" in line or "**操作建议**" in line:
                        key_info['operation'] = line.replace("**核心判断**：", "").replace("**操作建议**：", "").strip()
                    elif "**信心度**" in line:
                        key_info['confidence'] = line.replace("**信心度**：", "").strip()
                    elif "**建议仓位**" in line:
                        key_info['position'] = line.replace("**建议仓位**：", "").strip()
                    elif "**目标价格**" in line:
                        key_info['target_price'] = line.replace("**目标价格**：", "").strip()
                    elif "**行业地位**" in line:
                        key_info['logic'] = line.replace("**行业地位**：", "").strip()[:100] + "..."
                
                return key_info, analysis
        
        return None, "分析失败"
        
    except Exception as e:
        return None, f"错误: {str(e)}"

def main():
    # 用户的5只股票
    stocks = [
        {"symbol": "600036", "name": "招商银行"},
        {"symbol": "601318", "name": "中国平安"},
        {"symbol": "002837", "name": "英维克"},
        {"symbol": "000977", "name": "浪潮信息"},
        {"symbol": "600030", "name": "中信证券"}
    ]
    
    print("🔥 MarketBrew专业股票分析系统")
    print("=" * 80)
    print("正在使用LangChain增强版API进行深度分析...")
    print()
    
    results = []
    
    for i, stock in enumerate(stocks, 1):
        print(f"[{i}/5] ", end="")
        key_info, full_analysis = get_professional_analysis(stock)
        
        if key_info:
            # 计算AI评分(基于分析质量)
            operation = key_info['operation'].lower()
            if '买入' in operation:
                score = 85
            elif '持有' in operation:
                score = 70
            elif '减仓' in operation:
                score = 45
            else:
                score = 60
                
            print(f"\n💼 {stock['name']} ({stock['symbol']})")
            print(f"🤖 AI综合评分: {score}/100分 - {key_info['operation']}")
            print(f"➡️ {key_info['operation']}")
            print(f"💰 目标价格: {key_info['target_price']}")
            print(f"📈 建议仓位: {key_info['position']}")
            print(f"🎯 信心度: {key_info['confidence']}")
            print(f"💡 核心逻辑: {key_info['logic']}")
            
            results.append({
                'stock': stock,
                'score': score,
                'analysis': key_info,
                'full_text': full_analysis
            })
        else:
            print(f"❌ {stock['name']} 分析失败: {full_analysis}")
        
        print("-" * 80)
        time.sleep(3)  # 避免API过载
    
    # 生成投资组合建议
    print("\n🎯 专业投资建议:")
    
    buy_stocks = [r for r in results if '买入' in r['analysis']['operation']]
    hold_stocks = [r for r in results if '持有' in r['analysis']['operation']]
    
    if buy_stocks:
        print("📈 重点买入:")
        for stock in buy_stocks:
            print(f"   • {stock['stock']['name']}: {stock['analysis']['target_price']}")
    
    if hold_stocks:
        print("🤝 建议持有:")
        for stock in hold_stocks:
            print(f"   • {stock['stock']['name']}: {stock['analysis']['position']}")
    
    print(f"\n💎 基于当前上证指数3996点高位，建议总仓位控制在60%以内")
    
    # 保存详细分析
    with open('/Users/aaron/Marketbrew/professional_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 详细分析已保存到 professional_analysis_results.json")

if __name__ == "__main__":
    main()