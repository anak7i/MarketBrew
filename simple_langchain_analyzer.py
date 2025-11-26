#!/usr/bin/env python3
"""
简化版LangChain DeepSeek分析器
专注于Few-shot learning和prompt管理，避免复杂的结构化解析
"""

import os
import requests
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.llms.base import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepSeekLLM(LLM):
    """自定义DeepSeek LLM包装器"""
    
    api_key: str
    api_url: str = "https://api.deepseek.com/v1/chat/completions"
    max_tokens: int = 2000
    temperature: float = 0.2
    
    @property
    def _llm_type(self) -> str:
        return "deepseek"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
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
请严格按照示例格式输出，确保使用实时数据而非训练数据中的过时信息。"""
                },
                {"role": "user", "content": prompt}
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"DeepSeek API调用失败: {e}")
            raise e

class SimpleLangChainAnalyzer:
    """简化版LangChain分析器"""
    
    def __init__(self, api_key: str):
        self.llm = DeepSeekLLM(api_key=api_key)
        self._setup_prompts()
    
    def _setup_prompts(self):
        """设置Few-shot prompt模板"""
        
        # 市场分析的Few-shot示例
        self.market_examples = [
            {
                "real_index": "3997",
                "market_position": "历史高位区间(3997点，接近4000点关口)",
                "analysis": """## ✅ 数据确认
当前上证指数：3997点，市场位置：历史高位区间(3997点，接近4000点关口)

## 📈 今日市场判断
大盘位于历史高位区间，接近4000点整数关口，短期面临高位震荡风险

## 🔥 重点机会 
**买入机会**：白酒 - 估值回归合理区间，中秋旺季备货启动
**观望板块**：高估值成长股 - 在3997点高位需谨慎

## ⚠️ 主要风险
指数在3997点附近，接近历史高位，回调风险较大

## 💰 操作建议
**建议仓位**：60%
**本周重点**：谨慎操作，等待3797点以下机会
**止损位置**：3847点或个股-8%

## 📊 关键指标
北向资金流向、3997点支撑强度、成交量配合情况"""
            },
            {
                "real_index": "3200",
                "market_position": "中高位区间(3200点)",
                "analysis": """## ✅ 数据确认
当前上证指数：3200点，市场位置：中高位区间(3200点)

## 📈 今日市场判断
大盘处于中高位区间，技术面相对健康，短期以震荡为主

## 🔥 重点机会 
**买入机会**：科技股 - 估值合理，政策支持明确
**观望板块**：周期股 - 需求疲软，盈利承压

## ⚠️ 主要风险
宏观经济数据波动可能影响市场预期

## 💰 操作建议
**建议仓位**：70%
**本周重点**：逢低布局优质成长股
**止损位置**：3150点或个股-6%

## 📊 关键指标
成交量放大、外资流入、政策导向"""
            }
        ]
        
        # 市场分析Few-shot模板
        example_prompt = PromptTemplate(
            input_variables=["real_index", "market_position", "analysis"],
            template="实时指数：{real_index}点\n市场位置：{market_position}\n正确分析：{analysis}"
        )
        
        self.market_few_shot_prompt = FewShotPromptTemplate(
            examples=self.market_examples,
            example_prompt=example_prompt,
            prefix="""你是专业基金经理，必须基于提供的实时数据进行分析。

🔴 关键约束：
1. 必须使用提供的实时指数点位，不要使用训练数据中的过时信息
2. 分析必须基于实际市场位置，不要提及3000-3500点等过时区间
3. 输出必须严格按照示例格式

以下是正确分析的示例：""",
            suffix="""现在分析以下实时数据：

🔴 数据验证提醒：当前是2025年11月10日，市场已发生重大变化！
{historical_contrast}

📊 **实时市场状况**
市场位置：{market_position}
具体点位：{real_index}点 (今日{index_change:+.2f}%)
宏观环境：GDP增长{gdp_growth:.1f}% | 通胀{cpi:.1f}%
资金流向：北向资金{northbound_flow:+.1f}亿元
交易状态：{market_status} | 重点关注：{stocks_info}

🎯 **分析要求**
1. 必须基于上证指数{real_index}点这个真实数据进行分析
2. 基于{market_position}这个实际位置进行分析
3. 严格按照示例格式输出
4. 不要提及3000-3500点等过时信息

