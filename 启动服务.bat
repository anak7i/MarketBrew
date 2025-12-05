@echo off
chcp 65001 >nul
cls
echo ============================================================
echo 🚀 MarketBrew 市场温度计 - 服务启动
echo ============================================================
echo.

echo [步骤 1/2] 检查 Python 环境...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python 未安装或未添加到环境变量
    pause
    exit /b 1
)
echo ✅ Python 环境正常
echo.

echo [步骤 2/2] 启动价格服务...
echo 📊 端口: 5000
echo 🌡️ 功能: 市场温度计
echo.
echo 提示: 服务启动后会显示详细信息
echo      按 Ctrl+C 可停止服务
echo.
echo ============================================================
echo.

python price_service.py

pause
