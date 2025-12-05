#!/usr/bin/env python3
"""
资金流向择时API服务 - 演示版本（包含模拟数据）
用于非交易时间展示界面效果
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from datetime import datetime, timedelta
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)


def generate_demo_data():
    """生成演示数据"""

    # 生成历史数据
    def gen_history(days, base_flow):
        history = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            # 随机生成流入流出，有正有负
            flow = base_flow + random.uniform(-base_flow*0.5, base_flow*0.5)
            history.append({
                'date': date,
                'total_flow': round(flow, 2),
                'sh_flow': round(flow * 0.6, 2),
                'sz_flow': round(flow * 0.4, 2),
                'sh_balance': round(5000 + random.uniform(-200, 200), 2),
                'sz_balance': round(4000 + random.uniform(-150, 150), 2),
                'inflow': max(0, round(flow, 2)),
                'outflow': min(0, round(flow, 2))
            })
        return history

    # 计算周期统计
    def calc_periods(history):
        periods_data = {}
        for period in [1, 3, 7, 14, 28]:
            period_history = history[:min(period, len(history))]
            total_inflow = sum(max(0, d['total_flow']) for d in period_history)
            total_outflow = sum(min(0, d['total_flow']) for d in period_history)
            net_flow = sum(d['total_flow'] for d in period_history)

            periods_data[f'{period}d'] = {
                'period': period,
                'inflow': round(total_inflow, 2),
                'outflow': round(abs(total_outflow), 2),
                'net_flow': round(net_flow, 2),
                'avg_daily_flow': round(net_flow / period if period > 0 else 0, 2),
                'flow_ratio': round((total_inflow / abs(total_outflow) if total_outflow != 0 else 0), 2)
            }
        return periods_data

    # 生成北向资金数据
    north_history = gen_history(30, 30)  # 基础流入30亿
    # 生成ETF资金数据
    etf_history = gen_history(30, 15)    # 基础流入15亿
    # 生成主力资金数据
    main_history = gen_history(30, 80)   # 基础流入80亿

    # 生成择时信号
    north_3d = sum(d['total_flow'] for d in north_history[:3])
    etf_7d = sum(d['total_flow'] for d in etf_history[:7])
    main_1d = main_history[0]['total_flow']

    score = 0
    signals = []

    if north_3d > 50:
        signals.append("北向资金3日净流入超50亿，市场情绪积极")
        score += 2
    elif north_3d < -50:
        signals.append("北向资金3日净流出超50亿，需谨慎")
        score -= 2

    if etf_7d > 20:
        signals.append("ETF资金7日持续流入，机构看好后市")
        score += 1
    elif etf_7d < -20:
        signals.append("ETF资金7日持续流出，机构减仓")
        score -= 1

    if main_1d > 100:
        signals.append("主力资金今日大幅流入，短期看多")
        score += 1
    elif main_1d < -100:
        signals.append("主力资金今日大幅流出，短期看空")
        score -= 1

    # 信号级别
    if score >= 3:
        level = "strong_bullish"
        suggestion = "强烈看多"
    elif score >= 1:
        level = "bullish"
        suggestion = "偏多"
    elif score <= -3:
        level = "strong_bearish"
        suggestion = "强烈看空"
    elif score <= -1:
        level = "bearish"
        suggestion = "偏空"
    else:
        level = "neutral"
        suggestion = "中性观望"

    return {
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'north_bound': {
            'latest': north_history[0],
            'periods': calc_periods(north_history),
            'history': north_history[:7]
        },
        'etf_flow': {
            'latest': etf_history[0],
            'periods': calc_periods(etf_history),
            'history': etf_history[:7]
        },
        'main_force': {
            'latest': main_history[0],
            'periods': calc_periods(main_history),
            'history': main_history[:7]
        },
        'timing_signal': {
            'score': score,
            'level': level,
            'suggestion': suggestion,
            'signals': signals,
            'timestamp': datetime.now().isoformat()
        },
        'is_demo': True,
        'demo_notice': '当前为演示数据（周末非交易日），实际数据请在交易时间查看'
    }


@app.route('/')
def index():
    """首页"""
    return jsonify({
        'service': 'MarketBrew资金流向择时API (演示版)',
        'version': '1.0-demo',
        'status': 'running',
        'notice': '当前使用模拟数据，实际数据请在交易时间使用',
        'endpoints': {
            '/api/timing/comprehensive': '获取综合择时数据（演示）',
            '/api/timing/north-bound': '获取北向资金数据（演示）',
            '/api/timing/etf-flow': '获取ETF资金流数据（演示）',
            '/api/timing/main-force': '获取主力资金数据（演示）',
            '/api/timing/signal': '获取择时信号（演示）'
        }
    })


@app.route('/api/timing/comprehensive', methods=['GET'])
def get_comprehensive_timing():
    """获取综合择时数据"""
    try:
        logger.info("收到综合择时数据请求（演示模式）")
        data = generate_demo_data()

        return jsonify({
            'success': True,
            'data': data,
            'message': '数据获取成功（演示数据）'
        })

    except Exception as e:
        logger.error(f"获取综合择时数据失败: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': '数据获取失败'
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'capital_timing_api_demo',
        'mode': 'demonstration',
        'timestamp': datetime.now().isoformat()
    })


def main():
    """启动服务"""
    print("=" * 80)
    print("🚀 MarketBrew 资金流向择时API服务 - 演示版")
    print("=" * 80)
    print()
    print("⚠️  注意: 当前使用模拟演示数据")
    print("   原因: 周末非交易日 / API接口维护")
    print("   用途: 展示界面效果和功能演示")
    print()
    print("📊 服务信息:")
    print("   • 端口: 5001")
    print("   • 访问地址: http://localhost:5001")
    print("   • 模式: 演示模式（模拟数据）")
    print()
    print("🌐 主要接口:")
    print("   • GET  /api/timing/comprehensive  - 获取综合择时数据")
    print("   • GET  /health                     - 健康检查")
    print()
    print("💡 提示:")
    print("   • 数据为模拟生成，仅用于展示")
    print("   • 交易时间使用 capital_timing_api.py 获取真实数据")
    print("   • 前端页面会显示「演示数据」提示")
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
