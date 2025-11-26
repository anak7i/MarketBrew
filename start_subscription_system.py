#!/usr/bin/env python3
"""
股票订阅推送系统启动脚本
一键启动API服务器、调度器和Web界面
"""

import os
import sys
import time
import subprocess
import threading
import signal
from datetime import datetime

class SubscriptionSystemLauncher:
    def __init__(self):
        self.processes = {}
        self.running = False
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """处理退出信号"""
        print(f"\n收到退出信号 {signum}")
        self.stop_all()
        sys.exit(0)
    
    def check_dependencies(self):
        """检查系统依赖"""
        print("🔍 检查系统依赖...")
        
        required_files = [
            'subscription_manager.py',
            'subscription_api_server.py', 
            'subscription_scheduler.py',
            'stock_subscription.html',
            'unified_decision_engine.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
            else:
                print(f"  ✅ {file}")
        
        if missing_files:
            print(f"❌ 缺少必要文件:")
            for file in missing_files:
                print(f"  - {file}")
            return False
        
        # 检查Python包
        required_packages = ['requests', 'schedule']
        for package in required_packages:
            try:
                __import__(package)
                print(f"  ✅ {package}")
            except ImportError:
                print(f"  ❌ {package} (请运行: pip3 install {package})")
                return False
        
        print("✅ 所有依赖检查通过\n")
        return True
    
    def start_api_server(self):
        """启动API服务器"""
        try:
            print("🚀 启动订阅API服务器...")
            
            process = subprocess.Popen(
                [sys.executable, 'subscription_api_server.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes['api_server'] = process
            print("✅ API服务器启动成功 (端口: 8527)")
            
            # 给服务器一些时间启动
            time.sleep(2)
            
            return True
            
        except Exception as e:
            print(f"❌ API服务器启动失败: {e}")
            return False
    
    def start_scheduler(self):
        """启动调度器"""
        try:
            print("⏰ 启动推送调度器...")
            
            process = subprocess.Popen(
                [sys.executable, 'subscription_scheduler.py'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes['scheduler'] = process
            print("✅ 推送调度器启动成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 推送调度器启动失败: {e}")
            return False
    
    def open_web_interface(self):
        """打开Web界面"""
        try:
            print("🌐 打开订阅管理界面...")
            
            html_path = os.path.abspath('stock_subscription.html')
            
            # 根据操作系统选择打开方式
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['open', html_path])
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.run(['xdg-open', html_path])
            elif sys.platform.startswith('win'):  # Windows
                os.startfile(html_path)
            
            print("✅ Web界面已打开")
            return True
            
        except Exception as e:
            print(f"❌ 打开Web界面失败: {e}")
            print(f"💡 请手动打开: {html_path}")
            return False
    
    def test_system(self):
        """测试系统功能"""
        print("\n🧪 系统功能测试...")
        
        try:
            # 测试订阅管理器
            from subscription_manager import StockSubscriptionManager
            manager = StockSubscriptionManager()
            
            print("  ✅ 订阅管理器加载成功")
            
            # 测试添加订阅
            test_result = manager.add_subscription("000001", "平安银行")
            if test_result:
                print("  ✅ 添加订阅功能正常")
                
                # 移除测试订阅
                manager.remove_subscription("000001")
                print("  ✅ 移除订阅功能正常")
            
            # 测试API连接
            import requests
            try:
                response = requests.get("http://localhost:8527/api/status", timeout=5)
                if response.status_code == 200:
                    print("  ✅ API服务器响应正常")
                else:
                    print("  ⚠️ API服务器响应异常")
            except:
                print("  ⚠️ API服务器连接失败")
            
            print("✅ 系统测试完成\n")
            return True
            
        except Exception as e:
            print(f"❌ 系统测试失败: {e}")
            return False
    
    def monitor_processes(self):
        """监控进程状态"""
        while self.running:
            try:
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        print(f"⚠️ {name} 进程异常退出")
                        del self.processes[name]
                
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ 进程监控异常: {e}")
                time.sleep(10)
    
    def stop_all(self):
        """停止所有服务"""
        print("\n🛑 正在停止所有服务...")
        
        self.running = False
        
        for name, process in self.processes.items():
            try:
                print(f"  停止 {name}...")
                process.terminate()
                
                # 等待进程结束
                try:
                    process.wait(timeout=5)
                    print(f"  ✅ {name} 已停止")
                except subprocess.TimeoutExpired:
                    print(f"  🔥 强制终止 {name}")
                    process.kill()
                    process.wait()
                    
            except Exception as e:
                print(f"  ❌ 停止 {name} 失败: {e}")
        
        self.processes.clear()
        print("✅ 所有服务已停止")
    
    def show_status(self):
        """显示系统状态"""
        print(f"\n📊 系统状态 ({datetime.now().strftime('%H:%M:%S')})")
        print("=" * 50)
        
        for name, process in self.processes.items():
            status = "运行中" if process.poll() is None else "已停止"
            pid = process.pid if process.poll() is None else "N/A"
            print(f"  {name}: {status} (PID: {pid})")
        
        if not self.processes:
            print("  没有运行中的服务")
        
        print("\n🔗 访问地址:")
        print("  订阅管理: stock_subscription.html")
        print("  API服务: http://localhost:8527/api/status")
        print("  决策中心: ai_decision_center.html")
    
    def start_all(self):
        """启动所有服务"""
        print("=" * 60)
        print("📱 股票订阅推送系统")
        print("=" * 60)
        print("🎯 功能: 股票订阅管理 + 每日智能推送")
        print("⏰ 推送: 每天早上8:00自动分析并推送")
        print("📊 内容: 价格变化 + 操作建议 + 风险提示")
        print("=" * 60)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        success = True
        
        # 启动API服务器
        if not self.start_api_server():
            success = False
        
        # 启动调度器
        if success and not self.start_scheduler():
            success = False
        
        # 测试系统
        if success and not self.test_system():
            print("⚠️ 系统测试失败，但继续运行")
        
        # 打开Web界面
        if success:
            self.open_web_interface()
        
        if success:
            print("🎉 股票订阅推送系统启动成功!")
            print("\n💡 使用说明:")
            print("1. 在Web界面添加您关注的股票")
            print("2. 系统将在每天8:00自动分析并推送")
            print("3. 您可以手动触发推送或测试功能")
            print("4. 查看推送历史和统计信息")
            
            self.running = True
            
            # 启动进程监控
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            # 显示状态
            self.show_status()
            
            return True
        else:
            print("❌ 系统启动失败")
            self.stop_all()
            return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票订阅推送系统')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    parser.add_argument('--stop', action='store_true', help='停止所有服务')
    
    args = parser.parse_args()
    
    launcher = SubscriptionSystemLauncher()
    
    if args.status:
        launcher.show_status()
        return
    
    if args.stop:
        launcher.stop_all()
        return
    
    try:
        success = launcher.start_all()
        
        if success:
            print(f"\n按 Ctrl+C 停止系统")
            
            # 保持运行
            try:
                while launcher.running:
                    cmd = input().strip().lower()
                    if cmd == 'status':
                        launcher.show_status()
                    elif cmd == 'quit' or cmd == 'exit':
                        break
                    elif cmd == 'help':
                        print("命令: status, quit, exit, help")
            except (KeyboardInterrupt, EOFError):
                pass
        else:
            print("❌ 系统启动失败")
            
    except Exception as e:
        print(f"❌ 启动异常: {e}")
    finally:
        launcher.stop_all()

if __name__ == "__main__":
    main()