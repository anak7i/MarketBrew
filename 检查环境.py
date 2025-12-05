#!/usr/bin/env python3
"""
环境检查脚本
检查 MarketBrew 运行所需的所有依赖
"""

import sys
import subprocess

print("=" * 60)
print("🔍 MarketBrew 环境检查")
print("=" * 60)
print()

# 检查 Python 版本
print("[1/5] 检查 Python 版本...")
version = sys.version_info
print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
if version.major < 3 or (version.major == 3 and version.minor < 7):
    print("⚠️  警告: 建议使用 Python 3.7 或更高版本")
print()

# 检查必需的包
print("[2/5] 检查依赖包...")
required_packages = {
    'flask': 'Flask',
    'flask_cors': 'Flask-CORS',
    'requests': 'Requests',
}

missing_packages = []
for module_name, package_name in required_packages.items():
    try:
        __import__(module_name)
        print(f"✅ {package_name} 已安装")
    except ImportError:
        print(f"❌ {package_name} 未安装")
        missing_packages.append(package_name.lower())

print()

# 检查可选包
print("[3/5] 检查可选依赖...")
optional_packages = {
    'pandas': 'Pandas',
    'numpy': 'NumPy',
}

for module_name, package_name in optional_packages.items():
    try:
        __import__(module_name)
        print(f"✅ {package_name} 已安装")
    except ImportError:
        print(f"⚠️  {package_name} 未安装（可选）")

print()

# 检查关键文件
print("[4/5] 检查关键文件...")
import os
files_to_check = [
    'price_service.py',
    'market_temperature.html',
    'eastmoney_data_service.py',
]

for filename in files_to_check:
    if os.path.exists(filename):
        print(f"✅ {filename}")
    else:
        print(f"❌ {filename} 不存在")

print()

# 检查端口占用
print("[5/5] 检查端口 5000...")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', 5000))
sock.close()

if result == 0:
    print("⚠️  端口 5000 已被占用")
    print("   提示: 可能服务已在运行，或被其他程序占用")
else:
    print("✅ 端口 5000 可用")

print()
print("=" * 60)

# 总结
if missing_packages:
    print("❌ 环境检查未通过")
    print()
    print("需要安装以下依赖:")
    print(f"   pip install {' '.join(missing_packages)}")
    print()
    print("或一键安装:")
    print("   pip install flask flask-cors requests")
else:
    print("✅ 环境检查通过！")
    print()
    print("可以启动服务:")
    print("   1. 双击运行: 启动服务.bat")
    print("   2. 或手动运行: python price_service.py")
    print("   3. 然后打开: 市场温度计.html")

print("=" * 60)
