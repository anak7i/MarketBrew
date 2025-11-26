#!/usr/bin/env python3
"""
批量AI分析器 - 高效版本
"""

import os
import json
import glob
import time
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from update_trading_log import update_trading_log_page

class BatchAIAnalyzer:
    def __init__(self):
        self.api_key = "sk-2700d9ebbb4c4374a8f697ae759d06fb"
        self.data_dir = "./data"
        self.max_workers = 3  # 降低并发数避免API限流
        self.request_delay = 1  # 请求间隔1秒
        
    def call_deepseek_api(self, prompt, retries=2):
        """调用DeepSeek API"""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "简洁分析A股，格式：操作:[买入/卖出/持有] 理由:[一句话]"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 80,
            "temperature": 0.2
        }
        
        for attempt in range(retries + 1):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=20)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == retries:
                    return f"操作:持有 理由:分析失败 {str(e)[:20]}"
                time.sleep(2)
    
    def analyze_stock(self, symbol, stock_num, total_stocks):
        """分析单只股票"""
        try:
            if stock_num % 10 == 0:  # 每10只股票报告一次进度
                progress = (stock_num / total_stocks) * 100
                print(f"📊 分析进度: {stock_num}/{total_stocks} ({progress:.1f}%)")
            
            # 读取股票数据
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            if not os.path.exists(data_file):
                return symbol, {'error': '无数据文件', 'timestamp': datetime.now().isoformat()}
            
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            time_series = stock_data.get('Time Series (Daily)', {})
            if not time_series:
                return symbol, {'error': '无交易数据', 'timestamp': datetime.now().isoformat()}
            
            # 获取最新数据
            latest_date = max(time_series.keys())
            latest_data = time_series[latest_date]
            
            # 极简提示词
            price = latest_data.get('4. sell price', '0')
            volume = latest_data.get('5. volume', '0')
            
            prompt = f"股票{symbol} 价格{price} 成交量{volume} 分析:"
            
            # 请求间隔
            time.sleep(self.request_delay)
            
            # AI分析
            analysis = self.call_deepseek_api(prompt)
            
            return symbol, {
                'analysis': analysis,
                'price': price,
                'volume': volume,
                'date': latest_date,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return symbol, {'error': str(e), 'timestamp': datetime.now().isoformat()}
    
    def analyze_batch(self, batch_size=50):
        """批量分析股票"""
        start_time = datetime.now()
        print(f"\n🚀 批量AI股票分析开始 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # 获取所有股票文件
        stock_files = glob.glob(os.path.join(self.data_dir, 'daily_prices_[0-9]*.json'))
        all_symbols = []
        
        for file_path in stock_files:
            filename = os.path.basename(file_path)
            symbol = filename.replace('daily_prices_', '').replace('.json', '')
            all_symbols.append(symbol)
        
        all_symbols.sort()
        total_stocks = len(all_symbols)
        
        print(f"📊 发现 {total_stocks} 只股票")
        print(f"🎯 分析前 {batch_size} 只股票")
        print(f"⚡ 并发设置: {self.max_workers} 线程")
        print(f"⏱️ 请求间隔: {self.request_delay} 秒")
        print()
        
        # 只分析前batch_size只股票
        symbols_to_analyze = all_symbols[:batch_size]
        results = {}
        
        # 使用线程池分析
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_stock, symbol, i+1, len(symbols_to_analyze)): symbol 
                for i, symbol in enumerate(symbols_to_analyze)
            }
            
            for future in as_completed(future_to_symbol):
                symbol, result = future.result()
                results[symbol] = result
        
        # 统计结果
        successful = sum(1 for r in results.values() if 'error' not in r)
        failed = len(results) - successful
        
        buy_signals = []
        sell_signals = []
        hold_signals = []
        
        print(f"\n📈 分析结果统计:")
        print("=" * 50)
        
        for symbol, data in results.items():
            if 'error' in data:
                print(f"❌ {symbol}: {data['error']}")
                continue
            
            analysis = data.get('analysis', '').lower()
            if '买入' in analysis:
                buy_signals.append((symbol, data))
                print(f"🟢 {symbol}: 买入信号 - {data['analysis']}")
            elif '卖出' in analysis:
                sell_signals.append((symbol, data))
                print(f"🔴 {symbol}: 卖出信号 - {data['analysis']}")
            else:
                hold_signals.append((symbol, data))
        
        print(f"\n📊 操作统计:")
        print(f"  • 分析成功: {successful}/{len(symbols_to_analyze)}")
        print(f"  • 买入信号: {len(buy_signals)}")
        print(f"  • 卖出信号: {len(sell_signals)}")
        print(f"  • 持有观望: {len(hold_signals)}")
        
        # 显示所有买入卖出信号
        if buy_signals or sell_signals:
            print(f"\n🎯 重要交易信号:")
            print("=" * 40)
            for symbol, data in buy_signals + sell_signals:
                action = "买入" if "买入" in data['analysis'] else "卖出"
                print(f"📍 {symbol} ({action}): {data['analysis']}")
        
        # 更新交易记录页面
        try:
            print(f"\n📋 更新交易记录页面...")
            update_trading_log_page(results)
            print("✅ 交易记录页面更新完成!")
        except Exception as e:
            print(f"❌ 交易记录页面更新失败: {e}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 批量分析完成!")
        print(f"⏱️ 耗时: {duration}")
        print(f"⚡ 平均每只: {duration.total_seconds()/len(symbols_to_analyze):.1f}秒")
        
        return results

def main():
    analyzer = BatchAIAnalyzer()
    
    print("🤖 DeepSeek批量AI股票分析器")
    print("=" * 40)
    print("选择分析规模:")
    print("1. 分析前20只股票 (快速测试)")
    print("2. 分析前50只股票 (小批量)")
    print("3. 分析前100只股票 (中批量)")
    print("4. 分析全部443只股票 (完整分析)")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        analyzer.analyze_batch(20)
    elif choice == "2":
        analyzer.analyze_batch(50)
    elif choice == "3":
        analyzer.analyze_batch(100)
    elif choice == "4":
        analyzer.analyze_batch(443)
    else:
        print("❌ 无效选择，默认分析20只")
        analyzer.analyze_batch(20)

if __name__ == "__main__":
    main()