@echo off
chcp 65001 >nul
echo ========================================
echo AlphaBloom 资金流向择时服务
echo ========================================
echo.

echo [1/2] 检查Python环境...
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)

python --version
echo.

echo [2/2] 启动资金流向择时API服务...
echo.
echo 📊 服务将在 http://localhost:5001 启动
echo 🌐 前端页面: capital_timing.html
echo.
echo 按 Ctrl+C 可停止服务
echo ========================================
echo.

cd /d "%~dp0"
python capital_timing_api.py

pause
