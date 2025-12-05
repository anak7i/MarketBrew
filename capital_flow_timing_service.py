#!/usr/bin/env python3
"""
资金流向择时服务
整合北向资金、ETF资金、主力资金的多周期流入流出数据
"""

import requests
import json
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import pandas as pd
from eastmoney_data_service import eastmoney_service
from tushare_pro_service import get_tushare_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CapitalFlowTimingService:
    """资金流向择时服务"""

    def __init__(self, use_tushare: bool = True):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.eastmoney.com/',
            'Accept': '*/*'
        })
        self.base_url = 'https://datacenter-web.eastmoney.com'
        self.push_url = 'https://push2his.eastmoney.com'
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存

        # 初始化Tushare Pro服务（如果启用）
        self.use_tushare = use_tushare
        self.tushare_service = None
        if self.use_tushare:
            try:
                tushare_token = os.getenv('TUSHARE_TOKEN')
                if tushare_token:
                    self.tushare_service = get_tushare_service(token=tushare_token)
                    logger.info("✅ 使用Tushare Pro数据源")
                else:
                    logger.warning("⚠️ 未设置TUSHARE_TOKEN环境变量，将使用东方财富数据源")
                    self.use_tushare = False
            except Exception as e:
                logger.warning(f"⚠️ Tushare Pro初始化失败: {e}，将使用东方财富数据源")
                self.use_tushare = False

    def get_north_bound_flow_history(self, days: int = 28) -> List[Dict]:
        """
        获取北向资金历史流向数据
        优先使用Tushare Pro，失败时回退到东方财富API

        Args:
            days: 获取天数

        Returns:
            历史数据列表，每条包含日期和流入金额
        """
        cache_key = f"north_bound_history_{days}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        # 优先使用Tushare Pro
        if self.use_tushare and self.tushare_service:
            try:
                logger.info(f"🔄 使用Tushare Pro获取北向资金数据（{days}天）...")
                history = self.tushare_service.get_north_bound_flow(days=days)
                if history:
                    self.cache[cache_key] = {'data': history, 'timestamp': time.time()}
                    logger.info(f"✅ Tushare Pro获取北向资金{len(history)}天历史数据")
                    return history
                else:
                    logger.warning("⚠️ Tushare Pro返回空数据，尝试使用东方财富...")
            except Exception as e:
                logger.warning(f"⚠️ Tushare Pro获取失败: {e}，回退到东方财富数据源")

        # 回退到东方财富API
        try:
            logger.info(f"🔄 使用东方财富API获取北向资金数据（{days}天）...")

            # 使用东方财富数据中心API
            url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
            params = {
                'reportName': 'RPT_MUTUAL_STOCK_NORTHSTA',  # 北向资金统计报表
                'columns': 'ALL',
                'pageSize': str(days),
                'sortColumns': 'TRADE_DATE',
                'sortTypes': '-1',  # 降序
                'source': 'WEB',
                'client': 'WEB'
            }

            response = self.session.get(url, params=params, timeout=30)  # 增加超时到30秒
            logger.info(f"✅ 东方财富API响应成功，状态码: {response.status_code}")

            data = response.json()

            history = []
            if data and 'result' in data and data['result'] and 'data' in data['result']:
                items = data['result']['data']

                for item in items[:days]:
                    try:
                        # 解析数据
                        date_str = str(item.get('TRADE_DATE', ''))[:10]
                        north_money = float(item.get('NORTH_MONEY', 0)) / 100000000  # 转为亿
                        sh_money = float(item.get('HGTJLR', 0)) / 100000000  # 沪股通
                        sz_money = float(item.get('SGTJLR', 0)) / 100000000  # 深股通

                        history.append({
                            'date': date_str,
                            'total_flow': round(north_money, 2),
                            'sh_flow': round(sh_money, 2),
                            'sz_flow': round(sz_money, 2),
                            'sh_balance': round(float(item.get('HGTYLJE', 0)) / 100000000, 2),
                            'sz_balance': round(float(item.get('SGTYLJE', 0)) / 100000000, 2),
                            'source': 'EastMoney'
                        })
                    except Exception as e:
                        logger.debug(f"处理数据行失败: {e}")
                        continue

            if history:
                self.cache[cache_key] = {'data': history, 'timestamp': time.time()}
                logger.info(f"✅ 东方财富获取北向资金{len(history)}天历史数据")
            else:
                logger.warning("⚠️ 北向资金历史数据为空（可能是非交易日）")
                # 返回占位数据以便前端显示
                history = [{
                    'date': '暂无数据',
                    'total_flow': 0,
                    'sh_flow': 0,
                    'sz_flow': 0,
                    'sh_balance': 0,
                    'sz_balance': 0
                }]

            return history

        except requests.Timeout:
            logger.error(f"⏱️ 获取北向资金数据超时（30秒）")
            return [{
                'date': '请求超时',
                'total_flow': 0,
                'sh_flow': 0,
                'sz_flow': 0,
                'sh_balance': 0,
                'sz_balance': 0
            }]
        except Exception as e:
            logger.error(f"❌ 获取北向资金历史数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return [{
                'date': '获取失败',
                'total_flow': 0,
                'sh_flow': 0,
                'sz_flow': 0,
                'sh_balance': 0,
                'sz_balance': 0
            }]

    def get_etf_flow_history(self, days: int = 28) -> List[Dict]:
        """
        获取ETF资金流向历史数据（使用东方财富Choice API）

        Args:
            days: 获取天数

        Returns:
            历史数据列表
        """
        cache_key = f"etf_flow_history_{days}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            # 使用东方财富ETF资金流API
            url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
            params = {
                'reportName': 'RPT_ETF_FUNDFLOW',  # ETF资金流报表
                'columns': 'ALL',
                'pageSize': str(days),
                'sortColumns': 'TRADE_DATE',
                'sortTypes': '-1',
                'source': 'WEB',
                'client': 'WEB',
                'filter': '(TRADE_DATE>="2020-01-01")'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            history = []
            if data and 'result' in data and data['result'] and 'data' in data['result']:
                items = data['result']['data']

                for item in items[:days]:
                    try:
                        date_str = str(item.get('TRADE_DATE', ''))[:10]
                        # ETF净流入（单位：元，转为亿）
                        net_flow = float(item.get('NET_INFLOW', 0)) / 100000000

                        history.append({
                            'date': date_str,
                            'total_flow': round(net_flow, 2),
                            'inflow': max(0, round(net_flow, 2)),
                            'outflow': min(0, round(net_flow, 2))
                        })
                    except Exception as e:
                        logger.debug(f"处理ETF数据失败: {e}")
                        continue

            if history:
                self.cache[cache_key] = {'data': history, 'timestamp': time.time()}
                logger.info(f"✅ 获取ETF资金流{len(history)}天历史数据（东方财富真实数据）")
            else:
                logger.warning("ETF资金流数据为空，生成占位数据")
                # 生成占位数据
                for i in range(days):
                    date = datetime.now() - timedelta(days=i)
                    history.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'total_flow': 0.0,
                        'inflow': 0,
                        'outflow': 0
                    })

            return history

        except Exception as e:
            logger.error(f"获取ETF资金流历史数据失败: {e}")
            # 返回占位数据
            history = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'total_flow': 0.0,
                    'inflow': 0,
                    'outflow': 0
                })
            return history

    def get_main_force_flow_history(self, days: int = 28) -> List[Dict]:
        """
        获取主力资金流向历史数据（使用东方财富Choice API）

        Args:
            days: 获取天数

        Returns:
            历史数据列表
        """
        cache_key = f"main_force_history_{days}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            # 使用东方财富主力资金流API
            url = "http://datacenter-web.eastmoney.com/api/data/v1/get"
            params = {
                'reportName': 'RPT_MAIN_FORCE_FLOW',  # 主力资金流报表
                'columns': 'ALL',
                'pageSize': str(days),
                'sortColumns': 'TRADE_DATE',
                'sortTypes': '-1',
                'source': 'WEB',
                'client': 'WEB',
                'filter': '(TRADE_DATE>="2020-01-01")'
            }

            response = self.session.get(url, params=params, timeout=10)
            data = response.json()

            history = []
            if data and 'result' in data and data['result'] and 'data' in data['result']:
                items = data['result']['data']

                for item in items[:days]:
                    try:
                        date_str = str(item.get('TRADE_DATE', ''))[:10]
                        # 主力净流入（单位：元，转为亿）
                        main_net = float(item.get('MAIN_FORCE_NET', 0)) / 100000000
                        super_large = float(item.get('SUPER_LARGE_NET', 0)) / 100000000
                        large = float(item.get('LARGE_NET', 0)) / 100000000
                        medium = float(item.get('MEDIUM_NET', 0)) / 100000000
                        small = float(item.get('SMALL_NET', 0)) / 100000000

                        history.append({
                            'date': date_str,
                            'total_flow': round(main_net, 2),
                            'super_large': round(super_large, 2),
                            'large': round(large, 2),
                            'medium': round(medium, 2),
                            'small': round(small, 2)
                        })
                    except Exception as e:
                        logger.debug(f"处理主力资金数据失败: {e}")
                        continue

            if history:
                self.cache[cache_key] = {'data': history, 'timestamp': time.time()}
                logger.info(f"✅ 获取主力资金{len(history)}天历史数据（东方财富真实数据）")
            else:
                logger.warning("主力资金数据为空，生成占位数据")
                # 生成占位数据
                for i in range(days):
                    date = datetime.now() - timedelta(days=i)
                    history.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'total_flow': 0.0,
                        'super_large': 0.0,
                        'large': 0.0,
                        'medium': 0.0,
                        'small': 0.0
                    })

            return history

        except Exception as e:
            logger.error(f"获取主力资金历史数据失败: {e}")
            # 返回占位数据
            history = []
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                history.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'total_flow': 0.0,
                    'super_large': 0.0,
                    'large': 0.0,
                    'medium': 0.0,
                    'small': 0.0
                })
            return history

    def calculate_period_flow(self, history: List[Dict], periods: List[int] = [1, 3, 7, 14, 28]) -> Dict:
        """
        计算多周期资金流入流出统计

        Args:
            history: 历史数据列表
            periods: 统计周期列表（天数）

        Returns:
            多周期统计结果
        """
        if not history:
            return {}

        result = {}
        for period in periods:
            period_data = history[:min(period, len(history))]

            total_inflow = sum(max(0, d.get('total_flow', 0)) for d in period_data)
            total_outflow = sum(min(0, d.get('total_flow', 0)) for d in period_data)
            net_flow = sum(d.get('total_flow', 0) for d in period_data)

            result[f'{period}d'] = {
                'period': period,
                'inflow': round(total_inflow, 2),
                'outflow': round(abs(total_outflow), 2),
                'net_flow': round(net_flow, 2),
                'avg_daily_flow': round(net_flow / period if period > 0 else 0, 2),
                'flow_ratio': round((total_inflow / abs(total_outflow) if total_outflow != 0 else 0), 2)
            }

        return result

    def get_comprehensive_timing_data(self) -> Dict:
        """
        获取综合择时数据

        Returns:
            包含北向资金、ETF资金、主力资金的完整择时数据
        """
        logger.info("🚀 开始获取综合择时数据...")

        # 获取各类资金的历史数据
        north_history = self.get_north_bound_flow_history(days=30)
        etf_history = self.get_etf_flow_history(days=30)
        main_force_history = self.get_main_force_flow_history(days=30)

        # 计算多周期统计
        periods = [1, 3, 7, 14, 28]

        result = {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'north_bound': {
                'latest': north_history[0] if north_history else {},
                'periods': self.calculate_period_flow(north_history, periods),
                'history': north_history[:7]  # 最近7天
            },
            'etf_flow': {
                'latest': etf_history[0] if etf_history else {},
                'periods': self.calculate_period_flow(etf_history, periods),
                'history': etf_history[:7]
            },
            'main_force': {
                'latest': main_force_history[0] if main_force_history else {},
                'periods': self.calculate_period_flow(main_force_history, periods),
                'history': main_force_history[:7]
            },
            'timing_signal': self._generate_timing_signal(
                north_history, etf_history, main_force_history
            )
        }

        logger.info("✅ 综合择时数据获取完成")
        return result

    def _generate_timing_signal(self, north_history: List[Dict],
                                etf_history: List[Dict],
                                main_force_history: List[Dict]) -> Dict:
        """
        生成择时信号

        Returns:
            择时信号和建议
        """
        signals = []
        score = 0

        # 北向资金信号
        if north_history:
            north_3d = sum(d.get('total_flow', 0) for d in north_history[:3])
            if north_3d > 50:
                signals.append("北向资金3日净流入超50亿，市场情绪积极")
                score += 2
            elif north_3d < -50:
                signals.append("北向资金3日净流出超50亿，需谨慎")
                score -= 2

        # ETF资金信号
        if etf_history:
            etf_7d = sum(d.get('total_flow', 0) for d in etf_history[:7])
            if etf_7d > 20:
                signals.append("ETF资金7日持续流入，机构看好后市")
                score += 1
            elif etf_7d < -20:
                signals.append("ETF资金7日持续流出，机构减仓")
                score -= 1

        # 主力资金信号
        if main_force_history:
            main_1d = main_force_history[0].get('total_flow', 0) if main_force_history else 0
            if main_1d > 100:
                signals.append("主力资金今日大幅流入，短期看多")
                score += 1
            elif main_1d < -100:
                signals.append("主力资金今日大幅流出，短期看空")
                score -= 1

        # 综合评分
        if score >= 3:
            suggestion = "强烈看多"
            level = "strong_bullish"
        elif score >= 1:
            suggestion = "偏多"
            level = "bullish"
        elif score <= -3:
            suggestion = "强烈看空"
            level = "strong_bearish"
        elif score <= -1:
            suggestion = "偏空"
            level = "bearish"
        else:
            suggestion = "中性观望"
            level = "neutral"

        return {
            'score': score,
            'level': level,
            'suggestion': suggestion,
            'signals': signals,
            'timestamp': datetime.now().isoformat()
        }

    def compute_index_trend(self, index_code: str = '000300', above_days: int = 3, ma_short: int = 20, ma_long: int = 30) -> Dict[str, Any]:
        """基于日K判断指数是否站稳MA20/MA30并向上（使用东方财富K线）

        Returns:
            {
              'index_code','index_name','latest_close','ma20','ma30',
              'above_ma20','above_ma30','stand_above_days','ma20_slope','ma30_slope','is_uptrend'
            }
        """
        try:
            klines = eastmoney_service.get_kline_data(index_code, period='101', count=max(above_days + ma_long + 5, 60))
            if not klines:
                return {
                    'index_code': index_code,
                    'index_name': '指数',
                    'error': 'no_kline',
                    'is_uptrend': False
                }

            closes = [k['close'] for k in klines]
            name = klines[-1].get('name', '') if 'name' in klines[-1] else ''

            def moving_avg(arr, n):
                if len(arr) < n:
                    return []
                return [sum(arr[i-n:i]) / n for i in range(n, len(arr)+1)]

            ma20_series = moving_avg(closes, ma_short)
            ma30_series = moving_avg(closes, ma_long)
            if not ma20_series or not ma30_series:
                return {
                    'index_code': index_code,
                    'index_name': name or '指数',
                    'error': 'insufficient_data',
                    'is_uptrend': False
                }

            latest_close = closes[-1]
            latest_ma20 = ma20_series[-1]
            latest_ma30 = ma30_series[-1]

            above_ma20 = latest_close > latest_ma20
            above_ma30 = latest_close > latest_ma30
            stand_days = 0
            for i in range(1, above_days+1):
                c = closes[-i]
                m20 = ma20_series[-i]
                m30 = ma30_series[-i]
                if c > m20 and c > m30:
                    stand_days += 1
            ma20_slope = ma20_series[-1] - ma20_series[-2] if len(ma20_series) >= 2 else 0
            ma30_slope = ma30_series[-1] - ma30_series[-2] if len(ma30_series) >= 2 else 0

            is_uptrend = (above_ma20 and above_ma30 and stand_days >= above_days and
                          latest_ma20 > latest_ma30 and ma20_slope > 0)

            return {
                'index_code': index_code,
                'index_name': name or index_code,
                'latest_close': round(latest_close, 2),
                'ma20': round(latest_ma20, 2),
                'ma30': round(latest_ma30, 2),
                'above_ma20': above_ma20,
                'above_ma30': above_ma30,
                'stand_above_days': stand_days,
                'ma20_slope': round(ma20_slope, 4),
                'ma30_slope': round(ma30_slope, 4),
                'is_uptrend': bool(is_uptrend)
            }
        except Exception as e:
            logger.error(f"计算指数趋势失败: {e}")
            return {
                'index_code': index_code,
                'index_name': '指数',
                'error': str(e),
                'is_uptrend': False
            }

    def compute_emotion_phase(self) -> Dict[str, Any]:
        """情绪分期粗略判别（基于全市场涨跌与换手率分布，来源：东方财富股票列表）

        规则近似：
          - 冰点：上涨占比<0.3 且 高换手下跌占比高
          - 修复：上涨占比在0.45~0.65 且 净流入评分>=0 或 指数止跌
          - 加速：上涨占比>0.65 且 强势上涨占比高
          - 退潮：上涨占比<0.45 且 近期资金评分<=-1
        """
        try:
            stocks = eastmoney_service.get_stock_list(market='all')
            total = len(stocks)
            if total == 0:
                return {'phase': '未知', 'basis': ['市场列表为空'], 'metrics': {}}

            ups = sum(1 for s in stocks if s.get('change_pct', 0) > 0)
            strong_up = sum(1 for s in stocks if s.get('change_pct', 0) >= 0.02)
            high_to_down = sum(1 for s in stocks if s.get('change_pct', 0) < 0 and (s.get('turnover_rate', 0) or 0) > 0.03)

            up_ratio = ups / total
            strong_up_ratio = strong_up / total
            high_to_down_ratio = high_to_down / total

            basis = [
                f"上涨占比 {up_ratio:.2%}",
                f"强势上涨占比 {strong_up_ratio:.2%}",
                f"高换手下跌占比 {high_to_down_ratio:.2%}"
            ]

            comp = self.get_comprehensive_timing_data()
            score = comp.get('timing_signal', {}).get('score', 0)

            if up_ratio < 0.30 and high_to_down_ratio > 0.10:
                phase = '冰点'
            elif up_ratio > 0.65 and strong_up_ratio > 0.25:
                phase = '加速'
            elif up_ratio < 0.45 and score <= -1:
                phase = '退潮'
            else:
                phase = '修复'

            return {
                'phase': phase,
                'basis': basis,
                'metrics': {
                    'total': total,
                    'up_ratio': round(up_ratio, 4),
                    'strong_up_ratio': round(strong_up_ratio, 4),
                    'high_to_down_ratio': round(high_to_down_ratio, 4),
                    'score': score
                }
            }
        except Exception as e:
            logger.error(f"情绪分期计算失败: {e}")
            return {'phase': '未知', 'basis': [f'错误: {e}'], 'metrics': {}}

    def get_timing_overview(self, index_code: str = '000300') -> Dict[str, Any]:
        """择时区总览：趋势 + 资金 + 情绪"""
        trend = self.compute_index_trend(index_code=index_code)
        comp = self.get_comprehensive_timing_data()
        emotion = self.compute_emotion_phase()

        nb_net3 = sum(d.get('total_flow', 0) for d in self.get_north_bound_flow_history(days=3))
        etf_net7 = sum(d.get('total_flow', 0) for d in self.get_etf_flow_history(days=7))
        main_1d = (self.get_main_force_flow_history(days=1)[0].get('total_flow', 0)
                   if self.get_main_force_flow_history(days=1) else 0)

        capital_brief = {
            'north_3d': round(nb_net3, 2),
            'etf_7d': round(etf_net7, 2),
            'main_1d': round(main_1d, 2),
            'score': comp.get('timing_signal', {}).get('score', 0),
            'level': comp.get('timing_signal', {}).get('level', 'neutral')
        }

        return {
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trend': trend,
            'capital': capital_brief,
            'emotion': emotion
        }

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
timing_service = CapitalFlowTimingService()


