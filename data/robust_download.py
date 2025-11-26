#!/usr/bin/env python3
"""
稳定的A股数据下载器 - 带错误重试和网络优化
"""

import os
import sys
import time
import random
import glob
from datetime import datetime
from get_daily_price import all_hs300_symbols, get_daily_price_akshare

def get_remaining_symbols():
    """获取还未下载的股票代码"""
    existing_files = glob.glob('./daily_prices_[0-9]*.json')
    existing_symbols = [f.split('_')[-1].replace('.json', '') for f in existing_files]
    remaining = [s for s in all_hs300_symbols if s not in existing_symbols]
    return remaining, len(existing_symbols)

def download_with_retry(symbol, max_retries=3):
    """带重试机制的下载"""
    for attempt in range(max_retries):
        try:
            print(f"  📥 获取 {symbol} (尝试 {attempt + 1}/{max_retries})")
            get_daily_price_akshare(symbol)
            return True
        except Exception as e:
            print(f"    ❌ 失败: {str(e)[:100]}...")
            if attempt < max_retries - 1:
                wait_time = random.uniform(2, 5)  # 随机等待2-5秒
                print(f"    ⏳ 等待 {wait_time:.1f}s 后重试...")
                time.sleep(wait_time)
            else:
                print(f"    💥 {symbol} 下载失败，跳过")
                return False

def batch_download_robust():
    """稳定的批量下载"""
    print("🚀 启动稳定下载器")
    batch_size = 5  # 减小批次大小，提高稳定性
    
    while True:
        remaining, completed = get_remaining_symbols()
        
        if not remaining:
            print("🎉 所有股票数据下载完成！")
            break
            
        total = len(all_hs300_symbols)
        percentage = completed / total * 100
        
        print(f"\n📊 当前进度: {completed}/{total} ({percentage:.1f}%)")
        print(f"⏳ 剩余: {len(remaining)} 只股票")
        
        # 取下一批
        batch = remaining[:batch_size]
        print(f"🔄 处理批次: {batch}")
        
        success_count = 0
        for symbol in batch:
            if download_with_retry(symbol):
                success_count += 1
            
            # 随机延迟，避免请求过于规律
            delay = random.uniform(0.5, 1.5)
            time.sleep(delay)
        
        print(f"✅ 批次完成，成功: {success_count}/{len(batch)}")
        
        # 检查是否还有剩余
        remaining, completed = get_remaining_symbols()
        if remaining:
            wait_time = random.uniform(10, 20)  # 批次间随机等待
            print(f"⏳ 休息 {wait_time:.1f}s 后继续...")
            time.sleep(wait_time)

if __name__ == "__main__":
    os.chdir('/Users/aaron/AI-Trader/data')
    batch_download_robust()