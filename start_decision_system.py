#!/usr/bin/env python3
"""
AI决策系统启动器 - 一键启动完整系统
"""

import os
import sys
import subprocess
import time
import webbrowser
from datetime import datetime

def print_banner():
    """打印系统横幅"""
    print("=" * 60)
    print("🤖 DeepSeek AI股票决策系统")
    print("=" * 60)
    print("📊 智能分析443只A股，生成投资决策建议")
    print("🕰️ 每日8:00自动分析，支持手动触发")
    print("🎯 专注决策支持，操作简洁高效")
    print("=" * 60)
    print()

def check_dependencies():
    """检查系统依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查Python包
    required_packages = ['requests', 'schedule']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (缺失)")
            missing_packages.append(package)
    
    # 检查数据文件
    data_dir = "./data"
    if os.path.exists(data_dir):
        data_files = [f for f in os.listdir(data_dir) if f.startswith('daily_prices_') and f.endswith('.json')]
        print(f"  📊 股票数据文件: {len(data_files)}个")
    else:
        print(f"  ❌ 数据目录不存在: {data_dir}")
        return False
    
    # 检查核心文件
    core_files = [
        'unified_decision_engine.py',
        'decision_api_server.py', 
        'daily_scheduler.py',
        'ai_decision_center.html'
    ]
    
    for file in core_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (缺失)")
            return False
    
    if missing_packages:
        print(f"\n❌ 缺少必要的Python包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 所有依赖检查通过")
    return True

def start_api_server():
    """启动API服务器"""
    print("\n🌐 启动决策API服务器...")
    
    try:
        # 启动API服务器（后台进程）
        api_process = subprocess.Popen(
            [sys.executable, 'decision_api_server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查进程是否还在运行
        if api_process.poll() is None:
            print("✅ API服务器启动成功 (端口: 8526)")
            return api_process
        else:
            stdout, stderr = api_process.communicate()
            print(f"❌ API服务器启动失败: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ 启动API服务器失败: {e}")
        return None

def open_web_interface():
    """打开Web界面"""
    print("\n🌐 打开AI决策中心...")
    
    html_file = os.path.abspath('ai_decision_center.html')
    
    if os.path.exists(html_file):
        try:
            webbrowser.open(f'file://{html_file}')
            print(f"✅ 决策中心已打开: {html_file}")
            return True
        except Exception as e:
            print(f"❌ 打开Web界面失败: {e}")
            return False
    else:
        print(f"❌ Web界面文件不存在: {html_file}")
        return False

def show_system_status():
    """显示系统状态"""
    print("\n📊 系统状态:")
    
    try:
        # 导入决策引擎获取状态
        from unified_decision_engine import UnifiedDecisionEngine
        engine = UnifiedDecisionEngine()
        status = engine.get_analysis_status()
        
        print(f"  📅 上次分析: {status['last_analysis']}")
        print(f"  📈 股票数量: {status['stock_count']}")
        print(f"  📊 买入信号: {status['buy_signals']}")
        print(f"  📉 卖出信号: {status['sell_signals']}")
        print(f"  📋 持有建议: {status['hold_signals']}")
        print(f"  ⚠️  市场风险: {status['risk_level']}")
        print(f"  🕐 是否今日: {'是' if status['is_today'] else '否'}")
        
    except Exception as e:
        print(f"  ❌ 获取状态失败: {e}")

def show_usage_guide():
    """显示使用指南"""
    print("\n📖 使用指南:")
    print("1. 🚀 手动分析: 在Web界面点击'启动全量分析'按钮")
    print("2. ⏰ 自动分析: 每天早上8:00自动执行")
    print("3. 📊 查看决策: 在决策中心查看买入/卖出/持有建议")
    print("4. 📈 监控状态: 实时显示分析状态和市场概况")
    print()
    print("🔗 重要链接:")
    print("  • AI决策中心: ai_decision_center.html")
    print("  • API服务器: http://localhost:8526")
    print("  • 调度器管理: python daily_scheduler.py")

def main_menu():
    """主菜单"""
    print_banner()
    
    if not check_dependencies():
        print("\n❌ 系统依赖检查失败，请解决上述问题后重试")
        return
    
    print("\n🎯 请选择操作:")
    print("1. 🚀 启动完整系统 (推荐)")
    print("2. 🧪 测试分析功能")
    print("3. ⏰ 启动自动调度器")
    print("4. 📊 查看系统状态")
    print("5. 📖 使用指南")
    print("6. 🔧 单独启动API服务器")
    print("0. 退出")
    
    choice = input("\n请输入选择 (0-6): ").strip()
    
    if choice == "1":
        start_complete_system()
    elif choice == "2":
        test_analysis()
    elif choice == "3":
        start_scheduler()
    elif choice == "4":
        show_system_status()
    elif choice == "5":
        show_usage_guide()
    elif choice == "6":
        start_api_server_only()
    elif choice == "0":
        print("👋 再见！")
    else:
        print("❌ 无效选择")

def start_complete_system():
    """启动完整系统"""
    print("\n🚀 启动完整AI决策系统...")
    
    # 启动API服务器
    api_process = start_api_server()
    if not api_process:
        print("❌ 无法启动API服务器，系统启动失败")
        return
    
    # 等待服务器完全启动
    time.sleep(2)
    
    # 打开Web界面
    if not open_web_interface():
        print("❌ 无法打开Web界面")
        
        # 终止API服务器
        if api_process:
            api_process.terminate()
        return
    
    # 显示系统状态
    show_system_status()
    
    print("\n✅ 完整系统启动成功!")
    print("=" * 60)
    print("🌟 系统已就绪，可以开始使用:")
    print("  • 在浏览器中查看AI决策中心")
    print("  • 点击'启动全量分析'进行手动分析")
    print("  • 系统将在每天早上8:00自动分析")
    print("=" * 60)
    
    # 等待用户输入
    try:
        input("\n按 Enter 键停止系统...")
    except KeyboardInterrupt:
        pass
    
    # 停止API服务器
    if api_process:
        print("\n🛑 停止API服务器...")
        api_process.terminate()
        api_process.wait()
        print("✅ 系统已停止")

def test_analysis():
    """测试分析功能"""
    print("\n🧪 测试决策分析功能...")
    
    try:
        subprocess.run([sys.executable, 'unified_decision_engine.py', '2'], check=True)
    except subprocess.CalledProcessError:
        print("❌ 测试失败")
    except KeyboardInterrupt:
        print("\n🛑 测试中断")

def start_scheduler():
    """启动调度器"""
    print("\n⏰ 启动自动调度器...")
    
    try:
        subprocess.run([sys.executable, 'daily_scheduler.py'], check=True)
    except subprocess.CalledProcessError:
        print("❌ 调度器启动失败")
    except KeyboardInterrupt:
        print("\n🛑 调度器已停止")

def start_api_server_only():
    """仅启动API服务器"""
    print("\n🔧 启动API服务器...")
    
    try:
        subprocess.run([sys.executable, 'decision_api_server.py'], check=True)
    except subprocess.CalledProcessError:
        print("❌ API服务器启动失败")
    except KeyboardInterrupt:
        print("\n🛑 API服务器已停止")

if __name__ == "__main__":
    main_menu()