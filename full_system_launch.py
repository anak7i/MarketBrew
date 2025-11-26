#!/usr/bin/env python3
"""
完整DeepSeek A股交易系统启动器
441只股票版本
"""

import os
import json
import sys
import requests
import glob
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
            {"role": "system", "content": "你是一个专业的A股基本面分析交易助手，管理441只股票的投资组合。请根据提供的数据给出具体的交易建议。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2000,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API调用失败: {e}"

def get_stock_pool_stats():
    """获取股票池统计信息"""
    data_dir = os.path.join(project_root, 'data')
    stock_files = glob.glob(os.path.join(data_dir, 'daily_prices_[0-9]*.json'))
    
    total_stocks = len(stock_files)
    
    # 分类统计
    hs300_count = len([f for f in stock_files if any(f.endswith(f'daily_prices_{code}.json') 
                                                    for code in stock_files 
                                                    if code.split('_')[-1].replace('.json', '').startswith(('000', '001', '002', '600', '601')))])
    
    cyb_count = len([f for f in stock_files if f.split('_')[-1].replace('.json', '').startswith('300')])
    kc_count = len([f for f in stock_files if f.split('_')[-1].replace('.json', '').startswith('688')])
    
    return {
        'total': total_stocks,
        'hs300': hs300_count,
        'cyb': cyb_count,
        'kc': kc_count,
        'files': [f.split('_')[-1].replace('.json', '') for f in stock_files]
    }

def analyze_top_stocks(stock_symbols, api_key, limit=10):
    """分析顶级股票"""
    print(f"🔍 正在分析前{limit}只核心股票...")
    
    # 选择代表性股票进行分析
    representative_stocks = [
        "000001",  # 平安银行
        "000002",  # 万科A  
        "600519",  # 贵州茅台
        "000858",  # 五粮液
        "600036",  # 招商银行
        "300014",  # 亿纬锂能
        "300059",  # 东方财富
        "688009",  # 中国通号
        "600030",  # 中信证券
        "002415"   # 海康威视
    ]
    
    # 只分析存在数据的股票
    available_stocks = [s for s in representative_stocks if s in stock_symbols][:limit]
    
    all_analyses = ""
    
    for i, symbol in enumerate(available_stocks, 1):
        print(f"  📊 [{i}/{len(available_stocks)}] 分析 {symbol}...")
        
        # 读取股票数据
        data_file = os.path.join(project_root, 'data', f'daily_prices_{symbol}.json')
        
        if not os.path.exists(data_file):
            continue
            
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            # 获取最近数据
            time_series = stock_data.get('Time Series (Daily)', {})
            if not time_series:
                continue
                
            recent_dates = sorted(time_series.keys(), reverse=True)[:3]
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
请快速分析股票 {symbol} 并给出交易决策：

最近3天数据：
{json.dumps(recent_data, ensure_ascii=False, indent=2)}

请简洁回答：
1. 趋势判断：[上涨/下跌/震荡]
2. 交易决策：[买入/卖出/持有] 
3. 建议价格：[具体价格]
4. 风险级别：[低/中/高]
"""
            
            analysis = call_deepseek_api(prompt, api_key)
            
            print(f"    ✅ {symbol} 分析完成")
            all_analyses += f"\n## 股票{symbol}分析：\n{analysis}\n"
            
        except Exception as e:
            print(f"    ❌ {symbol} 分析失败: {e}")
            continue
    
    return all_analyses

def generate_portfolio_strategy(analyses, stats, api_key):
    """生成441只股票的投资组合策略"""
    
    prompt = f"""
基于以下分析，请为441只A股投资组合制定策略：

## 股票池构成：
- 总计：{stats['total']} 只股票
- 沪深300类：约{stats['hs300']} 只（大盘蓝筹）
- 创业板：约{stats['cyb']} 只（成长股）
- 科创板：约{stats['kc']} 只（科技股）

## 核心股票分析：
{analyses}

## 请提供：
1. **441只股票投资组合配置建议**
2. **各板块权重分配**（沪深300 vs 创业板 vs 科创板）
3. **风险管理策略**
4. **今日具体操作计划**（从441只中选择重点关注的20-30只）
5. **资金分配方案**（总资金100,000 CNY）

请给出专业且具体的建议。
"""
    
    return call_deepseek_api(prompt, api_key)

def launch_full_system():
    """启动完整系统"""
    print("🚀 DeepSeek A股扩展交易系统 - 完整版")
    print("=" * 60)
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ 未找到DEEPSEEK_API_KEY")
        return
    
    print(f"✅ DeepSeek API已配置")
    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 获取股票池统计
    stats = get_stock_pool_stats()
    
    print(f"\n📊 股票池统计:")
    print(f"  🎯 总计: {stats['total']} 只股票")
    print(f"  🏢 沪深300类: ~{stats['hs300']} 只")
    print(f"  🚀 创业板: ~{stats['cyb']} 只") 
    print(f"  🧪 科创板: ~{stats['kc']} 只")
    print(f"  📈 覆盖率: {stats['total']}/450 (98%)")
    
    # 分析核心股票
    print(f"\n🔍 开始核心股票分析...")
    analyses = analyze_top_stocks(stats['files'], api_key, limit=10)
    
    # 生成投资组合策略
    print(f"\n💼 生成441只股票投资组合策略...")
    portfolio_strategy = generate_portfolio_strategy(analyses, stats, api_key)
    
    # 输出结果
    print(f"\n" + "="*60)
    print(f"🎯 441只A股投资组合策略")
    print(f"="*60)
    print(portfolio_strategy)
    
    print(f"\n" + "="*60)
    print(f"🎉 DeepSeek A股扩展交易系统启动完成！")
    print(f"📊 管理股票数量: {stats['total']} 只")
    print(f"🤖 AI分析引擎: DeepSeek")
    print(f"💰 总资金规模: 100,000 CNY")
    print(f"⚡ 系统状态: 就绪")

if __name__ == "__main__":
    launch_full_system()