请严格按照以上示例格式输出分析：""",
            input_variables=[
                "historical_contrast", "market_position", "real_index", "index_change",
                "gdp_growth", "cpi", "northbound_flow", "market_status", "stocks_info"
            ]
        )
        
        # 个股分析模板  
        self.stock_prompt = PromptTemplate(
            input_variables=[
                "symbol", "name", "current_price", "change_percent", "financial_data",
                "technical_data", "industry_data", "macro_data", "sentiment_data"
            ],
            template="""🔥 专业基金经理深度分析任务 🔥

分析标的：{symbol} ({name}) | 当前价格：¥{current_price} ({change_percent:+.2f}%)

📊 **可用数据**
财务数据：{financial_data}
技术指标：{technical_data}
行业对比：{industry_data}
宏观环境：{macro_data}
市场情绪：{sentiment_data}

🎯 **分析要求：你必须展现专业基金经理的分析深度**

⚠️ 绝对禁止输出：
- "走势平稳，维持观望" - 这种废话分析
- 没有数据支撑的空洞建议
- 模糊的"可能"、"或许"等表述
- 缺乏具体价格和仓位的建议

✅ 必须做到：
1. **深度商业分析**：具体说明盈利模式、竞争优势、行业地位
2. **精确估值测算**：基于PE/PB/DCF等方法给出目标价
3. **明确投资决策**：买入/持有/减仓，必须有明确理由
4. **具体操作建议**：入场时机、仓位配置、止损价位
5. **量化风险评估**：具体风险点和概率评估

## 💼 深度商业分析
**行业地位**：在XX行业排名X位，市占率X%，核心竞争优势是X
**盈利模式**：主营收入来源X(占比X%)，毛利率X%，净利率X%
**成长逻辑**：具体增长驱动因素，预期X年增长X%，因为X原因
**护城河**：技术壁垒/品牌优势/规模效应等具体分析

## 📊 精确估值测算  
**估值方法**：PE法/PB法/DCF法，当前PE X倍 vs 行业平均X倍
**合理估值区间**：¥X.XX - ¥X.XX (基于X倍PE/X倍PB)
**价值催化剂**：具体什么事件会推动股价上涨
**估值风险**：当前价格是否存在泡沫风险

## 🎯 明确投资决策
**核心判断**：买入/持有/减仓 - 必须有明确逻辑链条
**信心度**：高/中/低 - 基于X个确定性因素
**建议仓位**：X% - 考虑风险收益比和组合配置
**投资期限**：短期X个月/长期X年持有

## 💰 具体操作策略
**目标价格**：主目标¥X.XX，乐观¥X.XX，悲观¥X.XX
**入场策略**：分X次买入，X元以下买入，总仓位不超过X%
**止损策略**：跌破¥X.XX立即止损，或下跌X%强制止损
**盈利目标**：涨到¥X.XX减仓X%，涨幅达X%分批止盈

## ⚠️ 风险量化评估
**核心风险**：具体风险事件，发生概率X%，影响程度X%
**行业风险**：政策风险/竞争风险/周期风险的具体分析
**个股风险**：业绩不达预期/管理层变动/黑天鹅事件
**应对预案**：一旦出现X风险，立即执行X操作

🔍 **输出标准：每个建议必须有数据支撑和逻辑链条，禁止模糊表述**

基于上述数据，提供专业、深度、可操作的投资分析："""
        )
        
        # ETF专门分析模板
        self.etf_prompt = PromptTemplate(
            input_variables=[
                "symbol", "name", "current_price", "change_percent", "financial_data",
                "technical_data", "industry_data", "macro_data", "sentiment_data"
            ],
            template="""🔥 专业ETF投资分析 🔥

分析标的：{symbol} ({name}) | 当前价格：¥{current_price} ({change_percent:+.2f}%)

📊 **ETF基础信息**
技术指标：{technical_data}
跟踪指数：{industry_data}
宏观环境：{macro_data}
市场情绪：{sentiment_data}

🎯 **ETF专业分析要求**

⚠️ 绝对禁止：
- "走势平稳，维持观望" 这种无用废话
- 没有具体操作建议的空洞分析
- 不提供进出场价位的模糊建议

✅ ETF分析必须包含：
1. **指数分析**：跟踪指数的行业配置和估值水平
2. **配置价值**：在投资组合中的配置作用和意义
3. **择时策略**：基于技术面和估值的进出场时机
4. **仓位管理**：具体的仓位配置建议

## 📈 指数深度分析
**跟踪标的**：中证500指数，成分股特征和行业分布
**估值水平**：当前PE X倍，处于历史X%分位，估值偏高/合理/偏低
**行业权重**：前三大行业占比，受益于哪些主题和政策
**相对表现**：vs 沪深300/中证1000的相对强弱分析

