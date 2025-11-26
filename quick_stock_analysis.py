#!/usr/bin/env python3
"""
快速股票分析脚本
专门为用户的5只股票提供完整分析
"""

import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor

def analyze_single_stock(stock_info):
    """分析单只股票"""
    try:
        print(f"🔍 开始分析 {stock_info['name']} ({stock_info['symbol']})...")
        
        response = requests.post(
            "http://localhost:5001/api/langchain/stock-analysis",
            json={"stocks": [stock_info]},
            timeout=120  # 2分钟超时
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('results') and len(data['results']) > 0:
                result = data['results'][0]
                analysis = result.get('analysis', '')
                
                # 提取关键信息
                lines = analysis.split('\n')
                
                # 寻找投资决策部分
                decision_section = ""
                target_price = ""
                confidence = ""
                position = ""
                
                for i, line in enumerate(lines):
                    if "投资决策" in line or "## 🎯" in line:
                        # 读取后面几行
                        for j in range(i+1, min(i+10, len(lines))):
                            if "**操作建议**" in lines[j]:
                                decision_section = lines[j].replace("**操作建议**：", "").strip()
                            elif "**建议仓位**" in lines[j]:
                                position = lines[j].replace("**建议仓位**：", "").strip()
                            elif "**信心度**" in lines[j]:
                                confidence = lines[j].replace("**信心度**：", "").strip()
                    elif "**目标价格**" in line:
                        target_price = line.replace("**目标价格**：", "").strip()
                
                return {
                    'symbol': stock_info['symbol'],
                    'name': stock_info['name'],
                    'decision': decision_section,
                    'target_price': target_price,
                    'confidence': confidence,
                    'position': position,
                    'full_analysis': analysis,
                    'status': 'success'
                }
        
        return {
            'symbol': stock_info['symbol'],
            'name': stock_info['name'],
            'status': 'timeout',
            'error': 'API响应超时'
        }
        
    except Exception as e:
        return {
            'symbol': stock_info['symbol'],
            'name': stock_info['name'],
            'status': 'error',
            'error': str(e)
        }

def main():
    # 用户提供的5只股票
    stocks = [
        {"symbol": "600036", "name": "招商银行"},
        {"symbol": "601318", "name": "中国平安"},
        {"symbol": "002837", "name": "英维克"},
        {"symbol": "000977", "name": "浪潮信息"},
        {"symbol": "600030", "name": "中信证券"}
    ]
    
    print("🚀 开始批量股票分析...")
    print("=" * 60)
    
    # 逐个分析(避免并发导致超时)
    results = []
    for stock in stocks:
        result = analyze_single_stock(stock)
        results.append(result)
        
        print(f"📊 {result['name']} ({result['symbol']}):")
        if result['status'] == 'success':
            print(f"   ➡️ 操作建议: {result['decision']}")
            print(f"   💰 目标价格: {result['target_price']}")
            print(f"   📈 信心度: {result['confidence']}")
            print(f"   💼 建议仓位: {result['position']}")
            
            # AI评分计算(基于分析内容)
            if '买入' in result['decision']:
                score = 75
            elif '持有' in result['decision']:
                score = 60
            elif '减仓' in result['decision']:
                score = 40
            else:
                score = 50
                
            print(f"   🤖 AI综合评分: {score}/100分")
        else:
            print(f"   ❌ 分析失败: {result.get('error', '未知错误')}")
        
        print("-" * 60)
        time.sleep(2)  # 防止API过载
    
    # 保存详细结果
    with open('/Users/aaron/Marketbrew/stock_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("✅ 所有分析完成，详细结果已保存到 stock_analysis_results.json")

if __name__ == "__main__":
    main()