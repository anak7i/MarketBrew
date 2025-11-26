#!/usr/bin/env python3
"""
风险警报服务
提供REST API接口，为前端提供风险预警数据
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from risk_alert_monitor import RiskAlertMonitor
from datetime import datetime

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化风险监控器
risk_monitor = RiskAlertMonitor()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "Risk Alert Service",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/risk/overview', methods=['GET'])
def get_risk_overview():
    """获取风险概览"""
    try:
        analysis = risk_monitor.get_complete_risk_analysis()
        
        # 构建概览数据
        overview = {
            "timestamp": analysis["timestamp"],
            "overall_score": analysis["overall_assessment"]["overall_score"],
            "risk_level": analysis["overall_assessment"]["risk_level"],
            "key_risks": analysis["overall_assessment"]["key_risks"],
            "recommendations": analysis["overall_assessment"]["recommendations"],
            "breakdown": analysis["overall_assessment"]["breakdown"],
            "alert_count": {
                "high": len([alert for alert in analysis["regulatory_risks"]["current_alerts"] if alert["level"] == "高"]),
                "medium": len([alert for alert in analysis["regulatory_risks"]["current_alerts"] if alert["level"] == "中等"]),
                "low": len([alert for alert in analysis["regulatory_risks"]["current_alerts"] if alert["level"] == "低"])
            }
        }
        
        return jsonify({
            "success": True,
            "data": overview,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取风险概览失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/risk/regulatory', methods=['GET'])
def get_regulatory_risks():
    """获取监管风险数据"""
    try:
        data = risk_monitor.get_regulatory_risks()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取监管风险数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/risk/real-estate', methods=['GET'])
def get_real_estate_risks():
    """获取地产风险数据"""
    try:
        data = risk_monitor.get_real_estate_risks()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取地产风险数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/risk/geopolitical', methods=['GET'])
def get_geopolitical_risks():
    """获取地缘政治风险数据"""
    try:
        data = risk_monitor.get_geopolitical_risks()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取地缘政治风险数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/risk/financial', methods=['GET'])
def get_financial_risks():
    """获取金融系统风险数据"""
    try:
        data = risk_monitor.get_financial_system_risks()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取金融系统风险数据失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/risk/assessment', methods=['GET'])
def get_overall_assessment():
    """获取整体风险评估"""
    try:
        data = risk_monitor.calculate_overall_risk_score()
        
        return jsonify({
            "success": True,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取整体风险评估失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/risk/alerts', methods=['GET'])
def get_active_alerts():
    """获取活跃警报"""
    try:
        regulatory_data = risk_monitor.get_regulatory_risks()
        real_estate_data = risk_monitor.get_real_estate_risks()
        
        # 合并所有警报
        alerts = []
        
        # 监管警报
        for alert in regulatory_data["current_alerts"]:
            alerts.append({
                "id": f"reg_{len(alerts)}",
                "category": "监管政策",
                "level": alert["level"],
                "title": alert["title"],
                "description": alert["description"],
                "probability": alert["probability"],
                "timeline": alert["timeline"],
                "affected_sectors": alert["affected_sectors"],
                "date": alert["date"]
            })
            
        # 地产链警报
        for risk in real_estate_data["supply_chain_risks"]:
            if risk["impact_score"] >= 80:
                alerts.append({
                    "id": f"re_{len(alerts)}",
                    "category": "地产链",
                    "level": "高" if risk["risk_level"] == "高" else "中等",
                    "title": f"{risk['category']}行业风险",
                    "description": risk["description"],
                    "probability": risk["impact_score"],
                    "timeline": "短期(1-3个月)",
                    "affected_sectors": [risk["category"]],
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
        
        return jsonify({
            "success": True,
            "data": {
                "total_alerts": len(alerts),
                "alerts": alerts,
                "summary": {
                    "high": len([a for a in alerts if a["level"] == "高"]),
                    "medium": len([a for a in alerts if a["level"] == "中等"]),
                    "low": len([a for a in alerts if a["level"] == "低"])
                }
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取活跃警报失败: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    logger.info("启动风险警报服务...")
    app.run(debug=True, host='0.0.0.0', port=5012)