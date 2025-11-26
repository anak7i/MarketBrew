#!/usr/bin/env python3
"""
检查下载进度的工具
"""

import json
import glob
import os
from datetime import datetime
from get_daily_price import all_hs300_symbols

def check_progress():
    """检查当前下载进度"""
    print("📊 A股数据下载进度检查")
    print("=" * 50)
    
    # 检查数据文件
    existing_files = glob.glob('./daily_prices_[0-9]*.json')
    completed = len(existing_files)
    total = len(all_hs300_symbols)
    percentage = completed / total * 100
    
    print(f"📈 总体进度: {completed}/{total} ({percentage:.1f}%)")
    
    # 检查进度日志
    if os.path.exists('download_progress.json'):
        try:
            with open('download_progress.json', 'r') as f:
                progress = json.load(f)
            
            print(f"⏰ 最后更新: {progress['timestamp']}")
            print(f"📍 当前处理: {progress.get('current_symbol', 'N/A')}")
        except:
            print("⚠️ 无法读取进度日志")
    
    # 分类统计
    hs300_count = len([f for f in existing_files if f.split('_')[-1].replace('.json', '').startswith(('000', '001', '002', '600', '601'))])
    cyb_count = len([f for f in existing_files if f.split('_')[-1].replace('.json', '').startswith('300')])
    kc_count = len([f for f in existing_files if f.split('_')[-1].replace('.json', '').startswith('688')])
    
    print(f"\n📋 分类统计:")
    print(f"  🏢 沪深300类: {hs300_count} 只")
    print(f"  🚀 创业板类: {cyb_count} 只") 
    print(f"  🧪 科创板类: {kc_count} 只")
    
    # 进度条
    bar_length = 30
    filled_length = int(bar_length * completed / total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    print(f"\n📊 进度条: [{bar}] {percentage:.1f}%")
    
    # 预估剩余时间
    remaining = total - completed
    if remaining > 0:
        # 假设每只股票需要4秒（包括延迟）
        estimated_seconds = remaining * 4
        estimated_minutes = estimated_seconds / 60
        print(f"⏱️ 预估剩余时间: {estimated_minutes:.1f} 分钟")
    else:
        print("🎉 下载已完成！")

if __name__ == "__main__":
    check_progress()