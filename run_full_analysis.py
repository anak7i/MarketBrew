#!/usr/bin/env python3
"""
直接运行全量分析
"""

from daily_full_analyzer import DailyFullAnalyzer

def main():
    print("🚀 启动全量442只股票AI分析...")
    analyzer = DailyFullAnalyzer()
    analyzer.daily_analysis()

if __name__ == "__main__":
    main()