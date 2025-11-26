#!/usr/bin/env python3
"""
诊断报告生成源头 - 找出谁还在调用旧API
"""

import requests
import json
from datetime import datetime

def test_api_responses():
    """测试两个API的响应差异"""
    
    test_stocks = [
        {"symbol": "600036", "name": "招商银行"},
        {"symbol": "601318", "name": "中国平安"},
        {"symbol": "002837", "name": "英维克"}
    ]
    
    print("🔍 API响应诊断分析")
    print("=" * 80)
    
    # 测试旧版API
    print("\n❌ 旧版API (/api/stock-analysis) 响应:")
    try:
        response = requests.post(
            "http://localhost:5001/api/stock-analysis",
            json={"stocks": test_stocks},
            timeout=30
        )
        if response.status_code == 200:
            old_data = response.json()
            if old_data.get('results'):
                for result in old_data['results'][:2]:
                    print(f"   {result['symbol']} {result['name']}: {result.get('analysis', '')[:100]}...")
        else:
            print(f"   API调用失败: {response.status_code}")
    except Exception as e:
        print(f"   API错误: {e}")
    
    print("\n✅ 新版API (/api/langchain/stock-analysis) 响应:")
    try:
        response = requests.post(
            "http://localhost:5001/api/langchain/stock-analysis",
            json={"stocks": [test_stocks[0]]},  # 只测试一只股票
            timeout=60
        )
        if response.status_code == 200:
            new_data = response.json()
            if new_data.get('results'):
                result = new_data['results'][0]
                analysis = result.get('analysis', '')
                
                # 提取关键信息
                lines = analysis.split('\n')
                key_info = []
                for line in lines:
                    if any(keyword in line for keyword in ['操作建议', '目标价格', '建议仓位', '信心度']):
                        key_info.append(line.strip())
                
                print(f"   {result.get('symbol')} 分析质量:")
                for info in key_info[:4]:
                    print(f"     {info}")
        else:
            print(f"   API调用失败: {response.status_code}")
    except Exception as e:
        print(f"   API错误: {e}")
    
    print("\n🎯 问题诊断:")
    print("如果你的报告显示'60分持有'，说明:")
    print("1. 报告生成程序使用的是旧版API")
    print("2. 或者有缓存的旧数据")
    print("3. 或者使用了不同的界面入口")
    
    print("\n🔧 解决方案:")
    print("1. 检查浏览器缓存并刷新页面")
    print("2. 确认使用的界面文件 (stock_subscription.html)")
    print("3. 检查是否有其他后台任务生成报告")

def check_running_processes():
    """检查正在运行的相关进程"""
    import subprocess
    
    print("\n🔍 检查运行中的进程:")
    try:
        # 检查Python进程
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        market_processes = []
        for line in lines:
            if 'python' in line and any(keyword in line for keyword in ['market', 'report', 'analysis', 'deepseek']):
                market_processes.append(line.strip())
        
        if market_processes:
            print("   发现相关进程:")
            for process in market_processes[:5]:
                print(f"     {process}")
        else:
            print("   未发现相关后台进程")
            
    except Exception as e:
        print(f"   检查进程失败: {e}")

if __name__ == "__main__":
    test_api_responses()
    check_running_processes()
    
    print("\n" + "=" * 80)
    print("💡 如果问题仍然存在，请:")
    print("1. 清除浏览器缓存")
    print("2. 使用 stock_subscription.html 界面")
    print("3. 或者直接访问: http://localhost:5001/api_test_page.html")