#!/usr/bin/env python3
"""
测试Tushare Pro集成
验证北向资金和市场概览功能
"""

import os
import sys


def test_tushare_token():
    """测试Tushare Token配置"""
    print("=" * 80)
    print("🧪 测试1: Tushare Token配置")
    print("=" * 80)

    token = os.getenv('TUSHARE_TOKEN')
    if token:
        print(f"✅ 已配置TUSHARE_TOKEN: {token[:10]}...")
        return True
    else:
        print("⚠️  未配置TUSHARE_TOKEN环境变量")
        print("💡 系统将使用东方财富数据源作为备用")
        return False


def test_tushare_service():
    """测试Tushare Pro服务"""
    print("\n" + "=" * 80)
    print("🧪 测试2: Tushare Pro数据服务")
    print("=" * 80)

    try:
        from tushare_pro_service import TushareProService

        token = os.getenv('TUSHARE_TOKEN')
        if not token:
            print("⏭️  跳过（未配置token）")
            return False

        service = TushareProService(token=token)
        print("✅ Tushare Pro服务初始化成功")

        # 测试北向资金
        print("\n📊 测试北向资金接口...")
        north_data = service.get_north_bound_flow(days=3)
        if north_data:
            print(f"✅ 成功获取{len(north_data)}天北向资金数据")
            print(f"   最新数据: {north_data[0]}")
        else:
            print("⚠️  北向资金数据为空（可能是积分不足或非交易日）")

        # 测试市场概览
        print("\n📈 测试市场概览接口...")
        market_data = service.get_market_overview()
        if market_data:
            print(f"✅ 成功获取市场概况")
            if 'total_stocks' in market_data:
                print(f"   总股票数: {market_data['total_stocks']}")
                print(f"   上涨: {market_data.get('up_stocks', 'N/A')}")
                print(f"   下跌: {market_data.get('down_stocks', 'N/A')}")
            else:
                print("   ⚠️  数据不完整")
        else:
            print("⚠️  市场概况数据为空（可能是积分不足或非交易日）")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_capital_flow_service():
    """测试资金流向择时服务"""
    print("\n" + "=" * 80)
    print("🧪 测试3: 资金流向择时服务（集成测试）")
    print("=" * 80)

    try:
        from capital_flow_timing_service import CapitalFlowTimingService

        service = CapitalFlowTimingService(use_tushare=True)
        print("✅ 资金流向择时服务初始化成功")

        print("\n📊 测试北向资金流向...")
        north_history = service.get_north_bound_flow_history(days=5)
        if north_history:
            print(f"✅ 成功获取{len(north_history)}天数据")
            if north_history[0]:
                data_source = north_history[0].get('source', '未知')
                print(f"   数据源: {data_source}")
                print(f"   最新日期: {north_history[0].get('date', 'N/A')}")
                print(f"   净流入: {north_history[0].get('total_flow', 0)}亿元")
        else:
            print("⚠️  未获取到北向资金数据")

        print("\n🎯 测试综合择时数据...")
        timing_data = service.get_comprehensive_timing_data()
        if timing_data:
            print("✅ 成功获取综合择时数据")
            signal = timing_data.get('timing_signal', {})
            print(f"   择时信号: {signal.get('suggestion', 'N/A')}")
            print(f"   综合评分: {signal.get('score', 0)}")
            print(f"   信号数量: {len(signal.get('signals', []))}")
        else:
            print("⚠️  未获取到综合择时数据")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_index_service():
    """测试市场指数服务"""
    print("\n" + "=" * 80)
    print("🧪 测试4: 市场指数服务（集成测试）")
    print("=" * 80)

    try:
        from market_index_service import MarketIndexProvider

        provider = MarketIndexProvider(use_tushare=True)
        print("✅ 市场指数服务初始化成功")

        print("\n📈 测试市场概览...")
        overview = provider._get_market_overview()
        if overview:
            print("✅ 成功获取市场概览")
            if 'total_stocks' in overview:
                print(f"   总股票数: {overview['total_stocks']}")
                print(f"   上涨: {overview.get('up_stocks', 'N/A')}")
                print(f"   下跌: {overview.get('down_stocks', 'N/A')}")
                print(f"   数据源: {overview.get('source', '未知')}")
            else:
                print("   ⚠️  数据不完整（可能使用了备用数据源）")
        else:
            print("⚠️  未获取到市场概览数据")

        print("\n📊 测试主要指数数据...")
        indices_data = provider.get_main_indices_data()
        if indices_data:
            print("✅ 成功获取主要指数数据")
            indices = indices_data.get('indices', {})
            print(f"   指数数量: {len(indices)}")
            market_status = indices_data.get('market_status', {})
            print(f"   市场状态: {market_status.get('status', 'N/A')}")
        else:
            print("⚠️  未获取到主要指数数据")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n🚀 开始测试Tushare Pro集成...")
    print()

    results = []

    # 测试1: Token配置
    has_token = test_tushare_token()
    results.append(("Token配置", has_token or "使用备用数据源"))

    # 测试2: Tushare服务（仅当有token时）
    if has_token:
        tushare_ok = test_tushare_service()
        results.append(("Tushare Pro服务", tushare_ok))

    # 测试3: 资金流向服务
    capital_ok = test_capital_flow_service()
    results.append(("资金流向服务", capital_ok))

    # 测试4: 市场指数服务
    market_ok = test_market_index_service()
    results.append(("市场指数服务", market_ok))

    # 总结
    print("\n" + "=" * 80)
    print("📋 测试总结")
    print("=" * 80)

    for name, result in results:
        if result is True:
            status = "✅ 通过"
        elif result is False:
            status = "❌ 失败"
        else:
            status = f"⚠️  {result}"
        print(f"{name:20s}: {status}")

    print("\n" + "=" * 80)
    passed = sum(1 for _, r in results if r is True)
    total = len([r for _, r in results if r is not False])

    if passed == len(results):
        print("🎉 所有测试通过！")
    elif passed > 0:
        print(f"✅ {passed}/{total} 项测试通过")
        print("💡 部分功能可能需要配置Tushare Pro token")
    else:
        print("⚠️  测试未完全通过，请检查配置")

    print("\n💡 提示:")
    if not has_token:
        print("   - 未配置TUSHARE_TOKEN，系统使用东方财富数据源")
        print("   - 这是正常的，功能不受影响")
        print("   - 如需使用Tushare Pro，请参考 TUSHARE_PRO_SETUP.md")
    else:
        print("   - 已配置Tushare Pro，优先使用Tushare数据源")
        print("   - 如遇到问题会自动回退到东方财富数据源")
        print("   - 查看日志了解详细的数据源使用情况")

    print("=" * 80)


if __name__ == "__main__":
    main()
