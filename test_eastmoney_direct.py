#!/usr/bin/env python3
"""
直接测试东方财富API
"""
import requests
import json

def test_eastmoney_api():
    print("=" * 60)
    print("直接测试东方财富北向资金API")
    print("=" * 60)
    print()

    url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        'reportName': 'RPT_MUTUAL_STOCK_NORTHSTA',
        'columns': 'ALL',
        'pageSize': '5',
        'sortColumns': 'TRADE_DATE',
        'sortTypes': '-1',
        'source': 'WEB',
        'client': 'WEB'
    }

    print("请求URL:", url)
    print("参数:", params)
    print()
    print("正在请求...")

    try:
        response = requests.get(url, params=params, timeout=15)
        print(f"状态码: {response.status_code}")
        print()

        data = response.json()

        if data and 'result' in data and data['result'] and 'data' in data['result']:
            items = data['result']['data']
            print(f"✅ 成功获取 {len(items)} 条数据")
            print()
            print("最近5天数据:")
            print("-" * 60)

            for item in items[:5]:
                date_str = str(item.get('TRADE_DATE', ''))[:10]
                north_money = float(item.get('NORTH_MONEY', 0)) / 100000000
                print(f"日期: {date_str}, 北向流入: {north_money:.2f} 亿")
        else:
            print("❌ 响应数据结构异常")
            print("响应内容:", json.dumps(data, ensure_ascii=False, indent=2)[:500])

    except requests.Timeout:
        print("❌ 请求超时！")
        print("可能原因:")
        print("  1. 网络连接慢")
        print("  2. 东方财富服务器响应慢")
        print("  3. 防火墙拦截")
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 60)

if __name__ == "__main__":
    test_eastmoney_api()
    input("\n按回车键退出...")
