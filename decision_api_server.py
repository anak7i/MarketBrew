#!/usr/bin/env python3
"""
决策API服务器 - 为AI决策中心提供数据接口
"""

import os
import json
import threading
import subprocess
import random
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
from batch_optimized_decision_engine import BatchOptimizedDecisionEngine
from capital_flow_timing_service import CapitalFlowTimingService
from market_index_service import MarketIndexProvider
from market_mood_analyzer import MarketMoodAnalyzer

class DecisionAPIHandler(BaseHTTPRequestHandler):
    """决策API请求处理器"""

    def __init__(self, *args, **kwargs):
        self.engine = BatchOptimizedDecisionEngine()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/api/status':
            self.handle_status_request()
        elif parsed_path.path == '/api/decisions':
            self.handle_decisions_request()
        elif parsed_path.path == '/api/analysis-status':
            self.handle_analysis_status_request()
        elif parsed_path.path == '/api/market-stats':
            self.handle_market_stats()
        elif parsed_path.path == '/api/capital-timing':
            self.handle_capital_timing()
        elif parsed_path.path == '/api/market-mood':
            self.handle_market_mood()
        elif parsed_path.path == '/api/test-capital':
            self.handle_test_capital()
        elif parsed_path.path == '/health':
            self.handle_health_check()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/trigger-analysis':
            self.handle_trigger_analysis()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_status_request(self):
        """处理系统状态请求"""
        try:
            status = self.engine.get_analysis_status()
            
            # 添加服务器状态信息
            status.update({
                "server_time": datetime.now().isoformat(),
                "server_status": "running",
                "api_version": "1.0",
                "analysis_running": getattr(self.server, 'analysis_running', False)
            })
            
            self.send_json_response(status)
            
        except Exception as e:
            self.send_json_response({
                "error": str(e),
                "server_status": "error"
            }, status_code=500)
    
    def handle_decisions_request(self):
        """处理决策数据请求"""
        try:
            latest_data = self.engine.get_latest_decisions()
            
            if latest_data:
                # 构建前端需要的数据结构
                response_data = {
                    "analysis_time": latest_data["analysis_time"],
                    "buy_stocks": latest_data["buy_stocks"],
                    "sell_stocks": latest_data["sell_stocks"],
                    "hold_stocks": latest_data["hold_stocks"],
                    "market_context": latest_data.get("market_context", "")
                }
                self.send_json_response(response_data)
            else:
                self.send_json_response({
                    "message": "暂无决策数据，请先执行分析",
                    "has_data": False
                })
                
        except Exception as e:
            self.send_json_response({
                "error": str(e),
                "has_data": False
            }, status_code=500)
    
    def handle_analysis_status_request(self):
        """处理分析状态请求"""
        try:
            analysis_running = getattr(self.server, 'analysis_running', False)
            last_result = getattr(self.server, 'last_analysis_result', None)
            completed_time = getattr(self.server, 'analysis_completed_time', None)
            
            status_data = {
                'analysis_running': analysis_running,
                'last_result': last_result,
                'completed_time': completed_time.isoformat() if completed_time else None,
                'server_time': datetime.now().isoformat()
            }
            
            self.send_json_response(status_data)
            
        except Exception as e:
            self.send_json_response({
                "error": str(e)
            }, status_code=500)
    
    def handle_trigger_analysis(self):
        """处理触发分析请求"""
        try:
            # 检查是否已有分析在运行
            if getattr(self.server, 'analysis_running', False):
                self.send_json_response({
                    'success': False,
                    'error': '已有分析任务在运行中',
                    'status': 'running'
                })
                return
            
            # 标记分析开始
            self.server.analysis_running = True
            self.server.last_analysis_result = None
            
            # 在后台线程中启动分析
            analysis_thread = threading.Thread(target=self.run_analysis_background)
            analysis_thread.daemon = True
            analysis_thread.start()
            
            self.send_json_response({
                'success': True,
                'message': '决策分析已启动',
                'estimated_time': '15-20分钟',
                'status': 'started'
            })
            
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e),
                'status': 'error'
            }, status_code=500)
    
    def run_analysis_background(self):
        """在后台运行分析"""
        try:
            print(f"🚀 开始后台决策分析 - {datetime.now().strftime('%H:%M:%S')}")
            
            # 使用统一决策引擎执行分析
            result = self.engine.run_full_analysis()
            
            if result:
                print("✅ 后台决策分析完成")
                self.server.last_analysis_result = "success"
            else:
                print("❌ 后台决策分析失败")
                self.server.last_analysis_result = "failed"
                
        except Exception as e:
            print(f"❌ 后台分析异常: {e}")
            self.server.last_analysis_result = f"exception: {str(e)}"
        finally:
            self.server.analysis_running = False
            self.server.analysis_completed_time = datetime.now()
    
    def handle_market_stats(self):
        """处理市场统计请求（使用Tushare Pro或东方财富备用）"""
        try:
            print(f"[DEBUG] 开始处理市场统计请求 - {datetime.now().strftime('%H:%M:%S')}")

            # 优先使用MarketIndexProvider（支持Tushare Pro）
            market_provider = self.server.market_provider
            print(f"[DEBUG] 使用MarketIndexProvider获取市场概览...")

            market_overview = market_provider._get_market_overview()

            if market_overview and market_overview.get('total_stocks', 0) > 1000:
                # 使用Tushare Pro或备用数据源的市场概览
                print(f"[DEBUG] ✅ 获取市场概览成功，数据源: {market_overview.get('source', '未知')}")

                total_count = market_overview.get('total_stocks', 0)
                up_count = market_overview.get('up_stocks', 0)
                down_count = market_overview.get('down_stocks', 0)
                flat_count = market_overview.get('unchanged_stocks', 0)

                data = {
                    "total_count": total_count,
                    "up_count": up_count,
                    "down_count": down_count,
                    "flat_count": flat_count,
                    "up_down_ratio": round(up_count / down_count, 2) if down_count > 0 else 0,
                    "data_source": market_overview.get('source', '未知'),
                    "timestamp": datetime.now().isoformat()
                }

                print(f"[DEBUG] 市场统计数据: 总计{total_count}, 上涨{up_count}, 下跌{down_count}, 平盘{flat_count}")
            else:
                # 回退：使用东方财富API
                print(f"[WARNING] MarketIndexProvider数据不足，回退到东方财富API")
                from eastmoney_data_service import eastmoney_service

                stock_list = eastmoney_service.get_stock_list(market='all')

                if not stock_list:
                    print(f"[ERROR] 东方财富API也失败，返回空数据")
                    data = {
                        "total_count": 0,
                        "up_count": 0,
                        "down_count": 0,
                        "flat_count": 0,
                        "up_down_ratio": 0,
                        "timestamp": datetime.now().isoformat(),
                        "data_source": "fallback_failed"
                    }
                else:
                    # 统计涨跌股票数量
                    up_count = sum(1 for stock in stock_list if stock.get('change_pct', 0) > 0)
                    down_count = sum(1 for stock in stock_list if stock.get('change_pct', 0) < 0)
                    flat_count = sum(1 for stock in stock_list if stock.get('change_pct', 0) == 0)
                    total_count = len(stock_list)
                    up_down_ratio = round(up_count / down_count, 2) if down_count > 0 else 0

                    data = {
                        "total_count": total_count,
                        "up_count": up_count,
                        "down_count": down_count,
                        "flat_count": flat_count,
                        "up_down_ratio": up_down_ratio,
                        "timestamp": datetime.now().isoformat(),
                        "data_source": "eastmoney_fallback"
                    }

                    print(f"[DEBUG] 东方财富备用数据: 总计{total_count}, 上涨{up_count}, 下跌{down_count}, 平盘{flat_count}")

            self.send_json_response({
                "success": True,
                "data": data
            })

        except Exception as e:
            print(f"[ERROR] ❌ 获取市场统计失败: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)

    def handle_capital_timing(self):
        """处理资金流向择时请求"""
        try:
            print(f"[DEBUG] 开始处理资金流向请求 - {datetime.now().strftime('%H:%M:%S')}")

            # 获取北向资金多周期统计数据
            capital_service = self.server.capital_service
            print(f"[DEBUG] 获取到共享服务实例: {capital_service}")

            north_history = capital_service.get_north_bound_flow_history(days=30)
            print(f"[DEBUG] 获取到北向资金历史数据: {len(north_history) if north_history else 0} 条")

            if not north_history:
                # 如果没有数据，返回空结构
                print("[DEBUG] ⚠️ 没有北向资金数据")
                self.send_json_response({
                    "success": False,
                    "error": "暂无北向资金数据"
                }, status_code=500)
                return

            # 计算多周期统计
            periods = capital_service.calculate_period_flow(north_history, [1, 3, 7, 14, 28])
            print(f"[DEBUG] 计算多周期统计完成: {periods}")

            data = {
                "latest": north_history[0] if north_history else {},
                "periods": periods,
                "history": north_history[:7],  # 最近7天
                "timestamp": datetime.now().isoformat()
            }

            print(f"[DEBUG] ✅ 资金流向数据准备完成，准备发送响应")
            self.send_json_response({
                "success": True,
                "data": data
            })

        except Exception as e:
            print(f"[ERROR] ❌ 获取资金流向数据失败: {e}")
            import traceback
            traceback.print_exc()
            logging.error(f"获取资金流向数据失败: {e}")
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)

    def handle_test_capital(self):
        """测试资金服务连接和数据获取"""
        try:
            print(f"[TEST] 🧪 开始测试资金服务 - {datetime.now().strftime('%H:%M:%S')}")

            # 测试1: 检查服务实例
            has_service = hasattr(self.server, 'capital_service')
            service_obj = self.server.capital_service if has_service else None

            print(f"[TEST] 服务实例存在: {has_service}")
            print(f"[TEST] 服务对象: {service_obj}")

            # 测试2: 尝试获取数据
            test_result = {
                "service_exists": has_service,
                "service_type": str(type(service_obj)) if service_obj else None,
                "timestamp": datetime.now().isoformat()
            }

            if has_service and service_obj:
                try:
                    # 测试获取北向资金数据
                    print("[TEST] 尝试获取北向资金数据...")
                    north_data = service_obj.get_north_bound_flow_history(days=5)
                    test_result["north_data_count"] = len(north_data) if north_data else 0
                    test_result["north_data_sample"] = north_data[0] if north_data else None
                    print(f"[TEST] ✅ 成功获取 {test_result['north_data_count']} 条数据")
                except Exception as e:
                    test_result["north_data_error"] = str(e)
                    print(f"[TEST] ❌ 获取数据失败: {e}")

            print(f"[TEST] 测试结果: {test_result}")

            self.send_json_response({
                "success": True,
                "test_result": test_result,
                "message": "资金服务测试完成"
            })

        except Exception as e:
            print(f"[TEST] ❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)

    def handle_market_mood(self):
        """处理市场情绪请求（Market Mood）"""
        try:
            print(f"[DEBUG] 开始处理Market Mood请求 - {datetime.now().strftime('%H:%M:%S')}")

            # 获取Market Mood分析器和缓存
            mood_analyzer = self.server.mood_analyzer
            current_time = time.time()

            # 检查缓存
            cache_valid = (
                hasattr(self.server, 'mood_cache') and
                self.server.mood_cache and
                (current_time - self.server.mood_cache_time) < 120  # 2分钟缓存
            )

            if cache_valid:
                print("[DEBUG] 📋 使用缓存的Market Mood数据")
                cached_data = self.server.mood_cache.copy()
                cached_data['cached'] = True
                self.send_json_response({
                    "success": True,
                    "data": cached_data,
                    "timestamp": datetime.now().isoformat()
                })
                return

            # 执行新的分析
            print("[DEBUG] 🔍 开始Market Mood分析...")
            start_time = time.time()

            if not mood_analyzer:
                print("[ERROR] ❌ Market Mood分析器未初始化")
                self.send_json_response({
                    "success": False,
                    "error": "Market Mood analyzer not initialized"
                }, status_code=500)
                return

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

            # 添加情绪描述
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
            result_data['cached'] = False

            # 缓存结果
            self.server.mood_cache = result_data
            self.server.mood_cache_time = current_time

            print(f"[DEBUG] ✅ Market Mood分析完成: {mood_result.mood_score:.1f}分 - {mood_result.action_type}")

            self.send_json_response({
                "success": True,
                "data": result_data,
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            print(f"[ERROR] ❌ Market Mood分析失败: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)

    def handle_health_check(self):
        """健康检查"""
        self.send_json_response({
            'status': 'healthy',
            'service': 'Decision API Server (with Market Mood)',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0',
            'services': {
                'capital_flow': hasattr(self.server, 'capital_service'),
                'market_overview': hasattr(self.server, 'market_provider'),
                'market_mood': hasattr(self.server, 'mood_analyzer')
            }
        })

    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")

class DecisionAPIServer:
    """决策API服务器"""

    def __init__(self, port=8526):
        self.port = port
        self.server = None

        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        # 创建共享服务实例
        self.logger.info("初始化 CapitalFlowTimingService...")
        self.capital_service = CapitalFlowTimingService()
        self.logger.info("✅ CapitalFlowTimingService 初始化完成")

        self.logger.info("初始化 MarketIndexProvider...")
        self.market_provider = MarketIndexProvider()
        self.logger.info("✅ MarketIndexProvider 初始化完成")

        self.logger.info("初始化 MarketMoodAnalyzer...")
        self.mood_analyzer = MarketMoodAnalyzer()
        self.logger.info("✅ MarketMoodAnalyzer 初始化完成")
    
    def start(self):
        """启动服务器"""
        try:
            self.server = HTTPServer(('localhost', self.port), DecisionAPIHandler)

            # 初始化服务器状态
            self.server.analysis_running = False
            self.server.last_analysis_result = None
            self.server.analysis_completed_time = None

            # 将共享服务实例附加到服务器对象
            self.server.capital_service = self.capital_service
            self.server.market_provider = self.market_provider
            self.server.mood_analyzer = self.mood_analyzer

            # 初始化Market Mood缓存
            self.server.mood_cache = None
            self.server.mood_cache_time = 0

            self.logger.info("✅ 共享服务实例已附加到服务器")
            
            print(f"🌐 决策API服务器启动成功!")
            print(f"📱 服务地址: http://localhost:{self.port}")
            print(f"🔗 API端点:")
            print(f"  • POST /api/trigger-analysis - 触发决策分析")
            print(f"  • GET  /api/status - 查询系统状态")
            print(f"  • GET  /api/decisions - 获取决策数据")
            print(f"  • GET  /api/analysis-status - 查询分析状态")
            print(f"  • GET  /api/market-stats - 市场涨跌统计（支持Tushare Pro）")
            print(f"  • GET  /api/capital-timing - 北向资金流向（支持Tushare Pro）")
            print(f"  • GET  /api/market-mood - 市场情绪分析（Market Mood）")
            print(f"  • GET  /health - 健康检查")
            print(f"  • GET  /api/test-capital - 🧪 测试资金服务连接")
            print(f"\n💡 提示: 已集成Market Mood服务，无需单独启动5010端口")
            print(f"⏹️  按 Ctrl+C 停止服务")
            print("=" * 50)
            
            # 启动服务器
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\\n👋 决策API服务器已停止")
        except Exception as e:
            self.logger.error(f"❌ 服务器启动失败: {e}")
        finally:
            if self.server:
                self.server.shutdown()

def main():
    """主函数"""
    import sys
    
    port = 8526
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 端口号必须是数字")
            return
    
    server = DecisionAPIServer(port)
    server.start()

if __name__ == "__main__":
    main()