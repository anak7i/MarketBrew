#!/usr/bin/env python3
"""
东方财富统一数据服务
替代akshare，所有数据从东方财富API获取
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EastMoneyDataService:
    """东方财富统一数据服务"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.eastmoney.com/',
            'Accept': '*/*'
        })

        self.base_url = 'https://datacenter-web.eastmoney.com'
        self.quote_url = 'https://push2.eastmoney.com'
        self.cache = {}
        self.cache_duration = 60

    def get_stock_realtime(self, symbol: str) -> Optional[Dict]:
        """获取股票实时数据"""
        try:
            # 判断市场
            market = '1' if symbol.startswith('6') else '0'
            secid = f"{market}.{symbol}"

            url = f"{self.base_url}/api/qt/stock/get"
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f107,f152,f161,f162,f163,f164,f165,f166,f167,f168,f169,f170,f171'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'data' in data and data['data']:
                d = data['data']
                return {
                    'symbol': symbol,
                    'name': d.get('f58', ''),
                    'price': d.get('f43', 0) / 100,  # 当前价
                    'open': d.get('f46', 0) / 100,   # 开盘价
                    'high': d.get('f44', 0) / 100,   # 最高价
                    'low': d.get('f45', 0) / 100,    # 最低价
                    'volume': d.get('f47', 0),        # 成交量
                    'amount': d.get('f48', 0),        # 成交额
                    'change_pct': d.get('f170', 0) / 100,  # 涨跌幅
                    'change': d.get('f169', 0) / 100       # 涨跌额
                }

            logger.warning(f"获取{symbol}数据失败")
            return None

        except Exception as e:
            logger.error(f"获取{symbol}实时数据失败: {e}")
            return None

    def get_etf_realtime(self, symbol: str) -> Optional[Dict]:
        """获取ETF实时数据"""
        return self.get_stock_realtime(symbol)

    def get_etf_list(self) -> List[Dict]:
        """获取ETF列表"""
        cache_key = "etf_list"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            url = f"{self.base_url}/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': '1000',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'b:MK0021,b:MK0022,b:MK0023,b:MK0024',  # ETF
                'fields': 'f12,f14,f2,f3,f4,f5,f6,f7,f15,f16,f17,f18'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'data' in data and 'diff' in data['data']:
                etf_list = []
                for item in data['data']['diff']:
                    etf_list.append({
                        'code': item.get('f12', ''),
                        'name': item.get('f14', ''),
                        'price': item.get('f2', 0) / 100,
                        'change_pct': item.get('f3', 0) / 100,
                        'change': item.get('f4', 0) / 100,
                        'volume': item.get('f5', 0),
                        'amount': item.get('f6', 0),
                        'amplitude': item.get('f7', 0) / 100
                    })

                self.cache[cache_key] = {'data': etf_list, 'timestamp': time.time()}
                logger.info(f"✅ 获取到{len(etf_list)}只ETF数据")
                return etf_list

            return []

        except Exception as e:
            logger.error(f"获取ETF列表失败: {e}")
            return []

    def get_stock_list(self, market: str = 'all') -> List[Dict]:
        """获取股票列表"""
        try:
            # 市场筛选
            market_filter = {
                'all': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',
                'sh': 'm:1 t:2,m:1 t:23',
                'sz': 'm:0 t:6,m:0 t:80',
                'cyb': 'm:0 t:80',
                'kcb': 'm:1 t:23'
            }.get(market, 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23')

            url = f"{self.base_url}/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': '5000',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': market_filter,
                'fields': 'f12,f14,f2,f3,f4,f5,f6,f7,f8,f9,f10,f15,f16,f17,f18,f62'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'data' in data and 'diff' in data['data']:
                stock_list = []
                for item in data['data']['diff']:
                    stock_list.append({
                        'code': item.get('f12', ''),
                        'name': item.get('f14', ''),
                        'price': item.get('f2', 0) / 100,
                        'change_pct': item.get('f3', 0) / 100,
                        'volume': item.get('f5', 0),
                        'amount': item.get('f6', 0),
                        'turnover_rate': item.get('f8', 0) / 100,
                        'main_force_net': item.get('f62', 0)
                    })

                logger.info(f"✅ 获取到{len(stock_list)}只股票数据")
                return stock_list

            return []

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def get_north_bound_flow(self) -> Dict[str, float]:
        """获取北向资金流向"""
        cache_key = "north_bound"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            url = f"{self.base_url}/api/qt/kamt.rtmin/get"
            params = {
                'fields1': 'f1,f2,f3,f4',
                'fields2': 'f51,f52,f53,f54,f55,f56',
                'ut': 'b2884a393a59ad64002292a3e90d46a5'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'data' in data:
                hk2sh = data['data'].get('hk2sh', [])  # 沪股通
                hk2sz = data['data'].get('hk2sz', [])  # 深股通

                sh_flow = 0.0
                sz_flow = 0.0

                # 获取最新流入数据
                if hk2sh and len(hk2sh) > 0:
                    latest_sh = hk2sh[-1].split(',')
                    if len(latest_sh) >= 4:
                        sh_flow = float(latest_sh[3]) / 100000000  # 转为亿元

                if hk2sz and len(hk2sz) > 0:
                    latest_sz = hk2sz[-1].split(',')
                    if len(latest_sz) >= 4:
                        sz_flow = float(latest_sz[3]) / 100000000

                result = {
                    'total': round(sh_flow + sz_flow, 2),
                    'sh': round(sh_flow, 2),
                    'sz': round(sz_flow, 2),
                    'timestamp': datetime.now().isoformat()
                }

                self.cache[cache_key] = {'data': result, 'timestamp': time.time()}
                logger.info(f"✅ 北向资金: 沪{sh_flow:.1f}亿 + 深{sz_flow:.1f}亿 = {sh_flow+sz_flow:.1f}亿")
                return result

            return {'total': 0.0, 'sh': 0.0, 'sz': 0.0}

        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
            return {'total': 0.0, 'sh': 0.0, 'sz': 0.0}

    def get_main_force_flow(self, index_code: str = '000300') -> Dict[str, float]:
        """获取主力资金流向"""
        try:
            url = f"{self.base_url}/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': '300',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f62',
                'fs': f'i:{index_code}',
                'fields': 'f12,f14,f62'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'data' in data and 'diff' in data['data']:
                total_flow = sum(item.get('f62', 0) for item in data['data']['diff'])
                total_flow_yi = total_flow / 100000000

                result = {
                    'total': round(total_flow_yi, 2),
                    'sh': round(total_flow_yi * 0.6, 2),
                    'sz': round(total_flow_yi * 0.4, 2)
                }

                logger.info(f"✅ 主力资金: {total_flow_yi:.1f}亿")
                return result

            return {'total': 0.0, 'sh': 0.0, 'sz': 0.0}

        except Exception as e:
            logger.error(f"获取主力资金失败: {e}")
            return {'total': 0.0, 'sh': 0.0, 'sz': 0.0}

    def get_index_data(self, index_code: str = '000300') -> Optional[Dict]:
        """获取指数数据"""
        try:
            # 判断市场: 上证1, 深证0
            market = '1' if index_code.startswith('000') or index_code.startswith('880') else '0'
            secid = f"{market}.{index_code}"

            url = f"{self.base_url}/api/qt/stock/get"
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f84,f85,f86,f168,f169,f170'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'data' in data:
                d = data['data']
                return {
                    'code': index_code,
                    'name': d.get('f58', ''),
                    'price': d.get('f43', 0) / 100,
                    'open': d.get('f46', 0) / 100,
                    'high': d.get('f44', 0) / 100,
                    'low': d.get('f45', 0) / 100,
                    'volume': d.get('f47', 0),
                    'amount': d.get('f48', 0),
                    'change_pct': d.get('f170', 0) / 100,
                    'change': d.get('f169', 0) / 100
                }

            return None

        except Exception as e:
            logger.error(f"获取指数{index_code}数据失败: {e}")
            return None

    def get_kline_data(self, symbol: str, period: str = '101', count: int = 100) -> List[Dict]:
        """获取K线数据
        period: 101=日K, 102=周K, 103=月K
        """
        try:
            market = '1' if symbol.startswith('6') or symbol.startswith('000') else '0'
            secid = f"{market}.{symbol}"

            url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
            params = {
                'secid': secid,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': period,
                'fqt': '1',
                'beg': '0',
                'end': '20500101'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            if data and 'data' in data and 'klines' in data['data']:
                klines = []
                for kline in data['data']['klines'][-count:]:
                    parts = kline.split(',')
                    if len(parts) >= 11:
                        klines.append({
                            'date': parts[0],
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'high': float(parts[3]),
                            'low': float(parts[4]),
                            'volume': float(parts[5]),
                            'amount': float(parts[6]),
                            'amplitude': float(parts[7]),
                            'change_pct': float(parts[8]),
                            'change': float(parts[9]),
                            'turnover_rate': float(parts[10])
                        })

                logger.info(f"✅ 获取{symbol}的{len(klines)}条K线数据")
                return klines

            return []

        except Exception as e:
            logger.error(f"获取{symbol}K线数据失败: {e}")
            return []

    def _is_cache_valid(self, key: str, duration: int = None) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False

        cache_duration = duration if duration else self.cache_duration
        return (time.time() - self.cache[key]['timestamp']) < cache_duration

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")

# 全局实例
eastmoney_service = EastMoneyDataService()

# 测试函数
def main():
    print("🚀 东方财富数据服务测试")
    print("=" * 60)

    # 测试股票实时数据
    stock = eastmoney_service.get_stock_realtime('000001')
    print(f"\n📊 股票实时: {stock}")

    # 测试ETF数据
    etf = eastmoney_service.get_etf_realtime('510300')
    print(f"\n📈 ETF实时: {etf}")

    # 测试北向资金
    north = eastmoney_service.get_north_bound_flow()
    print(f"\n💰 北向资金: {north}")

    # 测试主力资金
    main_force = eastmoney_service.get_main_force_flow()
    print(f"\n🏛️ 主力资金: {main_force}")

    # 测试指数数据
    index = eastmoney_service.get_index_data('000300')
    print(f"\n📊 沪深300: {index}")

    # 测试K线数据
    klines = eastmoney_service.get_kline_data('000300', count=5)
    print(f"\n📉 K线数据(最近5天): {klines}")

if __name__ == "__main__":
    main()
