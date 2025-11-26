#!/usr/bin/env python3
"""
分批获取A股数据 - 避免长时间运行导致超时
"""

import os
import sys
import time
from get_daily_price import all_hs300_symbols, get_daily_price, existing_symbols

def batch_download(batch_size=20):
    """分批下载股票数据"""
    need_download = [symbol for symbol in all_hs300_symbols if symbol not in existing_symbols]
    
    print(f"需要下载 {len(need_download)} 只股票数据")
    print(f"分批大小: {batch_size} 只/批")
    
    # 分批处理
    for batch_num in range(0, len(need_download), batch_size):
        batch = need_download[batch_num:batch_num + batch_size]
        
        print(f"\n🔄 处理第 {batch_num//batch_size + 1} 批 ({len(batch)} 只股票)")
        print(f"批次范围: {batch[0]} - {batch[-1]}")
        
        for i, symbol in enumerate(batch, 1):
            print(f"  进度: {i}/{len(batch)} - 获取 {symbol}")
            try:
                get_daily_price(symbol)
                time.sleep(0.2)  # 增加延迟避免过于频繁
            except Exception as e:
                print(f"  ❌ 获取 {symbol} 失败: {e}")
                continue
        
        print(f"✅ 第 {batch_num//batch_size + 1} 批完成")
        
        # 检查当前总数
        import glob
        current_files = glob.glob('./daily_prices_[0-9]*.json')
        print(f"📊 当前总共有 {len(current_files)} 只股票数据")
        
        # 批次间休息
        if batch_num + batch_size < len(need_download):
            print("⏳ 休息5秒...")
            time.sleep(5)

if __name__ == "__main__":
    print("🚀 开始分批获取A股数据")
    batch_download(batch_size=30)
    print("🎉 分批下载完成！")