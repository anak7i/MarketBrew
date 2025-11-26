#!/usr/bin/env python3
"""
机构行为监控服务
提供REST API接口，为前端提供机构行为数据
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from institutional_monitor import InstitutionalMonitor
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化监控器
institutional_monitor = InstitutionalMonitor()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "Institutional Monitoring Service", 
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/institutional/overview', methods=['GET'])
def get_institutional_overview():
    """获取机构行为概览"""
    try:
        data = institutional_monitor.get_complete_analysis()
        
        # 构建概览数据
        overview = {
            "timestamp": data["timestamp"],
            "summary": {
                "consensus_score": data["consensus_analysis"]["consensus_level"]["score"],
                "consensus_desc": data["consensus_analysis"]["consensus_level"]["description"], 
                "main_trend": data["consensus_analysis"]["consensus_level"]["trend"],
                "key_signals": {
                    "northbound_flow": data["foreign_capital"]["northbound_capital"]["today_net_inflow"],
                    "etf_rebalancing": len(data["etf_rebalancing"]["tracking_etfs"]),
                    "social_security_moves": len(data["social_security"]["recent_positions"])
                }
            },
            "sector_consensus": data["consensus_analysis"]["sector_consensus"],
            "timing_signals": data["consensus_analysis"]["timing_signals"]
        }
        
        return jsonify({
            "success": True,
            "data": overview,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取机构行为概览失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/institutional/etf', methods=['GET'])
def get_etf_data():
    """获取ETF调仓数据"""
    try:
        data = institutional_monitor.get_etf_rebalancing_signals()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取ETF数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/institutional/social-security', methods=['GET'])
def get_social_security_data():
    """获取社保资金数据"""
    try:
        data = institutional_monitor.get_social_security_movements()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取社保数据失败: {e}")
        return jsonify({
            "success": False, 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/institutional/foreign-capital', methods=['GET'])  
def get_foreign_capital_data():
    """获取外资数据"""
    try:
        data = institutional_monitor.get_qfii_foreign_capital()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取外资数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/institutional/private-equity', methods=['GET'])
def get_private_equity_data():
    """获取私募基金数据"""
    try:
        data = institutional_monitor.get_private_equity_signals()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取私募数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/institutional/insurance', methods=['GET'])
def get_insurance_data():
    """获取保险资金数据"""
    try:
        data = institutional_monitor.get_insurance_funds_activity()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取保险资金数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/institutional/consensus', methods=['GET'])
def get_consensus_analysis():
    """获取机构共识分析"""
    try:
        data = institutional_monitor.analyze_institutional_consensus()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取机构共识分析失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    logger.info("启动机构行为监控服务...")
    app.run(debug=True, host='0.0.0.0', port=5011)