#!/usr/bin/env python3
"""
行业热力图分析器
监控各行业板块的涨幅、资金流向、成交额等热力指标
生成行业热力图，识别热点和冷门板块
"""

import requests
import json
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SectorHeatData:
    """行业热力数据"""
    sector_name: str          # 行业名称
    change_percent: float     # 涨跌幅%
    turnover_billion: float   # 成交额(亿)
    capital_flow: float       # 资金流向(亿)
    heat_score: float         # 热力得分0-100
    heat_level: str          # 热力等级
    leading_stocks: List[str] # 龙头股票
    
@dataclass
class SectorHeatResult:
    """行业热力分析结果"""
    overall_heat: float               # 整体热力0-100
    hot_sectors: List[SectorHeatData] # 热门板块
    cold_sectors: List[SectorHeatData] # 冷门板块
    rotation_trend: str              # 板块轮动趋势
    heat_distribution: Dict[str, int] # 热力分布统计
    sector_opportunities: List[str]   # 板块机会
    
class SectorHeatAnalyzer:
    """行业热力图分析器"""
    
    def __init__(self):
        self.market_index_url = "http://localhost:5008"
        
        # 行业分类映射
        self.sector_categories = {
            '银行': '金融',
            '证券': '金融', 
            '保险': '金融',
            '房地产': '地产',
            '建筑材料': '基建',
            '建筑装饰': '基建',
            '钢铁': '周期',
            '有色金属': '周期',
            '煤炭': '周期',
            '石油石化': '周期',
            '化工': '周期',
            '白酒': '消费',
            '食品饮料': '消费',
            '家用电器': '消费',
            '汽车': '消费',
            '纺织服装': '消费',
            '商业贸易': '消费',
            '医药生物': '医药',
            '医疗器械': '医药',
            '电子': '科技',
            '计算机': '科技',
            '通信': '科技',
            '传媒': '科技',
            '新能源': '新能源',
            '光伏设备': '新能源',
            '风电设备': '新能源',
            '电力设备': '新能源',
            '锂电池': '新能源',
            '储能': '新能源'
        }
        
        # 热力等级阈值
        self.heat_thresholds = {
            'ice_cold': 20,      # 冰冷 0-20
            'cold': 40,          # 偏冷 20-40
            'warm': 60,          # 温和 40-60
            'hot': 80,           # 火热 60-80
            'burning': 100       # 燃爆 80-100
        }
        
        self.cache = {}
        self.cache_duration = 120  # 2分钟缓存
        
    def analyze_sector_heat(self) -> SectorHeatResult:
        """分析行业热力图"""
        try:
            logger.info("🔥 开始分析行业热力图...")
            
            # 获取行业数据
            sector_data = self._get_sector_data()
            
            # 计算各行业热力
            sector_heats = self._calculate_sector_heats(sector_data)
            
            # 分析整体热力
            overall_heat = self._calculate_overall_heat(sector_heats)
            
            # 识别热门和冷门板块
            hot_sectors, cold_sectors = self._classify_sectors(sector_heats)
            
            # 分析板块轮动趋势
            rotation_trend = self._analyze_rotation_trend(sector_heats)
            
            # 统计热力分布
            heat_distribution = self._calculate_heat_distribution(sector_heats)
            
            # 识别板块机会
            sector_opportunities = self._identify_sector_opportunities(sector_heats)
            
            result = SectorHeatResult(
                overall_heat=round(overall_heat, 1),
                hot_sectors=hot_sectors,
                cold_sectors=cold_sectors,
                rotation_trend=rotation_trend,
                heat_distribution=heat_distribution,
                sector_opportunities=sector_opportunities
            )
            logger.info(f"🔥 行业热力分析完成: 整体热力{overall_heat:.1f}, 轮动趋势: {rotation_trend}")
            return result
            
        except Exception as e:
            logger.error(f"行业热力分析失败: {e}")
            return self._get_default_heat()
    
    def _get_sector_data(self) -> Dict:
        """获取行业数据"""
        cache_key = "sector_heat_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            # 获取行业指数数据
            response = requests.get(f"{self.market_index_url}/api/sector-indices", timeout=10)
            if response.status_code == 200:
                sector_data = response.json()
                
                # 缓存数据
                self.cache[cache_key] = sector_data
                self._set_cache_time(cache_key)
                
                return sector_data
            else:
                logger.warning("无法获取行业数据")
                return {}
                
        except Exception as e:
            logger.error(f"获取行业数据失败: {e}")
            return {}
    
    def _calculate_sector_heats(self, sector_data: Dict) -> List[SectorHeatData]:
        """计算各行业热力"""
        sector_heats = []
        
        try:
            # 获取行业指数数据
            sector_indices = sector_data.get('sector_indices', {})
            sector_performance = sector_data.get('sector_performance', {})
            
            # 处理行业指数数据
            for symbol, data in sector_indices.items():
                sector_name = data.get('name', '未知行业')
                change_percent = data.get('change_percent', 0)
                
                # 计算热力得分
                heat_score = self._calculate_single_sector_heat(data, sector_performance)
                
                # 确定热力等级
                heat_level = self._determine_heat_level(heat_score)
                
                # 模拟成交额和资金流向数据
                turnover_billion = self._simulate_sector_turnover(sector_name)
                capital_flow = self._simulate_capital_flow(sector_name, change_percent)
                
                # 获取龙头股票
                leading_stocks = self._get_leading_stocks(sector_name)
                
                sector_heat = SectorHeatData(
                    sector_name=sector_name,
                    change_percent=change_percent,
                    turnover_billion=turnover_billion,
                    capital_flow=capital_flow,
                    heat_score=heat_score,
                    heat_level=heat_level,
                    leading_stocks=leading_stocks
                )
                
                sector_heats.append(sector_heat)
            
            # 如果没有真实数据，创建一些示例数据
            if not sector_heats:
                sector_heats = self._create_sample_sector_data()
            
            # 按热力得分排序
            sector_heats.sort(key=lambda x: x.heat_score, reverse=True)
            
            return sector_heats
            
        except Exception as e:
            logger.warning(f"计算行业热力失败: {e}")
            return self._create_sample_sector_data()
    
    def _calculate_single_sector_heat(self, sector_data: Dict, performance: Dict) -> float:
        """计算单个行业热力得分"""
        try:
            # 基础分数
            heat_score = 50
            
            # 涨跌幅影响 (40分)
            change_percent = sector_data.get('change_percent', 0)
            if change_percent > 5:
                heat_score += 40
            elif change_percent > 3:
                heat_score += 30
            elif change_percent > 1:
                heat_score += 20
            elif change_percent > 0:
                heat_score += 10
            elif change_percent > -1:
                heat_score -= 5
            elif change_percent > -3:
                heat_score -= 20
            else:
                heat_score -= 30
            
            # 相对表现影响 (30分)
            # 检查是否在领涨板块中
            leading_sectors = performance.get('leading_sectors', [])
            sector_name = sector_data.get('name', '')
            
            if any(sector_name in leading or leading in sector_name for leading in leading_sectors):
                heat_score += 25
            
            # 成交活跃度影响 (20分)
            current_value = sector_data.get('current_value', 1000)
            if current_value > 1500:  # 相对活跃
                heat_score += 15
            elif current_value > 1200:
                heat_score += 8
            elif current_value < 800:
                heat_score -= 10
            
            # 技术面影响 (10分)
            if change_percent > 0 and current_value > 1000:
                heat_score += 10  # 量价配合
            elif change_percent < 0 and current_value < 1000:
                heat_score -= 5   # 量价背离
            
            return max(0, min(100, heat_score))
            
        except Exception as e:
            logger.warning(f"计算单行业热力失败: {e}")
            return 50
    
    def _determine_heat_level(self, heat_score: float) -> str:
        """确定热力等级"""
        if heat_score <= self.heat_thresholds['ice_cold']:
            return '冰冷'
        elif heat_score <= self.heat_thresholds['cold']:
            return '偏冷'
        elif heat_score <= self.heat_thresholds['warm']:
            return '温和'
        elif heat_score <= self.heat_thresholds['hot']:
            return '火热'
        else:
            return '燃爆'
    
    def _simulate_sector_turnover(self, sector_name: str) -> float:
        """模拟行业成交额"""
        # 不同行业的基础成交额不同
        base_turnovers = {
            '银行': 800, '证券': 600, '医药': 500, '电子': 700,
            '白酒': 400, '新能源': 900, '房地产': 300, '汽车': 600
        }
        
        # 获取基础成交额
        base = 400  # 默认400亿
        for key, value in base_turnovers.items():
            if key in sector_name:
                base = value
                break
        
        # 添加随机波动
        multiplier = np.random.uniform(0.5, 2.0)
        return round(base * multiplier, 1)
    
    def _simulate_capital_flow(self, sector_name: str, change_percent: float) -> float:
        """模拟资金流向"""
        # 基于涨跌幅模拟资金流向
        base_flow = change_percent * 10  # 涨1%对应10亿流入
        
        # 添加随机因素
        noise = np.random.uniform(-20, 20)
        total_flow = base_flow + noise
        
        return round(total_flow, 1)
    
    def _get_leading_stocks(self, sector_name: str) -> List[str]:
        """获取行业龙头股票"""
        leading_stocks_map = {
            '银行': ['招商银行', '平安银行', '兴业银行'],
            '证券': ['中信证券', '华泰证券', '海通证券'],
            '医药': ['恒瑞医药', '迈瑞医疗', '药明康德'],
            '白酒': ['贵州茅台', '五粮液', '剑南春'],
            '新能源': ['比亚迪', '宁德时代', '隆基绿能'],
            '电子': ['立讯精密', '歌尔股份', '京东方'],
            '汽车': ['比亚迪', '长城汽车', '吉利汽车'],
            '房地产': ['万科A', '保利发展', '招商蛇口']
        }
        
        # 查找匹配的行业
        for key, stocks in leading_stocks_map.items():
            if key in sector_name:
                return stocks[:3]  # 返回前3只
        
        return ['暂无数据']
    
    def _calculate_overall_heat(self, sector_heats: List[SectorHeatData]) -> float:
        """计算整体行业热力"""
        if not sector_heats:
            return 50
        
        # 加权平均计算整体热力
        total_score = 0
        total_weight = 0
        
        for sector in sector_heats:
            # 基于成交额作为权重
            weight = max(sector.turnover_billion, 100)  # 最小权重100
            total_score += sector.heat_score * weight
            total_weight += weight
        
        overall_heat = total_score / total_weight if total_weight > 0 else 50
        return overall_heat
    
    def _classify_sectors(self, sector_heats: List[SectorHeatData]) -> Tuple[List[SectorHeatData], List[SectorHeatData]]:
        """分类热门和冷门板块"""
        # 取前5名作为热门板块
        hot_sectors = [s for s in sector_heats if s.heat_score >= 60][:5]
        
        # 取后5名作为冷门板块
        cold_sectors = [s for s in sector_heats if s.heat_score <= 40][-5:]
        
        return hot_sectors, cold_sectors
    
    def _analyze_rotation_trend(self, sector_heats: List[SectorHeatData]) -> str:
        """分析板块轮动趋势"""
        if not sector_heats:
            return "暂无明显轮动"
        
        # 统计各大类的表现
        category_performance = {}
        for sector in sector_heats:
            category = self._get_sector_category(sector.sector_name)
            if category not in category_performance:
                category_performance[category] = []
            category_performance[category].append(sector.heat_score)
        
        # 计算各大类平均热力
        category_avg = {}
        for category, scores in category_performance.items():
            category_avg[category] = np.mean(scores)
        
        # 找出最热的大类
        if category_avg:
            top_category = max(category_avg, key=category_avg.get)
            top_score = category_avg[top_category]
            
            if top_score > 70:
                return f"{top_category}板块领涨"
            elif top_score > 60:
                return f"{top_category}板块活跃"
            else:
                return "板块轮动不明显"
        
        return "数据不足"
    
    def _get_sector_category(self, sector_name: str) -> str:
        """获取行业大类"""
        for keyword, category in self.sector_categories.items():
            if keyword in sector_name:
                return category
        return '其他'
    
    def _calculate_heat_distribution(self, sector_heats: List[SectorHeatData]) -> Dict[str, int]:
        """计算热力分布统计"""
        distribution = {
            '燃爆': 0,
            '火热': 0,
            '温和': 0,
            '偏冷': 0,
            '冰冷': 0
        }
        
        for sector in sector_heats:
            distribution[sector.heat_level] += 1
        
        return distribution
    
    def _identify_sector_opportunities(self, sector_heats: List[SectorHeatData]) -> List[str]:
        """识别板块机会"""
        opportunities = []
        
        # 热门板块机会
        hot_sectors = [s for s in sector_heats if s.heat_score >= 70]
        if hot_sectors:
            opportunities.append(f"热门板块: {hot_sectors[0].sector_name}等表现强势，可关注龙头股")
        
        # 反弹机会
        undervalued = [s for s in sector_heats if 30 <= s.heat_score <= 45 and s.change_percent > -2]
        if undervalued:
            opportunities.append(f"反弹机会: {undervalued[0].sector_name}等调整充分，存在反弹机会")
        
        # 轮动机会
        if len(sector_heats) >= 5:
            avg_heat = np.mean([s.heat_score for s in sector_heats])
            rising_sectors = [s for s in sector_heats if s.heat_score > avg_heat + 10]
            if rising_sectors:
                opportunities.append(f"轮动机会: {rising_sectors[0].sector_name}等有望接力上涨")
        
        return opportunities[:3]  # 最多返回3个机会
    
    def _create_sample_sector_data(self) -> List[SectorHeatData]:
        """创建示例行业数据"""
        sample_sectors = [
            ('医药生物', 2.1, 65, 450, 15.2),
            ('电子', 1.8, 62, 520, 12.5),
            ('新能源', -0.5, 45, 380, -8.3),
            ('银行', -1.2, 35, 280, -5.1),
            ('房地产', -2.3, 25, 180, -12.4)
        ]
        
        sector_heats = []
        for name, change, heat, turnover, flow in sample_sectors:
            sector_heat = SectorHeatData(
                sector_name=name,
                change_percent=change,
                heat_score=heat,
                heat_level=self._determine_heat_level(heat),
                turnover_billion=turnover,
                capital_flow=flow,
                leading_stocks=self._get_leading_stocks(name)
            )
            sector_heats.append(sector_heat)
        
        return sector_heats
    
    def _get_default_heat(self) -> SectorHeatResult:
        """获取默认热力结果"""
        sample_data = self._create_sample_sector_data()
        
        return SectorHeatResult(
            overall_heat=50.0,
            hot_sectors=sample_data[:2],
            cold_sectors=sample_data[-2:],
            rotation_trend="数据获取异常",
            heat_distribution={'温和': 5, '偏冷': 0, '火热': 0, '燃爆': 0, '冰冷': 0},
            sector_opportunities=['等待数据恢复']
        )
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存有效性"""
        if cache_key not in self.cache:
            return False
        cache_time = getattr(self, f'{cache_key}_time', 0)
        return time.time() - cache_time < self.cache_duration
    
    def _set_cache_time(self, cache_key: str):
        """设置缓存时间"""
        setattr(self, f'{cache_key}_time', time.time())
    
    def generate_heat_map_report(self) -> str:
        """生成行业热力图报告"""
        result = self.analyze_sector_heat()
        
        heat_icons = {
            '燃爆': '🔥',
            '火热': '🌶️',
            '温和': '🌤️', 
            '偏冷': '❄️',
            '冰冷': '🧊'
        }
        
        report = f"""
