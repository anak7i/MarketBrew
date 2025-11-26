#!/bin/bash

# AlphaBloom 服务启动脚本
# 启动所有必需的后台服务以支持增强版批量股票分析

echo "🚀 启动 AlphaBloom 增强版服务..."
echo "=================================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "📍 工作目录: $SCRIPT_DIR"

# 服务配置
declare -A SERVICES=(
    ["price_service"]="price_service.py:5002"
    ["decision_service"]="decision_api_server.py:5001" 
    ["news_service"]="news_and_announcements_service.py:5007"
    ["sentiment_service"]="market_sentiment_service.py:5005"
    ["market_index_service"]="market_index_service.py:5008"
    ["entry_signal_service"]="entry_signal_service.py:5009"
    ["market_mood_service"]="market_mood_service.py:5010"
)

# 检查端口占用函数
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0  # 端口被占用
    else
        return 1  # 端口可用
    fi
}

# 启动服务函数
start_service() {
    local service_name=$1
    local script_and_port=$2
    local script=$(echo $script_and_port | cut -d':' -f1)
    local port=$(echo $script_and_port | cut -d':' -f2)
    
    echo "🔄 检查 $service_name 服务..."
    
    if check_port $port; then
        echo "✅ $service_name 已在端口 $port 运行"
        return 0
    fi
    
    if [ ! -f "$script" ]; then
        echo "❌ 服务脚本不存在: $script"
        return 1
    fi
    
    echo "🚀 启动 $service_name 服务 (端口 $port)..."
    nohup python3 "$script" > "logs/${service_name}.log" 2>&1 &
    local pid=$!
    echo "   PID: $pid"
    
    # 等待服务启动
    sleep 3
    
    if check_port $port; then
        echo "✅ $service_name 启动成功"
        return 0
    else
        echo "❌ $service_name 启动失败，检查日志: logs/${service_name}.log"
        return 1
    fi
}

# 启动所有服务
echo ""
echo "🔧 启动核心服务..."
echo ""

started_services=0
total_services=${#SERVICES[@]}

for service_name in "${!SERVICES[@]}"; do
    if start_service "$service_name" "${SERVICES[$service_name]}"; then
        ((started_services++))
    fi
    echo ""
done

# 服务启动总结
echo "=================================================="
echo "📊 服务启动总结: $started_services/$total_services 个服务成功启动"
echo ""

if [ $started_services -eq $total_services ]; then
    echo "🎉 所有 AlphaBloom 服务启动成功！"
    echo ""
    echo "🌐 服务访问地址:"
    echo "   📈 实时价格服务:     http://localhost:5002"
    echo "   🤖 AI决策服务:       http://localhost:5001"  
    echo "   📰 新闻公告服务:     http://localhost:5007"
    echo "   📊 市场情绪服务:     http://localhost:5005"
    echo "   📉 大盘指数服务:     http://localhost:5008"
    echo "   🎯 进场信号服务:     http://localhost:5009"
    echo "   🎭 市场情绪监控服务: http://localhost:5010"
    echo ""
    echo "🔧 测试命令:"
    echo "   python3 test_market_integration.py  # 测试大盘数据集成"
    echo "   python3 batch_optimized_decision_engine.py  # 批量分析性能评估"
    echo "   python3 test_entry_signal_system.py  # 测试进场信号系统"
    echo ""
    echo "💡 使用方法:"
    echo "   from batch_optimized_decision_engine import BatchOptimizedDecisionEngine"
    echo "   engine = BatchOptimizedDecisionEngine()"
    echo "   results = engine.analyze_batch_stocks(['000001', '000002', '000977'])"
    echo ""
    echo "⚡ 性能特点:"
    echo "   • 支持443只股票批量分析 (6-10分钟)"
    echo "   • 集成大盘环境背景分析"
    echo "   • 8线程并发 + 数据缓存优化"
    echo "   • DeepSeek AI智能决策分析"
    echo "   • Market Mood市场情绪监控系统"
    
elif [ $started_services -gt 0 ]; then
    echo "⚠️  部分服务启动成功，部分失败"
    echo "💡 检查失败服务的日志文件: logs/*.log"
    echo "🔧 手动启动失败的服务: python3 [服务脚本]"
else
    echo "❌ 所有服务启动失败"
    echo "💡 请检查:"
    echo "   1. Python3 环境是否正确"
    echo "   2. 依赖包是否已安装: pip install -r requirements.txt"
    echo "   3. 端口是否被占用"
    echo "   4. 日志文件: logs/*.log"
fi

echo ""
echo "📋 管理命令:"
echo "   查看运行状态: lsof -i :5001-5008"
echo "   停止所有服务: pkill -f 'python3.*service'"
echo "   查看日志:     tail -f logs/*.log"
echo "=================================================="