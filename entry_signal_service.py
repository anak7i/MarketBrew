#!/usr/bin/env python3
"""
进场信号API服务
为AlphaBloom系统提供进场信号分析的API接口
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime
from daily_entry_signal_analyzer import DailyEntrySignalAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 全局分析器实例
signal_analyzer = DailyEntrySignalAnalyzer()

@app.route('/api/entry-signal', methods=['GET'])
def get_entry_signal():
    """获取当日进场信号"""
    try:
        result = signal_analyzer.analyze_daily_entry_signal()
        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取进场信号失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/entry-signal/config', methods=['GET'])
def get_signal_config():
    """获取信号分析配置"""
    try:
        config = {
            'weights': signal_analyzer.weights,
            'veto_conditions': signal_analyzer.veto_conditions,
            'cache_duration': signal_analyzer.cache_duration
        }
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/entry-signal/weights', methods=['POST'])
def update_weights():
    """更新评分权重"""
    try:
        new_weights = request.get_json()
        
        # 验证权重总和为1
        if abs(sum(new_weights.values()) - 1.0) > 0.01:
            return jsonify({
                'success': False,
                'error': '权重总和必须为1.0'
            }), 400
        
        # 更新权重
        signal_analyzer.weights.update(new_weights)
        
        logger.info(f"权重已更新: {new_weights}")
        return jsonify({
            'success': True,
            'message': '权重更新成功',
            'new_weights': signal_analyzer.weights
        })
        
    except Exception as e:
        logger.error(f"更新权重失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'service': 'MarketBrew Entry Signal Service',
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🎯 MarketBrew 进场信号服务启动中...")
    print("=" * 50)
    print("🌐 服务端口: 5009")
    print("🔗 服务地址: http://localhost:5009")
    print("📊 功能: 当日进场时机分析")
    print("\n可用接口:")
    print("  GET  /api/entry-signal        - 获取当日进场信号")
    print("  GET  /api/entry-signal/config - 获取分析配置")
    print("  POST /api/entry-signal/weights - 更新权重配置")
    print("  GET  /health                  - 健康检查")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5009, debug=True)