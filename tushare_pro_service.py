#!/usr/bin/env python3
"""
Tushare Pro 数据服务
提供北向资金、市场概览等数据
"""

import tushare as ts
import pandas as pd
import logging
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TushareProService:
    """Tushare Pro 数据服务封装"""

    def __init__(self, token: Optional[str] = None):
        """
        初始化Tushare Pro服务

        Args:
            token: Tushare Pro API token，如果不提供则从环境变量TUSHARE_TOKEN读取
        """
        self.token = token or os.getenv('TUSHARE_TOKEN')
        if not self.token:
            raise ValueError("请提供Tushare Pro token或设置环境变量TUSHARE_TOKEN")

        ts.set_token(self.token)
        self.pro = ts.pro_api()
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存
        logger.info("✅ Tushare Pro服务初始化成功")

    def get_north_bound_flow(self, start_date: Optional[str] = None,
                            end_date: Optional[str] = None,
                            days: int = 30) -> List[Dict]:
        """
        获取北向资金流向数据

        Args:
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            days: 获取天数（如果不指定日期范围）

        Returns:
            北向资金流向数据列表
        """
        cache_key = f"north_bound_{days}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            # 如果没有指定日期，使用最近N天
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            logger.info(f"📡 获取北向资金数据：{start_date} 至 {end_date}")

            # 获取北向资金流向（沪股通+深股通）
            df = self.pro.moneyflow_hsgt(
                start_date=start_date,
                end_date=end_date
            )

            if df.empty:
                logger.warning("⚠️ 北向资金数据为空")
                return []

            # 按日期降序排序
            df = df.sort_values('trade_date', ascending=False)

            # 转换数据格式
            history = []
            for _, row in df.iterrows():
                try:
                    # 北向资金 = 沪股通 + 深股通
                    ggt_ss = float(row.get('ggt_ss', 0)) if pd.notna(row.get('ggt_ss')) else 0
                    hgt = float(row.get('hgt', 0)) if pd.notna(row.get('hgt')) else 0
                    sgt = float(row.get('sgt', 0)) if pd.notna(row.get('sgt')) else 0
                    north_money = hgt + sgt

                    # 余额数据
                    hgt_ylje = float(row.get('north_money', 0)) if pd.notna(row.get('north_money')) else 0

                    date_str = str(row['trade_date'])
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

                    history.append({
                        'date': formatted_date,
                        'total_flow': round(north_money / 100, 2),  # 转为亿元
                        'sh_flow': round(hgt / 100, 2),  # 沪股通，转为亿元
                        'sz_flow': round(sgt / 100, 2),  # 深股通，转为亿元
                        'sh_balance': round(hgt_ylje / 100, 2) if hgt_ylje else 0,
                        'sz_balance': 0,  # Tushare暂无深股通余额单独数据
                        'source': 'Tushare Pro'
                    })
                except Exception as e:
                    logger.debug(f"处理数据行失败: {e}")
                    continue

            if history:
                self.cache[cache_key] = {'data': history, 'timestamp': time.time()}
                logger.info(f"✅ 获取北向资金{len(history)}天数据（Tushare Pro）")

            return history

        except Exception as e:
            logger.error(f"❌ 获取北向资金数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    def get_market_overview(self, trade_date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取市场概况数据

        Args:
            trade_date: 交易日期，格式YYYYMMDD，默认为最新交易日

        Returns:
            市场概况数据字典
        """
        cache_key = f"market_overview_{trade_date or 'latest'}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']

        try:
            # 如果没有指定日期，获取最新交易日
            if not trade_date:
                trade_date = self._get_latest_trade_date()

            logger.info(f"📡 获取市场概况：{trade_date}")

            # 获取主要指数数据（上证指数、深证成指、创业板指）
            indices_data = {}
            index_codes = ['000001.SH', '399001.SZ', '399006.SZ', '000300.SH']

            for index_code in index_codes:
                try:
                    df = self.pro.index_daily(
                        ts_code=index_code,
                        start_date=trade_date,
                        end_date=trade_date
                    )
                    if not df.empty:
                        row = df.iloc[0]
                        indices_data[index_code] = {
                            'close': float(row['close']),
                            'change': float(row['pct_chg']),
                            'volume': float(row['vol']),
                            'amount': float(row['amount'])
                        }
                except Exception as e:
                    logger.debug(f"获取{index_code}数据失败: {e}")

            # 获取涨跌停统计（使用daily_basic接口）
            try:
                # 获取当日所有股票的基本信息
                df_basic = self.pro.daily_basic(
                    trade_date=trade_date,
                    fields='ts_code,close,turnover_rate,volume_ratio,pe,pb'
                )

                if not df_basic.empty:
                    total_stocks = len(df_basic)

                    # 获取当日涨跌数据
                    df_daily = self.pro.daily(
                        trade_date=trade_date,
                        fields='ts_code,pct_chg'
                    )

                    if not df_daily.empty:
                        # 合并数据
                        df_merged = pd.merge(df_basic, df_daily, on='ts_code', how='left')

                        # 统计涨跌
                        up_stocks = len(df_merged[df_merged['pct_chg'] > 0])
                        down_stocks = len(df_merged[df_merged['pct_chg'] < 0])
                        unchanged_stocks = len(df_merged[df_merged['pct_chg'] == 0])

                        # 统计涨跌停（中国A股涨跌停限制为±10%，科创板和创业板为±20%）
                        limit_up_stocks = len(df_merged[df_merged['pct_chg'] >= 9.9])
                        limit_down_stocks = len(df_merged[df_merged['pct_chg'] <= -9.9])

                        overview = {
                            'total_stocks': total_stocks,
                            'up_stocks': up_stocks,
                            'down_stocks': down_stocks,
                            'unchanged_stocks': unchanged_stocks,
                            'limit_up_stocks': limit_up_stocks,
                            'limit_down_stocks': limit_down_stocks,
                            'up_ratio': round(up_stocks / total_stocks, 4) if total_stocks > 0 else 0,
                            'down_ratio': round(down_stocks / total_stocks, 4) if total_stocks > 0 else 0,
                            'indices': indices_data,
                            'trade_date': trade_date,
                            'source': 'Tushare Pro',
                            'timestamp': datetime.now().isoformat()
                        }

                        self.cache[cache_key] = {'data': overview, 'timestamp': time.time()}
                        logger.info(f"✅ 获取市场概况：{up_stocks}涨 {down_stocks}跌 {unchanged_stocks}平")
                        return overview

            except Exception as e:
                logger.error(f"获取涨跌统计失败: {e}")

            # 如果获取失败，返回基础数据
            return {
                'indices': indices_data,
                'trade_date': trade_date,
                'source': 'Tushare Pro (partial)',
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"❌ 获取市场概况失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}

    def get_index_daily(self, ts_code: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None, days: int = 30) -> pd.DataFrame:
        """
        获取指数日线数据

        Args:
            ts_code: 指数代码，如 000001.SH
            start_date: 开始日期
            end_date: 结束日期
            days: 天数

        Returns:
            指数日线数据DataFrame
        """
        try:
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

            df = self.pro.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            logger.info(f"✅ 获取{ts_code}指数数据{len(df)}条")
            return df

        except Exception as e:
            logger.error(f"❌ 获取指数{ts_code}数据失败: {e}")
            return pd.DataFrame()

    def _get_latest_trade_date(self) -> str:
        """
        获取最新交易日期

        Returns:
            交易日期字符串，格式YYYYMMDD
        """
        try:
            # 获取最近的交易日历
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')

            df = self.pro.trade_cal(
                start_date=start_date,
                end_date=end_date,
                is_open='1'
            )

            if not df.empty:
                # 返回最新的交易日
                latest_date = df.iloc[-1]['cal_date']
                return str(latest_date)
            else:
                # 如果没有数据，返回今天
                return datetime.now().strftime('%Y%m%d')

        except Exception as e:
            logger.error(f"获取最新交易日失败: {e}")
            return datetime.now().strftime('%Y%m%d')

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False
        return time.time() - self.cache[cache_key]['timestamp'] < self.cache_duration

    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")


# 全局实例（需要在使用前设置token）
_tushare_service = None


def get_tushare_service(token: Optional[str] = None) -> TushareProService:
    """
    获取Tushare Pro服务实例

    Args:
        token: Tushare Pro token

    Returns:
        TushareProService实例
    """
    global _tushare_service
    if _tushare_service is None:
        _tushare_service = TushareProService(token=token)
    return _tushare_service


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Tushare Pro 数据服务测试")
    print("=" * 80)
    print()

    # 从环境变量或用户输入获取token
    token = os.getenv('TUSHARE_TOKEN')
    if not token:
        print("请设置环境变量 TUSHARE_TOKEN 或在代码中提供token")
        print("获取token: https://tushare.pro/register")
        exit(1)

    try:
        service = TushareProService(token=token)

        # 测试1: 获取北向资金
        print("[测试1] 获取北向资金流向数据...")
        north_data = service.get_north_bound_flow(days=5)
        if north_data:
            print(f"✅ 成功获取{len(north_data)}天北向资金数据")
            print(f"最新数据: {north_data[0]}")
        else:
            print("❌ 获取北向资金数据失败")

        print()

        # 测试2: 获取市场概况
        print("[测试2] 获取市场概况...")
        market_data = service.get_market_overview()
        if market_data:
            print(f"✅ 成功获取市场概况")
            print(f"总股票数: {market_data.get('total_stocks', 'N/A')}")
            print(f"上涨: {market_data.get('up_stocks', 'N/A')}")
            print(f"下跌: {market_data.get('down_stocks', 'N/A')}")
        else:
            print("❌ 获取市场概况失败")

        print()
        print("=" * 80)
        print("✅ 测试完成")
        print("=" * 80)

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
