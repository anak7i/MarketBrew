#!/usr/bin/env python3
"""
简化的A股交易系统启动脚本
不依赖MCP，直接使用DeepSeek API进行股票分析
"""

import os
import json
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Add project path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import local modules
from data.get_daily_price import all_hs300_symbols
from tools.price_tools import get_yesterday_date, get_open_prices, get_yesterday_open_and_close_price

def print_banner():
    """打印系统启动横幅"""
    print("=" * 50)
    print("🚀 DeepSeek A股扩展交易系统")
    print(f"📊 股票池: {len(all_hs300_symbols)} 只 A股")
    print("🤖 AI模型: DeepSeek")
    print("=" * 50)

def check_environment():
    """检查环境配置"""
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ 未找到DEEPSEEK_API_KEY环境变量")
        print("请在.env文件中配置你的DeepSeek API密钥")
        return False
    
    print(f"✅ DeepSeek API密钥已配置: {api_key[:10]}...")
    return True

def check_data_availability():
    """检查股票数据可用性"""
    data_dir = os.path.join(project_root, 'data')
    stock_files = []
    
    for symbol in all_hs300_symbols:
        file_path = os.path.join(data_dir, f'daily_prices_{symbol}.json')
        if os.path.exists(file_path):
            stock_files.append(symbol)
    
    print(f"📊 发现 {len(stock_files)} 只股票数据文件")
    print(f"💼 可交易股票: {stock_files[:10]}..." if len(stock_files) > 10 else f"💼 可交易股票: {stock_files}")
    
    return stock_files

def simple_stock_analysis():
    """简化的股票分析"""
    print("\n📈 开始股票分析...")
    
    # 获取今日日期
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"📅 交易日期: {today}")
    
    # 检查数据文件
    available_stocks = check_data_availability()
    
    if not available_stocks:
        print("❌ 未找到可用的股票数据")
        return
    
    # 简单分析前5只股票
    print("\n🔍 分析前5只股票:")
    for i, symbol in enumerate(available_stocks[:5]):
        print(f"{i+1}. 股票代码: {symbol}")
        
        # 读取股票数据
        data_file = os.path.join(project_root, 'data', f'daily_prices_{symbol}.json')
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 获取最新价格信息
            time_series = data.get('Time Series (Daily)', {})
            if time_series:
                latest_date = max(time_series.keys())
                latest_data = time_series[latest_date]
                
                buy_price = latest_data.get('1. buy price', 'N/A')
                sell_price = latest_data.get('4. sell price', 'N/A')
                volume = latest_data.get('5. volume', 'N/A')
                
                print(f"   📊 最新交易日: {latest_date}")
                print(f"   💰 开盘价: {buy_price}")
                print(f"   💰 收盘价: {sell_price}")
                print(f"   📦 成交量: {volume}")
            else:
                print(f"   ❌ 无数据")
                
        except Exception as e:
            print(f"   ❌ 读取数据失败: {e}")
        
        print()

def main():
    """主函数"""
    print_banner()
    
    # 检查环境
    if not check_environment():
        return
    
    print("\n🔧 系统状态检查:")
    print("✅ 环境配置正常")
    
    # 进行简化的股票分析
    simple_stock_analysis()
    
    print("\n🎉 DeepSeek A股交易系统分析完成!")
    print("💡 这是一个简化版本，展示了系统的基本功能")
    print("📝 要完整运行需要解决MCP依赖问题")

if __name__ == "__main__":
    main()