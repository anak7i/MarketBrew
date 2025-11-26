#!/usr/bin/env python3
"""
股票订阅推送定时调度器
负责每日定时分析和推送订阅股票
"""

import time
import schedule
import logging
from datetime import datetime, timedelta
import threading
import signal
import sys

from subscription_manager import StockSubscriptionManager

class SubscriptionScheduler:
    """订阅推送定时调度器"""
    
    def __init__(self, push_time="08:00"):
        self.subscription_manager = StockSubscriptionManager()
        self.push_time = push_time
        self.running = False
        self.scheduler_thread = None
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('subscription_scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """处理退出信号"""
        self.logger.info(f"收到退出信号 {signum}")
        self.stop()
        sys.exit(0)
    
    def daily_push_job(self):
        """每日推送任务"""
        try:
            self.logger.info("🚀 开始执行每日订阅推送任务")
            
            # 检查是否为交易日 (可以根据需要添加节假日判断)
            today = datetime.now()
            if today.weekday() >= 5:  # 周六日
                self.logger.info("📅 今天是周末，跳过推送")
                return
            
            # 执行推送
            result = self.subscription_manager.daily_analysis_and_push()
            
            self.logger.info(f"✅ 每日推送完成: {result}")
            
            # 清理旧历史记录 (保留30天)
            cleaned = self.subscription_manager.cleanup_old_history(30)
            if cleaned > 0:
                self.logger.info(f"🧹 清理了 {cleaned} 条旧记录")
            
        except Exception as e:
            self.logger.error(f"❌ 每日推送任务失败: {e}")
            
            # 发送错误通知
            try:
                error_push = {
                    "symbol": "SYSTEM",
                    "name": "系统通知",
                    "title": "❌ 每日推送失败",
                    "content": f"推送任务执行失败: {str(e)}",
                    "decision": "系统错误",
                    "price": 0,
                    "timestamp": datetime.now().isoformat(),
                    "push_type": "system_error"
                }
                self.subscription_manager.send_push_notification(error_push)
            except:
                pass
    
    def test_push_job(self):
        """测试推送任务"""
        try:
            self.logger.info("🧪 执行测试推送")
            
            subscriptions = self.subscription_manager.get_subscriptions()
            if not subscriptions:
                self.logger.warning("没有订阅股票，跳过测试推送")
                return
            
            # 随机选择一只股票进行测试
            import random
            test_stock = random.choice(subscriptions)
            
            analysis = self.subscription_manager.analyze_subscription(test_stock['symbol'])
            if analysis:
                analysis['title'] = f"🧪 [测试] {analysis['title']}"
                analysis['push_type'] = 'scheduled_test'
                
                self.subscription_manager.send_push_notification(analysis)
                self.logger.info(f"✅ 测试推送完成: {test_stock['symbol']}")
            else:
                self.logger.warning("无法获取测试数据")
                
        except Exception as e:
            self.logger.error(f"❌ 测试推送失败: {e}")
    
    def health_check_job(self):
        """健康检查任务"""
        try:
            stats = self.subscription_manager.get_statistics()
            
            self.logger.info(f"💊 健康检查 - 订阅数: {stats['active_subscriptions']}, "
                           f"今日推送: {stats['today_pushes']}")
            
            # 检查是否需要发送状态报告
            if stats['active_subscriptions'] > 0 and stats['today_pushes'] == 0:
                current_hour = datetime.now().hour
                if current_hour >= 9:  # 9点后还没有推送
                    self.logger.warning("⚠️ 今日尚未推送，可能存在问题")
                    
        except Exception as e:
            self.logger.error(f"❌ 健康检查失败: {e}")
    
    def schedule_jobs(self):
        """设置定时任务"""
        # 每日推送任务 
        schedule.every().day.at(self.push_time).do(self.daily_push_job)
        
        # 测试推送 (每周一次，周日晚上)
        schedule.every().sunday.at("20:00").do(self.test_push_job)
        
        # 健康检查 (每小时)
        schedule.every().hour.do(self.health_check_job)
        
        self.logger.info(f"📅 已设置定时任务:")
        self.logger.info(f"  🕗 每日推送: {self.push_time}")
        self.logger.info(f"  🧪 测试推送: 周日 20:00")
        self.logger.info(f"  💊 健康检查: 每小时")
    
    def run_scheduler(self):
        """运行调度器"""
        self.logger.info("⏰ 调度器线程启动")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(10)  # 每10秒检查一次
            except Exception as e:
                self.logger.error(f"❌ 调度器异常: {e}")
                time.sleep(30)  # 出错后等30秒再继续
        
        self.logger.info("⏰ 调度器线程退出")
    
    def start(self):
        """启动调度器"""
        if self.running:
            self.logger.warning("调度器已在运行")
            return False
        
        self.logger.info("🚀 启动股票订阅推送调度器")
        
        # 设置定时任务
        self.schedule_jobs()
        
        # 启动调度器线程
        self.running = True
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # 显示下次推送时间
        next_run = schedule.next_run()
        if next_run:
            self.logger.info(f"⏱️ 下次推送时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
    
    def stop(self):
        """停止调度器"""
        if not self.running:
            self.logger.warning("调度器未运行")
            return False
        
        self.logger.info("🛑 正在停止调度器...")
        
        self.running = False
        
        # 等待线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # 清空调度任务
        schedule.clear()
        
        self.logger.info("✅ 调度器已停止")
        return True
    
    def get_status(self):
        """获取调度器状态"""
        return {
            "running": self.running,
            "push_time": self.push_time,
            "next_run": schedule.next_run().isoformat() if schedule.next_run() else None,
            "scheduled_jobs": len(schedule.jobs),
            "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False,
            "subscriptions": len(self.subscription_manager.get_subscriptions())
        }
    
    def run_once(self):
        """立即执行一次推送"""
        self.logger.info("🔥 立即执行推送任务")
        self.daily_push_job()
    
    def add_custom_job(self, time_str, job_func, job_name):
        """添加自定义任务"""
        try:
            schedule.every().day.at(time_str).do(job_func)
            self.logger.info(f"➕ 添加自定义任务: {job_name} at {time_str}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 添加任务失败: {e}")
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票订阅推送调度器')
    parser.add_argument('--time', default='08:00', help='推送时间 (格式: HH:MM)')
    parser.add_argument('--once', action='store_true', help='立即执行一次推送后退出')
    parser.add_argument('--test', action='store_true', help='执行测试推送后退出')
    
    args = parser.parse_args()
    
    scheduler = SubscriptionScheduler(push_time=args.time)
    
    if args.once:
        print("🔥 执行一次性推送...")
        scheduler.run_once()
        print("✅ 推送完成")
        return
    
    if args.test:
        print("🧪 执行测试推送...")
        scheduler.test_push_job()
        print("✅ 测试完成")
        return
    
    # 正常启动调度器
    try:
        success = scheduler.start()
        
        if success:
            print(f"📱 股票订阅推送调度器已启动")
            print(f"⏰ 推送时间: 每天 {args.time}")
            print(f"📊 当前订阅: {len(scheduler.subscription_manager.get_subscriptions())} 只股票")
            print(f"")
            print(f"命令选项:")
            print(f"  --once    立即执行一次推送")
            print(f"  --test    执行测试推送") 
            print(f"  --time    设置推送时间")
            print(f"")
            print(f"按 Ctrl+C 停止调度器")
            
            # 保持运行
            try:
                while scheduler.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ 调度器启动失败")
            
    except Exception as e:
        print(f"❌ 启动异常: {e}")
    finally:
        scheduler.stop()

if __name__ == "__main__":
    main()