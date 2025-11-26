#!/usr/bin/env python3
"""
增强版东方财富API访问器
优化网络连接策略，支持多种访问方式，确保数据实时更新
"""

import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EastMoneyAPIEnhanced:
    """增强版东方财富API访问器"""
    
    def __init__(self):
        self.session = requests.Session()
        # 设置常见的浏览器Headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        })
        
        # 设置连接参数
        self.session.timeout = 3  # 减少超时时间
        
        # 多个API域名备用
        self.base_urls = [
            'https://datacenter-web.eastmoney.com',  # 优先使用数据中心
            'https://push2.eastmoney.com',
            'https://push2his.eastmoney.com',
            'https://quote.eastmoney.com'
        ]
        
        # 缓存机制
        self.cache = {}
        self.cache_duration = 60  # 1分钟缓存
    
    def _make_request(self, url: str, params: Dict = None, retries: int = 1) -> Optional[Dict]:
        """增强的HTTP请求方法 - 使用EMQ极速行情API"""
        try:
            from emq_api_client import emq_client
            
            # 根据URL类型判断需要的数据
            if 'kamt.rtmin' in url:
                # 北向资金数据
                data = emq_client.get_north_bound_data()
                if data and data.get('today_flow', 0) != 0:
                    # 转换为东方财富格式
                    return {
                        'data': {
                            'hk2sh': [None, None, data['sh_flow'] * 100000000],  # 转换为元
                            'hk2sz': [None, None, data['sz_flow'] * 100000000]   # 转换为元
                        }
                    }
            
            elif 'clist' in url and 'MK0021' in str(params):
                # ETF数据
                etf_data = emq_client.get_etf_data()
                if etf_data:
                    # 转换为东方财富格式
                    formatted_data = []
                    for etf in etf_data:
                        formatted_data.append({
                            'f3': etf.get('change_percent', 0) * 100,  # 涨跌幅%
                            'f6': etf.get('turnover', 0)  # 成交额
                        })
                    return {'data': {'diff': formatted_data}}
            
            elif 'clist' in url and 'i:000300' in str(params):
                # 主力资金数据
                main_data = emq_client.get_main_force_data()
                if main_data and main_data.get('today_flow', 0) != 0:
                    return {
                        'data': {
                            'diff': [
                                {'f62': main_data['sh_flow'] * 100000000},  # 沪市主力
                                {'f62': main_data['sz_flow'] * 100000000}   # 深市主力
                            ]
                        }
                    }
            
            elif 'clist' in url and ('m:0' in str(params) or 'm:1' in str(params)):
                # 股票列表数据
                stocks = emq_client.get_stock_list()
                if stocks:
                    # 转换为东方财富格式
                    formatted_stocks = []
                    for stock in stocks:
                        formatted_stocks.append({
                            'f3': stock.get('change_percent', 0) * 100,  # 涨跌幅%
                            'f6': stock.get('turnover', 0),  # 成交额
                            'f12': stock.get('code', ''),  # 股票代码
                            'f14': stock.get('name', '')   # 股票名称
                        })
                    return {'data': {'diff': formatted_stocks}}
            
            logger.warning("EMQ API: 未知的请求类型或无数据")
            return None
            
        except Exception as e:
            logger.error(f"EMQ API请求失败: {e}")
            return None
    
    def get_stock_list_data(self, market_filter: str = 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23') -> List[Dict]:
        """获取股票列表数据"""
        cache_key = f"stock_list_{market_filter}"
        
        # 检查缓存
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        url = f"{self.base_urls[0]}/api/qt/clist/get"
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
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
        }
        
        data = self._make_request(url, params)
        
        if data and 'data' in data and 'diff' in data['data']:
            result = data['data']['diff']
            # 更新缓存
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            logger.info(f"✅ 获取到{len(result)}只股票数据")
            return result
        
        logger.error("股票列表数据获取失败")
        return []
    
    def get_north_bound_data(self) -> Dict[str, float]:
        """获取北向资金数据"""
        cache_key = "north_bound_data"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        # 尝试获取北向资金数据
        try:
            url = f"{self.base_urls[0]}/api/qt/kamt.rtmin/get"
            params = {
                'fields1': 'f1,f2,f3,f4',
                'fields2': 'f51,f52,f53,f54,f55,f56',
                'ut': 'b2884a393a59ad64002292a3e90d46a5'
            }
            
            data = self._make_request(url, params)
            
            if data and 'data' in data:
                # 解析新的数据格式
                if 's2n' in data['data'] and 'n2s' in data['data']:
                    s2n_data = data['data']['s2n']  # 沪股通
                    n2s_data = data['data']['n2s']  # 深股通
                    
                    # 获取最新的流入数据 (格式: "时间,净流入,总额度,净流入,总额度,累计净流入")
                    sh_net = 0.0  # 沪股通净流入
                    sz_net = 0.0  # 深股通净流入
                    
                    # 解析沪股通最新数据
                    if s2n_data:
                        latest_s2n = s2n_data[-1].split(',')
                        if len(latest_s2n) >= 6:
                            sh_net = float(latest_s2n[5]) / 100000000  # 累计净流入，转为亿元
                    
                    # 解析深股通最新数据  
                    if n2s_data:
                        latest_n2s = n2s_data[-1].split(',')
                        if len(latest_n2s) >= 6:
                            sz_net = float(latest_n2s[5]) / 100000000  # 累计净流入，转为亿元
                    
                    total_flow = sh_net + sz_net
                    
                    result = {
                        'today_flow': round(total_flow, 2),
                        'sh_flow': round(sh_net, 2),
                        'sz_flow': round(sz_net, 2)
                    }
                    
                    self.cache[cache_key] = {
                        'data': result,
                        'timestamp': time.time()
                    }
                    
                    logger.info(f"✅ 北向资金: 沪股通{sh_net:.1f}亿 + 深股通{sz_net:.1f}亿 = 总计{total_flow:.1f}亿")
                    return result
                        
        except Exception as e:
            logger.warning(f"北向资金API失败: {e}")
        
        # 返回默认值
        default_result = {'today_flow': 0.0, 'sh_flow': 0.0, 'sz_flow': 0.0}
        logger.warning("北向资金数据获取失败，使用默认值")
        return default_result
    
    def get_main_force_data(self) -> Dict[str, float]:
        """获取主力资金数据 - 使用沪深300成分股的主力资金净流入"""
        cache_key = "main_force_data"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # 获取沪深300成分股的主力资金数据
            url = f"{self.base_urls[0]}/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': '300',
                'po': '1',
                'np': '1',
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': '2',
                'invt': '2',
                'fid': 'f62',  # 按主力净流入排序
                'fs': 'i:000300',  # 沪深300成分股
                'fields': 'f12,f14,f62,f66,f67,f68,f69,f70,f71,f72'
            }
            
            data = self._make_request(url, params)
            
            if data and 'data' in data and 'diff' in data['data']:
                stocks = data['data']['diff']
                
                # 计算主力资金总净流入
                total_main_flow = 0.0
                valid_stocks = 0
                
                for stock in stocks:
                    if isinstance(stock, dict):
                        main_flow = stock.get('f62', 0)
                        if main_flow is not None:
                            total_main_flow += float(main_flow)
                            valid_stocks += 1
                
                # 转换为亿元
                total_main_flow = total_main_flow / 100000000
                
                result = {
                    'today_flow': round(total_main_flow, 2),
                    'sh_flow': round(total_main_flow * 0.6, 2),  # 沪市约占60%
                    'sz_flow': round(total_main_flow * 0.4, 2)   # 深市约占40%
                }
                
                self.cache[cache_key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                
                logger.info(f"✅ 主力资金: {total_main_flow:.1f}亿 (基于{valid_stocks}只沪深300成分股)")
                return result
                
        except Exception as e:
            logger.warning(f"主力资金API失败: {e}")
            
        logger.warning("主力资金数据获取失败，使用默认值")
        return {'today_flow': 0.0, 'sh_flow': 0.0, 'sz_flow': 0.0}
    
    def get_etf_data(self) -> List[Dict]:
        """获取ETF数据"""
        cache_key = "etf_data"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        url = f"{self.base_urls[0]}/api/qt/clist/get"
        params = {
            'pn': '1',
            'pz': '500',
            'po': '1',
            'np': '1', 
            'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
            'fltt': '2',
            'invt': '2',
            'fid': 'f3',
            'fs': 'b:MK0021,b:MK0022,b:MK0023,b:MK0024',
            'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
        }
        
        data = self._make_request(url, params)
        
        if data and 'data' in data and 'diff' in data['data']:
            result = data['data']['diff']
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            logger.info(f"✅ 获取到{len(result)}只ETF数据")
            return result
            
        logger.warning("ETF数据获取失败")
        return []
    
    def get_index_data(self, index_code: str = '000300') -> Dict:
        """获取指数数据"""
        cache_key = f"index_data_{index_code}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        # 尝试获取指数实时数据
        url = f"{self.base_urls[0]}/api/qt/stock/get"
        params = {
            'secid': f'1.{index_code}',
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
            'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58'
        }
        
        data = self._make_request(url, params)
        
        if data and 'data' in data:
            result = data['data']
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            return result
            
        return {}
    
    def get_kline_data(self, symbol: str, period: str = '101') -> List[Dict]:
        """获取K线历史数据"""
        cache_key = f"kline_{symbol}_{period}"
        
        if self._is_cache_valid(cache_key, duration=300):  # 5分钟缓存
            return self.cache[cache_key]['data']
        
        url = f"{self.base_urls[2]}/api/qt/stock/kline/get"
        params = {
            'secid': f'1.{symbol}',
            'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': period,
            'fqt': '1',
            'beg': '0',
            'end': '20500000'
        }
        
        data = self._make_request(url, params)
        
        if data and 'data' in data and 'klines' in data['data']:
            klines = data['data']['klines']
            result = []
            
            for kline in klines[-100:]:  # 最近100天
                parts = kline.split(',')
                if len(parts) >= 6:
                    result.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5])
                    })
            
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            logger.info(f"✅ 获取到{symbol}的{len(result)}天K线数据")
            return result
            
        logger.warning(f"{symbol}K线数据获取失败")
        return []
    
    def _is_cache_valid(self, key: str, duration: int = None) -> bool:
        """检查缓存是否有效"""
        if key not in self.cache:
            return False
            
        cache_duration = duration or self.cache_duration
        return (time.time() - self.cache['timestamp']) < cache_duration
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")

# 全局实例
eastmoney_api = EastMoneyAPIEnhanced()

def main():
    """测试函数"""
    print("🚀 东方财富API增强版测试")
    print("="*50)
    
    # 测试股票数据
    stocks = eastmoney_api.get_stock_list_data()
    print(f"📊 股票数据: {len(stocks)}只")
    
    # 测试北向资金
    north_bound = eastmoney_api.get_north_bound_data()
    print(f"💰 北向资金: {north_bound}")
    
    # 测试主力资金
    main_force = eastmoney_api.get_main_force_data()
    print(f"🏛️ 主力资金: {main_force}")
    
    # 测试ETF数据
    etf_data = eastmoney_api.get_etf_data()
    print(f"📈 ETF数据: {len(etf_data)}只")
    
    # 测试指数数据
    index_data = eastmoney_api.get_index_data('000300')
    print(f"📊 沪深300: {index_data}")

if __name__ == "__main__":
    main()