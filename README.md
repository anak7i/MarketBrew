# 📈 MarketBrew - A股智能订阅系统

> 基于腾讯财经API的实时股票信息订阅和智能分析平台

## ✨ 功能特性

- 🎯 **实时股票价格** - 基于腾讯财经API获取A股实时行情
- 📊 **智能简报生成** - AI分析市场动态，生成投资建议
- 🔔 **股票订阅管理** - 添加/删除关注股票，自动追踪
- 📱 **响应式设计** - 适配桌面和移动设备
- 🎨 **MarketBrew品牌** - 专业的UI设计和用户体验

## 🏗️ 系统架构

```
MarketBrew/
├── stock_subscription.html    # 前端页面
├── price_service.py          # 价格服务后端
├── start_price_service.sh    # 服务启动脚本
├── test_price_service.py     # 服务测试脚本
└── marketbrew-logo.png       # 品牌Logo
```

### 技术栈
- **前端**: HTML5, CSS3, JavaScript (原生)
- **后端**: Python Flask + 腾讯财经API
- **数据源**: 腾讯财经实时行情接口
- **UI框架**: 自定义响应式设计

## 🚀 快速开始

### 1. 环境要求
- Python 3.7+
- 现代浏览器 (Chrome, Firefox, Safari, Edge)

### 2. 安装依赖
```bash
# 安装 Python 依赖
pip3 install flask flask-cors requests
```

### 3. 启动服务

#### 方法一：使用启动脚本 (推荐)
```bash
chmod +x start_price_service.sh
./start_price_service.sh
```

#### 方法二：手动启动
```bash
python3 price_service.py
```

### 4. 打开网页
在浏览器中打开 `stock_subscription.html` 文件

## 📊 API接口说明

### 价格服务 (http://localhost:5000)

#### 获取单只股票
```bash
GET /api/stock/{symbol}

# 示例
curl http://localhost:5000/api/stock/000001
```

#### 批量获取股票
```bash
POST /api/stocks
Content-Type: application/json

{
  "symbols": ["000001", "600519", "000858"]
}
```

#### 市场状态
```bash
GET /api/market/status

# 返回值:
# - trading: 交易中
# - pre_market: 盘前
# - after_market: 盘后 
# - lunch_break: 午休
# - closed: 休市
```

#### 健康检查
```bash
GET /health
```

## 🧪 测试服务

```bash
# 运行测试脚本
python3 test_price_service.py
```

测试包括：
- ✅ 服务健康检查
- ✅ 市场状态获取
- ✅ 单只股票查询
- ✅ 批量股票查询

## 📈 使用指南

### 添加股票订阅
1. 在页面右上角的订阅框中输入股票代码或名称
2. 系统会自动显示匹配的股票建议
3. 点击建议项目或直接点击"添加订阅"按钮

### 查看实时行情
- 主页面显示关注股票的实时价格和涨跌幅
- 绿圆点 🟢 表示交易中
- 红圆点 🔴 表示已收盘
- 黄圆点 🟡 表示其他状态

### 生成智能简报
1. 点击"一键生成简报"按钮
2. 系统会自动收集市场数据和个股信息
3. AI分析后生成包含投资建议的详细简报

## 🎯 支持的股票代码格式

- **深圳市场**: `000001`, `002594`, `300750` 等
- **上海市场**: `600519`, `601318`, `688981` 等
- **ETF基金**: `510300`, `159919` 等

系统会自动识别市场并格式化为腾讯API要求的格式。

## ⚙️ 配置说明

### 端口配置
- 价格服务默认端口: `5000`
- 可在 `price_service.py` 中修改

### 请求频率限制
- 为避免触发API限制，系统内置了请求间隔控制
- 批量请求失败时会自动降级到单个请求

### 错误处理
- 网络错误时自动回退到模拟数据
- 显示友好的错误提示信息
- 服务不可用时优雅降级

## 🔧 开发与扩展

### 添加新的数据源
在 `price_service.py` 中的 `TencentFinanceAPI` 类基础上扩展：

```python
class NewDataSource:
    def get_stock_info(self, symbol):
        # 实现新的数据获取逻辑
        pass
```

### 自定义股票分析
在前端的 `generateStockAnalysis` 函数中添加新的分析逻辑。

### UI主题定制
修改 CSS 变量来调整颜色主题和样式。

## 📱 移动端适配

系统采用响应式设计，在不同设备上自动调整：
- 🖥️ 桌面端：卡片网格布局
- 📱 移动端：垂直堆叠布局
- 📊 数据显示优化适配小屏幕

## ⚠️ 注意事项

1. **数据准确性**: 腾讯财经API为第三方服务，数据仅供参考
2. **投资风险**: 系统分析结果不构成投资建议，投资有风险
3. **服务稳定性**: 需要网络连接，API可能存在访问限制
4. **浏览器兼容**: 建议使用现代浏览器以获得最佳体验

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目！

## 📄 许可证

本项目仅供学习和研究使用。

---

**MarketBrew - One Alpha Latte** ☕

让每一次投资决策都更加智能和从容。