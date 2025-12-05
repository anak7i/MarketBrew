#!/usr/bin/env python3
"""
正确测试 push2his API - 北向资金历史数据
"""
import requests
import json

print("="*70)
print("  测试 push2his API - 北向资金历史K线数据")
print("="*70)
print()

try:
    # 北向资金历史K线数据
    url = "http://push2his.eastmoney.com/api/qt/kamt.kline/get"
    params = {
        'fields1': 'f1,f2,f3,f4',
        'fields2': 'f51,f52,f53,f54,f55,f56',
        'klt': '101',  # 日线
        'lmt': '30',   # 最近30天
        'ut': 'b2884a393a59ad64002292a3e90d46a5'
    }

    print("请求URL:", url)
    print("参数:", params)
    print()

    response = requests.get(url, params=params, timeout=10)
    print(f"状态码: {response.status_code}")
    print()

    data = response.json()

    print("响应数据结构:")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:500])
    print()

    if data and 'data' in data:
        raw_data = data['data']

        print("="*70)
        print("解析数据:")
        print("="*70)

        # 沪股通 (hk2sh)
        if 'hk2sh' in raw_data:
            print("\n【沪股通数据】")
            hk2sh_data = raw_data['hk2sh']
            print(f"数据类型: {type(hk2sh_data)}")

            if isinstance(hk2sh_data, list):
                print(f"数据条数: {len(hk2sh_data)}")
                print("\n最近5天沪股通:")
                print(f"{'日期':<12} {'北向流入(亿)':<15}")
                print("-" * 30)
                for item in hk2sh_data[:5]:
                    if isinstance(item, str) and ',' in item:
                        parts = item.split(',')
                        if len(parts) >= 2:
                            date = parts[0]
                            flow = float(parts[1]) / 10000  # 转为亿
                            print(f"{date:<12} {flow:>12.2f}")
            elif isinstance(hk2sh_data, str):
                print("数据是字符串格式，需要分割")
                items = hk2sh_data.split(';')
                print(f"数据条数: {len(items)}")
                print("\n最近5天沪股通:")
                print(f"{'日期':<12} {'北向流入(亿)':<15}")
                print("-" * 30)
                for item in items[:5]:
                    if item and ',' in item:
                        parts = item.split(',')
                        if len(parts) >= 2:
                            date = parts[0]
                            flow = float(parts[1]) / 10000
                            print(f"{date:<12} {flow:>12.2f}")

        # 深股通 (hk2sz)
        if 'hk2sz' in raw_data:
            print("\n【深股通数据】")
            hk2sz_data = raw_data['hk2sz']
            print(f"数据类型: {type(hk2sz_data)}")

            if isinstance(hk2sz_data, str):
                items = hk2sz_data.split(';')
                print(f"数据条数: {len(items)}")
                print("\n最近5天深股通:")
                print(f"{'日期':<12} {'北向流入(亿)':<15}")
                print("-" * 30)
                for item in items[:5]:
                    if item and ',' in item:
                        parts = item.split(',')
                        if len(parts) >= 2:
                            date = parts[0]
                            flow = float(parts[1]) / 10000
                            print(f"{date:<12} {flow:>12.2f}")

        # 北向总计 (s2n)
        if 's2n' in raw_data:
            print("\n【北向总计】")
            s2n_data = raw_data['s2n']
            print(f"数据类型: {type(s2n_data)}")

            if isinstance(s2n_data, str):
                items = s2n_data.split(';')
                print(f"数据条数: {len(items)}")
                print("\n最近10天北向总流入:")
                print(f"{'日期':<12} {'北向流入(亿)':<15} {'沪股通(亿)':<15} {'深股通(亿)':<15}")
                print("-" * 60)
                for item in items[:10]:
                    if item and ',' in item:
                        parts = item.split(',')
                        if len(parts) >= 4:
                            date = parts[0]
                            total_flow = float(parts[1]) / 10000
                            sh_flow = float(parts[2]) / 10000
                            sz_flow = float(parts[3]) / 10000
                            print(f"{date:<12} {total_flow:>12.2f}     {sh_flow:>12.2f}     {sz_flow:>12.2f}")

        print()
        print("="*70)
        print("✅ 这个API返回的是历史K线数据，格式正确！")
        print("="*70)

    else:
        print("❌ 数据格式异常")

except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

input("\n按回车键退出...")
