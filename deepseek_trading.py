#!/usr/bin/env python3
"""
DeepSeek A股交易决策系统
直接调用DeepSeek API进行股票分析和交易决策
"""

import os
import json
import sys
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def call_deepseek_api(prompt, api_key):
    """调用DeepSeek API"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的A股基本面分析交易助手。请根据提供的股票数据给出具体的交易建议。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API调用失败: {e}"

def analyze_stock_with_ai(symbol, stock_data, api_key):
    """使用AI分析单只股票并给出决策"""
    
    # 获取最近5天的数据
    time_series = stock_data.get('Time Series (Daily)', {})
    recent_dates = sorted(time_series.keys(), reverse=True)[:5]
    
    recent_data = []
    for date in recent_dates:
        data = time_series[date]
        recent_data.append({
            "日期": date,
            "开盘价": data.get('1. buy price'),
            "收盘价": data.get('4. sell price'),
            "最高价": data.get('2. high'),
            "最低价": data.get('3. low'),
            "成交量": data.get('5. volume')
        })
    
    # 构建分析提示词
    prompt = f"""
请分析股票 {symbol} 的交易数据并给出具体的交易决策：

最近5天交易数据：
{json.dumps(recent_data, ensure_ascii=False, indent=2)}

请从以下角度进行分析：
1. 价格趋势分析
2. 成交量分析  
3. 技术面判断
4. 具体交易建议（买入/卖出/持有）
5. 建议交易数量和价格
6. 风险提示

请给出明确的交易决策，格式如下：
决策：[买入/卖出/持有]
理由：[分析原因]
建议价格：[具体价格]
建议数量：[股数，必须是100的倍数]
风险级别：[低/中/高]
"""
    
    return call_deepseek_api(prompt, api_key)

def get_portfolio_suggestion(stock_analyses, api_key):
    """获取投资组合建议"""
    
    prompt = f"""
基于以下个股分析结果，请给出整体投资组合建议：

{stock_analyses}

请提供：
1. 投资组合配置建议
2. 总体仓位控制
3. 风险管理策略
4. 今日具体操作计划

总资金：100,000 CNY
"""
    
    return call_deepseek_api(prompt, api_key)

def main():
    """主函数"""
    print("🤖 DeepSeek A股交易决策系统")
    print("=" * 50)
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ 未找到DEEPSEEK_API_KEY")
        return
    
    print(f"✅ API密钥已配置")
    print(f"📅 分析日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 分析前3只股票
    data_dir = os.path.join(project_root, 'data')
    stock_symbols = ['000001', '000002', '600519']  # 平安银行、万科A、贵州茅台
    
    all_analyses = ""
    
    for symbol in stock_symbols:
        print(f"🔍 正在分析股票 {symbol}...")
        
        # 读取股票数据
        data_file = os.path.join(data_dir, f'daily_prices_{symbol}.json')
        
        if not os.path.exists(data_file):
            print(f"❌ 未找到 {symbol} 的数据文件")
            continue
            
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            # AI分析
            analysis = analyze_stock_with_ai(symbol, stock_data, api_key)
            
            print(f"\n📊 股票 {symbol} AI分析结果：")
            print("-" * 40)
            print(analysis)
            print("\n" + "=" * 50 + "\n")
            
            all_analyses += f"股票{symbol}分析：\n{analysis}\n\n"
            
        except Exception as e:
            print(f"❌ 分析 {symbol} 时出错: {e}")
            continue
    
    # 生成投资组合建议
    print("💼 正在生成投资组合建议...")
    portfolio_advice = get_portfolio_suggestion(all_analyses, api_key)
    
    print("\n🎯 投资组合建议：")
    print("=" * 50)
    print(portfolio_advice)
    
    print("\n🎉 分析完成！")

if __name__ == "__main__":
    main()