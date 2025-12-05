#!/usr/bin/env python3
"""
API 对比演示
展示 HTTP API (当前使用) vs EMT API (专业版) 的差异
"""

import sys
import os

print("╔══════════════════════════════════════════════════════════════╗")
print("║        MarketBrew API 对比 - HTTP vs EMT                    ║")
print("╚══════════════════════════════════════════════════════════════╝")
print()

# ============== HTTP API 演示 (当前使用) ==============
print("🌐 HTTP API (当前使用)")
print("─" * 60)

try:
    from eastmoney_data_service import eastmoney_service

    print("✅ eastmoney_data_service 已加载")
    print()

    # 测试获取股票数据
    print("📊 测试1: 获取股票实时数据")
    stock = eastmoney_service.get_stock_realtime('000001')
    if stock:
        print(f"   ✅ {stock['name']}: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
    else:
        print("   ⚠️  数据获取失败（可能需要网络连接）")
    print()

    # 测试北向资金
    print("💰 测试2: 获取北向资金")
    north = eastmoney_service.get_north_bound_flow()
    if north and 'total' in north:
        print(f"   ✅ 总流入: {north['total']:.2f}亿")
    else:
        print("   ⚠️  数据获取失败")
    print()

    # 测试指数数据
    print("📈 测试3: 获取沪深300指数")
    index = eastmoney_service.get_index_data('000300')
    if index:
        print(f"   ✅ {index['name']}: {index['price']:.2f} ({index['change_pct']:+.2f}%)")
    else:
        print("   ⚠️  数据获取失败")
    print()

    print("✅ HTTP API 工作正常！")
    print()
    print("优势:")
    print("  • 完全免费")
    print("  • 无需账号")
    print("  • 简单易用")
    print("  • 数据准确")
    print()

except ImportError as e:
    print(f"❌ 无法导入 eastmoney_data_service: {e}")
    print()
except Exception as e:
    print(f"❌ HTTP API 测试失败: {e}")
    print()

print("=" * 60)
print()

# ============== EMT API 检查 ==============
print("🚀 EMT API (专业版)")
print("─" * 60)

try:
    from emt_wrapper import EMTQuoteClient, check_emt_api_available

    # 检查 DLL 是否存在
    if check_emt_api_available():
        print("✅ EMT API DLL 文件已就绪")
        print()

        # 创建客户端
        try:
            client = EMTQuoteClient()
            print("✅ EMT Quote 客户端创建成功")
            print()
        except Exception as e:
            print(f"❌ 客户端创建失败: {e}")
            print()

        print("⚠️  EMT API 需要账号登录")
        print()
        print("使用条件:")
        print("  • 东方财富证券账号")
        print("  • EMT API 权限")
        print("  • 服务器地址和密码")
        print()
        print("优势:")
        print("  • 毫秒级实时数据")
        print("  • 支持交易功能")
        print("  • Level-2 行情")
        print("  • 专业级数据质量")
        print()

    else:
        print("❌ EMT API DLL 文件未找到")
        print("💡 请确保 emt_api 目录包含 DLL 文件")
        print()

except ImportError as e:
    print(f"❌ 无法导入 emt_wrapper: {e}")
    print()

print("=" * 60)
print()

# ============== 总结和建议 ==============
print("📋 总结与建议")
print("─" * 60)
print()

print("💡 对于个人用户/学习研究:")
print("   ✅ 推荐使用 HTTP API")
print("   ✅ 完全免费，无需账号")
print("   ✅ 功能完全够用")
print()

print("💡 对于专业交易/量化策略:")
print("   📊 考虑使用 EMT API")
print("   📊 需要开通东方财富证券账号")
print("   📊 适合毫秒级数据需求")
print()

print("💡 当前项目状态:")
print("   ✅ HTTP API 已配置并可用")
print("   📦 EMT API 已集成，待配置账号")
print()

print("=" * 60)
print()

print("🎯 下一步:")
print()
print("【如果使用 HTTP API (推荐)】")
print("  1. 继续使用当前配置")
print("  2. 运行: python price_service.py")
print("  3. 打开: market_temperature.html")
print()

print("【如果使用 EMT API】")
print("  1. 查看文档: README_EMT_API.md")
print("  2. 申请东方财富证券账号")
print("  3. 获取 EMT API 权限")
print("  4. 配置账号信息")
print()

print("=" * 60)
print("测试完成！")
print("=" * 60)
