# 🚀 EMT API 集成说明

> 东方财富证券极速行情系统 API

## 📦 已集成内容

### EMT API C++ 版本 V2.25.0

我已经将东方财富证券的 EMT API 集成到项目中：

```
marketbrew/
├── emt_api/
│   ├── emt_api.dll              ← 主API (872KB)
│   ├── emt_quote_api.dll        ← 行情API (270KB)
│   ├── emt_trader_api_c.dll     ← 交易API (28KB)
│   └── doc/                     ← 完整文档
│       ├── 东方财富证券极速行情系统行情API开发手册.md
│       ├── 东方财富证券极速交易系统交易API开发手册.md
│       └── EMTTraderApi常见问题.md
```

## ⚠️ 重要说明

### EMT API vs HTTP API

|   | EMT API (专业版) | HTTP API (当前使用) |
|---|---|---|
| **费用** | 💰 需要开通（商业） | ✅ 免费 |
| **账号** | 📝 需要东方财富证券账号 | ❌ 无需账号 |
| **数据** | 🚀 极速实时（毫秒级） | ⚡ 实时（秒级） |
| **功能** | 📊 行情 + 📈 交易 | 📊 仅行情 |
| **技术** | C++ DLL (需封装) | HTTP REST API |
| **适用** | 专业交易、量化策略 | 个人研究、学习 |

### 当前项目状态

✅ **正在使用**: HTTP API (eastmoney_data_service.py)
- 免费，无需账号
- 适合个人使用
- 数据准确且实时

📦 **已集成**: EMT API (emt_api/)
- 供将来升级使用
- 需要开通东方财富证券账号
- 适合专业交易需求

## 🔧 如何使用 EMT API

### 前提条件

1. ✅ 拥有东方财富证券账号
2. ✅ 已开通 EMT API 权限
3. ✅ 获取服务器地址和端口
4. ✅ 获取用户名和密码

###步骤 1: 安装 Python ctypes（已内置）

```bash
# Python 自带，无需安装
```

### 步骤 2: 查看文档

```bash
# 查看行情API文档
notepad emt_api/doc/东方财富证券极速行情系统行情API开发手册.md

# 查看交易API文档
notepad emt_api/doc/东方财富证券极速交易系统交易API开发手册.md

# 查看常见问题
notepad emt_api/doc/EMTTraderApi常见问题.md
```

### 步骤 3: 使用 Python 包装器（示例）

我已经创建了一个 Python 包装器示例：`emt_wrapper.py`

```python
from emt_wrapper import EMTQuoteClient

# 创建客户端
client = EMTQuoteClient()

# 登录
client.login(
    server_ip="xxx.xxx.xxx.xxx",  # 服务器IP
    port=12345,                    # 端口
    username="your_username",      # 用户名
    password="your_password"       # 密码
)

# 订阅行情
client.subscribe_market_data(["000001", "600519"])

# 获取数据
data = client.get_market_data("000001")
print(data)
```

## 📊 API 功能对比

### HTTP API (当前使用)

✅ **优势**：
- 免费使用
- 无需账号
- 简单易用
- 支持 A 股全市场数据
- 实时更新（秒级）

❌ **限制**：
- 无交易功能
- 可能有访问频率限制
- 依赖网络连接

### EMT API (专业版)

✅ **优势**：
- 极速实时（毫秒级）
- 支持交易功能
- 专业级数据质量
- 支持 Level-2 行情
- 断线自动重连

❌ **限制**：
- 需要开通账号
- 可能需要付费
- C++ 接口（需封装）
- 配置较复杂

## 🎯 使用建议

### 个人学习/研究

**推荐**: HTTP API ✅

```python
from eastmoney_data_service import eastmoney_service

# 简单、免费、易用
stock = eastmoney_service.get_stock_realtime('000001')
```

### 专业交易/量化策略

**推荐**: EMT API 📊

```python
from emt_wrapper import EMTQuoteClient

# 毫秒级数据，支持交易
client = EMTQuoteClient()
# ... (需要账号)
```

### 混合使用

可以同时使用两种 API：

```python
# 行情查看：使用 HTTP API（免费）
from eastmoney_data_service import eastmoney_service
market_data = eastmoney_service.get_stock_list()

# 实盘交易：使用 EMT API（专业）
from emt_wrapper import EMTTraderClient
# trader = EMTTraderClient()  # 需要账号
```

## 📝 获取 EMT API 账号

### 申请流程

1. **开户**: 在东方财富证券开立证券账户
2. **申请**: 联系客服申请 EMT API 权限
3. **审核**: 等待审核通过
4. **配置**: 获取服务器地址、端口、账号密码

### 联系方式

- 官网: https://www.18.cn/
- 客服: 95357
- 邮箱: （咨询客服获取）

## 🔐 安全注意事项

### 保护账号信息

**❌ 不要**：
- 将账号密码写在代码里
- 将配置文件上传到 GitHub
- 分享服务器地址给他人

**✅ 应该**：
- 使用环境变量存储账号信息
- 使用配置文件（添加到 .gitignore）
- 定期更换密码

### 配置文件示例

创建 `.env` 文件（不要上传到 Git）：

```bash
# EMT API 配置
EMT_SERVER_IP=xxx.xxx.xxx.xxx
EMT_PORT=12345
EMT_USERNAME=your_username
EMT_PASSWORD=your_password
```

在代码中使用：

```python
import os
from dotenv import load_dotenv

load_dotenv()

client.login(
    server_ip=os.getenv('EMT_SERVER_IP'),
    port=int(os.getenv('EMT_PORT')),
    username=os.getenv('EMT_USERNAME'),
    password=os.getenv('EMT_PASSWORD')
)
```

## 📚 相关文档

### EMT API 文档

- 📖 [行情API开发手册](emt_api/doc/东方财富证券极速行情系统行情API开发手册.md)
- 📖 [交易API开发手册](emt_api/doc/东方财富证券极速交易系统交易API开发手册.md)
- 📖 [Lv2行情API开发手册](emt_api/doc/东方财富证券极速行情系统Lv2行情API开发手册.md)
- 📖 [常见问题](emt_api/doc/EMTTraderApi常见问题.md)
- 📖 [错误编码列表](emt_api/doc/EMTTraderApi错误编码列表.md)

### 项目文档

- 📖 [东方财富HTTP API说明](README_EASTMONEY_ONLY.md)
- 📖 [市场温度计使用指南](README_MARKET_TEMPERATURE.md)
- 📖 [项目配置完成说明](SETUP_COMPLETE.md)

## 💡 下一步

### 如果您有 EMT API 账号

1. 查看文档了解 API 功能
2. 配置环境变量
3. 运行测试脚本：`python test_emt_api.py`
4. 集成到 MarketBrew

### 如果您没有账号

1. 继续使用当前的 HTTP API ✅
2. 功能完全够用
3. 数据准确且实时
4. 完全免费

---

## 🤝 技术支持

### EMT API 相关

- 查看官方文档
- 联系东方财富客服
- 查看示例代码：`emt_api/demo/`

### HTTP API 相关

- 查看：`eastmoney_data_service.py`
- 文档：`README_EASTMONEY_ONLY.md`
- 测试：`python quick_test.py`

---

**MarketBrew** - 支持多种数据源，满足不同需求 📊

最后更新: 2025-11-26
