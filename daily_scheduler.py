#!/usr/bin/env python3
"""
每日自动调度器 - 每天早上8:00自动执行决策分析
"""

import os
import time
import schedule
from datetime import datetime, timedelta
import logging
from unified_decision_engine import UnifiedDecisionEngine

class DailyScheduler:
    def __init__(self):
        self.engine = UnifiedDecisionEngine()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daily_scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def morning_analysis_job(self):
        """晨间分析任务"""
        self.logger.info("🌅 开始执行每日晨间分析...")
        
        try:
            # 执行决策分析
            result = self.engine.run_full_analysis()
            
            if result:
                buy_count = result['summary']['buy_count']
                sell_count = result['summary']['sell_count'] 
                hold_count = result['summary']['hold_count']
                
                self.logger.info("✅ 每日晨间分析完成!")
                self.logger.info(f"📊 分析结果: 买入{buy_count}只, 卖出{sell_count}只, 持有{hold_count}只")
                
                # 发送完成通知
                self.send_completion_notification(result)
            else:
                self.logger.error("❌ 晨间分析失败")
                
        except Exception as e:
            self.logger.error(f"❌ 晨间分析异常: {e}")
    
    def send_completion_notification(self, result):
        """发送分析完成通知"""
        try:
            # 这里可以扩展为邮件、微信等通知方式
            summary = result['summary']
            notification_text = f"""
📊 DeepSeek AI每日分析完成
时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
买入推荐: {summary['buy_count']}只
卖出建议: {summary['sell_count']}只  
持有观望: {summary['hold_count']}只
市场风险: {summary['risk_level']}

请查看AI决策中心获取详细信息。
            """
            
            # 保存通知到文件
            with open('./latest_notification.txt', 'w', encoding='utf-8') as f:
                f.write(notification_text)
                
            self.logger.info("📧 分析完成通知已生成")
            
        except Exception as e:
            self.logger.error(f"❌ 通知发送失败: {e}")
    
    def check_market_open(self):
        """检查是否为交易日"""
        now = datetime.now()
        
        # 周末不执行
        if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            return False
        
        # 这里可以添加更多节假日检查逻辑
        # 简单起见，只检查周末
        return True
    
    def start_scheduler(self, analysis_time="08:00"):
        """启动调度器"""
        print(f"🚀 DeepSeek每日调度器启动")
        print(f"⏰ 分析时间: 每天{analysis_time}")
        print(f"📊 分析范围: 443只A股")
        print(f"🎯 目标: 生成每日投资决策")
        print("=" * 50)
        
        # 设置每日任务
        schedule.every().day.at(analysis_time).do(self.run_if_market_open)
        
        # 也可以设置多个时间点
        # schedule.every().day.at("08:00").do(self.run_if_market_open)
        # schedule.every().day.at("20:00").do(self.evening_summary)  # 晚间总结
        
        self.logger.info(f"⏰ 每日分析任务已设置: {analysis_time}")
        self.logger.info("🔄 调度器运行中，按Ctrl+C停止")
        
        # 显示下次执行时间
        next_run = schedule.next_run()
        if next_run:
            self.logger.info(f"⏳ 下次执行: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
                
                # 每小时显示一次状态
                if datetime.now().minute == 0:
                    next_run = schedule.next_run()
                    if next_run:
                        self.logger.info(f"⏳ 下次分析: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                        
        except KeyboardInterrupt:
            self.logger.info("\\n👋 每日调度器已停止")
    
    def run_if_market_open(self):
        """仅在交易日执行分析"""
        if self.check_market_open():
            self.morning_analysis_job()
        else:
            self.logger.info("📅 今日为非交易日，跳过分析")
    
    def evening_summary(self):
        """晚间总结（可选功能）"""
        self.logger.info("🌃 执行晚间总结...")
        
        try:
            # 获取当天的分析结果
            latest_data = self.engine.get_latest_decisions()
            
            if latest_data:
                analysis_time = datetime.fromisoformat(latest_data['analysis_time'])
                is_today = analysis_time.date() == datetime.now().date()
                
                if is_today:
                    summary_text = f"""
📊 今日AI决策总结
分析时间: {analysis_time.strftime('%H:%M')}
市场状况: {latest_data['summary']['market_analysis']}
风险等级: {latest_data['summary']['risk_level']}
                    """
                    
                    with open('./daily_summary.txt', 'w', encoding='utf-8') as f:
                        f.write(summary_text)
                    
                    self.logger.info("📝 晚间总结已生成")
                else:
                    self.logger.info("📅 今日暂未执行分析")
            else:
                self.logger.info("📅 暂无分析数据")
                
        except Exception as e:
            self.logger.error(f"❌ 晚间总结失败: {e}")

def main():
    """主函数"""
    scheduler = DailyScheduler()
    
    print("🤖 DeepSeek每日AI决策调度器")
    print("=" * 50)
    print("选择运行模式:")
    print("1. 标准模式 - 每天08:00执行")
    print("2. 测试模式 - 立即执行一次")
    print("3. 自定义时间")
    print("4. 查看调度状态")
    
    choice = input("\\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        scheduler.start_scheduler("08:00")
    elif choice == "2":
        print("🧪 测试模式 - 立即执行分析...")
        scheduler.morning_analysis_job()
    elif choice == "3":
        analysis_time = input("请输入分析时间(HH:MM格式，如09:30): ").strip()
        try:
            # 验证时间格式
            datetime.strptime(analysis_time, "%H:%M")
            scheduler.start_scheduler(analysis_time)
        except ValueError:
            print("❌ 时间格式错误，请使用HH:MM格式")
    elif choice == "4":
        # 显示当前状态
        engine = UnifiedDecisionEngine()
        status = engine.get_analysis_status()
        print(f"\\n📈 当前状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()