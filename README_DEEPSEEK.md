# 🤖 DeepSeek A股交易系统

简化版AI交易系统，专门使用DeepSeek API进行A股自动交易。

## 🎯 系统特点

- **单一AI模型**: 仅使用DeepSeek Chat
- **A股专业**: 针对中国A股市场优化
- **简单配置**: 只需配置一个API密钥
- **自动交易**: AI自主分析和交易A股

## ⚡ 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，填入你的DeepSeek API密钥
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
```

### 3. 一键启动
```bash
chmod +x start_deepseek_only.sh
./start_deepseek_only.sh
```

## 🔑 获取DeepSeek API密钥

1. 访问 [DeepSeek开放平台](https://platform.deepseek.com/)
2. 注册账号并登录
3. 进入API管理页面
4. 创建新的API密钥
5. 复制密钥到`.env`文件中

## 📊 交易配置

### 基本设置
- **初始资金**: 10万人民币
- **交易市场**: A股沪深300成分股
- **交易时间**: 9:30-11:30, 13:00-15:00
- **最小单位**: 100股(1手)

### 交易规则
- **T+1制度**: 当天买入，次日可卖
- **涨跌幅**: ±10%限制
- **自动止损**: AI自主判断

## 📈 运行流程

1. **数据获取**: 自动下载最新A股数据
2. **服务启动**: 启动交易和分析服务
3. **AI分析**: DeepSeek分析市场和个股
4. **自动交易**: 根据分析结果买卖股票
5. **记录日志**: 保存所有交易记录

## 📁 输出文件

### 交易记录
- `data/agent_data/deepseek-chat/position/position.jsonl` - 持仓变化
- `data/agent_data/deepseek-chat/log/日期/log.jsonl` - 每日交易日志

### 查看结果
```bash
# 查看最新持仓
tail -1 data/agent_data/deepseek-chat/position/position.jsonl

# 查看今日交易日志
ls data/agent_data/deepseek-chat/log/
```

## 🌐 Web界面

启动Web界面查看交易图表：
```bash
cd docs
python3 -m http.server 8000
# 访问 http://localhost:8000
```

## ⚙️ 自定义配置

编辑 `configs/deepseek_only_config.json` 可以调整：
- 交易日期范围
- 初始资金
- 最大交易步数
- 风险控制参数

## 🔧 故障排除

### API连接问题
```bash
# 测试API连接
curl -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
     https://api.deepseek.com/v1/models
```

### 端口占用
```bash
# 检查端口
netstat -tulpn | grep :800[0-3]

# 杀死占用进程
pkill -f start_mcp_services
```

### 数据更新
```bash
# 重新获取股票数据
cd data
python get_daily_price.py
python merge_jsonl.py
```

## 💡 使用建议

1. **模拟交易**: 首次使用建议用历史数据回测
2. **风险控制**: 设置合适的初始资金和止损点
3. **定期监控**: 查看AI的交易逻辑和表现
4. **数据更新**: 定期更新股票数据保持准确性

## 📞 技术支持

- 遇到问题请检查日志文件
- 确保网络连接正常
- 验证API密钥有效性
- DeepSeek API限制和计费说明请查阅官方文档

---

开始你的DeepSeek A股交易之旅！🚀