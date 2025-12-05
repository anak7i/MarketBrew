#!/usr/bin/env python3
"""
EMT API Python 包装器
使用 ctypes 调用东方财富证券 EMT API DLL

⚠️ 注意：使用此 API 需要东方财富证券账号和 EMT API 权限
如果没有账号，请使用 eastmoney_data_service.py (免费，无需账号)
"""

import ctypes
import os
import sys
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EMTQuoteClient:
    """
    EMT 行情 API Python 客户端

    ⚠️ 使用前提：
    1. 拥有东方财富证券账号
    2. 已开通 EMT API 权限
    3. 获取服务器地址、端口、用户名、密码

    示例：
        client = EMTQuoteClient()
        client.login("xxx.xxx.xxx.xxx", 12345, "username", "password")
        data = client.get_market_data("000001")
    """

    def __init__(self, dll_path: str = None):
        """
        初始化 EMT Quote客户端

        Args:
            dll_path: DLL文件路径，默认为项目目录下的 emt_api/emt_quote_api.dll
        """
        if dll_path is None:
            # 默认DLL路径
            dll_path = os.path.join(
                os.path.dirname(__file__),
                'emt_api',
                'emt_quote_api.dll'
            )

        if not os.path.exists(dll_path):
            raise FileNotFoundError(
                f"EMT API DLL 未找到: {dll_path}\n"
                f"请确保 emt_api 目录存在并包含 DLL 文件"
            )

        try:
            self.dll = ctypes.CDLL(dll_path)
            logger.info(f"✅ EMT Quote API DLL 加载成功: {dll_path}")
        except Exception as e:
            raise RuntimeError(f"加载 EMT API DLL 失败: {e}")

        self.is_connected = False
        self.api_instance = None

    def login(self, server_ip: str, port: int, username: str, password: str) -> bool:
        """
        登录 EMT 行情服务器

        Args:
            server_ip: 服务器IP地址
            port: 服务器端口
            username: 用户名
            password: 密码

        Returns:
            是否登录成功

        ⚠️ 需要有效的东方财富证券账号和 EMT API 权限
        """
        logger.info("=" * 60)
        logger.info("EMT API 登录")
        logger.info("=" * 60)
        logger.warning("⚠️  此功能需要东方财富证券账号和 EMT API 权限")
        logger.warning("⚠️  如果没有账号，请使用 eastmoney_data_service.py")
        logger.info("=" * 60)

        # 注意：实际的登录逻辑需要根据 EMT API 文档实现
        # 这里只是一个示例框架

        logger.error("❌ EMT API 登录未实现")
        logger.info("💡 原因：需要 C++ API 的完整封装")
        logger.info("💡 建议：使用 HTTP API (eastmoney_data_service.py)")

        return False

    def subscribe_market_data(self, symbols: List[str]) -> bool:
        """
        订阅行情数据

        Args:
            symbols: 股票代码列表，如 ["000001", "600519"]

        Returns:
            是否订阅成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到服务器，请先调用 login()")
            return False

        # 实际实现需要根据 EMT API 文档
        logger.warning("⚠️  订阅功能需要完整的 C++ API 封装")
        return False

    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        获取行情数据

        Args:
            symbol: 股票代码，如 "000001"

        Returns:
            行情数据字典，如果失败返回 None
        """
        if not self.is_connected:
            logger.error("❌ 未连接到服务器，请先调用 login()")
            return None

        # 实际实现需要根据 EMT API 文档
        logger.warning("⚠️  数据获取功能需要完整的 C++ API 封装")
        return None

    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            # 实际断开逻辑
            self.is_connected = False
            logger.info("🔌 已断开 EMT API 连接")


class EMTTraderClient:
    """
    EMT 交易 API Python 客户端

    ⚠️ 使用前提：
    1. 拥有东方财富证券账号
    2. 已开通 EMT API 权限
    3. 用于实盘交易需要额外审批
    """

    def __init__(self, dll_path: str = None):
        """初始化 EMT Trader 客户端"""
        if dll_path is None:
            dll_path = os.path.join(
                os.path.dirname(__file__),
                'emt_api',
                'emt_trader_api_c.dll'
            )

        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"EMT Trader API DLL 未找到: {dll_path}")

        try:
            self.dll = ctypes.CDLL(dll_path)
            logger.info(f"✅ EMT Trader API DLL 加载成功: {dll_path}")
        except Exception as e:
            raise RuntimeError(f"加载 EMT Trader API DLL 失败: {e}")

        self.is_connected = False

    def login(self, server_ip: str, port: int, username: str, password: str) -> bool:
        """登录交易服务器"""
        logger.warning("⚠️  交易 API 功能需要完整的 C++ API 封装和额外权限")
        logger.warning("⚠️  实盘交易风险极高，请谨慎使用")
        return False


def check_emt_api_available() -> bool:
    """
    检查 EMT API 是否可用

    Returns:
        True 如果 DLL 文件存在
    """
    dll_path = os.path.join(
        os.path.dirname(__file__),
        'emt_api',
        'emt_quote_api.dll'
    )
    return os.path.exists(dll_path)


def get_recommendation() -> str:
    """
    获取 API 使用建议

    Returns:
        建议信息字符串
    """
    return """
╔══════════════════════════════════════════════════════════════╗
║              EMT API vs HTTP API 使用建议                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ✅ 推荐使用 HTTP API (免费，无需账号)                        ║
║                                                              ║
║     from eastmoney_data_service import eastmoney_service    ║
║     stock = eastmoney_service.get_stock_realtime('000001')  ║
║                                                              ║
║  优势：                                                       ║
║    • 完全免费                                                ║
║    • 无需账号                                                ║
║    • 简单易用                                                ║
║    • 数据准确                                                ║
║    • 实时更新                                                ║
║                                                              ║
║  📊 EMT API 适用场景：                                       ║
║    • 专业量化交易                                             ║
║    • 毫秒级数据需求                                           ║
║    • 需要交易功能                                             ║
║    • 已有东财账号和权限                                        ║
║                                                              ║
║  💡 提示：                                                   ║
║     EMT API 需要完整的 C++ 封装才能在 Python 中使用           ║
║     建议专业用户联系东方财富证券获取官方 Python SDK            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


# 测试和示例
def main():
    """测试函数"""
    print("=" * 60)
    print("EMT API Python 包装器测试")
    print("=" * 60)
    print()

    # 检查 DLL 是否存在
    print("[1/3] 检查 EMT API DLL...")
    if check_emt_api_available():
        print("✅ EMT API DLL 文件存在")
    else:
        print("❌ EMT API DLL 文件不存在")
        print("💡 请确保 emt_api 目录包含所需的 DLL 文件")
        return

    print()

    # 创建客户端实例
    print("[2/3] 创建 EMT Quote 客户端...")
    try:
        client = EMTQuoteClient()
        print("✅ 客户端创建成功")
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        return

    print()

    # 显示使用建议
    print("[3/3] 使用建议:")
    print(get_recommendation())

    print()
    print("=" * 60)
    print("测试完成")
    print("=" * 60)
    print()
    print("💡 如需实际使用 EMT API:")
    print("   1. 开通东方财富证券账号")
    print("   2. 申请 EMT API 权限")
    print("   3. 获取服务器地址、端口、账号密码")
    print("   4. 联系东方财富获取官方 Python SDK（推荐）")
    print()
    print("💡 或者继续使用 HTTP API（推荐）:")
    print("   from eastmoney_data_service import eastmoney_service")
    print()


if __name__ == "__main__":
    main()
