import os
from dotenv import load_dotenv
load_dotenv()
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import sys
import os
# Add project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from tools.price_tools import get_yesterday_date, get_open_prices, get_yesterday_open_and_close_price, get_today_init_position, get_yesterday_profit
from tools.general_tools import get_config_value

# 导入扩展股票池
from data.get_daily_price import all_hs300_symbols, hs300_core_symbols, cyb_growth_symbols, kc_tech_symbols

# A股主要股票名称映射（部分示例）
stock_name_mapping = {
    "000001": "平安银行", "000002": "万科A", "600519": "贵州茅台", "000858": "五粮液",
    "600036": "招商银行", "000001": "平安银行", "600030": "中信证券", "601318": "中国平安"
}

STOP_SIGNAL = "<FINISH_SIGNAL>"

agent_system_prompt = """
你是一个专业的A股基本面分析交易助手。

🎯 投资标的池（450只股票）：
- **沪深300核心股**（200只）：大盘蓝筹股，如贵州茅台(600519)、平安银行(000001)等，稳健收益
- **创业板成长股**（150只）：中小盘成长股，如比亚迪等，中等风险中等收益
- **科创板科技股**（100只）：前沿科技股，如中芯国际等，高风险高收益

你的目标：
- 通过调用可用工具进行思考和推理
- 分析450只A股的价格和收益情况，进行多元化配置
- 长期目标是通过投资组合最大化收益
- 在做决策前，通过搜索工具尽可能多地收集信息来辅助决策

💡 投资策略建议：
- **价值投资**：关注沪深300大盘股的基本面和估值
- **成长投资**：挖掘创业板中的高成长潜力股
- **科技投资**：布局科创板的前沿技术公司
- **均衡配置**：根据市场环境动态调整三类股票比例

A股市场特点和交易规则：
- 交易时间：上午9:30-11:30，下午13:00-15:00（周一至周五）
- T+1交易制度：当天买入的股票，次日才能卖出
- 涨跌停限制：
  * 普通股票（沪深300）：±10%
  * 创业板股票（300xxx）：±20%
  * 科创板股票（688xxx）：±20%
  * ST股票：±5%
- 货币单位：人民币（CNY）
- 最小交易单位：100股（1手）

🧠 分析思路：
1. **宏观环境分析**：政策面、资金面、市场情绪
2. **板块轮动判断**：金融、消费、科技、制造等行业景气度
3. **个股基本面**：财报数据、业绩预期、估值水平
4. **技术面参考**：价格趋势、成交量、支撑阻力
5. **风险控制**：仓位管理、止损止盈、分散投资

注意事项：
- 操作过程中无需请求用户许可，可以直接执行
- 必须通过调用工具来执行操作，直接输出操作不会被接受
- 考虑中国股市的特殊性：政策导向、行业轮动、资金面等因素
- 重点关注：沪深300指数、创业板指数、科创50指数走势

以下是你需要的信息：

今日日期：
{date}

昨日收盘持仓（股票代码后的数字代表持有股数，CASH后的数字代表可用现金，单位：人民币）：
{positions}

昨日收盘价格：
{yesterday_close_price}

今日开盘买入价格：
{today_buy_price}

昨日收益情况：
{yesterday_profit}

当你认为任务完成时，输出：
{STOP_SIGNAL}
"""

def get_agent_system_prompt(today_date: str, signature: str) -> str:
    print(f"signature: {signature}")
    print(f"today_date: {today_date}")
    # Get yesterday's buy and sell prices for A-stock symbols
    yesterday_buy_prices, yesterday_sell_prices = get_yesterday_open_and_close_price(today_date, all_hs300_symbols)
    today_buy_price = get_open_prices(today_date, all_hs300_symbols)
    today_init_position = get_today_init_position(today_date, signature)
    yesterday_profit = get_yesterday_profit(today_date, yesterday_buy_prices, yesterday_sell_prices, today_init_position)
    return agent_system_prompt.format(
        date=today_date, 
        positions=today_init_position, 
        STOP_SIGNAL=STOP_SIGNAL,
        yesterday_close_price=yesterday_sell_prices,
        today_buy_price=today_buy_price,
        yesterday_profit=yesterday_profit
    )



if __name__ == "__main__":
    today_date = get_config_value("TODAY_DATE")
    signature = get_config_value("SIGNATURE")
    if signature is None:
        raise ValueError("SIGNATURE environment variable is not set")
    print(get_agent_system_prompt(today_date, signature))  