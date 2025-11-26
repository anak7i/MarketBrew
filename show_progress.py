#!/usr/bin/env python3
"""
简单的进度查看工具
"""

import glob
import os
from datetime import datetime

def show_simple_progress():
    """显示简单的下载进度"""
    os.chdir('data')
    
    # 统计数据文件
    a_stock_files = glob.glob('daily_prices_[0-9]*.json')
    us_stock_files = glob.glob('daily_prices_[A-Z]*.json')
    
    total_target = 450
    completed = len(a_stock_files)
    percentage = completed / total_target * 100
    
    print(f"🕒 {datetime.now().strftime('%H:%M:%S')}")
    print(f"📊 A股数据进度: {completed}/{total_target} ({percentage:.1f}%)")
    
    # 简单进度条
    bar_length = 40
    filled = int(bar_length * completed / total_target)
    bar = '█' * filled + '░' * (bar_length - filled)
    print(f"📈 [{bar}]")
    
    if completed >= total_target:
        print("🎉 所有A股数据下载完成！")
        return True
    else:
        remaining = total_target - completed
        print(f"⏳ 剩余: {remaining} 只股票")
        return False

if __name__ == "__main__":
    show_simple_progress()