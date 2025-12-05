#!/usr/bin/env python3
"""
东方财富API统一配置
所有数据获取统一使用东方财富API，不使用akshare
"""

import sys
import os

# 强制使用东方财富API
USE_EASTMONEY_ONLY = True
DISABLE_AKSHARE = True

# 数据源配置
DATA_SOURCE_CONFIG = {
    'stock_data': 'eastmoney',      # 股票数据：东方财富
    'etf_data': 'eastmoney',        # ETF数据：东方财富
    'index_data': 'eastmoney',      # 指数数据：东方财富
    'north_bound': 'eastmoney',     # 北向资金：东方财富
    'main_force': 'eastmoney',      # 主力资金：东方财富
    'market_mood': 'eastmoney',     # 市场情绪：东方财富
    'news': 'eastmoney',            # 新闻：东方财富
    'announcement': 'eastmoney'     # 公告：东方财富
}

# 东方财富API端点
EASTMONEY_ENDPOINTS = {
    'stock_list': 'https://datacenter-web.eastmoney.com/api/qt/clist/get',
    'stock_detail': 'https://datacenter-web.eastmoney.com/api/qt/stock/get',
    'north_bound': 'https://datacenter-web.eastmoney.com/api/qt/kamt.rtmin/get',
    'etf_list': 'https://datacenter-web.eastmoney.com/api/qt/clist/get',
    'index_data': 'https://datacenter-web.eastmoney.com/api/qt/stock/get',
    'kline': 'https://push2his.eastmoney.com/api/qt/stock/kline/get',
    'news': 'https://search-api-web.eastmoney.com/search/jsonp',
    'announcement': 'https://datacenter-web.eastmoney.com/api/data/v1/get'
}

# API请求配置
REQUEST_CONFIG = {
    'timeout': 10,
    'retry': 3,
    'cache_duration': 60,  # 缓存60秒
    'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

# 市场代码映射
MARKET_CODES = {
    'A股主板': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',
    '沪深300': 'i:000300',
    '上证50': 'i:000016',
    '创业板': 'm:0 t:80',
    'ETF': 'b:MK0021,b:MK0022,b:MK0023,b:MK0024',
    '科创板': 'm:1 t:23'
}

# 禁用akshare导入
if DISABLE_AKSHARE:
    import sys
    class AkShareBlocker:
        def find_module(self, fullname, path=None):
            if fullname == 'akshare':
                return self
            return None

        def load_module(self, fullname):
            raise ImportError(
                f"akshare is disabled. Use eastmoney_api_enhanced instead.\n"
                f"该项目已配置为只使用东方财富API，akshare已被禁用。"
            )

    # 安装导入钩子
    sys.meta_path.insert(0, AkShareBlocker())

print("✅ 东方财富API配置已加载 - akshare已禁用，所有数据源使用东方财富")
