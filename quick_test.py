#!/usr/bin/env python3
"""快速测试脚本"""

print("=" * 60)
print("🚀 东方财富API快速测试")
print("=" * 60)

# 测试1: 导入
print("\n[1/5] 导入数据服务...")
try:
    from eastmoney_data_service import eastmoney_service
    print("✅ 导入成功")
except Exception as e:
    print(f"❌ 导入失败: {e}")
    exit(1)

# 测试2: 股票数据
print("\n[2/5] 获取股票数据 (000001)...")
try:
    stock = eastmoney_service.get_stock_realtime('000001')
    if stock:
        print(f"✅ {stock['name']}: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
    else:
        print("⚠️ 无数据返回")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试3: ETF数据
print("\n[3/5] 获取ETF数据 (510300)...")
try:
    etf = eastmoney_service.get_etf_realtime('510300')
    if etf:
        print(f"✅ {etf['name']}: ¥{etf['price']:.2f} ({etf['change_pct']:+.2f}%)")
    else:
        print("⚠️ 无数据返回")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试4: 北向资金
print("\n[4/5] 获取北向资金...")
try:
    north = eastmoney_service.get_north_bound_flow()
    if north and 'total' in north:
        print(f"✅ 总流入: {north['total']:.2f}亿 (沪: {north['sh']:.2f}亿, 深: {north['sz']:.2f}亿)")
    else:
        print("⚠️ 无数据返回")
except Exception as e:
    print(f"❌ 错误: {e}")

# 测试5: 指数数据
print("\n[5/5] 获取沪深300指数...")
try:
    index = eastmoney_service.get_index_data('000300')
    if index:
        print(f"✅ {index['name']}: {index['price']:.2f} ({index['change_pct']:+.2f}%)")
    else:
        print("⚠️ 无数据返回")
except Exception as e:
    print(f"❌ 错误: {e}")

print("\n" + "=" * 60)
print("✅ 测试完成！")
print("=" * 60)
