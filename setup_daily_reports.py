#!/usr/bin/env python3
"""
设置每日定时日报系统
"""

import schedule
import time
import subprocess
from datetime import datetime
from daily_report_generator import DailyReportGenerator

def run_daily_report():
    """执行每日日报生成"""
    try:
        print(f"\n🌅 开始生成每日AI交易日报 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        generator = DailyReportGenerator()
        report_file = generator.generate_daily_report()
        
        print(f"✅ 每日日报生成完成: {report_file}")
        
    except Exception as e:
        print(f"❌ 每日日报生成失败: {e}")

def setup_schedule():
    """设置定时任务"""
    # 每天晚上8点生成日报
    schedule.every().day.at("20:00").do(run_daily_report)
    
    print("⏰ 每日AI交易日报定时系统已启动")
    print("📅 执行时间: 每天20:00")
    print("📊 分析范围: 30只代表性样本股票")
    print("📄 报告位置: ./daily_reports/")
    print("🛑 按Ctrl+C停止")
    print("=" * 50)
    
    # 立即生成一次日报
    print("🔥 立即生成今日日报...")
    run_daily_report()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
            
            # 显示下次执行时间
            next_run = schedule.next_run()
            if next_run:
                print(f"⏳ 下次日报生成: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            
        except KeyboardInterrupt:
            print("\n👋 每日日报定时系统已停止")
            break

if __name__ == "__main__":
    setup_schedule()