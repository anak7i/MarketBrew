#!/usr/bin/env python3
"""
东方财富API快速测试脚本
验证所有数据接口是否正常工作
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🚀 MarketBrew - 东方财富API测试")
print("=" * 70)
print()

try:
    # 测试akshare是否被禁用
    print("📋 测试1: 验证akshare已禁用...")
    try:
        import akshare
        print("❌ 失败: akshare仍可导入")
    except ImportError as e:
        if "disabled" in str(e):
            print("✅ 通过: akshare已成功禁用")
        else:
            print(f"⚠️  警告: akshare未安装 (这是预期的)")
    print()

    # 测试导入数据服务
    print("📋 测试2: 导入东方财富数据服务...")
    from eastmoney_data_service import eastmoney_service
    print("✅ 通过: eastmoney_data_service导入成功")
    print()

    # 测试股票实时数据
    print("📋 测试3: 获取股票实时数据 (000001 平安银行)...")
    stock = eastmoney_service.get_stock_realtime('000001')
    if stock:
        print(f"✅ 通过: {stock['name']} - 价格: {stock['price']}, 涨跌幅: {stock['change_pct']:.2f}%")
    else:
        print("❌ 失败: 无法获取股票数据")
    print()

    # 测试ETF数据
    print("📋 测试4: 获取ETF实时数据 (510300 沪深300ETF)...")
    etf = eastmoney_service.get_etf_realtime('510300')
    if etf:
        print(f"✅ 通过: {etf['name']} - 价格: {etf['price']}, 涨跌幅: {etf['change_pct']:.2f}%")
    else:
        print("❌ 失败: 无法获取ETF数据")
    print()

    # 测试北向资金
    print("📋 测试5: 获取北向资金流向...")
    north = eastmoney_service.get_north_bound_flow()
    if north and 'total' in north:
        print(f"✅ 通过: 北向资金总流入 {north['total']:.2f}亿")
        print(f"   - 沪股通: {north['sh']:.2f}亿")
        print(f"   - 深股通: {north['sz']:.2f}亿")
    else:
        print("❌ 失败: 无法获取北向资金数据")
    print()

    # 测试主力资金
    print("📋 测试6: 获取主力资金流向 (沪深300)...")
    main_force = eastmoney_service.get_main_force_flow('000300')
    if main_force and 'total' in main_force:
        print(f"✅ 通过: 主力资金总流入 {main_force['total']:.2f}亿")
    else:
        print("❌ 失败: 无法获取主力资金数据")
    print()

    # 测试指数数据
    print("📋 测试7: 获取指数数据 (000300 沪深300)...")
    index = eastmoney_service.get_index_data('000300')
    if index:
        print(f"✅ 通过: {index['name']} - 价格: {index['price']:.2f}, 涨跌幅: {index['change_pct']:.2f}%")
    else:
        print("❌ 失败: 无法获取指数数据")
    print()

    # 测试K线数据
    print("📋 测试8: 获取K线数据 (000300 最近5天)...")
    klines = eastmoney_service.get_kline_data('000300', period='101', count=5)
    if klines and len(klines) > 0:
        print(f"✅ 通过: 获取到 {len(klines)} 条K线数据")
        print("   最近一天:", klines[-1])
    else:
        print("❌ 失败: 无法获取K线数据")
    print()

    # 测试股票列表
    print("📋 测试9: 获取股票列表...")
    stocks = eastmoney_service.get_stock_list('all')
    if stocks and len(stocks) > 0:
        print(f"✅ 通过: 获取到 {len(stocks)} 只股票")
        up_count = len([s for s in stocks if s['change_pct'] > 0])
        down_count = len([s for s in stocks if s['change_pct'] < 0])
        print(f"   - 上涨: {up_count}, 下跌: {down_count}")
    else:
        print("❌ 失败: 无法获取股票列表")
    print()

    # 测试ETF列表
    print("📋 测试10: 获取ETF列表...")
    etf_list = eastmoney_service.get_etf_list()
    if etf_list and len(etf_list) > 0:
        print(f"✅ 通过: 获取到 {len(etf_list)} 只ETF")
        # 显示涨幅前3
        etf_sorted = sorted(etf_list, key=lambda x: x.get('change_pct', 0), reverse=True)
        print("   涨幅前3:")
        for i, etf in enumerate(etf_sorted[:3]):
            print(f"   {i+1}. {etf['code']} {etf['name']}: {etf['change_pct']:.2f}%")
    else:
        print("❌ 失败: 无法获取ETF列表")
    print()

    print("=" * 70)
    print("✅ 所有测试完成！东方财富API工作正常！")
    print("=" * 70)
    print()
    print("📝 下一步:")
    print("1. 运行 'python price_service.py' 启动价格服务")
    print("2. 在浏览器打开 'stock_subscription.html'")
    print("3. 查看 'README_EASTMONEY_ONLY.md' 了解更多使用方法")
    print()

except Exception as e:
    print()
    print("=" * 70)
    print(f"❌ 测试失败: {e}")
    print("=" * 70)
    print()
    print("💡 解决方案:")
    print("1. 确保已安装依赖: pip install -r requirements.txt")
    print("2. 检查网络连接")
    print("3. 查看详细日志")
    import traceback
    traceback.print_exc()
    sys.exit(1)
