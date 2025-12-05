# 📈 MarketBrew - 东方财富API专用版

> 所有数据源已配置为使用东方财富API，akshare已被禁用

## ✨ 配置说明

### 已完成的配置

1. **移除 akshare 依赖** ✅
   - `requirements.txt` 已更新，移除 akshare
   - 添加了 akshare 导入拦截器

2. **创建统一数据服务** ✅
   - `eastmoney_config.py` - 东方财富API统一配置
   - `eastmoney_data_service.py` - 统一数据获取服务
   - `eastmoney_api_enhanced.py` - 增强版API访问器（已存在）

3. **数据源映射** ✅
   - 股票数据 → 东方财富
   - ETF数据 → 东方财富
   - 指数数据 → 东方财富
   - 北向资金 → 东方财富
   - 主力资金 → 东方财富
   - 市场情绪 → 东方财富

## 🚀 快速开始

### 1. 安装依赖

```bash
cd marketbrew
pip install -r requirements.txt
```

**新的 requirements.txt 内容：**
```
flask>=2.0.0
flask-cors>=3.0.10
requests>=2.25.0
pandas>=1.5.0
numpy>=1.21.0
python-dotenv>=0.19.0
langchain>=0.3.0
langchain-openai>=0.1.0
```

### 2. 测试东方财富数据服务

```bash
python eastmoney_data_service.py
```

**测试内容：**
- ✅ 股票实时数据
- ✅ ETF实时数据
- ✅ 北向资金流向
- ✅ 主力资金流向
- ✅ 指数数据（沪深300）
- ✅ K线历史数据

### 3. 启动价格服务

```bash
python price_service.py
```

### 4. 打开前端页面

```bash
# 在浏览器中打开
open stock_subscription.html
```

## 📊 API 使用示例

### 使用统一数据服务

```python
from eastmoney_data_service import eastmoney_service

# 获取股票实时数据
stock = eastmoney_service.get_stock_realtime('000001')
print(stock)

# 获取ETF实时数据
etf = eastmoney_service.get_etf_realtime('510300')
print(etf)

# 获取北向资金
north = eastmoney_service.get_north_bound_flow()
print(f"北向资金总流入: {north['total']}亿")

# 获取主力资金
main_force = eastmoney_service.get_main_force_flow()
print(f"主力资金总流入: {main_force['total']}亿")

# 获取指数数据
index = eastmoney_service.get_index_data('000300')
print(f"沪深300: {index['price']}, 涨跌幅: {index['change_pct']}%")

# 获取K线数据
klines = eastmoney_service.get_kline_data('000300', period='101', count=20)
for kline in klines[-5:]:
    print(f"{kline['date']}: 收盘{kline['close']}, 涨跌幅{kline['change_pct']}%")
```

### 使用增强版API

```python
from eastmoney_api_enhanced import eastmoney_api

# 获取股票列表
stocks = eastmoney_api.get_stock_list_data()
print(f"获取到 {len(stocks)} 只股票")

# 获取ETF数据
etf_data = eastmoney_api.get_etf_data()
print(f"获取到 {len(etf_data)} 只ETF")

# 获取北向资金
north_bound = eastmoney_api.get_north_bound_data()
print(north_bound)

# 获取主力资金
main_force = eastmoney_api.get_main_force_data()
print(main_force)
```

## 🔧 数据源配置

所有数据源配置在 `eastmoney_config.py` 中：

```python
DATA_SOURCE_CONFIG = {
    'stock_data': 'eastmoney',      # 股票数据
    'etf_data': 'eastmoney',        # ETF数据
    'index_data': 'eastmoney',      # 指数数据
    'north_bound': 'eastmoney',     # 北向资金
    'main_force': 'eastmoney',      # 主力资金
    'market_mood': 'eastmoney',     # 市场情绪
    'news': 'eastmoney',            # 新闻
    'announcement': 'eastmoney'     # 公告
}
```

## 📡 东方财富API端点

主要使用的API端点（已配置）：

- **股票列表**: `https://datacenter-web.eastmoney.com/api/qt/clist/get`
- **股票详情**: `https://datacenter-web.eastmoney.com/api/qt/stock/get`
- **北向资金**: `https://datacenter-web.eastmoney.com/api/qt/kamt.rtmin/get`
- **K线数据**: `https://push2his.eastmoney.com/api/qt/stock/kline/get`

## ⚠️ akshare 已禁用

如果代码中尝试导入 akshare，会收到以下错误：

```
ImportError: akshare is disabled. Use eastmoney_api_enhanced instead.
该项目已配置为只使用东方财富API，akshare已被禁用。
```

## 📝 需要更新的文件

以下文件使用了 akshare，需要手动更新为使用东方财富API：

1. `akshare_etf_fetcher.py` - 使用 `eastmoney_data_service.get_etf_realtime()`
2. `real_news_fetcher.py` - 需要使用东方财富新闻API
3. `market_temperature_analyzer.py` - 使用 `eastmoney_data_service`
4. `data/get_expanded_stocks.py` - 使用 `eastmoney_data_service.get_stock_list()`
5. `data/get_daily_price.py` - 使用 `eastmoney_data_service.get_kline_data()`
6. `check_hs300_data.py` - 使用 `eastmoney_data_service.get_index_data('000300')`

## 🎯 数据获取示例

### 获取沪深300成分股

```python
from eastmoney_data_service import eastmoney_service

# 获取沪深300指数数据
hs300_index = eastmoney_service.get_index_data('000300')
print(f"沪深300指数: {hs300_index}")

# 获取沪深300成分股的主力资金
main_force = eastmoney_service.get_main_force_flow('000300')
print(f"沪深300主力资金: {main_force}")
```

### 获取市场情绪数据

```python
# 获取所有股票列表
all_stocks = eastmoney_service.get_stock_list('all')

# 统计涨跌情况
up_count = len([s for s in all_stocks if s['change_pct'] > 0])
down_count = len([s for s in all_stocks if s['change_pct'] < 0])

print(f"上涨: {up_count}, 下跌: {down_count}")
print(f"市场情绪: {'多头' if up_count > down_count else '空头'}")
```

### 获取ETF资金流向

```python
# 获取所有ETF
etf_list = eastmoney_service.get_etf_list()

# 按涨跌幅排序
etf_sorted = sorted(etf_list, key=lambda x: x['change_pct'], reverse=True)

print("涨幅前10的ETF:")
for etf in etf_sorted[:10]:
    print(f"{etf['code']} {etf['name']}: {etf['change_pct']:.2f}%")
```

## 💡 优势

使用东方财富API的优势：

1. **数据实时性** - 实时行情数据，延迟低
2. **稳定性强** - 东方财富官方API，稳定可靠
3. **覆盖全面** - 覆盖A股、ETF、指数等全市场数据
4. **无需安装** - 只需 requests 库，无需额外依赖
5. **免费使用** - 公开API，无需付费

## 📞 技术支持

如有问题，请查看：
- `eastmoney_data_service.py` - 数据服务实现
- `eastmoney_config.py` - 配置说明
- 日志输出 - 详细的调试信息

---

**MarketBrew - 100% 东方财富API** ☕

真实数据，实时更新，稳定可靠。
