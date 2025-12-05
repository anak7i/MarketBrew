#!/usr/bin/env python3
"""
快速测试API端点
"""
import requests
import json

def test_api():
    print("=" * 60)
    print("🧪 测试 API 端点")
    print("=" * 60)

    base_url = "http://localhost:8526"

    # 测试1: 市场统计
    print("\n1️⃣ 测试市场统计 API...")
    try:
        response = requests.get(f"{base_url}/api/market-stats", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        if data.get('success'):
            print("   ✅ 市场统计 API 正常")
        else:
            print(f"   ❌ API返回失败: {data.get('error')}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")

    # 测试2: 资金流向
    print("\n2️⃣ 测试资金流向 API...")
    try:
        response = requests.get(f"{base_url}/api/capital-timing", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()

        if data.get('success'):
            print("   ✅ 资金流向 API 正常")
            # 显示关键数据
            capital_data = data.get('data', {})
            latest = capital_data.get('latest', {})
            periods = capital_data.get('periods', {})

            print(f"   今日流入: {latest.get('total_flow', 0):.2f} 亿")
            print(f"   多周期数据: {list(periods.keys())}")
        else:
            print(f"   ❌ API返回失败: {data.get('error')}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")

    # 测试3: 服务测试端点
    print("\n3️⃣ 测试服务诊断端点...")
    try:
        response = requests.get(f"{base_url}/api/test-capital", timeout=5)
        print(f"   状态码: {response.status_code}")
        data = response.json()
        print(f"   测试结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_api()
