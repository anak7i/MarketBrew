#!/usr/bin/env python3
"""
快速数据下载器 - 使用腾讯财经API
"""

import requests
import json
import concurrent.futures
import time
from datetime import datetime, timedelta
import glob
from get_daily_price import all_hs300_symbols

def get_stock_data_qq(symbol):
    """使用腾讯财经API快速获取股票数据"""
    try:
        # 腾讯财经API - 速度更快
        market_prefix = "sz" if symbol.startswith(('000', '002', '300')) else "sh"
        url = f"http://qt.gtimg.cn/q={market_prefix}{symbol}"
        
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return None
            
        # 解析数据
        data_str = response.text.strip()
        if not data_str:
            return None
            
        # 简单的数据解析
        parts = data_str.split('~')
        if len(parts) < 50:  # 腾讯API返回约50个字段
            return None
            
        # 构造与原格式兼容的数据
        stock_data = {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": symbol,
                "3. Last Refreshed": datetime.now().strftime('%Y-%m-%d'),
                "4. Output Size": "Compact",
                "5. Time Zone": "Asia/Shanghai"
            },
            "Time Series (Daily)": {
                datetime.now().strftime('%Y-%m-%d'): {
                    "1. buy price": parts[5],  # 今开
                    "2. high": parts[33],      # 最高
                    "3. low": parts[34],       # 最低
                    "4. sell price": parts[3], # 现价
                    "5. volume": parts[6]      # 成交量
                }
            }
        }
        
        return stock_data
        
    except Exception as e:
        print(f"获取 {symbol} 失败: {e}")
        return None

def save_stock_data(symbol, data):
    """保存股票数据"""
    if not data:
        return False
        
    try:
        filename = f'daily_prices_{symbol}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def download_batch_fast(symbols, max_workers=10):
    """并发快速下载"""
    print(f"🚀 快速下载 {len(symbols)} 只股票")
    
    success_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_symbol = {
            executor.submit(get_stock_data_qq, symbol): symbol 
            for symbol in symbols
        }
        
        # 处理结果
        for future in concurrent.futures.as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                data = future.result()
                if data and save_stock_data(symbol, data):
                    success_count += 1
                    print(f"✅ {symbol} ({success_count}/{len(symbols)})")
                else:
                    print(f"❌ {symbol}")
            except Exception as e:
                print(f"💥 {symbol}: {e}")
    
    return success_count

def fast_download_main():
    """快速下载主程序"""
    print("⚡ 快速A股数据下载器")
    print("=" * 40)
    
    # 获取需要下载的股票
    existing_files = glob.glob('./daily_prices_[0-9]*.json')
    existing_symbols = [f.split('_')[-1].replace('.json', '') for f in existing_files]
    remaining = [s for s in all_hs300_symbols if s not in existing_symbols]
    
    print(f"📊 当前已有: {len(existing_symbols)} 只")
    print(f"📦 需要下载: {len(remaining)} 只")
    
    if not remaining:
        print("🎉 所有数据已完成！")
        return
    
    # 分批下载，每批50只
    batch_size = 50
    total_success = 0
    
    for i in range(0, len(remaining), batch_size):
        batch = remaining[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(remaining) + batch_size - 1) // batch_size
        
        print(f"\n🔄 批次 {batch_num}/{total_batches}")
        start_time = time.time()
        
        success = download_batch_fast(batch, max_workers=20)
        total_success += success
        
        elapsed = time.time() - start_time
        print(f"⏱️ 批次用时: {elapsed:.1f}s")
        print(f"📈 累计成功: {len(existing_symbols) + total_success}/{len(all_hs300_symbols)}")
        
        # 批次间短暂休息
        if i + batch_size < len(remaining):
            time.sleep(2)
    
    print(f"\n🎉 快速下载完成！")
    print(f"✅ 新增: {total_success} 只股票")

if __name__ == "__main__":
    import os
    os.chdir('/Users/aaron/AI-Trader/data')
    fast_download_main()