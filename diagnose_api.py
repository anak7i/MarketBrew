#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API诊断脚本 - 检查数据获取问题
"""

import sys
import io
import requests
import json
from datetime import datetime

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("AlphaBloom 数据获取诊断")
print("=" * 80)
print()

# 1. 测试基础连接
print("[1/5] 测试网络连接...")
try:
    r = requests.get('https://www.eastmoney.com', timeout=5)
    print(f"✓ 东方财富网连接正常 (状态码: {r.status_code})")
except Exception as e:
    print(f"✗ 网络连接失败: {e}")
print()

# 2. 测试北向资金API
print("[2/5] 测试北向资金API...")
try:
    url = "https://datacenter-web.eastmoney.com/api/hsgt/hist/query"
    params = {
        'type': '1',
        'pageSize': '5',
        'pageNum': '1',
        'sortField': 'TRADE_DATE',
        'sortType': 'desc'
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    print(f"状态码: {r.status_code}")
    print(f"响应长度: {len(r.text)} 字节")

    if data and 'data' in data:
        if 'data' in data['data'] and data['data']['data']:
            print(f"✓ 获取到 {len(data['data']['data'])} 条北向资金数据")
            print(f"最新数据示例: {data['data']['data'][0]}")
        else:
            print(f"✗ 数据为空")
            print(f"响应内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
    else:
        print(f"✗ 响应格式异常")
        print(f"响应内容: {r.text[:200]}")
except Exception as e:
    print(f"✗ 请求失败: {e}")
print()

# 3. 测试股票实时数据API
print("[3/5] 测试股票实时数据API...")
try:
    url = "https://datacenter-web.eastmoney.com/api/qt/stock/get"
    params = {
        'secid': '1.000001',  # 上证指数
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
        'fields': 'f43,f44,f45,f46,f57,f58'
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    print(f"状态码: {r.status_code}")

    if data and 'data' in data and data['data']:
        print(f"✓ 获取到上证指数数据")
        print(f"数据: {data['data']}")
    else:
        print(f"✗ 数据为空")
        print(f"响应: {json.dumps(data, ensure_ascii=False)}")
except Exception as e:
    print(f"✗ 请求失败: {e}")
print()

# 4. 测试主力资金API
print("[4/5] 测试主力资金API...")
try:
    url = "https://datacenter-web.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': '1',
        'pz': '5',
        'po': '1',
        'np': '1',
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': '2',
        'invt': '2',
        'fid': 'f62',
        'fs': 'i:000300',
        'fields': 'f12,f14,f62'
    }
    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    print(f"状态码: {r.status_code}")

    if data and 'data' in data and 'diff' in data['data']:
        print(f"✓ 获取到 {len(data['data']['diff'])} 只股票的主力资金数据")
        if data['data']['diff']:
            print(f"示例: {data['data']['diff'][0]}")
    else:
        print(f"✗ 数据为空")
        print(f"响应: {json.dumps(data, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"✗ 请求失败: {e}")
print()

# 5. 测试当前时间
print("[5/5] 检查交易时间...")
now = datetime.now()
print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"星期: {['一', '二', '三', '四', '五', '六', '日'][now.weekday()]}")

weekday = now.weekday()
hour = now.hour
minute = now.minute

is_trading_day = weekday < 5  # 周一到周五
is_trading_time = (
    (9 <= hour < 15) or  # 9:00-15:00
    (hour == 15 and minute == 0)  # 15:00
)

if not is_trading_day:
    print("⚠ 当前是周末，非交易日")
elif not is_trading_time:
    print("⚠ 当前是非交易时间")
else:
    print("✓ 当前是交易时间")
print()

# 总结
print("=" * 80)
print("诊断总结")
print("=" * 80)
print()
print("如果北向资金API返回空数据，可能原因：")
print("1. 当前非交易时间（周末或盘后）")
print("2. API接口参数需要调整")
print("3. 东方财富API限流")
print()
print("建议：")
print("1. 在交易时间（周一至周五 9:30-15:00）重新测试")
print("2. 使用模拟数据进行界面演示")
print("3. 检查网络代理设置")
print()
