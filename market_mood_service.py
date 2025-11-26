#!/usr/bin/env python3
"""
市场情绪与风险监控服务 (Market Mood Service)
提供REST API接口，帮助用户判断今天适不适合出手：追涨日/观望日/抄底日
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import time
from datetime import datetime
from market_mood_analyzer import MarketMoodAnalyzer, MarketMoodResult

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 全局变量
mood_analyzer = None
last_analysis_time = 0
cached_result = None
cache_duration = 120  # 2分钟缓存

def initialize_service():
    """初始化服务"""
    global mood_analyzer
    try:
        mood_analyzer = MarketMoodAnalyzer()
        logger.info("✅ Market Mood 分析器初始化成功")
        return True
    except Exception as e:
        logger.error(f"❌ Market Mood 分析器初始化失败: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'Market Mood Service',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/market-mood', methods=['GET'])
def get_market_mood():
    """获取市场情绪分析"""
    global last_analysis_time, cached_result
    
    try:
        current_time = time.time()
        
        # 检查缓存
        if cached_result and (current_time - last_analysis_time) < cache_duration:
            logger.info("📋 使用缓存的Market Mood数据")
            return jsonify({
                'success': True,
                'data': cached_result,
                'cached': True,
                'timestamp': datetime.now().isoformat()
            })
        
        # 执行新的分析
        logger.info("🔍 开始Market Mood分析...")
        start_time = time.time()
        
        if not mood_analyzer:
            return jsonify({
                'success': False,
                'error': 'Market Mood analyzer not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # 分析市场情绪
        mood_result = mood_analyzer.analyze_market_mood()
        
        # 转换为字典格式
        result_data = {
            'mood_score': mood_result.mood_score,
            'mood_level': mood_result.mood_level,
            'action_type': mood_result.action_type,
            'confidence': mood_result.confidence,
            'risk_alerts': mood_result.risk_alerts,
            'opportunities': mood_result.opportunities,
            'analysis_time': datetime.now().isoformat(),
            'processing_duration': round(time.time() - start_time, 2)
        }
        
        # 添加市场情绪描述
        mood_descriptions = {
            'panic': '😰 极度恐慌',
            'cautious': '😐 谨慎观望', 
            'neutral': '😶 中性平静',
            'optimistic': '😊 乐观积极',
            'euphoric': '🤩 过度亢奋'
        }
        
        action_descriptions = {
            '抄底日': '💰 适合逢低布局，关注优质标的',
            '观望日': '⏳ 建议静观其变，等待更好时机', 
            '追涨日': '🚀 可适度参与强势板块，控制仓位'
        }
        
        result_data['mood_description'] = mood_descriptions.get(mood_result.mood_level, mood_result.mood_level)
        result_data['action_description'] = action_descriptions.get(mood_result.action_type, '')
        
        # 缓存结果
        cached_result = result_data
        last_analysis_time = current_time
        
        logger.info(f"✅ Market Mood分析完成: {mood_result.mood_score:.1f}分 - {mood_result.action_type}")
        
        return jsonify({
            'success': True,
            'data': result_data,
            'cached': False,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Market Mood分析失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/market-mood/report', methods=['GET'])
def get_market_mood_report():
    """获取详细的市场情绪报告"""
    try:
        if not mood_analyzer:
            return jsonify({
                'success': False,
                'error': 'Market Mood analyzer not initialized'
            }), 500
        
        # 获取分析结果
        mood_result = mood_analyzer.analyze_market_mood()
        
        # 生成详细报告
        report = mood_analyzer.generate_mood_report(mood_result)
        
        return jsonify({
            'success': True,
            'data': {
                'report': report,
                'mood_score': mood_result.mood_score,
                'mood_level': mood_result.mood_level,
                'action_type': mood_result.action_type,
                'confidence': mood_result.confidence,
                'risk_alerts': mood_result.risk_alerts,
                'opportunities': mood_result.opportunities
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ 生成Market Mood报告失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market-mood/details', methods=['GET'])
def get_mood_details():
    """获取Market Mood各维度具体数据"""
    try:
        logger.info("📊 获取Market Mood详细数据...")
        
        if not mood_analyzer:
            return jsonify({'success': False, 'error': 'Analyzer not initialized'}), 500
        
        # 获取综合市场数据
        market_data = mood_analyzer._get_comprehensive_market_data()
        
        # 计算各维度详细数据
        details = {
            'market_temperature': mood_analyzer._get_temperature_details(market_data),
            'sector_heat': mood_analyzer._get_sector_details(market_data),
            'capital_flow': mood_analyzer._get_capital_details(market_data),
            'technical_signals': mood_analyzer._get_technical_details(market_data),
            'sentiment_indicators': mood_analyzer._get_sentiment_details(market_data)
        }
        
        return jsonify({
            'success': True,
            'data': details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取详细数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/market-mood/config', methods=['GET'])
def get_mood_config():
    """获取Market Mood配置信息"""
    if not mood_analyzer:
        return jsonify({'success': False, 'error': 'Analyzer not initialized'}), 500
    
    return jsonify({
        'success': True,
        'data': {
            'mood_thresholds': mood_analyzer.mood_thresholds,
            'action_mapping': mood_analyzer.action_mapping,
            'cache_duration': mood_analyzer.cache_duration,
            'analysis_dimensions': [
                '市场温度计 (涨跌家数、成交额、两融、ETF资金流)',
                '行业热力图 (涨幅/资金/成交额)', 
                '资金流向 (北向/南向资金、主力资金)',
                '技术信号 (突破/跌破关键位置)',
                '情绪指标 (恐慌/亢奋区间)'
            ],
            'service_info': {
                'name': 'Market Mood Service',
                'version': '1.0.0',
                'description': '市场情绪与风险监控系统，帮助判断今日市场策略'
            }
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/market-mood/refresh', methods=['POST'])
def refresh_market_mood():
    """强制刷新市场情绪分析"""
    global last_analysis_time, cached_result
    
    try:
        # 清除缓存
        last_analysis_time = 0
        cached_result = None
        
        logger.info("🔄 强制刷新Market Mood数据...")
        
        # 重新分析
        return get_market_mood()
        
    except Exception as e:
        logger.error(f"❌ 强制刷新失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': 'API endpoint not found',
        'available_endpoints': [
            'GET /health',
            'GET /api/market-mood',
            'GET /api/market-mood/report', 
            'GET /api/market-mood/config',
            'POST /api/market-mood/refresh'
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'Please check server logs for details'
    }), 500

if __name__ == '__main__':
    print("🎭 MarketBrew Market Mood 服务启动中...")
    print("=" * 60)
    
    # 初始化服务
    if not initialize_service():
        print("❌ 服务初始化失败")
        exit(1)
    
    print("🌐 服务端口: 5010")
    print("🔗 服务地址: http://localhost:5010")
    print("🎯 功能: 市场情绪监控与投资策略建议")
    print()
    print("可用接口:")
    print("  GET  /health                    - 健康检查")
    print("  GET  /api/market-mood           - 获取市场情绪分析")
    print("  GET  /api/market-mood/report    - 获取详细情绪报告")
    print("  GET  /api/market-mood/config    - 获取配置信息")
    print("  POST /api/market-mood/refresh   - 强制刷新分析")
    print("=" * 60)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5010,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Market Mood服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")