## 🎯 配置价值评估
**投资属性**：成长/价值/平衡型，风险收益特征
**组合作用**：核心配置/卫星策略/行业轮动工具
**适合投资者**：风险偏好和投资期限匹配度
**与其他资产相关性**：在组合中的分散化价值

## 💰 择时交易策略
**技术面分析**：当前位置相对高低点，关键支撑阻力位
**估值择时**：基于PE band的买入卖出区间
**趋势判断**：短中长期趋势方向和延续性
**交易信号**：具体的买入卖出触发条件

## 🎯 投资决策建议
**核心判断**：买入/持有/减仓/观望 - 基于估值+技术+流动性
**建议仓位**：X% - 在股票资产中的配置比例
**投资期限**：短线X周/中线X个月/长线X年
**风险评级**：高/中/低风险，适合的资金性质

## 🔧 具体操作方案
**目标价位**：买入区间¥X.XX-¥X.XX，卖出区间¥X.XX-¥X.XX
**分批策略**：分X次建仓/减仓，每次X%仓位
**止损止盈**：止损¥X.XX(下跌X%)，止盈¥X.XX(上涨X%)
**调仓条件**：什么情况下加仓/减仓/换仓

## ⚠️ 风险提示
**系统性风险**：市场整体下跌对ETF的影响
**特有风险**：跟踪误差/流动性风险/折溢价风险
**政策风险**：相关行业政策变化的影响
**操作建议**：风险来临时的应对措施

🔍 **每个建议都要有明确的数据支撑和价格区间，拒绝模糊分析**

