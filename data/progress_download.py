#!/usr/bin/env python3
"""
带进度显示的A股数据下载器
"""

import os
import sys
import time
import json
from datetime import datetime
from get_daily_price import all_hs300_symbols, get_daily_price

def get_current_progress():
    """获取当前下载进度"""
    import glob
    existing_files = glob.glob('./daily_prices_[0-9]*.json')
    existing_symbols = [f.split('_')[-1].replace('.json', '') for f in existing_files]
    return len(existing_symbols), existing_symbols

def save_progress_log(completed, total, current_symbol=""):
    """保存进度日志"""
    progress = {
        "timestamp": datetime.now().isoformat(),
        "completed": completed,
        "total": total,
        "percentage": round(completed/total*100, 2),
        "current_symbol": current_symbol
    }
    
    with open('download_progress.json', 'w') as f:
        json.dump(progress, f, indent=2)

def download_with_progress():
    """带进度显示的下载"""
    print("🚀 启动A股数据下载器")
    print(f"📊 目标: {len(all_hs300_symbols)} 只股票")
    
    while True:
        completed, existing_symbols = get_current_progress()
        remaining = [s for s in all_hs300_symbols if s not in existing_symbols]
        
        if not remaining:
            print("🎉 所有股票数据下载完成！")
            save_progress_log(completed, len(all_hs300_symbols), "完成")
            break
        
        print(f"\n📈 当前进度: {completed}/{len(all_hs300_symbols)} ({completed/len(all_hs300_symbols)*100:.1f}%)")
        print(f"⏳ 剩余: {len(remaining)} 只股票")
        
        # 下载接下来的10只股票
        batch = remaining[:10]
        print(f"🔄 下载批次: {batch}")
        
        for symbol in batch:
            try:
                print(f"  📥 获取 {symbol}...")
                get_daily_price(symbol)
                save_progress_log(completed + batch.index(symbol) + 1, len(all_hs300_symbols), symbol)
                time.sleep(0.3)  # 避免请求过快
            except Exception as e:
                print(f"  ❌ {symbol} 失败: {e}")
                continue
        
        # 更新进度
        completed, _ = get_current_progress()
        print(f"✅ 批次完成，总进度: {completed}/{len(all_hs300_symbols)}")
        
        if completed < len(all_hs300_symbols):
            print("⏳ 休息10秒后继续...")
            time.sleep(10)

if __name__ == "__main__":
    download_with_progress()