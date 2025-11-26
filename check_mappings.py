#!/usr/bin/env python3
import requests
from batch_optimized_decision_engine import BatchOptimizedDecisionEngine

engine = BatchOptimizedDecisionEngine()

# 测试更多股票代码
test_codes = ['000063', '000333', '000651', '000725', '000776', '002594', '600000', '600030', '601318', '601398',
              '000568', '000895', '002415', '002594', '300014', '300059', '688001', '688012']

print('检查股票名称映射准确性:')
print(f'{"代码":<8}{"映射名称":<15}{"API名称":<15}{"匹配":<5}{"价格":<10}')
print('-' * 70)

errors = []

for code in test_codes:
    mapped_name = engine.get_stock_name(code)
    
    try:
        response = requests.get(f'http://localhost:5002/api/stock/{code}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            api_name = data.get('name', '未知')
            price = data.get('current_price', 0)
            
            # 检查是否匹配（忽略空格和特殊字符）
            clean_mapped = mapped_name.replace(' ', '').replace('A', '').replace('Ａ', '')
            clean_api = api_name.replace(' ', '').replace('A', '').replace('Ａ', '')
            
            if clean_mapped == clean_api:
                match = '✅'
            else:
                match = '❌'
                errors.append({
                    'code': code,
                    'mapped': mapped_name,
                    'api': api_name,
                    'price': price
                })
            
            print(f'{code:<8}{mapped_name:<15}{api_name:<15}{match:<5}¥{price:<9.2f}')
                
        else:
            print(f'{code:<8}{mapped_name:<15}{"获取失败":<15}❌   {"N/A":<10}')
            
    except Exception as e:
        print(f'{code:<8}{mapped_name:<15}{"连接错误":<15}❌   {"N/A":<10}')

if errors:
    print(f'\n发现 {len(errors)} 个映射错误:')
    for error in errors:
        print(f'  {error["code"]}: 映射="{error["mapped"]}" vs API="{error["api"]}" (¥{error["price"]:.2f})')
else:
    print('\n✅ 所有检查的股票名称映射都正确!')