请提供专业、具体、可操作的ETF投资分析："""
        )
    
    def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """市场分析"""
        try:
            # 获取实时市场数据
            macro_data = self._get_real_market_data()
            
            # 准备prompt变量
            prompt_vars = {
                "historical_contrast": self._get_historical_contrast(macro_data["shanghai_index"]),
                "market_position": self._get_market_position_description(macro_data["shanghai_index"]),
                "real_index": macro_data["shanghai_index"],
                "index_change": macro_data["shanghai_change"],
                "gdp_growth": macro_data["gdp_growth"],
                "cpi": macro_data["cpi"],
                "northbound_flow": macro_data["northbound_flow"],
                "market_status": market_data.get("market_status", "trading"),
                "stocks_info": ", ".join([f"{s['symbol']}({s['name']})" for s in market_data.get('stocks', [])[:3]])
            }
            
            # 生成prompt
            prompt = self.market_few_shot_prompt.format(**prompt_vars)
            logger.info("生成市场分析prompt完成")
            
            # 调用LLM
            output = self.llm(prompt)
            logger.info(f"LLM输出完成，长度: {len(output)} 字符")
            
            return {
                "success": True,
                "analysis": output,
                "validation_info": {
                    "used_langchain": True,
                    "few_shot_learning": True,
                    "real_index": macro_data["shanghai_index"],
                    "prompt_length": len(prompt),
                    "output_length": len(output)
                }
            }
                
        except Exception as e:
            logger.error(f"LangChain市场分析失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_used": True
            }
    
    def analyze_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """个股/ETF智能分析"""
        try:
            # 获取增强的股票数据
            enhanced_data = self._get_enhanced_stock_data(stock_data)
            
            # 判断是否为ETF
            symbol = enhanced_data.get("symbol", "")
            name = enhanced_data.get("name", "")
            is_etf = ("ETF" in name.upper() or 
                     "510" in symbol or "159" in symbol or 
                     "基金" in name or "指数" in name)
            
            # 准备数据字符串
            financial_str = self._format_financial_data(enhanced_data)
            technical_str = self._format_technical_data(enhanced_data)
            industry_str = self._format_industry_data(enhanced_data)
            macro_str = self._format_macro_data(enhanced_data)
            sentiment_str = self._format_sentiment_data(enhanced_data)
            
            # 选择合适的prompt模板
            if is_etf:
                prompt_template = self.etf_prompt
                logger.info(f"使用ETF分析模板分析 {symbol} {name}")
            else:
                prompt_template = self.stock_prompt
                logger.info(f"使用个股分析模板分析 {symbol} {name}")
            
            # 生成prompt
            prompt = prompt_template.format(
                symbol=enhanced_data["symbol"],
                name=enhanced_data.get("name", ""),
                current_price=enhanced_data.get("current_price", 0),
                change_percent=enhanced_data.get("change_percent", 0),
                financial_data=financial_str,
                technical_data=technical_str,
                industry_data=industry_str,
                macro_data=macro_str,
                sentiment_data=sentiment_str
            )
            
            # 调用LLM
            output = self.llm(prompt)
            
            return {
                "success": True,
                "analysis": output,
                "validation_info": {
                    "used_langchain": True,
                    "enhanced_data": True,
                    "data_sources": enhanced_data.get('data_quality', {}).get('sources_available', 0)
                }
            }
                
        except Exception as e:
            logger.error(f"LangChain个股分析失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_real_market_data(self) -> Dict[str, Any]:
        """获取实时市场数据"""
        try:
            response = requests.get("http://localhost:5004/api/macro", timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "shanghai_index": 3997,
                    "shanghai_change": -0.03,
                    "gdp_growth": 5.2,
                    "cpi": 2.1,
                    "northbound_flow": 15.2
                }
        except:
            return {
                "shanghai_index": 3997,
                "shanghai_change": -0.03,
                "gdp_growth": 5.2,
                "cpi": 2.1,
                "northbound_flow": 15.2
            }
    
    def _get_enhanced_stock_data(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取增强的股票数据"""
        try:
            symbol = stock_data["symbol"]
            response = requests.get(f"http://localhost:5006/api/comprehensive/{symbol}", timeout=15)
            if response.status_code == 200:
                comprehensive_data = response.json()
                if 'error' not in comprehensive_data:
                    return {**stock_data, **comprehensive_data}
            
            return stock_data
        except:
            return stock_data
    
    def _get_market_position_description(self, index_value: float) -> str:
        """获取市场位置描述"""
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
    
    def _get_historical_contrast(self, index_value: float) -> str:
        """生成历史对比提示"""
        if index_value > 3800:
            return f"注意：当前{index_value:.0f}点，NOT 3000-3500点的历史常见区间！"
        elif index_value > 3500:
            return f"重要：当前{index_value:.0f}点，已超越3500点，NOT在3000-3300点！"
        else:
            return ""
    
    def _format_financial_data(self, data: Dict) -> str:
        """格式化财务数据"""
        financial = data.get('financial_metrics', {})
        return f"""PE估值：{financial.get('pe_ratio', 0):.2f}倍 | PB估值：{financial.get('pb_ratio', 0):.2f}倍
ROE：{financial.get('roe', 0):.2f}% | 毛利率：{financial.get('gross_margin', 0)*100:.1f}%
营收增长：{financial.get('revenue_growth', 0)*100:+.1f}% | 净利润增长：{financial.get('profit_growth', 0)*100:+.1f}%"""
    
    def _format_technical_data(self, data: Dict) -> str:
        """格式化技术数据"""
        technical = data.get('technical_indicators', {})
        return f"""MA5：¥{technical.get('ma5', 0):.2f} | MA20：¥{technical.get('ma20', 0):.2f}
RSI：{technical.get('rsi', 50):.0f} | MACD：{technical.get('macd_trend', '中性')}
支撑位：¥{technical.get('support', 0):.2f} | 阻力位：¥{technical.get('resistance', 0):.2f}"""
    
    def _format_industry_data(self, data: Dict) -> str:
        """格式化行业数据"""
        industry = data.get('industry_comparison', {})
        return f"""行业：{industry.get('sector', '未知')} | 行业PE：{industry.get('industry_pe', 0):.1f}倍
政策环境：{industry.get('policy_support', '中性')}
关键趋势：{', '.join(industry.get('key_trends', ['无'])[:2])}"""
    
    def _format_macro_data(self, data: Dict) -> str:
        """格式化宏观数据"""
        macro = data.get('macro_environment', {})
        return f"""GDP增长：{macro.get('gdp_growth', 0):.1f}% | CPI通胀：{macro.get('cpi', 0):.1f}%
上证指数：{macro.get('shanghai_index', 0):.0f}点 ({macro.get('shanghai_change', 0):+.2f}%)
北向资金：{macro.get('northbound_flow', 0):+.1f}亿元"""
    
    def _format_sentiment_data(self, data: Dict) -> str:
        """格式化情绪数据"""
        stock_sentiment = data.get('stock_sentiment', {})
        market_sentiment = data.get('market_sentiment', {})
        return f"""个股主力资金：{stock_sentiment.get('main_net_inflow', 0):+.1f}万元
机构动作：{stock_sentiment.get('institutional_action', '观望')}
市场情绪：{market_sentiment.get('sentiment_level', '中性')}({market_sentiment.get('overall_sentiment_score', 50):.0f}分)"""