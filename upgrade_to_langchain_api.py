#!/usr/bin/env python3
"""
批量升级脚本：将所有调用升级为LangChain增强版API
"""

import os
import glob
import re

def upgrade_file_api_calls(file_path):
    """升级单个文件的API调用"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 升级个股分析API
        if '/api/stock-analysis' in content and '/api/langchain/stock-analysis' not in content:
            content = content.replace('/api/stock-analysis', '/api/langchain/stock-analysis')
            modified = True
            print(f"  📊 升级个股分析API: {os.path.basename(file_path)}")
        
        # 升级市场分析API 
        if '/api/market-analysis' in content and '/api/langchain/market-analysis' not in content:
            content = content.replace('/api/market-analysis', '/api/langchain/market-analysis')
            modified = True
            print(f"  🏪 升级市场分析API: {os.path.basename(file_path)}")
        
        # 如果有修改，写回文件
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
        return False
        
    except Exception as e:
        print(f"  ❌ 处理文件失败 {file_path}: {e}")
        return False

def main():
    print("🚀 MarketBrew API升级工具")
    print("=" * 60)
    print("将所有调用升级为LangChain增强版API...")
    print()
    
    # 要升级的文件类型
    file_patterns = [
        "*.py",
        "*.html", 
        "*.js"
    ]
    
    total_files = 0
    upgraded_files = 0
    
    for pattern in file_patterns:
        print(f"🔍 搜索 {pattern} 文件...")
        
        # 搜索当前目录下的文件
        files = glob.glob(f"/Users/aaron/Marketbrew/{pattern}")
        files.extend(glob.glob(f"/Users/aaron/Marketbrew/**/{pattern}", recursive=True))
        
        # 过滤掉虚拟环境和缓存目录
        files = [f for f in files if not any(x in f for x in ['venv/', '__pycache__/', '.git/', 'node_modules/'])]
        
        for file_path in files:
            total_files += 1
            if upgrade_file_api_calls(file_path):
                upgraded_files += 1
    
    print()
    print("✅ 升级完成！")
    print(f"📁 检查文件总数: {total_files}")
    print(f"🔄 升级文件数量: {upgraded_files}")
    print()
    
    if upgraded_files > 0:
        print("🎯 升级效果:")
        print("• 所有API调用已切换为LangChain增强版")
        print("• 现在将获得专业级投资分析") 
        print("• 告别'60分持有'的模板化分析")
        print()
        print("📋 下一步:")
        print("1. 重启相关服务以应用更改")
        print("2. 测试界面功能确认升级成功")
    else:
        print("✅ 所有文件都已是最新版本，无需升级")

if __name__ == "__main__":
    main()