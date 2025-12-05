@echo off
chcp 65001 > nul
echo ================================
echo 启动并诊断决策API服务
echo ================================
echo.

cd /d C:\Users\86158\marketbrew

echo [1/4] 检查Python环境...
python --version
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    pause
    exit /b 1
)
echo ✅ Python环境正常
echo.

echo [2/4] 检查依赖包...
python -c "import flask; import requests" 2>nul
if errorlevel 1 (
    echo ⚠️ 缺少依赖包，正在安装...
    pip install flask flask-cors requests
)
echo ✅ 依赖包完整
echo.

echo [3/4] 启动决策API服务...
echo 服务将在后台启动，窗口将保持打开显示日志
echo.
start "决策API服务器" cmd /k "python decision_api_server.py"

echo ⏳ 等待服务启动...
timeout /t 5 /nobreak > nul

echo.
echo [4/4] 测试API端点...
python test_api.py

echo.
echo ================================
echo 诊断完成！
echo ================================
echo.
echo 如果测试失败，请查看"决策API服务器"窗口的日志
echo.
pause
