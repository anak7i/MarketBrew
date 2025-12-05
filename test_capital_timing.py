#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金流向择时服务测试脚本
"""

import sys
import io
import logging
from capital_flow_timing_service import timing_service
from eastmoney_data_service import eastmoney_service

# 设置输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def test_eastmoney_basic():
    """测试东方财富基础服务"""
    print("\n" + "=" * 80)
    print("测试1: 东方财富基础数据服务")
    print("=" * 80)

    # 测试北向资金
    print("\n[1.1] 测试北向资金实时数据...")
    north = eastmoney_service.get_north_bound_flow()
    print(f"结果: {north}")

    # 测试主力资金
    print("\n[1.2] 测试主力资金...")
    main = eastmoney_service.get_main_force_flow()
    print(f"结果: {main}")

    # 测试股票数据
    print("\n[1.3] 测试股票实时数据...")
    stock = eastmoney_service.get_stock_realtime('000001')
    print(f"结果: {stock}")

    return north, main, stock


def test_capital_timing_service():
    """测试资金流向择时服务"""
    print("\n" + "=" * 80)
    print("测试2: 资金流向择时服务")
    print("=" * 80)

    # 测试北向资金历史
    print("\n[2.1] 测试北向资金历史数据 (7天)...")
    try:
        north_history = timing_service.get_north_bound_flow_history(days=7)
        print(f"获取到 {len(north_history)} 天数据")
        if north_history:
            print(f"最新数据: {north_history[0]}")
    except Exception as e:
        print(f"错误: {e}")
        logger.exception("获取北向资金历史数据失败")

    # 测试ETF资金流历史
    print("\n[2.2] 测试ETF资金流历史数据 (7天)...")
    try:
        etf_history = timing_service.get_etf_flow_history(days=7)
        print(f"获取到 {len(etf_history)} 天数据")
        if etf_history:
            print(f"最新数据: {etf_history[0]}")
    except Exception as e:
        print(f"错误: {e}")
        logger.exception("获取ETF资金流历史数据失败")

    # 测试主力资金历史
    print("\n[2.3] 测试主力资金历史数据 (7天)...")
    try:
        main_history = timing_service.get_main_force_flow_history(days=7)
        print(f"获取到 {len(main_history)} 天数据")
        if main_history:
            print(f"最新数据: {main_history[0]}")
    except Exception as e:
        print(f"错误: {e}")
        logger.exception("获取主力资金历史数据失败")


def test_comprehensive_data():
    """测试综合择时数据"""
    print("\n" + "=" * 80)
    print("测试3: 综合择时数据")
    print("=" * 80)

    try:
        print("\n[3.1] 获取综合择时数据...")
        data = timing_service.get_comprehensive_timing_data()

        print("\n北向资金:")
        print(f"  最新: {data['north_bound']['latest']}")
        print(f"  周期统计:")
        for period, stats in data['north_bound']['periods'].items():
            print(f"    {period}: 净流入 {stats['net_flow']}亿")

        print("\nETF资金:")
        print(f"  最新: {data['etf_flow']['latest']}")
        print(f"  周期统计:")
        for period, stats in data['etf_flow']['periods'].items():
            print(f"    {period}: 净流入 {stats['net_flow']}亿")

        print("\n主力资金:")
        print(f"  最新: {data['main_force']['latest']}")
        print(f"  周期统计:")
        for period, stats in data['main_force']['periods'].items():
            print(f"    {period}: 净流入 {stats['net_flow']}亿")

        print("\n择时信号:")
        signal = data['timing_signal']
        print(f"  评分: {signal['score']}")
        print(f"  级别: {signal['level']}")
        print(f"  建议: {signal['suggestion']}")
        print(f"  信号:")
        for s in signal['signals']:
            print(f"    - {s}")

        return True

    except Exception as e:
        print(f"错误: {e}")
        logger.exception("获取综合择时数据失败")
        return False


def main():
    print("=" * 80)
    print("AlphaBloom 资金流向择时服务测试")
    print("=" * 80)

    # 测试1: 东方财富基础服务
    try:
        test_eastmoney_basic()
    except Exception as e:
        print(f"\n测试1失败: {e}")
        logger.exception("东方财富基础服务测试失败")

    # 测试2: 资金流向择时服务
    try:
        test_capital_timing_service()
    except Exception as e:
        print(f"\n测试2失败: {e}")
        logger.exception("资金流向择时服务测试失败")

    # 测试3: 综合择时数据
    success = False
    try:
        success = test_comprehensive_data()
    except Exception as e:
        print(f"\n测试3失败: {e}")
        logger.exception("综合择时数据测试失败")

    # 总结
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

    if success:
        print("\n状态: 所有测试通过")
        print("\n下一步:")
        print("1. 运行 start_capital_timing.bat 启动API服务")
        print("2. 在浏览器中打开 capital_timing.html 查看界面")
    else:
        print("\n状态: 部分测试失败")
        print("\n请检查:")
        print("1. 网络连接是否正常")
        print("2. 是否能访问东方财富网")
        print("3. 依赖包是否正确安装 (pip install flask flask-cors requests)")


if __name__ == "__main__":
    main()
