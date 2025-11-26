#!/usr/bin/env python3
"""
基于AkShare的真实ETF资金流向数据获取
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

class AkShareETFFetcher:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 主要ETF代码映射
        self.large_cap_etfs = {
            '510300': '沪深300ETF',
            '159919': '沪深300ETF',
            '510050': '50ETF',
            '159915': '创业板ETF',
            '510500': '中证500ETF'
        }
        
        self.small_cap_etfs = {
            '159922': '中小板ETF', 
            '159901': '深100ETF',
            '159905': '工银深红利ETF',
            '512690': '酒ETF',
            '512480': '半导体ETF'
        }
    
    def get_etf_real_time_data(self, symbol: str) -> Optional[Dict]:
        """获取单个ETF实时数据"""
        try:
            # 获取ETF实时数据
            df = ak.fund_etf_spot_em()
            
            # 查找指定代码
            etf_data = df[df['代码'] == symbol]
            if etf_data.empty:
                return None
            
            row = etf_data.iloc[0]
            return {
                'code': row['代码'],
                'name': row['名称'],
                'current_price': float(row['最新价']),
                'change_pct': float(row['涨跌幅']),
                'volume': float(row['成交量']),
                'turnover': float(row['成交额']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"获取ETF {symbol} 实时数据失败: {e}")
            return None
    
    def get_etf_fund_flow_estimation(self) -> Dict[str, Any]:
        """基于真实ETF数据估算资金流向"""
        try:
            # 获取所有ETF实时数据
            df = ak.fund_etf_spot_em()
            
            large_cap_flow = 0
            small_cap_flow = 0
            large_cap_details = []
            small_cap_details = []
            
            # 处理大盘ETF
            for code, name in self.large_cap_etfs.items():
                etf_data = df[df['代码'] == code]
                if not etf_data.empty:
                    row = etf_data.iloc[0]
                    turnover_yi = float(row['成交额']) / 100000000  # 转换为亿元
                    change_pct = float(row['涨跌幅'])
                    
                    # 资金流向估算：成交额 * 涨跌幅 * 流向系数
                    flow_coefficient = 0.6 if change_pct > 0 else -0.4  # 上涨更容易吸引资金
                    estimated_flow = turnover_yi * (change_pct / 100) * flow_coefficient
                    
                    large_cap_flow += estimated_flow
                    large_cap_details.append({
                        'code': code,
                        'name': row['名称'],
                        'turnover_yi': round(turnover_yi, 2),
                        'change_pct': change_pct,
                        'estimated_flow': round(estimated_flow, 2)
                    })
            
            # 处理小盘ETF
            for code, name in self.small_cap_etfs.items():
                etf_data = df[df['代码'] == code]
                if not etf_data.empty:
                    row = etf_data.iloc[0]
                    turnover_yi = float(row['成交额']) / 100000000
                    change_pct = float(row['涨跌幅'])
                    
                    flow_coefficient = 0.5 if change_pct > 0 else -0.3
                    estimated_flow = turnover_yi * (change_pct / 100) * flow_coefficient
                    
                    small_cap_flow += estimated_flow
                    small_cap_details.append({
                        'code': code, 
                        'name': row['名称'],
                        'turnover_yi': round(turnover_yi, 2),
                        'change_pct': change_pct,
                        'estimated_flow': round(estimated_flow, 2)
                    })
            
            net_inflow = large_cap_flow + small_cap_flow
            
            return {
                'large_cap_flow': round(large_cap_flow, 2),
                'small_cap_flow': round(small_cap_flow, 2), 
                'net_inflow_billion': round(net_inflow, 2),
                'data_source': 'AkShare真实ETF数据估算',
                'timestamp': datetime.now().isoformat(),
                'large_cap_details': large_cap_details,
                'small_cap_details': small_cap_details,
                'calculation_method': '成交额 × 涨跌幅 × 流向系数',
                'total_etfs_analyzed': len(large_cap_details) + len(small_cap_details)
            }
            
        except Exception as e:
            self.logger.error(f"获取ETF资金流向估算失败: {e}")
            return self._fallback_data()
    
    def get_individual_etf_fund_flow(self, symbol: str, days: int = 5) -> Optional[Dict]:
        """获取单个ETF的资金流向历史数据"""
        try:
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 尝试获取个股资金流向数据
            market = 'sh' if symbol.startswith('5') else 'sz'
            
            # 使用AkShare的个股资金流向接口
            df = ak.stock_individual_fund_flow(stock=symbol, market=market)
            
            if df.empty:
                return None
            
            # 获取最近数据
            recent_data = df.head(5)
            
            total_main_flow = recent_data['主力净流入-净额'].sum() / 100000000  # 转换为亿元
            
            return {
                'symbol': symbol,
                'days': days,
                'main_flow_billion': round(total_main_flow, 2),
                'data_source': 'AkShare个股资金流向',
                'timestamp': datetime.now().isoformat(),
                'daily_details': recent_data[['日期', '主力净流入-净额', '主力净流入-净占比']].to_dict('records')
            }
            
        except Exception as e:
            self.logger.error(f"获取ETF {symbol} 资金流向失败: {e}")
            return None
    
    def get_comprehensive_etf_flows(self) -> Dict[str, Any]:
        """获取综合ETF资金流向数据"""
        try:
            # 基础流向估算
            flow_estimation = self.get_etf_fund_flow_estimation()
            
            # 尝试获取主要ETF的详细资金流向
            detailed_flows = {}
            main_etfs = ['510300', '510050', '159915', '510500']  # 主要ETF代码
            
            for etf_code in main_etfs:
                individual_flow = self.get_individual_etf_fund_flow(etf_code)
                if individual_flow:
                    detailed_flows[etf_code] = individual_flow
            
            # 合并数据
            result = flow_estimation.copy()
            result['detailed_flows'] = detailed_flows
            result['data_quality'] = 'high' if detailed_flows else 'medium'
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取综合ETF流向失败: {e}")
            return self._fallback_data()
    
    def _fallback_data(self) -> Dict[str, Any]:
        """备用数据"""
        return {
            'large_cap_flow': 0,
            'small_cap_flow': 0,
            'net_inflow_billion': 0,
            'data_source': 'AkShare连接失败-备用数据',
            'timestamp': datetime.now().isoformat(),
            'error': True
        }

if __name__ == "__main__":
    # 测试新的ETF数据获取
    fetcher = AkShareETFFetcher()
    
    print("🚀 测试AkShare ETF真实数据获取...")
    
    # 测试获取综合数据
    data = fetcher.get_comprehensive_etf_flows()
    
    print(f"\n📊 ETF资金流向数据:")
    print(f"数据源: {data.get('data_source')}")
    print(f"大盘ETF流向: {data.get('large_cap_flow')}亿元")
    print(f"小盘ETF流向: {data.get('small_cap_flow')}亿元") 
    print(f"净流入: {data.get('net_inflow_billion')}亿元")
    print(f"数据质量: {data.get('data_quality', 'unknown')}")
    print(f"分析ETF数量: {data.get('total_etfs_analyzed', 0)}")
    
    if data.get('large_cap_details'):
        print(f"\n📈 大盘ETF详情:")
        for detail in data['large_cap_details'][:3]:  # 显示前3个
            print(f"  {detail['name']} ({detail['code']}): 成交额{detail['turnover_yi']}亿, 涨跌{detail['change_pct']}%, 估算流向{detail['estimated_flow']}亿")
    
    if data.get('small_cap_details'):
        print(f"\n📉 小盘ETF详情:")
        for detail in data['small_cap_details'][:3]:
            print(f"  {detail['name']} ({detail['code']}): 成交额{detail['turnover_yi']}亿, 涨跌{detail['change_pct']}%, 估算流向{detail['estimated_flow']}亿")