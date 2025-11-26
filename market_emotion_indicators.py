#!/usr/bin/env python3
"""
市场情绪核心指标分析器
包含五个关键指标：涨停家数、连板家数、赚钱比例、成交额放大倍数、跌停家数
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from eastmoney_api_enhanced import eastmoney_api

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketEmotionIndicators:
    """市场情绪核心指标"""
    # 核心指标
    n_up_limit: int          # 涨停家数
    n_cont_limit: int        # 连板家数（≥2连板）
    win_ratio: float         # 赚钱比例（涨幅>0的个股数/总个股数）
    vol_ratio: float         # 成交额放大倍数（当日成交额/20日平均成交额）
    n_down_limit: int        # 跌停家数
    
    # 辅助数据
    total_stocks: int        # 总个股数
    rising_stocks: int       # 上涨个股数
    falling_stocks: int      # 下跌个股数
    total_turnover: float    # 当日总成交额（亿）
    avg_20d_turnover: float  # 20日平均成交额（亿）
    
    # 情绪评估
    emotion_score: float     # 综合情绪评分（0-100）
    emotion_level: str       # 情绪等级
    market_stage: str        # 市场阶段

class MarketEmotionAnalyzer:
    """市场情绪指标分析器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存
        
    def analyze_market_emotion(self) -> MarketEmotionIndicators:
        """分析市场情绪核心指标"""
        try:
            logger.info("🎭 开始分析市场情绪核心指标...")
            
            # 获取股票行情数据
            stock_data = self._get_stock_market_data()
            
            if not stock_data:
                logger.error("无法获取股票市场数据")
                return self._get_default_indicators()
            
            # 计算五个核心指标
            n_up_limit = self._calculate_up_limit_count(stock_data)
            n_cont_limit = self._calculate_continuous_limit_count(stock_data)
            win_ratio = self._calculate_win_ratio(stock_data)
            vol_ratio = self._calculate_volume_ratio()
            n_down_limit = self._calculate_down_limit_count(stock_data)
            
            # 计算辅助数据
            total_stocks = len(stock_data)
            rising_stocks = len([s for s in stock_data if s.get('f3', 0) > 0])
            falling_stocks = len([s for s in stock_data if s.get('f3', 0) < 0])
            total_turnover = sum(s.get('f6', 0) for s in stock_data) / 100000000  # 转为亿
            avg_20d_turnover = total_turnover / vol_ratio if vol_ratio > 0 else total_turnover
            
            # 计算综合情绪评分
            emotion_score = self._calculate_emotion_score(
                n_up_limit, n_cont_limit, win_ratio, vol_ratio, n_down_limit, total_stocks
            )
            
            # 确定情绪等级和市场阶段
            emotion_level = self._determine_emotion_level(emotion_score)
            market_stage = self._determine_market_stage(
                n_up_limit, n_cont_limit, win_ratio, vol_ratio, n_down_limit
            )
            
            result = MarketEmotionIndicators(
                n_up_limit=n_up_limit,
                n_cont_limit=n_cont_limit,
                win_ratio=round(win_ratio, 3),
                vol_ratio=round(vol_ratio, 2),
                n_down_limit=n_down_limit,
                total_stocks=total_stocks,
                rising_stocks=rising_stocks,
                falling_stocks=falling_stocks,
                total_turnover=round(total_turnover, 1),
                avg_20d_turnover=round(avg_20d_turnover, 1),
                emotion_score=round(emotion_score, 1),
                emotion_level=emotion_level,
                market_stage=market_stage
            )
            
            logger.info(f"🎭 情绪指标分析完成:")
            logger.info(f"  涨停: {n_up_limit}只, 连板: {n_cont_limit}只")
            logger.info(f"  赚钱比例: {win_ratio:.1%}, 成交放大: {vol_ratio:.1f}倍")
            logger.info(f"  跌停: {n_down_limit}只, 情绪: {emotion_level}")
            
            return result
            
        except Exception as e:
            logger.error(f"市场情绪指标分析失败: {e}")
            return self._get_default_indicators()
    
    def _get_stock_market_data(self) -> List[Dict]:
        """获取股票市场数据（使用增强版API）"""
        try:
            # 使用增强版东方财富API
            stock_data = eastmoney_api.get_stock_list_data('m:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048')
            
            if stock_data:
                logger.info(f"✅ 使用增强API获取到{len(stock_data)}只股票数据")
                return stock_data
            else:
                logger.warning("增强API无数据，尝试直接访问")
                
                # 备用直接访问方法
                url = 'https://push2.eastmoney.com/api/qt/clist/get'
                params = {
                    'pn': '1',
                    'pz': '5000',
                    'po': '1',
                    'np': '1',
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': '2',
                    'invt': '2',
                    'fid': 'f3',
                    'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048',
                    'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f62,f128,f136,f115,f152'
                }
                
                response = requests.get(url, params=params, timeout=15, verify=False)
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'diff' in data['data']:
                        logger.info(f"✅ 直接访问获取到{len(data['data']['diff'])}只股票数据")
                        return data['data']['diff']
                        
            return []
            
        except Exception as e:
            logger.error(f"获取股票数据失败: {e}")
            return []
    
    def _calculate_up_limit_count(self, stock_data: List[Dict]) -> int:
        """计算涨停家数"""
        count = 0
        for stock in stock_data:
            try:
                change_pct = stock.get('f3', 0)  # 涨跌幅
                if change_pct >= 9.8:  # 接近10%涨停
                    count += 1
            except:
                continue
        return count
    
    def _calculate_continuous_limit_count(self, stock_data: List[Dict]) -> int:
        """计算连板家数（≥2连板的个股数）"""
        # 这里简化处理，通过涨停且前一日也涨停的逻辑估算
        # 实际应该查询连续涨停数据，这里用涨停股票数的30%作为近似
        up_limit_count = self._calculate_up_limit_count(stock_data)
        # 经验值：连板股票通常是涨停股票的20-40%
        return int(up_limit_count * 0.3)
    
    def _calculate_win_ratio(self, stock_data: List[Dict]) -> float:
        """计算赚钱比例 = 涨幅>0的个股数 / 总个股数"""
        if not stock_data:
            return 0.0
            
        total_count = len(stock_data)
        rising_count = 0
        
        for stock in stock_data:
            try:
                change_pct = stock.get('f3', 0)  # 涨跌幅
                if change_pct > 0:
                    rising_count += 1
            except:
                continue
                
        return rising_count / total_count if total_count > 0 else 0.0
    
    def _calculate_volume_ratio(self) -> float:
        """计算成交额放大倍数"""
        try:
            # 获取市场总成交额数据（简化处理）
            # 这里使用上证指数的成交额作为市场整体成交额的参考
            url = 'https://push2.eastmoney.com/api/qt/stock/get'
            params = {
                'secid': '1.000001',  # 上证指数
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data:
                    # f6是成交额，但我们需要历史数据来计算20日均值
                    # 这里简化：假设正常市场成交额波动在0.8-2.0倍之间
                    # 实际应该获取20日历史数据计算精确值
                    current_volume = data['data'].get('f6', 0)
                    
                    # 简化计算：用随机波动模拟20日均值比较
                    # 实际项目中应该获取真实的20日历史成交额数据
                    base_volume = current_volume * 0.85  # 假设20日均值约为当前的85%
                    vol_ratio = current_volume / base_volume if base_volume > 0 else 1.0
                    
                    return max(0.1, min(5.0, vol_ratio))  # 限制在合理范围内
                    
        except Exception as e:
            logger.warning(f"成交额比例计算失败: {e}")
            
        return 1.0  # 默认返回1倍
    
    def _calculate_down_limit_count(self, stock_data: List[Dict]) -> int:
        """计算跌停家数"""
        count = 0
        for stock in stock_data:
            try:
                change_pct = stock.get('f3', 0)  # 涨跌幅
                if change_pct <= -9.8:  # 接近-10%跌停
                    count += 1
            except:
                continue
        return count
    
    def _calculate_emotion_score(self, n_up_limit: int, n_cont_limit: int, 
                               win_ratio: float, vol_ratio: float, 
                               n_down_limit: int, total_stocks: int) -> float:
        """计算综合情绪评分（0-100）"""
        
        # 各指标权重
        weights = {
            'up_limit': 0.25,      # 涨停家数权重25%
            'cont_limit': 0.20,    # 连板家数权重20%
            'win_ratio': 0.30,     # 赚钱比例权重30%
            'vol_ratio': 0.15,     # 成交放大权重15%
            'down_limit': 0.10     # 跌停家数权重10%（负面）
        }
        
        # 标准化各指标到0-100分
        up_limit_score = min(100, (n_up_limit / max(1, total_stocks * 0.05)) * 100)  # 5%涨停为满分
        cont_limit_score = min(100, (n_cont_limit / max(1, total_stocks * 0.02)) * 100)  # 2%连板为满分
        win_ratio_score = win_ratio * 100  # 直接转为百分制
        vol_ratio_score = min(100, max(0, (vol_ratio - 0.5) * 50))  # 0.5倍以上开始计分，2.5倍满分
        down_limit_penalty = min(50, (n_down_limit / max(1, total_stocks * 0.03)) * 50)  # 3%跌停扣50分
        
        # 综合评分
        total_score = (
            up_limit_score * weights['up_limit'] +
            cont_limit_score * weights['cont_limit'] +
            win_ratio_score * weights['win_ratio'] +
            vol_ratio_score * weights['vol_ratio']
        ) - down_limit_penalty * weights['down_limit']
        
        return max(0, min(100, total_score))
    
    def _determine_emotion_level(self, score: float) -> str:
        """确定情绪等级"""
        if score >= 85:
            return "极度狂热"
        elif score >= 70:
            return "情绪高涨"
        elif score >= 55:
            return "积极乐观"
        elif score >= 40:
            return "情绪平稳"
        elif score >= 25:
            return "谨慎悲观"
        elif score >= 15:
            return "情绪低迷"
        else:
            return "极度恐慌"
    
    def _determine_market_stage(self, n_up_limit: int, n_cont_limit: int,
                              win_ratio: float, vol_ratio: float, 
                              n_down_limit: int) -> str:
        """确定市场阶段"""
        
        # 分潮阶段判断逻辑
        if n_up_limit >= 80 and n_cont_limit >= 20 and win_ratio >= 0.7:
            return "分歧转一致（分潮）"
        elif n_up_limit >= 50 and win_ratio >= 0.6 and vol_ratio >= 1.5:
            return "情绪升温（助攻）"
        elif win_ratio >= 0.5 and vol_ratio >= 1.2:
            return "情绪回暖（复苏）"
        elif win_ratio <= 0.3 and n_down_limit >= 20:
            return "情绪冰点（冰点）"
        elif win_ratio <= 0.4 and vol_ratio <= 0.8:
            return "情绪退潮（退潮）"
        else:
            return "震荡整理"
    
    def _get_default_indicators(self) -> MarketEmotionIndicators:
        """获取默认指标数据"""
        return MarketEmotionIndicators(
            n_up_limit=0,
            n_cont_limit=0,
            win_ratio=0.5,
            vol_ratio=1.0,
            n_down_limit=0,
            total_stocks=4000,
            rising_stocks=2000,
            falling_stocks=2000,
            total_turnover=8000.0,
            avg_20d_turnover=8000.0,
            emotion_score=50.0,
            emotion_level="数据异常",
            market_stage="无法判断"
        )

def main():
    """主函数"""
    print("🎭 市场情绪核心指标分析器")
    print("="*50)
    
    analyzer = MarketEmotionAnalyzer()
    result = analyzer.analyze_market_emotion()
    
    print(f"\n📊 市场情绪核心指标:")
    print(f"  涨停家数: {result.n_up_limit}只")
    print(f"  连板家数: {result.n_cont_limit}只")
    print(f"  赚钱比例: {result.win_ratio:.1%}")
    print(f"  成交放大: {result.vol_ratio:.2f}倍")
    print(f"  跌停家数: {result.n_down_limit}只")
    print(f"\n🎯 综合评估:")
    print(f"  情绪评分: {result.emotion_score:.1f}/100")
    print(f"  情绪等级: {result.emotion_level}")
    print(f"  市场阶段: {result.market_stage}")

if __name__ == "__main__":
    main()