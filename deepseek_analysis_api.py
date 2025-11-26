#!/usr/bin/env python3
"""
DeepSeek智能分析API服务
提供顶级基金经理级别的股票分析服务
"""

import os
import json
import requests
import numpy as np
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from output_validator import validate_market_analysis, get_fallback_analysis
from simple_langchain_analyzer import SimpleLangChainAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)

class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_ma(prices, period):
        """计算移动平均线"""
        if len(prices) < period:
            return None
        return sum(prices[-period:]) / period
    
    @staticmethod
    def calculate_rsi(prices, period=14):
        """计算RSI指标"""
        if len(prices) < period + 1:
            return 50  # 默认中性值
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    @staticmethod
    def calculate_macd(prices, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        if len(prices) < slow:
            return {"macd": 0, "signal": 0, "histogram": 0, "trend": "中性"}
        
        # 简化的MACD计算
        ema_fast = np.mean(prices[-fast:])
        ema_slow = np.mean(prices[-slow:])
        macd = ema_fast - ema_slow
        signal_line = np.mean([macd] * min(signal, len(prices)))
        histogram = macd - signal_line
        
        trend = "多头" if macd > signal_line else "空头" if macd < signal_line else "中性"
        
        return {
            "macd": round(macd, 4),
            "signal": round(signal_line, 4),
            "histogram": round(histogram, 4),
            "trend": trend
        }
    
    @staticmethod
    def calculate_support_resistance(prices, volume=None):
        """计算支撑阻力位"""
        if len(prices) < 10:
            current = prices[-1]
            return {
                "support": round(current * 0.95, 2),
                "resistance": round(current * 1.05, 2)
            }
        
        high = max(prices[-20:]) if len(prices) >= 20 else max(prices)
        low = min(prices[-20:]) if len(prices) >= 20 else min(prices)
        
        return {
            "support": round(low * 1.02, 2),  # 略高于最低点
            "resistance": round(high * 0.98, 2)  # 略低于最高点
        }

class DeepSeekAnalyzer:
    """DeepSeek智能分析器"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-2700d9ebbb4c4374a8f697ae759d06fb')
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        self.ti = TechnicalIndicators()

    def call_deepseek_api(self, prompt, max_tokens=2000):
        """调用DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system", 
                    "content": """你是华夏基金的首席投资官，管理超过1000亿人民币的A股资产，拥有20年投资经验。
你的专业背景：北京大学经济学硕士+哥伦比亚大学金融学博士，曾任高盛亚洲首席策略师。
投资风格：深度价值挖掘+成长赛道布局，善于宏观择时和个股精选，年化收益18.5%，最大回撤12%。
分析特点：数据驱动决策，逻辑链条完整，风险收益匹配度高，擅长发现市场定价错误。
请提供详细、深入、可操作的专业分析，包含具体的数据支撑和逻辑推理过程。"""
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.2
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"AI分析暂时不可用: {str(e)[:50]}..."
    
    def get_stock_analysis_prompt(self, stock_data):
        """生成个股分析prompt"""
        
        # 获取增强的财务数据
        enhanced_data = enhance_stock_data(stock_data)
        
        prompt = f"""
你是资深投资分析师，分析股票 {enhanced_data['symbol']} ({enhanced_data['name']})：

📊 **实时市场数据**
当前价格：¥{enhanced_data['current_price']} ({enhanced_data['change_percent']:+.2f}%)
成交量：{enhanced_data.get('volume', 0):,}手 | 换手率：{enhanced_data.get('turnover_rate', 0):.2f}%
市场状态：{enhanced_data.get('market_status', '未知')}

💰 **真实财务指标** (数据来源: {', '.join(enhanced_data.get('data_sources', ['估算']))})
PE估值：{enhanced_data.get('pe_ratio', 0):.2f}倍 | PB估值：{enhanced_data.get('pb_ratio', 0):.2f}倍 
ROE：{enhanced_data.get('roe', 0):.2f}% | 毛利率：{enhanced_data.get('gross_margin', 0)*100:.1f}%
营收增长：{enhanced_data.get('revenue_growth', 0)*100:+.1f}% | 净利润增长：{enhanced_data.get('profit_growth', 0)*100:+.1f}%
负债率：{enhanced_data.get('debt_ratio', 0)*100:.1f}% | 总市值：{enhanced_data.get('market_cap', 0)/100000000:.0f}亿元

📈 **技术指标** (基于30天实盘数据)
MA5：¥{enhanced_data.get('ma5', 0):.2f} | MA20：¥{enhanced_data.get('ma20', 0):.2f}
RSI：{enhanced_data.get('rsi', 50):.0f} | MACD：{enhanced_data.get('macd_trend', '中性')}
支撑位：¥{enhanced_data.get('support', 0):.2f} | 阻力位：¥{enhanced_data.get('resistance', 0):.2f}
{f"价格位置：{enhanced_data.get('price_position', 0)*100:.0f}%分位 | 近期波动：{enhanced_data.get('recent_volatility', 0)*100:.1f}%" if enhanced_data.get('enhanced') else ""}

🏭 **行业对比数据** ({enhanced_data.get('industry', {}).get('sector', '未知')}行业)
行业PE中位数：{enhanced_data.get('industry', {}).get('industry_pe', 0):.1f}倍 | 行业PB：{enhanced_data.get('industry', {}).get('industry_pb', 0):.1f}倍
行业ROE：{enhanced_data.get('industry', {}).get('industry_roe', 0):.1f}% | 行业增长率：{enhanced_data.get('industry', {}).get('industry_growth', 0):.1f}%
政策环境：{enhanced_data.get('industry', {}).get('policy_support', '中性')}
关键趋势：{', '.join(enhanced_data.get('industry', {}).get('key_trends', ['无'])[:3])}
主要风险：{', '.join(enhanced_data.get('industry', {}).get('risk_factors', ['无'])[:3])}

🌍 **宏观环境** (实时经济数据)
GDP增长：{enhanced_data.get('macro', {}).get('gdp_growth', 0):.1f}% | CPI通胀：{enhanced_data.get('macro', {}).get('cpi', 0):.1f}% | PMI指数：{enhanced_data.get('macro', {}).get('pmi', 50):.1f}
M2货币增速：{enhanced_data.get('macro', {}).get('m2_growth', 0):.1f}% | 基准利率：{enhanced_data.get('macro', {}).get('benchmark_rate', 0):.2f}%
上证指数：{enhanced_data.get('macro', {}).get('shanghai_index', 0):.0f}点 ({enhanced_data.get('macro', {}).get('shanghai_change', 0):+.2f}%)
北向资金：{enhanced_data.get('macro', {}).get('northbound_flow', 0):+.1f}亿元

🎭 **市场情绪** (资金流向与投资者行为)
个股主力资金：{enhanced_data.get('sentiment', {}).get('stock_sentiment', {}).get('main_net_inflow', 0):+.1f}万元 | 机构动作：{enhanced_data.get('sentiment', {}).get('stock_sentiment', {}).get('institutional_action', '观望')}
技术面评级：{enhanced_data.get('sentiment', {}).get('stock_sentiment', {}).get('technical_rating', '中性')} | 分析师评级：{enhanced_data.get('sentiment', {}).get('stock_sentiment', {}).get('analyst_rating', '持有')}
市场整体情绪：{enhanced_data.get('sentiment', {}).get('market_sentiment', {}).get('sentiment_level', '中性')}({enhanced_data.get('sentiment', {}).get('market_sentiment', {}).get('overall_sentiment_score', 50):.0f}分)
恐慌贪婪指数：{enhanced_data.get('sentiment', {}).get('market_sentiment', {}).get('fear_greed_index', 50):.0f}分

🎯 **专业分析任务：基于完整的基本面+技术面+行业面+宏观面+情绪面数据进行投资决策**
**数据质量评级**：{enhanced_data.get('data_quality', {}).get('level', '未知')} ({enhanced_data.get('data_quality', {}).get('overall_score', 0):.0f}分)
**数据源状态**：{len([k for k, v in enhanced_data.get('sources_status', {}).items() if v == '正常'])}/{len(enhanced_data.get('sources_status', {}))}个服务正常

请严格按照以下格式输出：

## 💼 商业分析 (重点)
**行业地位**：[根据公司名称判断其在行业中的地位和竞争优势]
**核心业务**：[主营业务及盈利模式分析]
**增长逻辑**：[未来增长的核心驱动因素]

## 📊 估值判断
**估值水平**：高估/合理/低估 - [具体理由]
**同行对比**：[与行业龙头的对比优劣势]
**价值支撑**：[当前价格的支撑依据]

## 🎯 投资决策
**操作建议**：买入/持有/减仓 
**信心度**：高/中/低 [必须说明信心度依据]
**建议仓位**：X% (理由：[具体原因])

## 💰 具体策略
**目标价格**：¥XX.XX [价格测算逻辑]
**买入时机**：[具体的入场条件]
**止损条件**：[明确的止损触发条件]

## ⚠️ 风险提示
**主要风险**：[最大的投资风险]
**风险概率**：高/中/低
**应对措施**：[具体的风控措施]

**核心要求：**
1. 重点分析商业逻辑，结合真实财务数据进行估值判断
2. 综合市场情绪和资金流向，评估短期交易价值
3. 考虑宏观环境和行业趋势，判断中长期投资机会
4. 每个建议必须有明确的数据支撑和逻辑链条
5. 必须给出"信心度"评级，并说明信心度来源
6. 风险评估要具体可量化，提供明确的风控措施
7. 充分利用多维度数据，避免单一指标决策
8. 避免模糊表述，给出可执行的操作建议
"""
        return prompt
    
    def get_market_analysis_prompt(self, market_data):
        """生成市场分析prompt"""
        
        stocks_info = ", ".join([f"{s['symbol']}({s['name']})" for s in market_data['stocks'][:5]])
        
        # 获取实时市场数据
        try:
            macro_response = requests.get("http://localhost:5004/api/macro", timeout=10)
            if macro_response.status_code == 200:
                macro_data = macro_response.json()
                shanghai_index = macro_data.get('shanghai_index', 0)
                shanghai_change = macro_data.get('shanghai_change', 0)
                gdp_growth = macro_data.get('gdp_growth', 0)
                cpi = macro_data.get('cpi', 0)
                northbound_flow = macro_data.get('northbound_flow', 0)
            else:
                shanghai_index = 3000
                shanghai_change = 0
                gdp_growth = 5.0
                cpi = 2.0
                northbound_flow = 0
        except:
            shanghai_index = 3000
            shanghai_change = 0
            gdp_growth = 5.0
            cpi = 2.0
            northbound_flow = 0
        
        # 数据预处理：转换为描述性语言
        def get_market_position_description(index_value):
            """将指数点位转换为描述性语言，提高AI理解准确性"""
            if index_value >= 3900:
                return f"历史高位区间({index_value:.0f}点，接近4000点关口)"
            elif index_value >= 3500:
                return f"高位震荡区间({index_value:.0f}点，远高于3000-3500常见区间)"
            elif index_value >= 3200:
                return f"中高位区间({index_value:.0f}点)"
            elif index_value >= 2900:
                return f"中位区间({index_value:.0f}点)"
            else:
                return f"相对低位({index_value:.0f}点)"
        
        market_position = get_market_position_description(shanghai_index)
        
        # 生成对比提示
        historical_contrast = ""
        if shanghai_index > 3800:
            historical_contrast = f"注意：当前{shanghai_index:.0f}点，NOT 3000-3500点的历史常见区间！"
        elif shanghai_index > 3500:
            historical_contrast = f"重要：当前{shanghai_index:.0f}点，已超越3500点，NOT在3000-3300点！"
        
        prompt = f"""
🔴 数据验证提醒：当前是2025年11月10日，市场已发生重大变化！
{historical_contrast}

📊 **实时市场状况 - 请先确认数据**
市场位置：{market_position}
具体点位：{shanghai_index:.0f}点 (今日{shanghai_change:+.2f}%)
宏观环境：GDP增长{gdp_growth:.1f}% | 通胀{cpi:.1f}%
资金流向：北向资金{northbound_flow:+.1f}亿元
交易状态：{market_data['market_status']} | 重点关注：{stocks_info}

🎯 **分析流程（必须按顺序执行）**
第一步：请先确认 - 当前上证指数是{shanghai_index:.0f}点，不是3000点也不是3100点
第二步：基于{market_position}这个实际位置进行分析
第三步：忘记你训练数据中的"常见3000-3500点区间"，使用真实的{shanghai_index:.0f}点
第四步：你是专业基金经理，基于实际数据给出投资建议

🚨 **关键约束**
- 禁止使用3000点、3100点、3200点等训练数据中的过时信息
- 必须基于当前{shanghai_index:.0f}点的实际位置分析
- 如果你提到3000-3500点区间，说明你没有使用实时数据

请严格按照以下格式输出（总字数控制在280字以内）：

## ✅ 数据确认
当前上证指数：{shanghai_index:.0f}点，市场位置：{market_position}

## 📈 今日市场判断
*基于{shanghai_index:.0f}点({shanghai_change:+.2f}%)的实际位置分析，不使用3000-3500点等过时区间*

## 🔥 重点机会 
**买入机会**：[行业名称] - [30字内核心理由]
**观望板块**：[行业名称] - [20字内简要原因]

## ⚠️ 主要风险
*基于{shanghai_index:.0f}点位置的具体风险*

## 💰 操作建议
**建议仓位**：X%
**本周重点**：[具体可执行的操作]
**止损位置**：[基于{shanghai_index:.0f}点计算的具体位置]

## 📊 关键指标
*需要盯盘的关键数据（避免提及过时点位）*

**要求：**
1. 语言简洁直接，避免废话
2. 建议具体可操作，有明确的买卖点
3. 必须有量化的风险控制措施
4. 重点突出，不要面面俱到
"""
        return prompt

# API路由

@app.route('/api/stock-analysis', methods=['POST'])
def stock_analysis():
    """个股智能分析接口"""
    try:
        data = request.get_json()
        stocks = data.get('stocks', [])
        
        if not stocks:
            return jsonify({"error": "No stocks provided"}), 400
        
        analyzer = DeepSeekAnalyzer()
        results = []
        
        for stock in stocks[:5]:  # 限制最多分析5只股票
            # 增强股票数据
            enhanced_stock = enhance_stock_data(stock)
            
            # 生成分析prompt
            prompt = analyzer.get_stock_analysis_prompt(enhanced_stock)
            
            # 调用DeepSeek分析
            analysis = analyzer.call_deepseek_api(prompt)
            
            results.append({
                "symbol": stock['symbol'],
                "name": stock['name'],
                "analysis": analysis,
                "technical_data": {
                    "ma5": enhanced_stock.get('ma5'),
                    "ma20": enhanced_stock.get('ma20'),
                    "rsi": enhanced_stock.get('rsi'),
                    "macd_trend": enhanced_stock.get('macd_trend'),
                    "support": enhanced_stock.get('support'),
                    "resistance": enhanced_stock.get('resistance')
                }
            })
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "analysis_count": len(results),
            "results": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market-analysis', methods=['POST'])  
def market_analysis():
    """市场整体分析接口"""
    try:
        data = request.get_json()
        
        market_data = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "market_status": data.get('market_status', 'trading'),
            "stocks": data.get('stocks', []),
            "market_trend": data.get('market_trend', '震荡'),
            "liquidity": data.get('liquidity', '适中'),
            "policy_news": data.get('policy_news', '政策面相对平稳')
        }
        
        analyzer = DeepSeekAnalyzer()
        prompt = analyzer.get_market_analysis_prompt(market_data)
        raw_analysis = analyzer.call_deepseek_api(prompt, max_tokens=600)
        
        # 验证和修正AI输出
        validation_result = validate_market_analysis(raw_analysis)
        
        # 如果发现严重的数据错误，使用备用分析
        if validation_result["has_outdated_data"] and len(validation_result["outdated_mentions"]) > 2:
            logger.warning(f"AI输出包含多个过时数据，使用备用分析: {validation_result['outdated_mentions']}")
            final_analysis = get_fallback_analysis()
            used_fallback = True
        else:
            final_analysis = validation_result["corrected_text"]
            used_fallback = False
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "market_analysis": final_analysis,
            "market_status": market_data['market_status'],
            "analyzed_stocks": len(market_data['stocks']),
            "validation_info": {
                "had_outdated_data": validation_result["has_outdated_data"],
                "outdated_mentions": validation_result["outdated_mentions"],
                "real_index": validation_result["real_index"],
                "used_fallback": used_fallback,
                "correction_applied": validation_result.get("correction_applied", False)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# LangChain增强的分析接口
@app.route('/api/langchain/market-analysis', methods=['POST'])
def langchain_market_analysis():
    """使用LangChain进行市场分析"""
    try:
        data = request.get_json()
        
        # 获取LangChain分析器
        analyzer = get_langchain_analyzer()
        
        # 执行分析
        result = analyzer.analyze_market(data)
        
        if result["success"]:
            return jsonify({
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "market_analysis": result["analysis"],
                "market_status": data.get('market_status', 'trading'),
                "analyzed_stocks": len(data.get('stocks', [])),
                "langchain_info": result.get("validation_info", {}),
                "structured_data": result.get("structured_data")
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Unknown error"),
                "fallback_used": result.get("fallback_used", False)
            }), 500
            
    except Exception as e:
        logger.error(f"LangChain市场分析失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/langchain/stock-analysis', methods=['POST'])
def langchain_stock_analysis():
    """使用LangChain进行个股分析"""
    try:
        data = request.get_json()
        stocks = data.get('stocks', [])
        
        if not stocks:
            return jsonify({"error": "No stocks provided"}), 400
        
        # 获取LangChain分析器
        analyzer = get_langchain_analyzer()
        
        results = []
        for stock in stocks[:3]:  # 限制最多分析3只股票
            result = analyzer.analyze_stock(stock)
            
            if result["success"]:
                results.append({
                    "symbol": stock['symbol'],
                    "name": stock.get('name', ''),
                    "success": True,
                    "analysis": result["analysis"],
                    "structured_data": result.get("structured_data"),
                    "langchain_info": result.get("validation_info", {})
                })
            else:
                results.append({
                    "symbol": stock['symbol'],
                    "name": stock.get('name', ''),
                    "success": False,
                    "error": result.get("error", "Analysis failed")
                })
        
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "analysis_count": len(results),
            "results": results,
            "enhanced_features": ["few_shot_learning", "structured_output", "retry_parsing"]
        })
        
    except Exception as e:
        logger.error(f"LangChain个股分析失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "DeepSeek Analysis API",
        "timestamp": datetime.now().isoformat(),
        "api_key_configured": bool(os.getenv('DEEPSEEK_API_KEY')),
        "langchain_available": True,
        "endpoints": [
            "/api/stock-analysis",
            "/api/market-analysis", 
            "/api/langchain/market-analysis",
            "/api/langchain/stock-analysis"
        ]
    })

