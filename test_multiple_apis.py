#!/usr/bin/env python3
"""
测试多个东方财富北向资金API
"""
import requests
import json
from datetime import datetime, timedelta

def test_api_1():
    """测试API 1: push2his 历史数据接口"""
    print("\n" + "="*60)
    print("API 1: push2his.eastmoney.com (历史数据)")
    print("="*60)

    try:
        # 北向资金实时和历史数据
        url = "http://push2his.eastmoney.com/api/qt/kamt.kline/get"
        params = {
            'fields1': 'f1,f2,f3,f4',
            'fields2': 'f51,f52,f53,f54,f55,f56',
            'klt': '101',  # 日线
            'lmt': '10',   # 最近10天
            'ut': 'b2884a393a59ad64002292a3e90d46a5'
        }

        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")

        data = response.json()

        if data and 'data' in data and data['data']:
            klines = data['data'].get('hk2sh', '').split(';')  # 沪股通数据
            print(f"✅ 获取到 {len(klines)} 条沪股通数据")
            print("\n最近数据示例:")
            for kline in klines[:3]:
                if kline:
                    parts = kline.split(',')
                    if len(parts) >= 2:
                        date = parts[0]
                        flow = float(parts[1]) / 100  # 转为亿
                        print(f"  日期: {date}, 流入: {flow:.2f}亿")
            return True
        else:
            print("❌ 数据格式异常")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_api_2():
    """测试API 2: datacenter 北向资金统计"""
    print("\n" + "="*60)
    print("API 2: datacenter-web.eastmoney.com (北向资金统计)")
    print("="*60)

    try:
        url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
        params = {
            'reportName': 'RPT_MUTUAL_HOLD_DET',  # 北向资金持股详情
            'columns': 'ALL',
            'pageSize': '10',
            'sortColumns': 'HOLD_DATE',
            'sortTypes': '-1',
            'source': 'WEB',
            'client': 'WEB'
        }

        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")

        data = response.json()

        if data and 'result' in data and data['result']:
            items = data['result'].get('data', [])
            print(f"✅ 获取到 {len(items)} 条数据")
            if items:
                print("\n最近数据示例:")
                for item in items[:3]:
                    date = str(item.get('HOLD_DATE', ''))[:10]
                    print(f"  日期: {date}")
            return True
        else:
            print("❌ 数据格式异常")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_api_3():
    """测试API 3: push2 实时北向资金"""
    print("\n" + "="*60)
    print("API 3: push2.eastmoney.com (实时北向资金)")
    print("="*60)

    try:
        # 实时北向资金
        url = "http://push2.eastmoney.com/api/qt/kamt/get"
        params = {
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13',
            'ut': 'b2884a393a59ad64002292a3e90d46a5'
        }

        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")

        data = response.json()

        if data and 'data' in data:
            north_data = data['data']
            print("✅ 获取到实时数据")
            print("\n当前北向资金:")

            # 沪股通
            if 'hk2sh' in north_data:
                sh_flow = north_data['hk2sh'].get('f2', 0) / 10000  # 转为亿
                print(f"  沪股通: {sh_flow:.2f}亿")

            # 深股通
            if 'hk2sz' in north_data:
                sz_flow = north_data['hk2sz'].get('f2', 0) / 10000
                print(f"  深股通: {sz_flow:.2f}亿")

            # 北向总计
            if 'n2s' in north_data:
                total_flow = north_data['n2s'].get('f2', 0) / 10000
                print(f"  北向总计: {total_flow:.2f}亿")

            return True
        else:
            print("❌ 数据格式异常")
            print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_api_4():
    """测试API 4: 北向资金每日统计"""
    print("\n" + "="*60)
    print("API 4: datacenter (北向资金每日统计 - 新版)")
    print("="*60)

    try:
        url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
        params = {
            'reportName': 'RPT_MUTUAL_MARKET_STA',  # 北向市场统计
            'columns': 'ALL',
            'pageSize': '10',
            'sortColumns': 'TRADE_DATE',
            'sortTypes': '-1',
            'source': 'WEB',
            'client': 'WEB'
        }

        response = requests.get(url, params=params, timeout=10)
        print(f"状态码: {response.status_code}")

        data = response.json()

        if data and 'result' in data and data['result']:
            items = data['result'].get('data', [])
            print(f"✅ 获取到 {len(items)} 条数据")
            if items:
                print("\n最近数据示例:")
                for item in items[:5]:
                    date = str(item.get('TRADE_DATE', ''))[:10]
                    # 尝试不同的字段名
                    net_flow = item.get('NORTH_MONEY', item.get('NET_AMOUNT', 0))
                    if net_flow:
                        net_flow = float(net_flow) / 100000000
                    print(f"  日期: {date}, 净流入: {net_flow:.2f}亿")
                    print(f"    可用字段: {list(item.keys())[:10]}")  # 显示前10个字段名
            return True
        else:
            print("❌ 数据格式异常")
            return False

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  测试多个东方财富北向资金API接口")
    print("="*60)

    results = {
        'API 1 (历史数据)': test_api_1(),
        'API 2 (持股详情)': test_api_2(),
        'API 3 (实时数据)': test_api_3(),
        'API 4 (每日统计)': test_api_4(),
    }

    print("\n" + "="*60)
    print("测试结果汇总:")
    print("="*60)
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name}: {status}")

    print("\n推荐使用成功的API接口")
    print("="*60)

    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
