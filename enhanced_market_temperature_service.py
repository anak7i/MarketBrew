#!/usr/bin/env python3
"""
增强版市场温度计服务
集成沪深300 MA20/MA30技术指标的市场温度监控服务
"""

from flask import Flask, jsonify, render_template_string
import logging
import time
import threading
from market_temperature_analyzer import MarketTemperatureAnalyzer
import json
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局分析器实例和缓存
analyzer = MarketTemperatureAnalyzer()

# 全局缓存和锁机制
global_cache = {}
CACHE_DURATION = 120  # 2分钟缓存
analysis_lock = threading.Lock()
is_analyzing = False

def get_cached_result():
    """获取缓存的结果"""
    now = time.time()
    if 'result' in global_cache:
        cache_time = global_cache['timestamp']
        if now - cache_time < CACHE_DURATION:
            return global_cache['result']
    return None

def set_cached_result(result):
    """设置缓存结果"""
    global_cache['result'] = result
    global_cache['timestamp'] = time.time()

@app.route('/api/market-temperature', methods=['GET'])
def get_market_temperature():
    """获取市场温度详细数据"""
    global is_analyzing
    
    try:
        # 首先尝试获取缓存结果
        cached_result = get_cached_result()
        if cached_result:
            logger.info(f"🎯 使用缓存数据 (温度: {cached_result.temperature_score}分)")
            result = cached_result
        else:
            # 检查是否有其他线程正在分析
            with analysis_lock:
                if is_analyzing:
                    # 如果正在分析，再次尝试获取缓存（可能刚刚完成）
                    cached_result = get_cached_result()
                    if cached_result:
                        logger.info("⏳ 等待分析完成，获取到最新缓存")
                        result = cached_result
                    else:
                        # 如果仍无缓存，返回默认数据避免阻塞
                        logger.warning("🚫 系统正在分析中，返回默认数据")
                        return jsonify({
                            'status': 'processing',
                            'message': '系统正在分析数据，请稍后刷新...',
                            'timestamp': datetime.now().isoformat()
                        })
                else:
                    # 开始分析
                    is_analyzing = True
                    try:
                        logger.info("🔄 缓存过期，重新分析...")
                        result = analyzer.analyze_market_temperature()
                        # 缓存新结果
                        set_cached_result(result)
                    finally:
                        is_analyzing = False
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'temperature_score': result.temperature_score,
                'temperature_level': result.temperature_level,
                'up_down_ratio': result.up_down_ratio,
                'turnover_billion': result.turnover_billion,
                'margin_balance': result.margin_balance,
                'etf_inflow': result.etf_inflow,
                'heat_sources': result.heat_sources,
                'cool_sources': result.cool_sources,
                # 沪深300技术指标
                'hs300': {
                    'price': result.hs300_price,
                    'change': result.hs300_change,
                    'ma20': result.hs300_ma20,
                    'ma30': result.hs300_ma30,
                    'ma20_5d_ago': result.hs300_ma20_5d_ago,
                    'ma30_5d_ago': result.hs300_ma30_5d_ago,
                    'vs_ma20': result.hs300_vs_ma20,
                    'vs_ma30': result.hs300_vs_ma30,
                    'signal': result.ma_signal
                },
                # 增强技术分析结果
                'enhanced_analysis': {
                    'signal': result.enhanced_signal,
                    'strength': result.signal_strength,
                    'consecutive_days': result.consecutive_days,
                    'volume_breakout': bool(result.volume_breakout),
                    'ma_trend_up': bool(result.ma_trend_up),
                    'pullback_hold': bool(result.pullback_hold)
                },
                # 资金流数据
                'money_flow': {
                    'today': {
                        'north_bound': result.today_north_bound,
                        'etf_inflow': result.today_etf_inflow,
                        'main_force': result.today_main_force
                    },
                    'three_days_total': {
                        'north_bound': result.north_bound_3d_total,
                        'etf_inflow': result.etf_inflow_3d_total,
                        'main_force': result.main_force_3d_total
                    },
                    'seven_days_total': {
                        'north_bound': result.north_bound_7d_total,
                        'etf_inflow': result.etf_inflow_7d_total,
                        'main_force': result.main_force_7d_total
                    },
                    'thirty_days_total': {
                        'north_bound': result.north_bound_30d_total,
                        'etf_inflow': result.etf_inflow_30d_total,
                        'main_force': result.main_force_30d_total
                    },
                    'trends': {
                        'north_bound': result.north_bound_trend,
                        'etf': result.etf_trend,
                        'main_force': result.main_force_trend
                    },
                    'score': result.money_flow_score,
                    'level': result.money_flow_level
                },
                # 情绪周期分析
                'sentiment_cycle': {
                    'phase': result.sentiment_phase,
                    'score': result.sentiment_score,
                    'confidence': result.sentiment_confidence,
                    'signals': {
                        'profit_effect': result.profit_effect_signal,
                        'high_standard': result.high_standard_signal,
                        'turnover': result.turnover_signal,
                        'theme': result.theme_signal,
                        'etf_sentiment': result.etf_sentiment_signal
                    }
                },
                # 核心市场情绪指标
                'emotion_indicators': {
                    'n_up_limit': result.n_up_limit,
                    'n_cont_limit': result.n_cont_limit,
                    'win_ratio': result.win_ratio,
                    'vol_ratio': result.vol_ratio,
                    'n_down_limit': result.n_down_limit,
                    'score': result.emotion_score,
                    'level': result.emotion_level,
                    'stage': result.market_stage
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取市场温度数据失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/temperature-report', methods=['GET'])
def get_temperature_report():
    """获取市场温度报告"""
    try:
        report = analyzer.generate_temperature_report()
        
        return jsonify({
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'report': report
        })
        
    except Exception as e:
        logger.error(f"生成温度报告失败: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/dashboard')
def temperature_dashboard():
    """市场温度计仪表板"""
    html_template = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🌡️ MarketBrew 市场温度计</title>
        <style>
            body {
                font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                padding: 30px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .temperature-display {
                text-align: center;
                margin: 30px 0;
                padding: 20px;
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
            }
            .temperature-score {
                font-size: 4rem;
                font-weight: bold;
                margin: 10px 0;
            }
            .temperature-level {
                font-size: 1.5rem;
                margin: 10px 0;
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .metric-card {
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 20px;
                text-align: center;
            }
            .metric-title {
                font-size: 0.9rem;
                opacity: 0.8;
                margin-bottom: 10px;
            }
            .metric-value {
                font-size: 1.8rem;
                font-weight: bold;
                margin: 10px 0;
            }
            .technical-section {
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 20px;
                margin: 20px 0;
            }
            .factors-section {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 30px 0;
            }
            .factors-card {
                background: rgba(255,255,255,0.1);
                border-radius: 15px;
                padding: 20px;
            }
            .factor-item {
                margin: 8px 0;
                padding: 8px;
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
            }
            .refresh-btn {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 10px;
                cursor: pointer;
                margin: 10px;
                font-size: 1rem;
            }
            .refresh-btn:hover {
                background: rgba(255,255,255,0.3);
            }
            .loading {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            .ma-indicator {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 10px 0;
                padding: 10px;
                background: rgba(255,255,255,0.1);
                border-radius: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌡️ MarketBrew 市场温度计</h1>
                <p>实时监控市场情绪与技术指标</p>
                <button class="refresh-btn" onclick="refreshData()">🔄 刷新数据</button>
            </div>
            
            <div class="loading" id="loading">📊 正在加载数据...</div>
            
            <div id="dashboard-content">
                <div class="temperature-display">
                    <div id="temperature-icon">🌤️</div>
                    <div class="temperature-score" id="temperature-score">--</div>
                    <div class="temperature-level" id="temperature-level">加载中...</div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-title">涨跌比例</div>
                        <div class="metric-value" id="up-down-ratio">--%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">成交金额</div>
                        <div class="metric-value" id="turnover">--亿元</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">两融变化</div>
                        <div class="metric-value" id="margin-change">--%</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">ETF资金流</div>
                        <div class="metric-value" id="etf-flow">--亿元</div>
                    </div>
                </div>
                
                <div class="technical-section">
                    <h3>📈 沪深300技术分析</h3>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-title">最新价格</div>
                            <div class="metric-value" id="hs300-price">--</div>
                            <div id="hs300-change">--</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">技术信号</div>
                            <div class="metric-value" id="ma-signal">--</div>
                        </div>
                    </div>
                    
                    <div class="ma-indicator">
                        <span>MA20均线</span>
                        <span id="ma20-value">--</span>
                        <span id="ma20-distance">--</span>
                    </div>
                    
                    <div class="ma-indicator">
                        <span>MA30均线</span>
                        <span id="ma30-value">--</span>
                        <span id="ma30-distance">--</span>
                    </div>
                    
                    <div class="ma-indicator">
                        <span>MA20(5天前)</span>
                        <span id="ma20-5d-ago">--</span>
                        <span id="ma20-trend">--</span>
                    </div>
                    
                    <div class="ma-indicator">
                        <span>MA30(5天前)</span>
                        <span id="ma30-5d-ago">--</span>
                        <span id="ma30-trend">--</span>
                    </div>
                </div>
                
                <div class="technical-section">
                    <h3>🔍 增强技术分析</h3>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-title">综合信号</div>
                            <div class="metric-value" id="enhanced-signal">--</div>
                            <div id="signal-strength">强度: --%</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-title">突破状态</div>
                            <div class="metric-value" id="consecutive-days">--天</div>
                            <div>连续突破</div>
                        </div>
                    </div>
                    
                    <div class="ma-indicator">
                        <span>放量突破</span>
                        <span id="volume-breakout">--</span>
                        <span>📊</span>
                    </div>
                    
                    <div class="ma-indicator">
                        <span>均线趋势</span>
                        <span id="ma-trend-up">--</span>
                        <span>📈</span>
                    </div>
                    
                    <div class="ma-indicator">
                        <span>回踩不破</span>
                        <span id="pullback-hold">--</span>
                        <span>💪</span>
                    </div>
                </div>
                
                <div class="technical-section">
                    <h3>💰 资金流分析</h3>
                    <div class="metrics-grid">
                    </div>
                    
                    <style>
                        .money-flow-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin: 20px 0;
                            background: rgba(255,255,255,0.1);
                            border-radius: 10px;
                            overflow: hidden;
                        }
                        .money-flow-table th, .money-flow-table td {
                            padding: 12px 15px;
                            text-align: center;
                            border-bottom: 1px solid rgba(255,255,255,0.1);
                        }
                        .money-flow-table th {
                            background: rgba(255,255,255,0.2);
                            font-weight: bold;
                        }
                        .money-flow-table tr:hover {
                            background: rgba(255,255,255,0.05);
                        }
                        .positive { color: #4ade80; }
                        .negative { color: #f87171; }
                        .neutral { color: #94a3b8; }
                    </style>
                    
                    <table class="money-flow-table">
                        <thead>
                            <tr>
                                <th>资金类型</th>
                                <th>今日</th>
                                <th>3日</th>
                                <th>1周</th>
                                <th>4周</th>
                                <th>趋势</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>北向资金</td>
                                <td id="today-north-bound">--亿</td>
                                <td id="north-bound-3d">--亿</td>
                                <td id="north-bound-1w">--亿</td>
                                <td id="north-bound-4w">--亿</td>
                                <td id="north-bound-trend">--</td>
                            </tr>
                            <tr>
                                <td>ETF资金</td>
                                <td id="today-etf-flow">--亿</td>
                                <td id="etf-flow-3d">--亿</td>
                                <td id="etf-flow-1w">--亿</td>
                                <td id="etf-flow-4w">--亿</td>
                                <td id="etf-trend">--</td>
                            </tr>
                            <tr>
                                <td>主力资金</td>
                                <td id="today-main-force">--亿</td>
                                <td id="main-force-3d">--亿</td>
                                <td id="main-force-1w">--亿</td>
                                <td id="main-force-4w">--亿</td>
                                <td id="main-force-trend">--</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <!-- 核心市场情绪指标 -->
                <div class="section">
                    <h3>🎭 核心市场情绪指标</h3>
                    <div class="emotion-indicators-grid">
                        <div class="emotion-card">
                            <div class="emotion-title">涨停家数</div>
                            <div class="emotion-value" id="n-up-limit">--只</div>
                            <div class="emotion-desc">N_up_limit</div>
                        </div>
                        <div class="emotion-card">
                            <div class="emotion-title">连板家数</div>
                            <div class="emotion-value" id="n-cont-limit">--只</div>
                            <div class="emotion-desc">N_cont_limit (≥2连板)</div>
                        </div>
                        <div class="emotion-card">
                            <div class="emotion-title">赚钱比例</div>
                            <div class="emotion-value" id="win-ratio">--%</div>
                            <div class="emotion-desc">Win_ratio (涨幅>0/总数)</div>
                        </div>
                        <div class="emotion-card">
                            <div class="emotion-title">成交放大</div>
                            <div class="emotion-value" id="vol-ratio">--倍</div>
                            <div class="emotion-desc">Vol_ratio (当日/20日均)</div>
                        </div>
                        <div class="emotion-card">
                            <div class="emotion-title">跌停家数</div>
                            <div class="emotion-value" id="n-down-limit">--只</div>
                            <div class="emotion-desc">N_down_limit (退潮&冰点参考)</div>
                        </div>
                    </div>
                    
                    <div class="emotion-summary">
                        <div class="emotion-score-display">
                            <div class="emotion-score-title">综合情绪评分</div>
                            <div class="emotion-score-value" id="emotion-score">--</div>
                            <div class="emotion-level" id="emotion-level">--</div>
                        </div>
                        <div class="market-stage">
                            <div class="stage-title">市场阶段判断</div>
                            <div class="stage-value" id="market-stage">--</div>
                        </div>
                    </div>
                    
                    <style>
                        .emotion-indicators-grid {
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                            gap: 15px;
                            margin: 20px 0;
                        }
                        .emotion-card {
                            background: rgba(255,255,255,0.08);
                            border-radius: 12px;
                            padding: 20px;
                            text-align: center;
                            transition: all 0.3s ease;
                            border: 1px solid rgba(255,255,255,0.1);
                        }
                        .emotion-card:hover {
                            background: rgba(255,255,255,0.12);
                            transform: translateY(-2px);
                        }
                        .emotion-title {
                            font-size: 0.9rem;
                            opacity: 0.8;
                            margin-bottom: 8px;
                            font-weight: 600;
                        }
                        .emotion-value {
                            font-size: 1.8rem;
                            font-weight: bold;
                            margin: 12px 0;
                            color: #60a5fa;
                        }
                        .emotion-desc {
                            font-size: 0.75rem;
                            opacity: 0.6;
                            line-height: 1.3;
                        }
                        .emotion-summary {
                            display: grid;
                            grid-template-columns: 1fr 1fr;
                            gap: 20px;
                            margin-top: 25px;
                            padding: 20px;
                            background: rgba(255,255,255,0.05);
                            border-radius: 15px;
                        }
                        .emotion-score-display, .market-stage {
                            text-align: center;
                        }
                        .emotion-score-title, .stage-title {
                            font-size: 1rem;
                            opacity: 0.8;
                            margin-bottom: 10px;
                        }
                        .emotion-score-value {
                            font-size: 2.5rem;
                            font-weight: bold;
                            color: #34d399;
                            margin: 10px 0;
                        }
                        .emotion-level {
                            font-size: 1.1rem;
                            font-weight: 600;
                            color: #fbbf24;
                        }
                        .stage-value {
                            font-size: 1.3rem;
                            font-weight: bold;
                            color: #a78bfa;
                            margin-top: 10px;
                        }
                    </style>
                </div>
                
                <div class="factors-section">
                    <div class="factors-card">
                        <h3>🔥 升温因素</h3>
                        <div id="heat-sources"></div>
                    </div>
                    <div class="factors-card">
                        <h3>❄️ 降温因素</h3>
                        <div id="cool-sources"></div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let isLoading = false;
            
            async function refreshData() {
                if (isLoading) return;
                
                isLoading = true;
                document.getElementById('loading').style.display = 'block';
                document.getElementById('dashboard-content').style.opacity = '0.5';
                
                try {
                    // Add cache-busting parameter and longer timeout
                    const timestamp = new Date().getTime();
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
                    
                    const response = await fetch(`/api/market-temperature?_t=${timestamp}`, {
                        signal: controller.signal,
                        cache: 'no-cache',
                        headers: {
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                        }
                    });
                    clearTimeout(timeoutId);
                    const result = await response.json();
                    
                    if (result.status === 'success') {
                        updateDashboard(result.data);
                    } else {
                        alert('数据获取失败: ' + result.message);
                    }
                } catch (error) {
                    console.error('Error:', error);
                    if (error.name === 'AbortError') {
                        alert('请求超时，服务器正在处理大量数据...');
                    } else {
                        alert('网络错误: ' + error.message);
                    }
                } finally {
                    isLoading = false;
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('dashboard-content').style.opacity = '1';
                }
            }
            
            function updateDashboard(data) {
                // 温度指标
                const tempIcons = {
                    '冰点': '🧊',
                    '偏冷': '❄️',
                    '温和': '🌤️',
                    '偏热': '🌡️',
                    '火热': '🔥'
                };
                
                document.getElementById('temperature-icon').textContent = tempIcons[data.temperature_level] || '🌤️';
                document.getElementById('temperature-score').textContent = data.temperature_score;
                document.getElementById('temperature-level').textContent = data.temperature_level;
                
                // 基础指标
                document.getElementById('up-down-ratio').textContent = (data.up_down_ratio * 100).toFixed(1) + '%';
                document.getElementById('turnover').textContent = data.turnover_billion.toFixed(0) + '亿元';
                document.getElementById('margin-change').textContent = (data.margin_balance >= 0 ? '+' : '') + data.margin_balance.toFixed(2) + '%';
                document.getElementById('etf-flow').textContent = (data.etf_inflow >= 0 ? '+' : '') + data.etf_inflow.toFixed(1) + '亿元';
                
                // 沪深300技术指标
                document.getElementById('hs300-price').textContent = data.hs300.price.toFixed(2);
                document.getElementById('hs300-change').textContent = (data.hs300.change >= 0 ? '+' : '') + data.hs300.change.toFixed(2) + '%';
                document.getElementById('ma-signal').textContent = data.hs300.signal;
                
                document.getElementById('ma20-value').textContent = data.hs300.ma20.toFixed(2);
                document.getElementById('ma20-distance').textContent = (data.hs300.vs_ma20 >= 0 ? '+' : '') + data.hs300.vs_ma20.toFixed(2) + '%';
                
                document.getElementById('ma30-value').textContent = data.hs300.ma30.toFixed(2);
                document.getElementById('ma30-distance').textContent = (data.hs300.vs_ma30 >= 0 ? '+' : '') + data.hs300.vs_ma30.toFixed(2) + '%';
                
                // MA20和MA30的5天前数据和趋势
                document.getElementById('ma20-5d-ago').textContent = data.hs300.ma20_5d_ago.toFixed(2);
                document.getElementById('ma30-5d-ago').textContent = data.hs300.ma30_5d_ago.toFixed(2);
                
                // 计算5天趋势
                const ma20_trend = data.hs300.ma20 - data.hs300.ma20_5d_ago;
                const ma30_trend = data.hs300.ma30 - data.hs300.ma30_5d_ago;
                
                document.getElementById('ma20-trend').textContent = (ma20_trend >= 0 ? '📈+' : '📉') + ma20_trend.toFixed(2);
                document.getElementById('ma30-trend').textContent = (ma30_trend >= 0 ? '📈+' : '📉') + ma30_trend.toFixed(2);
                
                // 增强技术分析数据
                if (data.enhanced_analysis) {
                    document.getElementById('enhanced-signal').textContent = data.enhanced_analysis.signal;
                    document.getElementById('signal-strength').textContent = '强度: ' + data.enhanced_analysis.strength.toFixed(1) + '%';
                    document.getElementById('consecutive-days').textContent = data.enhanced_analysis.consecutive_days;
                    document.getElementById('volume-breakout').textContent = data.enhanced_analysis.volume_breakout ? '✅ 是' : '❌ 否';
                    document.getElementById('ma-trend-up').textContent = data.enhanced_analysis.ma_trend_up ? '✅ 向上' : '❌ 向下';
                    document.getElementById('pullback-hold').textContent = data.enhanced_analysis.pullback_hold ? '✅ 守住' : '❌ 未守住';
                }
                
                // 资金流数据
                if (data.money_flow) {
                    const moneyFlow = data.money_flow;
                    
                    // 辅助函数：根据数值设置颜色样式
                    function setValueWithColor(elementId, value, suffix = '亿') {
                        const element = document.getElementById(elementId);
                        const displayValue = (value >= 0 ? '+' : '') + value.toFixed(1) + suffix;
                        element.textContent = displayValue;
                        
                        // 设置颜色
                        element.className = '';
                        if (value > 0) {
                            element.classList.add('positive');
                        } else if (value < 0) {
                            element.classList.add('negative');
                        } else {
                            element.classList.add('neutral');
                        }
                    }
                    
                    // 今日资金流（带颜色）
                    setValueWithColor('today-north-bound', moneyFlow.today.north_bound);
                    setValueWithColor('today-etf-flow', moneyFlow.today.etf_inflow);
                    setValueWithColor('today-main-force', moneyFlow.today.main_force);
                    
                    // 3天累计（带颜色）
                    setValueWithColor('north-bound-3d', moneyFlow.three_days_total.north_bound);
                    setValueWithColor('etf-flow-3d', moneyFlow.three_days_total.etf_inflow);
                    setValueWithColor('main-force-3d', moneyFlow.three_days_total.main_force);
                    
                    // 1周累计（带颜色）
                    setValueWithColor('north-bound-1w', moneyFlow.seven_days_total.north_bound);
                    setValueWithColor('etf-flow-1w', moneyFlow.seven_days_total.etf_inflow);
                    setValueWithColor('main-force-1w', moneyFlow.seven_days_total.main_force);
                    
                    // 4周累计（带颜色）
                    setValueWithColor('north-bound-4w', moneyFlow.thirty_days_total.north_bound);
                    setValueWithColor('etf-flow-4w', moneyFlow.thirty_days_total.etf_inflow);
                    setValueWithColor('main-force-4w', moneyFlow.thirty_days_total.main_force);
                    
                    // 趋势显示
                    document.getElementById('north-bound-trend').textContent = moneyFlow.trends.north_bound;
                    document.getElementById('etf-trend').textContent = moneyFlow.trends.etf;
                    document.getElementById('main-force-trend').textContent = moneyFlow.trends.main_force;
                }
                
                // 核心市场情绪指标
                if (data.emotion_indicators) {
                    const emotion = data.emotion_indicators;
                    
                    // 更新五个核心指标
                    document.getElementById('n-up-limit').textContent = emotion.n_up_limit + '只';
                    document.getElementById('n-cont-limit').textContent = emotion.n_cont_limit + '只';
                    document.getElementById('win-ratio').textContent = (emotion.win_ratio * 100).toFixed(1) + '%';
                    document.getElementById('vol-ratio').textContent = emotion.vol_ratio.toFixed(2) + '倍';
                    document.getElementById('n-down-limit').textContent = emotion.n_down_limit + '只';
                    
                    // 更新综合评估
                    document.getElementById('emotion-score').textContent = emotion.score.toFixed(1);
                    document.getElementById('emotion-level').textContent = emotion.level;
                    document.getElementById('market-stage').textContent = emotion.stage;
                    
                    // 根据评分动态调整颜色
                    const scoreElement = document.getElementById('emotion-score');
                    const levelElement = document.getElementById('emotion-level');
                    
                    if (emotion.score >= 70) {
                        scoreElement.style.color = '#10b981'; // 绿色
                        levelElement.style.color = '#10b981';
                    } else if (emotion.score >= 50) {
                        scoreElement.style.color = '#f59e0b'; // 黄色
                        levelElement.style.color = '#f59e0b';
                    } else {
                        scoreElement.style.color = '#ef4444'; // 红色
                        levelElement.style.color = '#ef4444';
                    }
                    
                    // 根据指标动态调整卡片颜色
                    const updateCardColor = (id, value, threshold, isPositive = true) => {
                        const element = document.getElementById(id);
                        if (element) {
                            const parentCard = element.closest('.emotion-card');
                            if (parentCard) {
                                if (isPositive ? value >= threshold : value <= threshold) {
                                    parentCard.style.background = 'rgba(34, 197, 94, 0.1)';
                                    parentCard.style.borderColor = 'rgba(34, 197, 94, 0.3)';
                                } else {
                                    parentCard.style.background = 'rgba(239, 68, 68, 0.1)';
                                    parentCard.style.borderColor = 'rgba(239, 68, 68, 0.3)';
                                }
                            }
                        }
                    };
                    
                    // 应用动态颜色
                    updateCardColor('n-up-limit', emotion.n_up_limit, 30, true);   // 涨停≥30只为好
                    updateCardColor('n-cont-limit', emotion.n_cont_limit, 10, true); // 连板≥10只为好
                    updateCardColor('win-ratio', emotion.win_ratio, 0.5, true);      // 赚钱比例≥50%为好
                    updateCardColor('vol-ratio', emotion.vol_ratio, 1.2, true);      // 成交放大≥1.2倍为好
                    updateCardColor('n-down-limit', emotion.n_down_limit, 10, false); // 跌停≤10只为好
                }
                
                // 升温/降温因素
                const heatSources = document.getElementById('heat-sources');
                heatSources.innerHTML = '';
                data.heat_sources.forEach(source => {
                    const div = document.createElement('div');
                    div.className = 'factor-item';
                    div.textContent = '• ' + source;
                    heatSources.appendChild(div);
                });
                
                const coolSources = document.getElementById('cool-sources');
                coolSources.innerHTML = '';
                data.cool_sources.forEach(source => {
                    const div = document.createElement('div');
                    div.className = 'factor-item';
                    div.textContent = '• ' + source;
                    coolSources.appendChild(div);
                });
                
                // 更新页面标题
                document.title = `🌡️ 市场温度: ${data.temperature_score}分 (${data.temperature_level}) - MarketBrew`;
            }
            
            // 页面加载时自动刷新数据
            window.onload = refreshData;
            
            // 每3分钟自动刷新 (延长间隔以减少服务器压力)
            setInterval(refreshData, 180000);
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template)

if __name__ == '__main__':
    logger.info("🌡️ 启动增强版市场温度计服务...")
    logger.info("📊 集成沪深300 MA20/MA30技术指标")
    logger.info("🌐 仪表板地址: http://localhost:5015/dashboard")
    logger.info("📡 API地址: http://localhost:5015/api/market-temperature")
    
    app.run(host='0.0.0.0', port=5015, debug=False)