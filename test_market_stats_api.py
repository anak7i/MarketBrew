#!/usr/bin/env python3
"""测试市场统计API"""
import requests
import json

print("="*70)
print("  测试市场统计API")
print("="*70)
print()

try:
    url = "http://localhost:8526/api/market-stats"
    print(f"请求URL: {url}")
    print()

    response = requests.get(url, timeout=30)
    print(f"状态码: {response.status_code}")
    print()

    if response.status_code == 200:
        data = response.json()
        print("响应数据:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print()

        if data.get('success'):
            market_data = data.get('data', {})
            print("="*70)
            print("市场统计结果:")
            print("="*70)
            print(f"总股票数: {market_data.get('total_count')}")
            print(f"上涨数量: {market_data.get('up_count')}")
            print(f"下跌数量: {market_data.get('down_count')}")
            print(f"平盘数量: {market_data.get('flat_count')}")
            print(f"涨跌比: {market_data.get('up_down_ratio')}")
            print(f"数据源: {market_data.get('data_source')}")
            print(f"更新时间: {market_data.get('timestamp')}")
            print()
            print("✅ API测试成功")
        else:
            print("❌ API返回失败")
    else:
        print(f"❌ HTTP错误: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ 无法连接到服务器")
    print("请确保 decision_api_server.py 正在运行")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print()
input("按回车键退出...")
