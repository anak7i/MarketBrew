#!/usr/bin/env python3
"""
快速测试分析器 - 只分析少量股票验证系统
"""

import os
import json
import glob
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from update_trading_log import update_trading_log_page

class QuickTestAnalyzer:
    def __init__(self):
        self.api_key = "sk-2700d9ebbb4c4374a8f697ae759d06fb"
        self.data_dir = "./data"
        
    def call_deepseek_api(self, prompt):
        """调用DeepSeek API"""
        import requests
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是专业的A股分析师，给出简洁明确的分析。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def analyze_single_stock(self, symbol):
        """分析单只股票"""
        try:
            print(f"🔍 分析 {symbol}...")
            
            # 读取股票数据
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            if not os.path.exists(data_file):
                return symbol, {'error': '数据文件不存在'}
            
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            # 获取股票名称
            stock_names = {
                '000001': '平安银行', '000002': '万科A', '600519': '贵州茅台',
                '300750': '宁德时代', '600036': '招商银行', '000858': '五粮液',
                '002594': '比亚迪', '000568': '泸州老窖', '002415': '海康威视',
                '000895': '双汇发展', '300059': '东方财富', '601318': '中国平安'
            }
            stock_name = stock_names.get(symbol, f'股票{symbol}')
            
            # 获取最新数据
            time_series = stock_data.get('Time Series (Daily)', {})
            if not time_series:
                return symbol, {'error': '无交易数据'}
            
            recent_dates = sorted(time_series.keys(), reverse=True)[:1]
            latest_data = time_series[recent_dates[0]]
            
            # 极简分析提示词
            prompt = f"""
股票{symbol}({stock_name})
价格:{latest_data.get('4. sell price')} 成交量:{latest_data.get('5. volume')}

给出交易建议，格式：
操作:[买入/卖出/持有]
理由:[一句话说明原因]
"""
            
            # 调用AI分析
            analysis = self.call_deepseek_api(prompt)
            
            result = {
                'symbol': symbol,
                'name': stock_name,
                'analysis': analysis,
                'price': latest_data.get('4. sell price'),
                'volume': latest_data.get('5. volume'),
                'date': recent_dates[0],
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ {symbol} 分析完成: {analysis}")
            return symbol, result
            
        except Exception as e:
            print(f"❌ {symbol} 分析失败: {e}")
            return symbol, {'error': str(e)}
    
    def quick_test(self):
        """快速测试分析"""
        print(f"\n🚀 快速测试AI分析系统 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 测试股票列表（选择有代表性的10只）
        test_stocks = ['000001', '000002', '600519', '300750', '600036', '000858', 
                      '002594', '000568', '002415', '300059']
        
        print(f"📊 测试股票: {len(test_stocks)}只")
        print("📍 测试股票列表:", ', '.join(test_stocks))
        print()
        
        results = {}
        
        # 并发分析
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_single_stock, symbol): symbol 
                for symbol in test_stocks
            }
            
            for future in as_completed(future_to_symbol):
                symbol, result = future.result()
                results[symbol] = result
        
        # 统计结果
        successful = sum(1 for r in results.values() if 'error' not in r)
        failed = len(results) - successful
        
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        print(f"\n📊 分析结果统计:")
        print("=" * 40)
        
        for symbol, data in results.items():
            if 'error' in data:
                print(f"❌ {symbol}: {data['error']}")
                continue
            
            analysis = data.get('analysis', '').lower()
            if '买入' in analysis:
                buy_count += 1
                print(f"📈 {symbol} {data['name']}: 买入建议")
            elif '卖出' in analysis:
                sell_count += 1
                print(f"📉 {symbol} {data['name']}: 卖出建议")
            else:
                hold_count += 1
                print(f"📊 {symbol} {data['name']}: 持有观望")
        
        print(f"\n📈 操作统计:")
        print(f"  • 成功分析: {successful}/{len(test_stocks)}")
        print(f"  • 买入建议: {buy_count}")
        print(f"  • 卖出建议: {sell_count}")
        print(f"  • 持有观望: {hold_count}")
        
        # 更新交易记录页面
        try:
            print(f"\n📋 更新交易记录页面...")
            update_trading_log_page(results)
            print("✅ 交易记录页面更新完成!")
            print("🌐 可通过以下方式查看:")
            print("   • 直接打开: /Users/aaron/AI-Trader/trading_log.html")
            print("   • 或访问主界面的'📋 交易日志'")
        except Exception as e:
            print(f"❌ 交易记录页面更新失败: {e}")
        
        print(f"\n🎉 快速测试完成!")
        return results

def main():
    analyzer = QuickTestAnalyzer()
    analyzer.quick_test()

if __name__ == "__main__":
    main()