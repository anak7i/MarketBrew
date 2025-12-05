#!/usr/bin/env python3
"""
详细测试API 2 - 查看所有字段
"""
import requests
import json

def test_api2_detail():
    print("="*70)
    print("  详细测试 API 2: RPT_MUTUAL_HOLD_DET")
    print("="*70)
    print()

    try:
        url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
        params = {
            'reportName': 'RPT_MUTUAL_HOLD_DET',
            'columns': 'ALL',
            'pageSize': '3',
            'sortColumns': 'HOLD_DATE',
            'sortTypes': '-1',
            'source': 'WEB',
            'client': 'WEB'
        }

        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")
        print()

        data = response.json()

        if data and 'result' in data and data['result']:
            items = data['result'].get('data', [])
            print(f"✅ 获取到 {len(items)} 条数据")
            print()

            if items:
                print("第一条数据的所有字段:")
                print("-" * 70)
                first_item = items[0]
                for key, value in first_item.items():
                    print(f"  {key:30s} = {value}")

                print()
                print("=" * 70)
                print("这是持股详情数据，可能不是我们需要的流入流出数据")
                print("=" * 70)
        else:
            print("❌ 数据格式异常")

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("="*70)
    print("  现在测试其他可能的 reportName")
    print("="*70)
    print()

    # 尝试其他reportName
    report_names = [
        'RPT_MUTUAL_STOCK_NORTHSTA',  # 原来用的
        'RPT_MUTUAL_MARKET_STA',      # 市场统计
        'RPT_MUTUAL_DEAL_HISTORY',    # 交易历史
        'RPT_MUTUAL_HOLDRANK',        # 持股排名
        'RPT_MUTUAL_BOARD_STA',       # 板块统计
    ]

    for report_name in report_names:
        print(f"\n测试 {report_name}:")
        print("-" * 70)
        try:
            params = {
                'reportName': report_name,
                'columns': 'ALL',
                'pageSize': '3',
                'sortColumns': 'TRADE_DATE',
                'sortTypes': '-1',
                'source': 'WEB',
                'client': 'WEB'
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'result' in data and data['result'] and 'data' in data['result']:
                items = data['result']['data']
                if items:
                    print(f"✅ 成功获取 {len(items)} 条数据")
                    first = items[0]
                    print(f"   字段数量: {len(first)}")
                    print(f"   关键字段: {list(first.keys())[:8]}")

                    # 查找可能的日期和金额字段
                    date_field = None
                    money_field = None

                    for key in first.keys():
                        if 'DATE' in key.upper():
                            date_val = str(first[key])[:10]
                            print(f"   日期字段 {key}: {date_val}")
                            date_field = key
                        if 'MONEY' in key.upper() or 'AMOUNT' in key.upper() or 'FLOW' in key.upper():
                            money_val = first[key]
                            print(f"   金额字段 {key}: {money_val}")
                            money_field = key

                    if date_field and money_field:
                        print(f"   ⭐ 这个API看起来有用！包含日期和金额字段")
                else:
                    print("   ⚠️ 返回空数据")
            else:
                print("   ❌ 数据格式不符")

        except Exception as e:
            print(f"   ❌ 请求失败: {e}")

    input("\n\n按回车键退出...")

if __name__ == "__main__":
    test_api2_detail()