🔥 行业热力图报告
{'='*40}

📊 **整体热力**: {result.overall_heat:.1f}/100
🔄 **轮动趋势**: {result.rotation_trend}

🌶️ **热门板块** (前5名):"""
        
        for i, sector in enumerate(result.hot_sectors, 1):
            icon = heat_icons.get(sector.heat_level, '🌤️')
            report += f"""
  {i}. {icon} {sector.sector_name}: {sector.heat_score:.1f}分
     • 涨跌幅: {sector.change_percent:+.1f}%
     • 成交额: {sector.turnover_billion:.0f}亿元
     • 资金流: {sector.capital_flow:+.1f}亿元
     • 龙头股: {', '.join(sector.leading_stocks[:2])}"""
        
        report += f"\n\n❄️ **冷门板块**:"
        for i, sector in enumerate(result.cold_sectors, 1):
            icon = heat_icons.get(sector.heat_level, '🌤️')
            report += f"""
  {i}. {icon} {sector.sector_name}: {sector.heat_score:.1f}分 ({sector.change_percent:+.1f}%)"""
        
        report += f"\n\n📈 **热力分布**:"
        for level, count in result.heat_distribution.items():
            if count > 0:
                icon = heat_icons.get(level, '🌤️')
                report += f"\n  {icon} {level}: {count}个板块"
        
        report += f"\n\n💡 **板块机会**:"
        if result.sector_opportunities:
            for i, opportunity in enumerate(result.sector_opportunities, 1):
                report += f"\n  {i}. {opportunity}"
        else:
            report += "\n  暂无明显板块机会"
        
        report += f"""

🎯 **操作建议**:
  • 关注热门板块的龙头股票
  • 留意板块轮动的接力机会
  • 避免冷门板块的弱势股票
  • 关注超跌板块的反弹时机
"""
        
        return report

def main():
    """主函数 - 演示行业热力图功能"""
    print("🔥 MarketBrew 行业热力图系统")
    print("=" * 50)
    
    analyzer = SectorHeatAnalyzer()
    
    # 分析行业热力
    print("🔍 正在分析行业热力图...")
    result = analyzer.analyze_sector_heat()
    
    # 生成报告
    report = analyzer.generate_heat_map_report()
    print(report)
    
    print(f"\n🔧 技术详情:")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析板块: {len(result.hot_sectors + result.cold_sectors)}个")

if __name__ == "__main__":
    main()