# 📁 已废弃文件列表

重构完成后，以下文件不再使用，可以考虑归档或删除：

## 🗑️ 旧界面文件
- `interactive_dashboard.html` - 原主控制台 → 已被 `ai_decision_center.html` 替代
- `trading_log.html` - 原交易日志页面 → 功能整合到决策中心
- `daily_reports/` 目录下的静态HTML - 功能整合到决策中心

## 🗑️ 重复的分析脚本
- `daily_full_analyzer.py` - 原全量分析器 → 已被 `unified_decision_engine.py` 替代
- `batch_ai_analyzer.py` - 原批量分析器 → 功能已整合
- `analyze_remaining.py` - 原剩余分析器 → 不再需要
- `quick_test_analyzer.py` - 原快速测试器 → 功能已整合
- `analysis_server.py` - 原API服务器 → 已被 `decision_api_server.py` 替代

## 🗑️ 旧启动脚本
- `run_complete_system.py` - 原系统演示 → 已被 `start_decision_system.py` 替代
- `run_full_analysis.py` - 原分析启动器 → 功能已整合
- `start_analysis.py` - 原分析脚本 → 功能已整合
- `ai_scheduler.py` - 原调度器 → 已被 `daily_scheduler.py` 替代

## 🗑️ 配置和工具文件
- `simple_dashboard.py` - 原简单界面 → 不再使用
- `dashboard.py` - 原界面脚本 → 不再使用
- `local_server.py` - 原本地服务器 → 功能已整合
- `test_streamlit.py` - Streamlit测试 → 不再使用Streamlit
- `update_trading_log.py` - 原日志更新器 → 功能已整合

## 🗑️ 多余的配置
- `configs/default_config.json` - 原默认配置 → 不再使用复杂配置
- `configs/deepseek_expanded_config.json` - 原扩展配置 → 不再使用
- `configs/deepseek_2025_config.json` - 原2025配置 → 不再使用

## ✅ 保留的核心文件

### 新系统核心
- `ai_decision_center.html` - ✨ 新的统一决策中心
- `unified_decision_engine.py` - ✨ 新的统一分析引擎  
- `decision_api_server.py` - ✨ 新的决策API服务器
- `daily_scheduler.py` - ✨ 新的自动调度系统
- `start_decision_system.py` - ✨ 新的一键启动脚本

### 数据和基础
- `data/` 目录 - 股票数据文件
- `decision_data/` 目录 - ✨ 新的决策数据目录
- `deepseek_trading.py` - 基础交易功能
- `configs/deepseek_only_config.json` - 基础配置

### 工具脚本  
- `data/get_daily_price.py` - 数据获取
- `data/fast_download.py` - 快速下载
- 其他data目录下的工具脚本

## 🔄 迁移指南

### 如果仍需要旧功能
1. **交易日志**: 使用决策中心的历史记录功能
2. **多页面**: 决策中心已整合所有必要功能
3. **复杂配置**: 新系统使用简化的配置方式
4. **多脚本**: 使用统一的启动脚本管理

### 数据迁移
- 旧的分析结果在 `daily_analysis/` 目录
- 新的决策数据在 `decision_data/` 目录
- 可以保留旧数据作为历史参考

## 🚮 清理建议

### 立即可删除
- 所有重复的分析脚本
- 旧的HTML界面文件
- 不使用的配置文件

### 谨慎处理
- 保留 `data/` 目录中的股票数据
- 保留基础的交易功能模块
- 备份重要的历史分析数据

### 清理命令 (可选)
```bash
# 创建备份目录
mkdir deprecated_backup

# 移动废弃文件到备份目录
mv interactive_dashboard.html deprecated_backup/
mv trading_log.html deprecated_backup/
mv daily_full_analyzer.py deprecated_backup/
mv analysis_server.py deprecated_backup/
# ... 其他废弃文件

# 清理空目录
rmdir daily_reports/ 2>/dev/null || true
```

---

⚠️ **注意**: 在删除任何文件之前，请确保新系统运行正常，并备份重要数据！