# 测试函数
def main():
    print("=" * 80)
    print("🎯 资金流向择时服务测试")
    print("=" * 80)
    print()

    # 获取综合择时数据
    print("[1/1] 获取综合择时数据...")
    data = timing_service.get_comprehensive_timing_data()

    print("\n" + "=" * 80)
    print("📊 北向资金")
    print("=" * 80)
    print(f"最新: {data['north_bound']['latest']}")
    print(f"\n多周期统计:")
    for period, stats in data['north_bound']['periods'].items():
        print(f"  {period}: 净流入 {stats['net_flow']}亿 (流入{stats['inflow']}亿 / 流出{stats['outflow']}亿)")

    print("\n" + "=" * 80)
    print("📈 ETF资金流")
    print("=" * 80)
    print(f"最新: {data['etf_flow']['latest']}")
    print(f"\n多周期统计:")
    for period, stats in data['etf_flow']['periods'].items():
        print(f"  {period}: 净流入 {stats['net_flow']}亿")

    print("\n" + "=" * 80)
    print("🏛️ 主力资金")
    print("=" * 80)
    print(f"最新: {data['main_force']['latest']}")
    print(f"\n多周期统计:")
    for period, stats in data['main_force']['periods'].items():
        print(f"  {period}: 净流入 {stats['net_flow']}亿")

    print("\n" + "=" * 80)
    print("🎯 择时信号")
    print("=" * 80)
    signal = data['timing_signal']
    print(f"综合评分: {signal['score']}")
    print(f"信号级别: {signal['level']}")
    print(f"投资建议: {signal['suggestion']}")
    print(f"\n具体信号:")
    for s in signal['signals']:
        print(f"  • {s}")

    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
