#!/usr/bin/env python3
"""
AI定时分析调度器
定期运行DeepSeek AI分析并保存结果
"""

import os
import time
import json
import schedule
from datetime import datetime, timedelta
from deepseek_trading import analyze_stock_with_ai, get_portfolio_suggestion

class AIScheduler:
    def __init__(self):
        self.api_key = "sk-2700d9ebbb4c4374a8f697ae759d06fb"
        self.data_dir = "./data"
        self.log_dir = "./ai_logs"
        
        # 创建日志目录
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def analyze_and_log(self):
        """执行AI分析并记录结果"""
        print(f"\n🤖 AI定时分析开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 分析的股票列表
        stock_symbols = ['000001', '000002', '300750', '600519', '600036', '000858']
        analysis_results = {}
        
        for symbol in stock_symbols:
            try:
                print(f"🔍 分析股票 {symbol}...")
                
                # 读取股票数据
                data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
                if not os.path.exists(data_file):
                    print(f"❌ 未找到 {symbol} 数据文件")
                    continue
                
                with open(data_file, 'r', encoding='utf-8') as f:
                    stock_data = json.load(f)
                
                # AI分析
                analysis = analyze_stock_with_ai(symbol, stock_data, self.api_key)
                analysis_results[symbol] = {
                    'timestamp': datetime.now().isoformat(),
                    'analysis': analysis,
                    'data_updated': stock_data.get('Meta Data', {}).get('3. Last Refreshed')
                }
                
                print(f"✅ {symbol} 分析完成")
                
            except Exception as e:
                print(f"❌ 分析 {symbol} 失败: {e}")
                analysis_results[symbol] = {
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }
        
        # 生成投资组合建议
        try:
            print("💼 生成投资组合建议...")
            all_analyses = ""
            for symbol, result in analysis_results.items():
                if 'analysis' in result:
                    all_analyses += f"股票{symbol}: {result['analysis']}\n\n"
            
            portfolio_advice = get_portfolio_suggestion(all_analyses, self.api_key)
            analysis_results['portfolio'] = {
                'timestamp': datetime.now().isoformat(),
                'advice': portfolio_advice
            }
            print("✅ 投资组合建议生成完成")
            
        except Exception as e:
            print(f"❌ 投资组合建议生成失败: {e}")
            analysis_results['portfolio'] = {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
        
        # 保存分析结果
        log_filename = f"ai_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_path = os.path.join(self.log_dir, log_filename)
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        print(f"📁 分析结果已保存: {log_path}")
        print(f"🎉 AI定时分析完成 - {datetime.now().strftime('%H:%M:%S')}")
        
        # 更新最新分析文件
        latest_path = os.path.join(self.log_dir, "latest_analysis.json")
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        return analysis_results
    
    def setup_schedule(self, interval_minutes=30):
        """设置分析计划"""
        print(f"⏰ 设置AI分析计划: 每{interval_minutes}分钟执行一次")
        schedule.every(interval_minutes).minutes.do(self.analyze_and_log)
        
        # 设置交易时间段分析（更频繁）
        schedule.every().monday.at("09:30").do(self.analyze_and_log)    # 开盘
        schedule.every().monday.at("11:30").do(self.analyze_and_log)    # 上午收盘
        schedule.every().monday.at("13:00").do(self.analyze_and_log)    # 下午开盘
        schedule.every().monday.at("15:00").do(self.analyze_and_log)    # 收盘
        
        schedule.every().tuesday.at("09:30").do(self.analyze_and_log)
        schedule.every().tuesday.at("11:30").do(self.analyze_and_log)
        schedule.every().tuesday.at("13:00").do(self.analyze_and_log)
        schedule.every().tuesday.at("15:00").do(self.analyze_and_log)
        
        schedule.every().wednesday.at("09:30").do(self.analyze_and_log)
        schedule.every().wednesday.at("11:30").do(self.analyze_and_log)
        schedule.every().wednesday.at("13:00").do(self.analyze_and_log)
        schedule.every().wednesday.at("15:00").do(self.analyze_and_log)
        
        schedule.every().thursday.at("09:30").do(self.analyze_and_log)
        schedule.every().thursday.at("11:30").do(self.analyze_and_log)
        schedule.every().thursday.at("13:00").do(self.analyze_and_log)
        schedule.every().thursday.at("15:00").do(self.analyze_and_log)
        
        schedule.every().friday.at("09:30").do(self.analyze_and_log)
        schedule.every().friday.at("11:30").do(self.analyze_and_log)
        schedule.every().friday.at("13:00").do(self.analyze_and_log)
        schedule.every().friday.at("15:00").do(self.analyze_and_log)
    
    def run_scheduler(self):
        """运行调度器"""
        print("🚀 AI定时分析调度器启动")
        print("📍 监控股票: 000001, 000002, 300750, 600519, 600036, 000858")
        print("⏰ 分析频率: 每30分钟 + 交易时间关键节点")
        print("📁 结果保存: ./ai_logs/")
        print("🛑 按Ctrl+C停止")
        print("=" * 60)
        
        # 立即执行一次分析
        print("🔥 立即执行首次分析...")
        self.analyze_and_log()
        
        # 开始调度循环
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
                # 显示下次执行时间
                next_run = schedule.next_run()
                if next_run:
                    now = datetime.now()
                    wait_time = next_run - now
                    hours = int(wait_time.total_seconds() // 3600)
                    minutes = int((wait_time.total_seconds() % 3600) // 60)
                    print(f"⏳ 下次分析: {next_run.strftime('%H:%M:%S')} (还有{hours}h{minutes}m)")
                
            except KeyboardInterrupt:
                print("\n👋 AI调度器已停止")
                break
            except Exception as e:
                print(f"❌ 调度器异常: {e}")
                time.sleep(300)  # 出错后等待5分钟重试

def main():
    """主函数"""
    scheduler = AIScheduler()
    
    print("🤖 DeepSeek AI定时分析系统")
    print("=" * 50)
    print("请选择运行模式:")
    print("1. 立即分析一次")
    print("2. 启动定时调度器(每30分钟)")
    print("3. 启动定时调度器(每15分钟)")
    print("4. 启动定时调度器(每60分钟)")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        scheduler.analyze_and_log()
    elif choice == "2":
        scheduler.setup_schedule(30)
        scheduler.run_scheduler()
    elif choice == "3":
        scheduler.setup_schedule(15)
        scheduler.run_scheduler()
    elif choice == "4":
        scheduler.setup_schedule(60)
        scheduler.run_scheduler()
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()