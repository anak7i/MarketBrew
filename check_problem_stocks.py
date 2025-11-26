#!/usr/bin/env python3
import requests
from batch_optimized_decision_engine import BatchOptimizedDecisionEngine

engine = BatchOptimizedDecisionEngine()

# 检查000839周围的股票代码，看是否有其他错误映射
nearby_codes = ['000838', '000839', '000840', '000841', '000842']

# 还有一些随机的股票
random_codes = ['000001', '000002', '300001', '300002', '600001', '600002', 
                '688001', '688002', '301001', '301002']

all_codes = nearby_codes + random_codes

print('检查可能有问题的股票映射:')
print(f'{"代码":<8}{"映射名称":<15}{"API名称":<15}{"匹配":<5}{"价格":<10}')
print('-' * 70)

errors = []
correct = 0

for code in all_codes:
    mapped_name = engine.get_stock_name(code)
    
    try:
        response = requests.get(f'http://localhost:5002/api/stock/{code}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            api_name = data.get('name', '未知')
            price = data.get('current_price', 0)
            
            # 检查是否匹配（更严格的检查）
            if mapped_name.startswith('股票'):
                # 如果我们的映射是"股票XXXXXX"格式，说明没有找到真实名称
                match = '⚠️'
                print(f'{code:<8}{mapped_name:<15}{api_name:<15}{match:<5}¥{price:<9.2f}')
                errors.append({
                    'code': code,
                    'mapped': mapped_name,
                    'api': api_name,
                    'price': price,
                    'type': 'missing_mapping'
                })
            else:
                # 有真实映射，检查是否正确
                clean_mapped = mapped_name.replace(' ', '').replace('A', '').replace('Ａ', '')
                clean_api = api_name.replace(' ', '').replace('A', '').replace('Ａ', '')
                
                if clean_mapped == clean_api:
                    match = '✅'
                    correct += 1
                else:
                    match = '❌'
                    errors.append({
                        'code': code,
                        'mapped': mapped_name,
                        'api': api_name,
                        'price': price,
                        'type': 'wrong_mapping'
                    })
                
                print(f'{code:<8}{mapped_name:<15}{api_name:<15}{match:<5}¥{price:<9.2f}')
                
        else:
            print(f'{code:<8}{mapped_name:<15}{"获取失败":<15}❌   {"N/A":<10}')
            
    except Exception as e:
        print(f'{code:<8}{mapped_name:<15}{"连接错误":<15}❌   {"N/A":<10}')

print(f'\n总结: 检查了{len(all_codes)}只股票')
print(f'✅ 正确映射: {correct}只')
print(f'❌ 错误映射: {len([e for e in errors if e["type"] == "wrong_mapping"])}只')  
print(f'⚠️  缺失映射: {len([e for e in errors if e["type"] == "missing_mapping"])}只')

if errors:
    print(f'\n问题详情:')
    for error in errors:
        if error['type'] == 'wrong_mapping':
            print(f'  错误映射 {error["code"]}: "{error["mapped"]}" 应该是 "{error["api"]}"')
        else:
            print(f'  缺失映射 {error["code"]}: 应该添加映射到 "{error["api"]}"')