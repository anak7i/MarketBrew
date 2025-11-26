#!/usr/bin/env python3
"""
智能监控和下载管理器
"""

import os
import time
import glob
from datetime import datetime, timedelta

def smart_monitor():
    """智能监控下载进度"""
    print("🤖 智能下载监控器启动")
    print("=" * 50)
    
    last_count = 0
    stall_time = None
    check_interval = 30  # 30秒检查一次
    
    while True:
        # 检查当前进度
        os.chdir('/Users/aaron/AI-Trader/data')
        current_files = glob.glob('daily_prices_[0-9]*.json')
        current_count = len(current_files)
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        percentage = current_count / 450 * 100
        
        # 进度条
        bar_length = 40
        filled = int(bar_length * current_count / 450)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\n🕒 {timestamp}")
        print(f"📊 进度: {current_count}/450 ({percentage:.1f}%)")
        print(f"📈 [{bar}]")
        
        # 检查是否有新增数据
        if current_count > last_count:
            new_files = current_count - last_count
            print(f"🆕 新增 {new_files} 只股票数据")
            last_count = current_count
            stall_time = None
        else:
            if stall_time is None:
                stall_time = datetime.now()
            else:
                stall_duration = datetime.now() - stall_time
                print(f"⏸️ 已停滞 {stall_duration.seconds//60} 分钟")
        
        # 完成检查
        if current_count >= 450:
            print("🎉 所有数据下载完成！")
            break
        
        # 估算完成时间
        if current_count > 0:
            # 基于当前进度估算
            elapsed_time = datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)
            estimated_total_time = elapsed_time * 450 / current_count
            remaining_time = estimated_total_time - elapsed_time
            
            if remaining_time.total_seconds() > 0:
                hours = int(remaining_time.total_seconds() // 3600)
                minutes = int((remaining_time.total_seconds() % 3600) // 60)
                print(f"⏱️ 预计完成时间: {hours}小时{minutes}分钟后")
        
        # 显示最新文件
        if current_files:
            latest_file = max(current_files, key=os.path.getmtime)
            latest_symbol = latest_file.split('_')[-1].replace('.json', '')
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
            print(f"📁 最新: {latest_symbol} ({mod_time.strftime('%H:%M:%S')})")
        
        print(f"⏳ 等待 {check_interval} 秒后重新检查...")
        time.sleep(check_interval)

if __name__ == "__main__":
    try:
        smart_monitor()
    except KeyboardInterrupt:
        print("\n👋 监控器已停止")