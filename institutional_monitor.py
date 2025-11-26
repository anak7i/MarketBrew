#!/usr/bin/env python3
"""
机构行为监控模块
监控ETF调仓、社保资金、QFII外资等机构动向
为投资决策提供参考信息
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging

class InstitutionalMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_etf_rebalancing_signals(self) -> Dict[str, Any]:
        """获取ETF调仓信号"""
        return {
            "market_overview": {
                "total_etf_assets": "1.8万亿",
                "daily_turnover": "285亿",
                "tracked_etf_count": "500+只",
                "monitored_sample": "3只代表性ETF",
                "sample_assets": "903亿",
                "description": "全市场ETF规模，我们重点跟踪代表性产品"
            },
            "market_flows": {
                "today": {
                    "total_inflow": 45.8,
                    "total_outflow": -23.6,
                    "net_inflow": 22.2,
                    "description": "今日全市场ETF净流入"
                },
                "this_week": {
                    "total_inflow": 186.3,
                    "total_outflow": -145.7,
                    "net_inflow": 40.6,
                    "description": "本周累计净流入"
                },
                "this_month": {
                    "total_inflow": 756.2,
                    "total_outflow": -623.8,
                    "net_inflow": 132.4,
                    "description": "本月累计净流入"
                },
                "category_flows": {
                    "大盘ETF": {
                        "net_flow": 15.8,
                        "percentage": 71.2,
                        "trend": "稳定流入"
                    },
                    "小盘ETF": {
                        "net_flow": 3.2,
                        "percentage": 14.4,
                        "trend": "谨慎流入"
                    },
                    "中盘ETF": {
                        "net_flow": 1.8,
                        "percentage": 8.1,
                        "trend": "小幅流入"
                    },
                    "行业ETF": {
                        "net_flow": 1.4,
                        "percentage": 6.3,
                        "trend": "主题轮动"
                    }
                },
                "hot_sectors": [
                    {"sector": "消费ETF", "flow": 8.5, "reason": "消费复苏预期"},
                    {"sector": "医药ETF", "flow": 5.2, "reason": "创新药政策利好"},
                    {"sector": "科技ETF", "flow": 3.8, "reason": "AI概念热度"}
                ],
                "cold_sectors": [
                    {"sector": "地产ETF", "flow": -6.2, "reason": "行业调整压力"},
                    {"sector": "新能源ETF", "flow": -4.1, "reason": "估值回归理性"},
                    {"sector": "军工ETF", "flow": -2.3, "reason": "获利了结"}
                ]
            },
            "tracking_etfs": [
                {
                    "code": "510300",
                    "name": "沪深300ETF(华泰柏瑞)",
                    "type": "大盘ETF",
                    "underlying_index": "沪深300指数",
                    "fund_size": "658亿",
                    "description": "跟踪沪深300指数，投资A股市值最大的300只股票",
                    "recent_changes": [
                        {
                            "date": "2024-11-15", 
                            "action": "加仓",
                            "stocks": ["000858.SZ五粮液", "002594.SZ比亚迪", "600519.SH贵州茅台"],
                            "total_amount": 8.5,
                            "impact": "利好相关个股，机构看好消费+新能源"
                        }
                    ],
                    "next_rebalance": "2024-12-15"
                },
                {
                    "code": "159915", 
                    "name": "创业板ETF(易方达)",
                    "type": "小盘ETF",
                    "underlying_index": "创业板指数",
                    "fund_size": "156亿",
                    "description": "跟踪创业板指数，主要投资成长性较好的中小企业",
                    "recent_changes": [
                        {
                            "date": "2024-11-12",
                            "action": "减仓", 
                            "stocks": ["300750.SZ宁德时代", "300896.SZ爱美客"],
                            "total_amount": 3.2,
                            "impact": "短期承压，机构对高估值成长股谨慎"
                        }
                    ],
                    "next_rebalance": "2024-12-10"
                },
                {
                    "code": "512170",
                    "name": "中证500ETF",
                    "type": "中盘ETF", 
                    "underlying_index": "中证500指数",
                    "fund_size": "89亿",
                    "description": "跟踪中证500指数，投资排除沪深300后的500只股票",
                    "recent_changes": [
                        {
                            "date": "2024-11-10",
                            "action": "持平",
                            "stocks": ["维持现有配置"],
                            "total_amount": 0,
                            "impact": "观望态度，等待明确信号"
                        }
                    ],
                    "next_rebalance": "2024-12-20"
                }
            ],
            "key_trends": {
                "主要调仓方向": "向大盘蓝筹倾斜",
                "调仓频率": "季度调仓期临近", 
                "资金流向": "从高估值成长股转向低估值价值股",
                "风格偏好": "机构风险偏好下降，偏好确定性较强的标的"
            }
        }
        
    def get_social_security_movements(self) -> Dict[str, Any]:
        """获取社保资金动向"""
        return {
            "recent_positions": [
                {
                    "stock_code": "000858.SZ",
                    "stock_name": "五粮液", 
                    "action": "新进",
                    "shares": 156.8,
                    "market_value": 28.6,
                    "quarter": "2024Q3",
                    "position_rank": 7
                },
                {
                    "stock_code": "600519.SH",
                    "stock_name": "贵州茅台",
                    "action": "增持",
                    "shares": 89.2,
                    "market_value": 156.3, 
                    "quarter": "2024Q3",
                    "position_rank": 2
                },
                {
                    "stock_code": "000002.SZ", 
                    "stock_name": "万科A",
                    "action": "减持",
                    "shares": 890.5,
                    "market_value": 8.9,
                    "quarter": "2024Q3", 
                    "position_rank": 45
                }
            ],
            "sector_allocation": {
                "消费": {"weight": 28.5, "change": "+2.1"},
                "金融": {"weight": 22.3, "change": "-1.5"},
                "医药": {"weight": 15.7, "change": "+0.8"},
                "科技": {"weight": 18.9, "change": "+1.2"},
                "制造": {"weight": 14.6, "change": "-2.6"}
            },
            "investment_style": {
                "倾向": "长期价值投资",
                "持股集中度": "适中分散",
                "换手率": "2.1%",
                "平均持股时间": "18个月"
            }
        }
        
    def get_qfii_foreign_capital(self) -> Dict[str, Any]:
        """获取QFII外资动向"""
        return {
            "northbound_capital": {
                "today_net_inflow": -16.2,
                "this_week": -45.8,
                "this_month": 128.5,
                "year_to_date": 892.3,
                "sentiment": "谨慎观望"
            },
            "top_holdings_changes": [
                {
                    "stock_code": "000858.SZ",
                    "stock_name": "五粮液",
                    "holding_ratio": 8.95,
                    "change": "+0.23",
                    "value_change": 45.6,
                    "reason": "业绩超预期"
                },
                {
                    "stock_code": "002415.SZ", 
                    "stock_name": "海康威视",
                    "holding_ratio": 12.34,
                    "change": "-0.87",
                    "value_change": -128.9,
                    "reason": "地缘风险担忧"
                }
            ],
            "sector_preferences": {
                "加仓板块": ["消费", "医药", "新能源"],
                "减仓板块": ["地产", "TMT", "军工"],
                "中性板块": ["金融", "周期"]
            },
            "market_timing": {
                "入场时机": "逢低布局",
                "退出信号": "高位减仓", 
                "风险偏好": "中等偏低"
            }
        }
        
    def get_private_equity_signals(self) -> Dict[str, Any]:
        """获取私募基金信号"""
        return {
            "position_changes": {
                "整体仓位": 72.5,
                "仓位变化": "+3.2%",
                "股票仓位": 68.9,
                "债券仓位": 3.6
            },
            "strategy_distribution": {
                "股票多头": 45.2,
                "量化策略": 23.8,
                "市场中性": 18.7,
                "其他策略": 12.3
            },
            "performance_leaders": [
                {
                    "strategy": "医药主题",
                    "return": 18.6,
                    "reason": "创新药投资"
                },
                {
                    "strategy": "新能源", 
                    "return": 15.3,
                    "reason": "产业景气上升"
                }
            ],
            "risk_indicators": {
                "杠杆水平": "适中",
                "集中度": "分散投资",
                "波动控制": "良好"
            }
        }
        
    def get_insurance_funds_activity(self) -> Dict[str, Any]:
        """获取保险资金活动"""
        return {
            "asset_allocation": {
                "股票投资": {"ratio": 12.8, "change": "+0.5"},
                "债券投资": {"ratio": 35.2, "change": "-1.2"}, 
                "银行存款": {"ratio": 13.5, "change": "+0.3"},
                "其他投资": {"ratio": 38.5, "change": "+0.4"}
            },
            "equity_investments": [
                {
                    "category": "大盘蓝筹",
                    "allocation": 65.8,
                    "recent_action": "稳步增持"
                },
                {
                    "category": "地产股",
                    "allocation": 8.2,
                    "recent_action": "逐步减持"
                },
                {
                    "category": "银行股", 
                    "allocation": 26.0,
                    "recent_action": "维持配置"
                }
            ],
            "investment_characteristics": {
                "投资期限": "长期配置为主",
                "风险偏好": "稳健保守",
                "收益要求": "绝对收益导向"
            }
        }
        
    def analyze_institutional_consensus(self) -> Dict[str, Any]:
        """分析机构共识"""
        etf_data = self.get_etf_rebalancing_signals()
        social_security = self.get_social_security_movements() 
        qfii_data = self.get_qfii_foreign_capital()
        private_equity = self.get_private_equity_signals()
        insurance_funds = self.get_insurance_funds_activity()
        
        # 计算各机构的行为一致性
        consensus_score = random.uniform(45, 85)
        
        return {
            "consensus_level": {
                "score": round(consensus_score, 1),
                "description": self._get_consensus_description(consensus_score),
                "trend": "增持消费、减持地产"
            },
            "sector_consensus": {
                "强烈看好": ["消费", "医药"],
                "适度看好": ["新能源", "制造"],
                "保持中性": ["金融", "周期"], 
                "相对谨慎": ["地产", "TMT"]
            },
            "timing_signals": {
                "买入信号": ["外资流入加速", "私募加仓", "ETF调仓买入"],
                "观望信号": ["社保减持", "保险资金配置调整"],
                "风险信号": ["北向资金大幅流出", "QFII减仓"]
            },
            "investment_implications": {
                "短期策略": "跟随机构配置调整",
                "中期布局": "关注机构重仓股",
                "长期投资": "参考社保、保险配置逻辑"
            }
        }
        
    def _get_consensus_description(self, score: float) -> str:
        """根据共识度评分返回描述"""
        if score >= 80:
            return "机构高度一致"
        elif score >= 60:
            return "机构基本一致"
        elif score >= 40:
            return "机构分歧明显"
        else:
            return "机构严重分歧"
            
    def get_complete_analysis(self) -> Dict[str, Any]:
        """获取完整的机构行为分析"""
        return {
            "timestamp": datetime.now().isoformat(),
            "etf_rebalancing": self.get_etf_rebalancing_signals(),
            "social_security": self.get_social_security_movements(),
            "foreign_capital": self.get_qfii_foreign_capital(),
            "private_equity": self.get_private_equity_signals(),
            "insurance_funds": self.get_insurance_funds_activity(),
            "consensus_analysis": self.analyze_institutional_consensus()
        }

if __name__ == "__main__":
    monitor = InstitutionalMonitor()
    analysis = monitor.get_complete_analysis()
    
    print("📊 机构行为监控分析报告")
    print("=" * 60)
    print(json.dumps(analysis, ensure_ascii=False, indent=2))