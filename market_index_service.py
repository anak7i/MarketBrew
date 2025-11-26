#!/usr/bin/env python3
"""
MarketBrew 大盘指数数据服务
提供上证指数、深证成指、创业板指等大盘数据，为AI决策提供市场环境背景
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import threading
from real_market_data_fetcher import RealMarketDataFetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DATABASE = 'market_indices.db'

class MarketIndexProvider:
    """市场指数数据提供器"""
    
    def __init__(self):
        self.price_service_url = "http://localhost:5002"  # 复用价格服务
        self.real_fetcher = RealMarketDataFetcher()  # 真实数据获取器
        self.init_database()
        self.cache = {}
        self.cache_expiry = 300  # 5分钟缓存
        
    def init_database(self):
        """初始化指数数据库"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 指数基本信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS index_info (
                symbol VARCHAR(20) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                market VARCHAR(50),
                category VARCHAR(50),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 指数实时数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS index_realtime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                current_value DECIMAL(10,2),
                change_value DECIMAL(10,2),
                change_percent DECIMAL(6,3),
                volume BIGINT,
                turnover DECIMAL(15,2),
                timestamp TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (symbol) REFERENCES index_info(symbol)
            )
        ''')
        
        # 市场概况表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_overview (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trading_date DATE,
                total_market_cap DECIMAL(15,2),
                tradable_market_cap DECIMAL(15,2),
                pe_ratio DECIMAL(6,2),
                pb_ratio DECIMAL(6,2),
                dividend_yield DECIMAL(6,3),
                up_stocks INTEGER,
                down_stocks INTEGER,
                unchanged_stocks INTEGER,
                limit_up_stocks INTEGER,
                limit_down_stocks INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入主要指数基本信息
        index_list = [
            ('000001', '上证指数', '上海', '综合指数', '上海证券交易所综合指数'),
            ('399001', '深证成指', '深圳', '成份指数', '深圳证券交易所成份指数'),
            ('399006', '创业板指', '深圳', '创业板', '创业板指数'),
            ('000300', '沪深300', '全市场', '宽基指数', '沪深300指数'),
            ('000905', '中证500', '全市场', '中盘指数', '中证500指数'),
            ('000852', '中证1000', '全市场', '小盘指数', '中证1000指数'),
            ('399005', '中小板指', '深圳', '中小板', '中小板综合指数'),
            ('000016', '上证50', '上海', '蓝筹指数', '上证50指数'),
            ('399102', '创业板综', '深圳', '创业板', '创业板综合指数'),
            ('000688', '科创50', '上海', '科创板', '科创板50指数')
        ]
        
        cursor.executemany('''
            INSERT OR REPLACE INTO index_info (symbol, name, market, category, description)
            VALUES (?, ?, ?, ?, ?)
        ''', index_list)
        
        conn.commit()
        conn.close()
        logger.info("市场指数数据库初始化完成")

    def get_main_indices_data(self) -> Dict[str, Any]:
        """获取主要指数实时数据"""
        cache_key = "main_indices"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # 主要指数代码
            main_symbols = ['000001', '399001', '399006', '000300', '000905']
            
            # 获取实时数据
            indices_data = {}
            for symbol in main_symbols:
                index_data = self._get_index_realtime_data(symbol)
                if index_data:
                    indices_data[symbol] = index_data
                    
            # 获取市场概况
            market_overview = self._get_market_overview()
            
            result = {
                'indices': indices_data,
                'market_overview': market_overview,
                'market_status': self._determine_market_status(indices_data),
                'timestamp': datetime.now().isoformat()
            }
            
            # 缓存结果
            self.cache[cache_key] = {
                'data': result,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"获取主要指数数据失败: {e}")
            return self._get_fallback_indices_data()

    def _get_index_realtime_data(self, symbol: str) -> Optional[Dict]:
        """获取单个指数实时数据"""
        try:
            # 优先使用真实数据获取器
            real_data = self.real_fetcher.get_real_index_data(symbol)
            if real_data:
                return real_data
            
            # 备用：尝试从价格服务获取指数数据
            response = requests.post(
                f"{self.price_service_url}/api/indices",
                json={"symbols": [symbol]},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if symbol in data:
                    return data[symbol]
            
            # 无法获取真实数据时返回空
            logger.warning(f"🚫 无法获取{symbol}真实数据，跳过")
            return None
            
        except Exception as e:
            logger.warning(f"🚫 获取{symbol}实时数据失败: {e}")
            return None


    def _get_index_name(self, symbol: str) -> str:
        """获取指数名称"""
        name_map = {
            '000001': '上证指数',
            '399001': '深证成指', 
            '399006': '创业板指',
            '000300': '沪深300',
            '000905': '中证500'
        }
        return name_map.get(symbol, f"指数{symbol}")

    def _get_market_overview(self) -> Dict[str, Any]:
        """获取市场概况数据"""
        try:
            # 优先使用真实市场概况数据
            real_overview = self.real_fetcher.get_real_market_overview()
            if real_overview and real_overview.get('total_stocks', 0) > 1000:
                logger.info(f"✅ 使用真实市场概况数据: {real_overview['up_stocks']}涨{real_overview['down_stocks']}跌")
                return real_overview
        except Exception as e:
            logger.warning(f"获取真实市场概况失败: {e}")
        
        # 无法获取真实市场概况数据，移除模拟数据
        logger.info("🚫 移除模拟的市场概况数据")
        return {}

    def _determine_market_status(self, indices_data: Dict) -> Dict[str, Any]:
        """判断市场整体状态"""
        if not indices_data:
            return {'status': '无数据', 'description': '市场数据获取失败'}
        
        # 计算主要指数平均涨跌幅
        changes = []
        for symbol, data in indices_data.items():
            if 'change_percent' in data:
                changes.append(data['change_percent'])
        
        if not changes:
            return {'status': '未知', 'description': '无法判断市场状态'}
            
        avg_change = sum(changes) / len(changes)
        
        # 判断市场状态
        if avg_change > 1.5:
            status = '强势上涨'
            description = '大盘全线飘红，市场情绪乐观'
            trend = 'bullish'
        elif avg_change > 0.5:
            status = '温和上涨'
            description = '大盘小幅上涨，市场表现平稳'
            trend = 'mild_bullish'
        elif avg_change > -0.5:
            status = '震荡整理'
            description = '大盘窄幅震荡，多空博弈激烈'
            trend = 'sideways'
        elif avg_change > -1.5:
            status = '温和下跌'
            description = '大盘小幅调整，市场谨慎观望'
            trend = 'mild_bearish'
        else:
            status = '弱势下跌'
            description = '大盘深度调整，市场恐慌情绪浓厚'
            trend = 'bearish'
        
        return {
            'status': status,
            'trend': trend,
            'description': description,
            'avg_change': round(avg_change, 2),
            'strength': abs(avg_change)
        }

    def get_sector_indices(self) -> Dict[str, Any]:
        """获取行业指数数据"""
        try:
            # 尝试获取真实行业指数数据
            real_sector_data = self.real_fetcher.get_real_sector_data()
            if real_sector_data:
                logger.info("✅ 使用真实行业指数数据")
                return real_sector_data
            
            # 无法获取真实行业数据，移除模拟数据
            logger.info("🚫 移除模拟行业指数数据")
            return {
                'sector_indices': {},
                'sector_performance': {},
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取行业指数失败: {e}")
            return {
                'sector_indices': {},
                'sector_performance': {},
                'timestamp': datetime.now().isoformat()
            }

    def _analyze_sector_performance(self, sector_data: Dict) -> Dict[str, Any]:
        """分析行业表现"""
        if not sector_data:
            return {}
        
        # 按涨跌幅排序
        sector_changes = []
        for symbol, data in sector_data.items():
            if 'change_percent' in data:
                sector_changes.append({
                    'symbol': symbol,
                    'name': data.get('name', ''),
                    'category': data.get('category', ''),
                    'change_percent': data['change_percent']
                })
        
        sector_changes.sort(key=lambda x: x['change_percent'], reverse=True)
        
        return {
            'best_performing': sector_changes[:3],
            'worst_performing': sector_changes[-3:],
            'sector_rotation': self._detect_sector_rotation(sector_changes),
            'leading_sectors': [s['category'] for s in sector_changes[:3]],
            'lagging_sectors': [s['category'] for s in sector_changes[-3:]]
        }

    def _detect_sector_rotation(self, sector_changes: List) -> str:
        """检测板块轮动情况"""
        if not sector_changes:
            return "无明显轮动"
        
        # 简单的板块轮动检测逻辑
        top_categories = [s['category'] for s in sector_changes[:2]]
        
        if '科技' in top_categories:
            return "科技板块领涨"
        elif '金融' in top_categories:
            return "金融板块活跃"
        elif '消费' in top_categories:
            return "消费板块强势"
        elif '新能源' in top_categories:
            return "新能源概念热度高"
        else:
            return "多板块轮动"

    def get_market_summary_for_ai(self) -> str:
        """为AI分析生成市场环境摘要"""
        try:
            main_data = self.get_main_indices_data()
            sector_data = self.get_sector_indices()
            
            # 构建AI可读的市场摘要
            indices = main_data.get('indices', {})
            market_status = main_data.get('market_status', {})
            market_overview = main_data.get('market_overview', {})
            
            # 主要指数情况
            index_summary = []
            for symbol, data in indices.items():
                name = data.get('name', symbol)
                change = data.get('change_percent', 0)
                index_summary.append(f"{name}{change:+.1f}%")
            
            # 只保留真实数据：大盘状态和指数
            summary = f"""市场环境:
大盘: {market_status.get('description', '震荡整理')}
指数: {', '.join(index_summary)}"""
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"生成AI市场摘要失败: {e}")
            return "市场环境: 数据获取异常，建议谨慎操作"

    def _get_fallback_indices_data(self) -> Dict[str, Any]:
        """获取备用指数数据"""
        return {
            'indices': {
                '000001': {'name': '上证指数', 'current_value': 3100, 'change_percent': 0.0}
            },
            'market_overview': {
                'market_sentiment': '中性',
                'up_stocks': 2000,
                'down_stocks': 2000
            },
            'market_status': {'status': '震荡整理', 'description': '数据获取异常'}
        }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False
        return time.time() - self.cache[cache_key]['timestamp'] < self.cache_expiry

# 创建全局数据提供器实例
index_provider = MarketIndexProvider()

# Flask API路由
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'service': 'MarketBrew Index Data Service',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/main-indices', methods=['GET'])
def get_main_indices():
    """获取主要指数数据"""
    try:
        data = index_provider.get_main_indices_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"获取主要指数失败: {e}")
        return jsonify({'error': '获取主要指数数据失败'}), 500

@app.route('/api/sector-indices', methods=['GET'])
def get_sector_indices():
    """获取行业指数数据"""
    try:
        data = index_provider.get_sector_indices()
        return jsonify(data)
    except Exception as e:
        logger.error(f"获取行业指数失败: {e}")
        return jsonify({'error': '获取行业指数数据失败'}), 500

@app.route('/api/market-summary', methods=['GET'])
def get_market_summary():
    """获取市场摘要（供AI使用）"""
    try:
        summary = index_provider.get_market_summary_for_ai()
        return jsonify({
            'success': True,
            'market_summary': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取市场摘要失败: {e}")
        return jsonify({'error': '获取市场摘要失败'}), 500

@app.route('/api/market-status', methods=['GET'])
def get_market_status():
    """获取市场状态判断"""
    try:
        main_data = index_provider.get_main_indices_data()
        status = main_data.get('market_status', {})
        return jsonify(status)
    except Exception as e:
        logger.error(f"获取市场状态失败: {e}")
        return jsonify({'error': '获取市场状态失败'}), 500

if __name__ == '__main__':
    print("📈 MarketBrew 大盘指数服务启动中...")
    print("=== 服务信息 ===")
    print("🌐 服务端口: 5008")
    print("🔗 服务地址: http://localhost:5008")
    print("📊 数据源: 主要指数 + 行业指数 + 市场概况")
    print("\n可用接口:")
    print("  GET  /api/main-indices    - 获取主要指数数据")
    print("  GET  /api/sector-indices  - 获取行业指数数据") 
    print("  GET  /api/market-summary  - 获取市场摘要(AI用)")
    print("  GET  /api/market-status   - 获取市场状态判断")
    print("  GET  /health             - 健康检查")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5008, debug=True)