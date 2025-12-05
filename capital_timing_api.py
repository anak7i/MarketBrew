#!/usr/bin/env python3
"""
资金流向择时API服务
提供HTTP API接口供前端调用
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from capital_flow_timing_service import timing_service
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求


@app.route('/')
def index():
    """首页"""
    return jsonify({
        'service': 'MarketBrew资金流向择时API',
        'version': '1.0',
        'status': 'running',
        'endpoints': {
            '/api/timing/comprehensive': '获取综合择时数据',
            '/api/timing/north-bound': '获取北向资金数据',
            '/api/timing/etf-flow': '获取ETF资金流数据',
            '/api/timing/main-force': '获取主力资金数据',
            '/api/timing/signal': '获取择时信号'
        }
    })


@app.route('/api/timing/comprehensive', methods=['GET'])
def get_comprehensive_timing():
    """获取综合择时数据"""
    try:
        logger.info("收到综合择时数据请求")
        data = timing_service.get_comprehensive_timing_data()

        return jsonify({
            'success': True,
            'data': data,
            'message': '数据获取成功'
        })

    except Exception as e:
        logger.error(f"获取综合择时数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '数据获取失败'
        }), 500


@app.route('/api/timing/north-bound', methods=['GET'])
def get_north_bound():
    """获取北向资金数据"""
    try:
        days = request.args.get('days', 30, type=int)
        logger.info(f"收到北向资金数据请求，天数: {days}")

        history = timing_service.get_north_bound_flow_history(days=days)
        periods = timing_service.calculate_period_flow(history)

        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'periods': periods,
                'latest': history[0] if history else {}
            },
            'message': '数据获取成功'
        })

    except Exception as e:
        logger.error(f"获取北向资金数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '数据获取失败'
        }), 500


@app.route('/api/timing/etf-flow', methods=['GET'])
def get_etf_flow():
    """获取ETF资金流数据"""
    try:
        days = request.args.get('days', 30, type=int)
        logger.info(f"收到ETF资金流数据请求，天数: {days}")

        history = timing_service.get_etf_flow_history(days=days)
        periods = timing_service.calculate_period_flow(history)

        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'periods': periods,
                'latest': history[0] if history else {}
            },
            'message': '数据获取成功'
        })

    except Exception as e:
        logger.error(f"获取ETF资金流数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '数据获取失败'
        }), 500


@app.route('/api/timing/main-force', methods=['GET'])
def get_main_force():
    """获取主力资金数据"""
    try:
        days = request.args.get('days', 30, type=int)
        logger.info(f"收到主力资金数据请求，天数: {days}")

        history = timing_service.get_main_force_flow_history(days=days)
        periods = timing_service.calculate_period_flow(history)

        return jsonify({
            'success': True,
            'data': {
                'history': history,
                'periods': periods,
                'latest': history[0] if history else {}
            },
            'message': '数据获取成功'
        })

    except Exception as e:
        logger.error(f"获取主力资金数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '数据获取失败'
        }), 500


@app.route('/api/timing/signal', methods=['GET'])
def get_timing_signal():
    """获取择时信号"""
    try:
        logger.info("收到择时信号请求")

        # 获取历史数据
        north_history = timing_service.get_north_bound_flow_history(days=30)
        etf_history = timing_service.get_etf_flow_history(days=30)
        main_force_history = timing_service.get_main_force_flow_history(days=30)

        # 生成信号
        signal = timing_service._generate_timing_signal(
            north_history, etf_history, main_force_history
        )

        return jsonify({
            'success': True,
            'data': signal,
            'message': '信号获取成功'
        })

    except Exception as e:
        logger.error(f"获取择时信号失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '信号获取失败'
        }), 500


@app.route('/api/timing/trend', methods=['GET'])
def get_trend():
    """获取指数MA20/MA30趋势判定（默认沪深300: 000300）"""
    try:
        index_code = request.args.get('index', '000300')
        above_days = request.args.get('above_days', default=3, type=int)
        result = timing_service.compute_index_trend(index_code=index_code, above_days=above_days)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"获取趋势失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/timing/overview', methods=['GET'])
def get_overview():
    """择时区总览：趋势 + 资金 + 情绪"""
    try:
        index_code = request.args.get('index', '000300')
        data = timing_service.get_timing_overview(index_code=index_code)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        logger.error(f"获取择时区总览失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/timing/clear-cache', methods=['POST'])
def clear_cache():
    """清空缓存"""
    try:
        timing_service.clear_cache()
        return jsonify({
            'success': True,
            'message': '缓存已清空'
        })

    except Exception as e:
        logger.error(f"清空缓存失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '清空缓存失败'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'capital_timing_api',
        'timestamp': datetime.now().isoformat()
    })


def main():
    """启动服务"""
    print("=" * 80)
    print("🚀 MarketBrew 资金流向择时API服务")
    print("=" * 80)
    print()
    print("📊 服务信息:")
    print("   • 端口: 5001")
    print("   • 访问地址: http://localhost:5001")
    print("   • API文档: http://localhost:5001/")
    print()
    print("🌐 主要接口:")
    print("   • GET  /api/timing/comprehensive  - 获取综合择时数据")
    print("   • GET  /api/timing/north-bound    - 获取北向资金数据")
    print("   • GET  /api/timing/etf-flow       - 获取ETF资金流数据")
    print("   • GET  /api/timing/main-force     - 获取主力资金数据")
    print("   • GET  /api/timing/signal         - 获取择时信号")
    print("   • POST /api/timing/clear-cache    - 清空缓存")
    print()
    print("=" * 80)
    print("✅ 服务启动中...")
    print("=" * 80)
    print()

    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,
        threaded=True
    )


if __name__ == '__main__':
    main()