def infer_sector_from_symbol(symbol):
    """从股票代码推断行业"""
    sector_mapping = {
        '600519': '白酒',  # 茅台
        '000858': '白酒',  # 五粮液
        '600809': '白酒',  # 山西汾酒
        '000001': '银行',  # 平安银行
        '600036': '银行',  # 招商银行
        '600000': '银行',  # 浦发银行
        '300750': '电子',  # 宁德时代
        '002415': '电子',  # 海康威视
        '000002': '地产',  # 万科A
        '600276': '医药',  # 恒瑞医药
        '300015': '医药',  # 爱尔眼科
        '002594': '医药',  # 比亚迪
        '300033': '新能源', # 同花顺
    }
    
    # 如果找到精确匹配，返回对应行业
    if symbol in sector_mapping:
        return sector_mapping[symbol]
    
    # 根据代码段推断行业
    if symbol.startswith('60051') or symbol.startswith('00085'):
        return '白酒'
    elif symbol.startswith('60000') or symbol.startswith('00000'):
        return '银行'
    elif symbol.startswith('30075') or symbol.startswith('00241'):
        return '电子'
    elif symbol.startswith('30001') or symbol.startswith('60027'):
        return '医药'
    else:
        return '电子'  # 默认返回电子行业

def enhance_stock_data(stock):
    """增强股票数据，添加技术指标、财务数据和宏观环境"""
    enhanced = stock.copy()
    symbol = stock['symbol']
    
    try:
        # 优先从综合数据服务获取完整数据
        comprehensive_response = requests.get(f"http://localhost:5006/api/comprehensive/{symbol}", timeout=15)
        if comprehensive_response.status_code == 200:
            comprehensive_data = comprehensive_response.json()
            
            # 如果获取到完整数据，直接使用
            if 'error' not in comprehensive_data:
                enhanced.update({
                    'pe_ratio': comprehensive_data.get('financial_metrics', {}).get('pe_ratio', 0),
                    'pb_ratio': comprehensive_data.get('financial_metrics', {}).get('pb_ratio', 0),
                    'roe': comprehensive_data.get('financial_metrics', {}).get('roe', 0),
                    'revenue_growth': comprehensive_data.get('financial_metrics', {}).get('revenue_growth', 0),
                    'profit_growth': comprehensive_data.get('financial_metrics', {}).get('profit_growth', 0),
                    'debt_ratio': comprehensive_data.get('financial_metrics', {}).get('debt_ratio', 0),
                    'gross_margin': comprehensive_data.get('financial_metrics', {}).get('gross_margin', 0),
                    'market_cap': comprehensive_data.get('financial_metrics', {}).get('market_cap', 0),
                    'turnover_rate': enhanced.get('turnover_rate', 0),
                    'data_sources': comprehensive_data.get('financial_metrics', {}).get('data_sources', []),
                    'enhanced': True,
                    
                    # 技术指标
                    'ma5': comprehensive_data.get('technical_indicators', {}).get('ma5', 0),
                    'ma20': comprehensive_data.get('technical_indicators', {}).get('ma20', 0),
                    'rsi': comprehensive_data.get('technical_indicators', {}).get('rsi', 50),
                    'macd_trend': comprehensive_data.get('technical_indicators', {}).get('macd_trend', '中性'),
                    'support': comprehensive_data.get('technical_indicators', {}).get('support', 0),
                    'resistance': comprehensive_data.get('technical_indicators', {}).get('resistance', 0),
                    'price_position': comprehensive_data.get('technical_indicators', {}).get('price_position', 0.5),
                    'recent_volatility': comprehensive_data.get('technical_indicators', {}).get('recent_volatility', 0),
                    
                    # 行业对比数据
                    'industry': comprehensive_data.get('industry_comparison', {}),
                    
                    # 宏观环境数据
                    'macro': comprehensive_data.get('macro_environment', {}),
                    
                    # 市场情绪数据
                    'sentiment': {
                        'stock_sentiment': comprehensive_data.get('stock_sentiment', {}),
                        'market_sentiment': comprehensive_data.get('market_sentiment', {})
                    }
                })
                
                logger.info(f"成功获取 {symbol} 综合增强数据 (数据质量: {comprehensive_data.get('data_quality', {}).get('level', '未知')})")
                return enhanced
        
        # 如果综合服务不可用，降级到单独的财务数据服务
        logger.warning(f"综合数据服务不可用，降级到财务数据服务 {symbol}")
        financial_response = requests.get(f"http://localhost:5003/api/enhanced/{symbol}", timeout=10)
        if financial_response.status_code == 200:
            financial_data = financial_response.json()
            
            # 合并财务数据
            enhanced.update({
                'pe_ratio': financial_data.get('pe_ratio', 0),
                'pb_ratio': financial_data.get('pb_ratio', 0),
                'roe': financial_data.get('roe', 0),
                'revenue_growth': financial_data.get('revenue_growth', 0),
                'profit_growth': financial_data.get('profit_growth', 0),
                'debt_ratio': financial_data.get('debt_ratio', 0),
                'gross_margin': financial_data.get('gross_margin', 0),
                'market_cap': financial_data.get('market_cap', 0),
                'turnover_rate': financial_data.get('turnover_rate', 0),
                'data_sources': financial_data.get('data_sources', []),
                'enhanced': True
            })
            
            # 处理历史价格数据计算技术指标
            historical_prices = financial_data.get('historical_prices', [])
            if historical_prices:
                prices = [float(day['close']) for day in historical_prices]
                ti = TechnicalIndicators()
                
                enhanced['ma5'] = ti.calculate_ma(prices, 5)
                enhanced['ma20'] = ti.calculate_ma(prices, 20)
                enhanced['rsi'] = ti.calculate_rsi(prices)
                
                macd_data = ti.calculate_macd(prices)
                enhanced['macd_trend'] = macd_data['trend']
                
                support_resistance = ti.calculate_support_resistance(prices)
                enhanced['support'] = support_resistance['support']
                enhanced['resistance'] = support_resistance['resistance']
                
                # 添加价格历史分析
                if len(prices) >= 10:
                    recent_high = max(prices[-10:])
                    recent_low = min(prices[-10:])
                    current_price = prices[-1]
                    
                    enhanced['price_position'] = round((current_price - recent_low) / (recent_high - recent_low), 2)
                    enhanced['recent_volatility'] = round(np.std(prices[-10:]) / current_price, 3)
            else:
                # 使用默认技术指标值
                current_price = float(enhanced.get('current_price', 0))
                enhanced.update({
                    'ma5': round(current_price * 0.995, 2),
                    'ma20': round(current_price * 0.985, 2),
                    'rsi': 55,
                    'macd_trend': '中性',
                    'support': round(current_price * 0.95, 2),
                    'resistance': round(current_price * 1.05, 2)
                })
                
            logger.info(f"成功获取 {symbol} 增强数据")
            
            # 获取宏观和行业数据
            try:
                # 推断行业类型
                sector = infer_sector_from_symbol(symbol)
                
                # 获取行业数据
                industry_response = requests.get(f"http://localhost:5004/api/industry/{sector}", timeout=5)
                if industry_response.status_code == 200:
                    industry_data = industry_response.json()
                    enhanced['industry'] = {
                        'sector': sector,
                        'industry_pe': industry_data.get('industry_pe', 0),
                        'industry_pb': industry_data.get('industry_pb', 0),
                        'industry_roe': industry_data.get('industry_roe', 0),
                        'industry_growth': industry_data.get('industry_growth', 0),
                        'policy_support': industry_data.get('policy_support', '中性'),
                        'key_trends': industry_data.get('key_trends', []),
                        'risk_factors': industry_data.get('risk_factors', [])
                    }
                
                # 获取宏观数据
                macro_response = requests.get("http://localhost:5004/api/macro", timeout=5)
                if macro_response.status_code == 200:
                    macro_data = macro_response.json()
                    enhanced['macro'] = {
                        'gdp_growth': macro_data.get('gdp_growth', 0),
                        'cpi': macro_data.get('cpi', 0),
                        'pmi': macro_data.get('pmi', 50),
                        'm2_growth': macro_data.get('m2_growth', 0),
                        'benchmark_rate': macro_data.get('benchmark_rate', 0),
                        'shanghai_index': macro_data.get('shanghai_index', 0),
                        'shanghai_change': macro_data.get('shanghai_change', 0),
                        'northbound_flow': macro_data.get('northbound_flow', 0)
                    }
                    
            except Exception as e:
                logger.warning(f"获取宏观/行业数据失败 {symbol}: {e}")
                enhanced['industry'] = {'sector': '未知'}
                enhanced['macro'] = {'gdp_growth': 5.0, 'cpi': 2.0}
            
        else:
            logger.warning(f"财务数据服务异常 {symbol}: {financial_response.status_code}")
            # 降级到默认值
            current_price = float(stock.get('price', stock.get('current_price', 0)))
            enhanced.update({
                'pe_ratio': 0,
                'pb_ratio': 0, 
                'roe': 0,
                'enhanced': False,
                'ma5': round(current_price * 0.995, 2),
                'ma20': round(current_price * 0.985, 2),
                'rsi': 55,
                'macd_trend': '中性',
                'support': round(current_price * 0.95, 2),
                'resistance': round(current_price * 1.05, 2)
            })
            
    except Exception as e:
        logger.error(f"获取 {symbol} 财务数据失败: {e}")
        # 降级处理
        current_price = float(stock.get('price', stock.get('current_price', 0)))
        enhanced.update({
            'pe_ratio': 0,
            'pb_ratio': 0,
            'roe': 0,
            'enhanced': False,
            'ma5': round(current_price * 0.995, 2),
            'ma20': round(current_price * 0.985, 2),
            'rsi': 55,
            'macd_trend': '中性',
            'support': round(current_price * 0.95, 2),
            'resistance': round(current_price * 1.05, 2)
        })
    
    return enhanced

