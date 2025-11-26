# 🤖 DeepSeek AI决策中心

## 📖 系统概述

DeepSeek AI决策中心是一个专注于投资决策的智能股票分析系统，通过AI技术对443只A股进行全面分析，为投资者提供明确的买入、卖出、持有建议。

### 🎯 核心特色
- **决策导向**: 专注于给出明确的投资操作建议
- **自动化**: 每天早上8:00自动分析，生成当日投资策略
- **统一界面**: 单一决策中心，操作简洁直观
- **AI驱动**: 基于DeepSeek大模型的专业分析

## 🏗️ 系统架构

### 核心组件
```
AI决策中心/
├── 🌐 前端界面
│   └── ai_decision_center.html          # 统一决策中心界面
├── 🧠 分析引擎  
│   └── unified_decision_engine.py       # 统一决策分析引擎
├── 🔗 API服务
│   └── decision_api_server.py           # 决策API服务器
├── ⏰ 调度系统
│   └── daily_scheduler.py               # 每日自动调度器
└── 🚀 启动管理
    └── start_decision_system.py         # 一键启动脚本
```

### 数据流
```
股票数据 → AI分析引擎 → 决策数据 → API服务 → Web界面
    ↓           ↓           ↓         ↓        ↓
  443只A股   智能分析    买卖持建议   实时API   决策展示
```

## 🚀 快速开始

### 1. 启动系统
```bash
python start_decision_system.py
```
选择 "1. 🚀 启动完整系统"

### 2. 使用决策中心
- 浏览器自动打开AI决策中心界面
- 点击 "🚀 启动全量分析" 进行手动分析
- 查看买入、卖出、持有建议
- 了解AI分析依据和风险提示

### 3. 自动化运行
- 系统每天早上8:00自动分析
- 或启动调度器: `python daily_scheduler.py`

## 📊 功能特性

### 🎯 AI决策中心 (主界面)
- **市场总览**: 443只股票分析状态
- **决策建议**: 清晰的买入/卖出/持有分类
- **智能排序**: 按AI置信度排序推荐
- **风险提示**: 突出显示关键风险点
- **一键操作**: 简化的手动触发分析

### 🧠 智能分析引擎
- **全量覆盖**: 分析443只A股(沪深300+创业板+科创板)
- **DeepSeek AI**: 使用专业大模型分析
- **决策导向**: 专注生成操作建议
- **批量处理**: 高效并发分析
- **置信度评估**: 量化决策可信度

### ⏰ 自动化调度
- **定时分析**: 每天早上8:00自动执行
- **交易日检测**: 自动跳过周末和节假日  
- **结果通知**: 分析完成后生成通知
- **历史记录**: 保存每日分析结果

### 🔗 API服务
- **实时数据**: 提供最新决策数据
- **状态监控**: 分析进度和系统状态
- **手动触发**: 支持随时启动分析
- **CORS支持**: 前端无缝集成

## 📁 数据结构

### 决策数据格式
```json
{
  "analysis_date": "2025-11-06",
  "summary": {
    "buy_count": 12,
    "sell_count": 5,
    "hold_count": 426,
    "market_analysis": "市场分析文本",
    "risk_level": "中等"
  },
  "decisions": {
    "buy": [
      {
        "symbol": "000001",
        "name": "平安银行", 
        "decision": "买入",
        "strength": "强烈",
        "reason": "技术突破，建议买入",
        "price": 11.53,
        "change_pct": 0.9,
        "confidence": 0.85
      }
    ],
    "sell": [...],
    "hold": [...]
  }
}
```

### 目录结构
```
decision_data/                    # 决策数据目录
├── decision_data_20251106.json  # 每日详细决策
├── latest_decision.json         # 最新决策数据
└── ...

logs/                            # 日志目录  
├── decision_engine.log          # 分析引擎日志
├── daily_scheduler.log          # 调度器日志
└── ...
```

## 🔧 配置说明

### 环境要求
- Python 3.7+
- 必要包: requests, schedule
- 股票数据: data/daily_prices_*.json

### API配置
- DeepSeek API Key: 在 `unified_decision_engine.py` 中配置
- API服务端口: 默认8526，可在 `decision_api_server.py` 中修改
- 调度时间: 默认8:00，可在 `daily_scheduler.py` 中修改

### 分析参数
- 并发数量: 默认5个线程
- 批处理大小: 默认50只股票/批
- API超时: 30秒
- 重试次数: 3次

## 🆚 重构对比

### ❌ 重构前问题
- 3个分散的HTML页面
- 多个重复的分析脚本  
- 按钮功能混乱重复
- 数据不同步
- 操作复杂需要跳转

### ✅ 重构后优势
- 统一的决策中心界面
- 整合的分析引擎
- 清晰的决策流程
- 自动化调度
- 专注投资决策

## 🛠️ 开发指南

### 添加新功能
1. 在 `unified_decision_engine.py` 中扩展分析逻辑
2. 在 `decision_api_server.py` 中添加API端点
3. 在 `ai_decision_center.html` 中增加前端功能

### 自定义分析策略
修改 `build_decision_prompt()` 方法中的提示词模板

### 扩展通知方式
在 `daily_scheduler.py` 的 `send_completion_notification()` 中添加邮件、微信等

## 🔍 故障排除

### 常见问题
1. **API服务无法启动**: 检查端口8526是否被占用
2. **分析失败**: 检查DeepSeek API密钥和网络连接
3. **数据缺失**: 确认data目录下有股票数据文件
4. **Web界面无响应**: 检查API服务器是否正常运行

### 日志查看
```bash
tail -f decision_engine.log      # 查看分析日志
tail -f daily_scheduler.log     # 查看调度日志
```

### 手动测试
```bash
python unified_decision_engine.py    # 测试分析引擎
python decision_api_server.py        # 测试API服务
python daily_scheduler.py            # 测试调度器
```

## 📝 更新日志

### v2.0.0 (2025-11-06)
- 🎯 重构为统一决策中心
- 🧠 整合分析引擎
- ⏰ 添加自动调度
- 🌐 优化用户界面
- 🔗 标准化API接口

## 📞 支持

如有问题，请检查:
1. 系统依赖是否完整
2. 数据文件是否存在  
3. API密钥是否正确
4. 日志文件中的错误信息

---

🎯 **专注决策，简化操作，让AI为您的投资保驾护航！**