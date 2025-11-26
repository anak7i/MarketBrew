# 🇨🇳 AI-Trader A股版本

欢迎使用AI-Trader A股版本！这是一个专为中国A股市场设计的AI交易竞技场，让多个AI模型在A股市场中自主交易竞争。

## 🌟 A股版本特色

### 📈 市场特点
- **交易标的**: 沪深300指数成分股（前100只）
- **货币单位**: 人民币（CNY）
- **初始资金**: 10万元人民币
- **交易时间**: 上午9:30-11:30，下午13:00-15:00
- **时区**: Asia/Shanghai

### 🔄 A股交易规则
- **T+1制度**: 当天买入，次日才能卖出
- **涨跌幅限制**: 
  - 普通股票: ±10%
  - ST股票: ±5%
  - 科创板/创业板: ±20%
- **最小交易单位**: 100股（1手）

### 🤖 参赛AI模型
- **Claude 3.7 Sonnet** - A股策略专家
- **DeepSeek Chat v3.1** - 中国本土AI模型  
- **通义千问3-Max** - 阿里巴巴AI模型
- **Gemini 2.5 Flash** - Google AI模型
- **GPT-5** - OpenAI最新模型

## 🚀 快速开始

### 📋 环境准备

1. **安装Python 3.8+**
2. **安装依赖库**:
   ```bash
   pip install -r requirements.txt
   ```

### 🔑 配置环境变量

创建 `.env` 文件：
```bash
# AI模型API配置
OPENAI_API_BASE=https://your-openai-proxy.com/v1
OPENAI_API_KEY=your_openai_key

# 其他AI模型API keys
DEEPSEEK_API_KEY=your_deepseek_key
QWEN_API_KEY=your_qwen_key
GEMINI_API_KEY=your_gemini_key

# MCP服务端口配置
MATH_HTTP_PORT=8000
SEARCH_HTTP_PORT=8001
TRADE_HTTP_PORT=8002
GETPRICE_HTTP_PORT=8003

# AI代理配置
AGENT_MAX_STEP=30
```

### ⚡ 一键启动

```bash
# 给启动脚本执行权限
chmod +x start_a_stock.sh

# 启动A股交易竞技场
./start_a_stock.sh
```

### 📊 手动步骤启动

如果一键启动遇到问题，可以按步骤手动启动：

1. **获取A股数据**:
   ```bash
   cd data
   python get_daily_price.py  # 获取沪深300成分股数据
   python merge_jsonl.py      # 合并数据格式
   cd ..
   ```

2. **启动MCP服务**:
   ```bash
   cd agent_tools
   python start_mcp_services.py
   cd ..
   ```

3. **启动AI竞技场**:
   ```bash
   python main.py configs/a_stock_config.json
   ```

## 📊 数据源说明

### 🔄 akshare数据库
- **优势**: 完全免费，数据覆盖全面
- **数据范围**: A股、港股、期货、基金等
- **更新频率**: 实时更新
- **无需API Key**: 直接使用，无需注册

### 📈 支持的股票
项目包含沪深300指数中的前100只活跃股票，包括：
- **银行股**: 平安银行(000001)、招商银行(600036)等
- **科技股**: 各种科技龙头股
- **消费股**: 贵州茅台(600519)、五粮液(000858)等  
- **其他行业**: 制造业、新能源、医药等

## ⚙️ 配置文件说明

### 📁 configs/a_stock_config.json
```json
{
  "market_type": "A_STOCK",
  "currency": "CNY", 
  "initial_cash": 100000.0,
  "trading_hours": {
    "morning_start": "09:30",
    "morning_end": "11:30", 
    "afternoon_start": "13:00",
    "afternoon_end": "15:00"
  },
  "trading_rules": {
    "t_plus_1": true,
    "min_lot_size": 100
  }
}
```

## 📈 查看结果

### 🌐 Web界面
```bash
cd docs
python3 -m http.server 8000
# 访问 http://localhost:8000
```

### 📊 性能分析
- **数据位置**: `data/agent_data_a_stock/`
- **每个AI模型**: 独立的交易记录和持仓文件
- **日志格式**: JSON Lines (.jsonl)

## 🔍 故障排除

### 1. 数据获取失败
```bash
# 检查网络连接
ping www.baidu.com

# 重新安装akshare
pip uninstall akshare
pip install akshare --upgrade
```

### 2. MCP服务启动失败
```bash
# 检查端口占用
netstat -tulpn | grep :800[0-3]

# 手动启动各个服务
python agent_tools/tool_math.py
python agent_tools/tool_trade.py
python agent_tools/tool_get_price_local.py
python agent_tools/tool_jina_search.py
```

### 3. AI模型API问题
- 确认API密钥正确
- 检查网络代理设置
- 验证模型服务可用性

## 🆚 A股 vs 美股版本对比

| 特性 | A股版本 | 美股版本 |
|------|---------|----------|
| 交易标的 | 沪深300成分股 | NASDAQ 100 |
| 货币 | 人民币(CNY) | 美元(USD) |
| 初始资金 | 10万人民币 | 1万美元 |
| 交易时间 | 9:30-15:00 | 9:30-16:00 |
| 交易制度 | T+1 | T+0 |
| 涨跌幅 | ±10% | 无限制 |
| 数据源 | akshare | Alpha Vantage |

## 🤝 贡献指南

欢迎为A股版本贡献代码和策略！

### 🎯 贡献方向
- **策略优化**: 适合A股市场的交易策略
- **数据增强**: 更多A股数据源集成
- **功能扩展**: A股特有功能（如融资融券、转债等）
- **本土化**: 更好的中文支持和界面

### 📝 提交流程
1. Fork项目
2. 创建功能分支
3. 实现A股相关功能
4. 提交Pull Request

## 📞 支持与反馈

- **GitHub Issues**: 报告A股版本相关问题
- **功能建议**: 提出A股市场特有需求
- **交流讨论**: 分享A股交易策略和心得

---

## 🎯 开始你的A股AI交易之旅！

```bash
./start_a_stock.sh
```

让AI模型在A股市场中自主交易，看看哪个AI能在中国股市中脱颖而出！ 🚀

---

*愿AI与你同在，愿收益与你相伴！* 📈✨