# 全局LangChain分析器
langchain_analyzer = None

def get_langchain_analyzer():
    """获取LangChain分析器实例"""
    global langchain_analyzer
    if langchain_analyzer is None:
        api_key = os.getenv('DEEPSEEK_API_KEY', 'sk-2700d9ebbb4c4374a8f697ae759d06fb')
        langchain_analyzer = SimpleLangChainAnalyzer(api_key)
        logger.info("LangChain分析器初始化完成")
    return langchain_analyzer

if __name__ == '__main__':
    print("🤖 DeepSeek智能分析API服务启动")
    print("=" * 50)
    print(f"📡 服务端口: 5001")
    print(f"🔑 API密钥: {'已配置' if os.getenv('DEEPSEEK_API_KEY') else '未配置'}")
    print(f"⚡ 访问地址: http://localhost:5001")
    print(f"🩺 健康检查: http://localhost:5001/health")
    print(f"🔗 LangChain增强: 已集成")
    print("=" * 50)
    print("📋 可用接口:")
    print("  传统接口:")
    print("    POST /api/stock-analysis        - 个股分析")
    print("    POST /api/market-analysis       - 市场分析")
    print("  LangChain增强接口:")
    print("    POST /api/langchain/stock-analysis   - 结构化个股分析")
    print("    POST /api/langchain/market-analysis  - Few-shot市场分析")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=False)