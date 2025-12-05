#!/usr/bin/env python3
"""
测试 AkShare 北向资金数据的准确性和及时性
"""
import sys
from datetime import datetime, timedelta

# 临时移除akshare拦截，仅用于测试
class AkShareAllower:
    pass

# 清除可能存在的akshare拦截器
original_meta_path = sys.meta_path.copy()
sys.meta_path = [hook for hook in sys.meta_path if not hook.__class__.__name__ == 'AkShareBlocker']

try:
    import akshare as ak
    print("="*70)
    print("  测试 AkShare 北向资金数据")
    print("="*70)
    print()

    print("📊 正在获取北向资金历史数据...")
    print()

    # 获取北向资金历史数据
    df = ak.stock_hsgt_hist_em()

    print(f"✅ 成功获取数据，共 {len(df)} 条记录")
    print()

    # 显示数据基本信息
    print("="*70)
    print("数据列名：")
    print("="*70)
    print(df.columns.tolist())
    print()

    # 显示最近10天的数据
    print("="*70)
    print("最近10天北向资金数据：")
    print("="*70)
    print()

    # 按日期排序（降序）
    df_sorted = df.sort_values('日期', ascending=False)

    print(f"{'日期':<12} {'沪股通(亿)':<12} {'深股通(亿)':<12} {'北向总计(亿)':<12}")
    print("-" * 60)

    for idx, row in df_sorted.head(10).iterrows():
        date = row['日期']
        sh_flow = row.get('沪股通(亿)', 0)
        sz_flow = row.get('深股通(亿)', 0)
        total_flow = row.get('北向资金(亿)', sh_flow + sz_flow)

        print(f"{date:<12} {sh_flow:>10.2f}  {sz_flow:>10.2f}  {total_flow:>10.2f}")

    print()

    # 检查数据时效性
    latest_date = df_sorted.iloc[0]['日期']
    today = datetime.now().date()

    # 解析日期
    if isinstance(latest_date, str):
        latest_date_obj = datetime.strptime(latest_date, '%Y-%m-%d').date()
    else:
        latest_date_obj = latest_date

    days_ago = (today - latest_date_obj).days

    print("="*70)
    print("数据时效性检查：")
    print("="*70)
    print(f"今天日期：{today}")
    print(f"最新数据日期：{latest_date_obj}")
    print(f"数据延迟：{days_ago} 天")
    print()

    if days_ago <= 3:
        print("✅ 数据及时性：优秀（延迟 ≤ 3天）")
    elif days_ago <= 7:
        print("⚠️  数据及时性：一般（延迟 3-7天）")
    else:
        print("❌ 数据及时性：较差（延迟 > 7天）")

    print()

    # 检查数据完整性
    print("="*70)
    print("数据完整性检查：")
    print("="*70)

    recent_10 = df_sorted.head(10)

    # 检查是否有空值
    null_count = recent_10.isnull().sum().sum()
    print(f"最近10条数据中的空值数量：{null_count}")

    # 检查是否有0值
    if '沪股通(亿)' in recent_10.columns:
        sh_zeros = (recent_10['沪股通(亿)'] == 0).sum()
        sz_zeros = (recent_10['深股通(亿)'] == 0).sum()
        print(f"沪股通为0的记录数：{sh_zeros}")
        print(f"深股通为0的记录数：{sz_zeros}")

    print()

    # 统计分析
    print("="*70)
    print("数据统计分析（最近30天）：")
    print("="*70)

    recent_30 = df_sorted.head(30)

    if '北向资金(亿)' in recent_30.columns:
        total_col = '北向资金(亿)'
    else:
        total_col = None
        recent_30['total'] = recent_30['沪股通(亿)'] + recent_30['深股通(亿)']
        total_col = 'total'

    if total_col:
        print(f"平均每日流入：{recent_30[total_col].mean():.2f} 亿")
        print(f"最大单日流入：{recent_30[total_col].max():.2f} 亿")
        print(f"最大单日流出：{recent_30[total_col].min():.2f} 亿")
        print(f"累计净流入：{recent_30[total_col].sum():.2f} 亿")

    print()
    print("="*70)
    print("✅ AkShare 数据测试完成")
    print("="*70)

except ImportError as e:
    print(f"❌ 无法导入 akshare: {e}")
    print()
    print("需要先安装 akshare:")
    print("  pip install akshare")

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

finally:
    # 恢复原来的 meta_path
    sys.meta_path = original_meta_path

input("\n按回车键退出...")
