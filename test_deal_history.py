#!/usr/bin/env python3
"""
详细测试 RPT_MUTUAL_DEAL_HISTORY
"""
import requests
import json

url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
params = {
    'reportName': 'RPT_MUTUAL_DEAL_HISTORY',
    'columns': 'ALL',
    'pageSize': '10',
    'sortColumns': 'TRADE_DATE',
    'sortTypes': '-1',
    'source': 'WEB',
    'client': 'WEB'
}

print("="*70)
print("  测试 RPT_MUTUAL_DEAL_HISTORY (北向资金交易历史)")
print("="*70)
print()

try:
    response = requests.get(url, params=params, timeout=10)
    print(f"状态码: {response.status_code}")
    print()

    data = response.json()

    if data and 'result' in data and data['result'] and 'data' in data['result']:
        items = data['result']['data']
        print(f"✅ 成功获取 {len(items)} 条数据")
        print()

        print("最近10天北向资金流向:")
        print("-" * 70)
        print(f"{'日期':<12} {'类型':<10} {'资金流入':<12} {'净成交额':<12} {'买入':<12} {'卖出':<12}")
        print("-" * 70)

        for item in items:
            date = str(item.get('TRADE_DATE', ''))[:10]
            mtype = item.get('MUTUAL_TYPE', '')
            fund_inflow = item.get('FUND_INFLOW')
            net_deal = item.get('NET_DEAL_AMT')
            buy_amt = item.get('BUY_AMT')
            sell_amt = item.get('SELL_AMT')

            # 转换为亿
            if fund_inflow:
                fund_inflow = f"{float(fund_inflow)/100000000:.2f}亿"
            else:
                fund_inflow = "N/A"

            if net_deal:
                net_deal = f"{float(net_deal)/100000000:.2f}亿"
            else:
                net_deal = "N/A"

            if buy_amt:
                buy_amt = f"{float(buy_amt)/100000000:.2f}亿"
            else:
                buy_amt = "N/A"

            if sell_amt:
                sell_amt = f"{float(sell_amt)/100000000:.2f}亿"
            else:
                sell_amt = "N/A"

            # MUTUAL_TYPE: 1=沪股通, 2=深股通, 3=港股通沪, 4=港股通深
            type_name = {
                '1': '沪股通',
                '2': '深股通',
                '3': '港股通沪',
                '4': '港股通深'
            }.get(str(mtype), str(mtype))

            print(f"{date:<12} {type_name:<10} {fund_inflow:<12} {net_deal:<12} {buy_amt:<12} {sell_amt:<12}")

        print()
        print("="*70)
        print("第一条完整数据示例:")
        print("="*70)
        for key, value in items[0].items():
            print(f"  {key:20s} = {value}")

        print()
        print("="*70)
        print("✅ 这个API完美符合需求！")
        print("="*70)
        print()
        print("关键字段说明:")
        print("  TRADE_DATE     - 交易日期")
        print("  MUTUAL_TYPE    - 类型 (1=沪股通, 2=深股通)")
        print("  NET_DEAL_AMT   - 净买入额（我们需要的主要数据）")
        print("  BUY_AMT        - 买入金额")
        print("  SELL_AMT       - 卖出金额")
        print()

    else:
        print("❌ 数据格式异常")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500])

except Exception as e:
    print(f"❌ 请求失败: {e}")
    import traceback
    traceback.print_exc()

input("\n按回车键退出...")
