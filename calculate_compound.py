#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复利计算器 - 计算 2020-2026 年复利累计收益
"""

# 月度收益率数据（从回测结果整理）
monthly_returns = {
    # 2020 年
    '2020-01': 1.0533,
    '2020-02': 1.9403,
    '2020-03': 5.2981,
    '2020-04': 1.8983,
    '2020-05': 1.9573,
    '2020-06': 1.2305,
    '2020-07': 3.0441,
    '2020-08': 2.4921,
    '2020-09': 1.9128,
    '2020-10': 1.9804,
    '2020-11': 1.5648,
    '2020-12': 0.00,  # 无信号
    
    # 2021 年
    '2021-01': 2.2905,
    '2021-02': 1.1968,
    '2021-03': 2.4674,
    '2021-04': 1.0839,
    '2021-05': 1.4011,
    '2021-06': 1.8660,
    '2021-07': 5.1168,
    '2021-08': 0.5609,
    '2021-09': 1.7749,
    '2021-10': 0.6070,
    '2021-11': 0.6520,
    '2021-12': 1.2497,
    
    # 2022 年
    '2022-01': 1.6538,
    '2022-02': 1.0086,
    '2022-03': 4.9374,
    '2022-04': 2.6006,
    '2022-05': 3.0107,
    '2022-06': 2.9083,
    '2022-07': 1.5479,
    '2022-08': 0.4250,
    '2022-09': 1.5355,
    '2022-10': 3.4837,
    '2022-11': 1.7612,
    '2022-12': 1.0746,
    
    # 2023 年
    '2023-01': 0.4634,
    '2023-02': -0.0125,  # 亏损
    '2023-03': 0.4206,
    '2023-04': 0.2235,
    '2023-05': 0.00,  # 无信号
    '2023-06': -0.0108,  # 亏损
    '2023-07': 0.8517,
    '2023-08': 0.3850,
    '2023-09': 0.00,  # 无信号
    '2023-10': 1.0832,
    '2023-11': 1.1375,
    '2023-12': 0.3327,
    
    # 2024 年
    '2024-01': 1.2387,
    '2024-02': 1.9143,
    '2024-03': 0.7106,
    '2024-04': 0.4752,
    '2024-05': 0.3469,
    '2024-06': 0.9944,
    '2024-07': 1.2663,
    '2024-08': 0.8833,
    '2024-09': 1.9602,
    '2024-10': 2.0034,
    '2024-11': 1.7610,
    '2024-12': 0.3960,
    
    # 2025 年
    '2025-01': 3.4654,
    '2025-02': 0.8214,
    '2025-03': 1.6622,
    '2025-04': 2.4906,
    '2025-05': 1.1605,
    '2025-06': 0.00,  # 无信号
    '2025-07': 0.00,  # 无信号
    '2025-08': 2.5005,
    '2025-09': 1.7052,
    '2025-10': 5.9715,
    '2025-11': 3.4899,
    '2025-12': 1.1920,
    
    # 2026 年 Q1
    '2026-01': 3.1619,
    '2026-02': 3.1358,
    '2026-03': 6.3160,
}

def calculate_compound():
    """计算复利累计收益"""
    initial_capital = 100000
    capital = initial_capital
    
    print("="*80)
    print(" " * 30 + "2020-2026 年复利累计收益计算")
    print("="*80)
    print(f"初始资金：¥{initial_capital:,.2f}")
    print(f"回测期间：2020-01 至 2026-03 (75 个月)")
    print("="*80)
    print()
    
    # 按年汇总
    yearly_data = {}
    monthly_compound = initial_capital
    
    for month, return_rate in sorted(monthly_returns.items()):
        year = month[:4]
        
        if return_rate == 0:
            # 无信号月份，资金不变
            continue
        
        # 计算当月收益
        month_profit = capital * return_rate
        capital += month_profit
        
        if year not in yearly_data:
            yearly_data[year] = {
                'start': capital - month_profit,
                'end': capital,
                'profit': month_profit,
                'return': return_rate,
                'months': []
            }
        else:
            yearly_data[year]['end'] = capital
            yearly_data[year]['profit'] += month_profit
            yearly_data[year]['months'].append(return_rate)
        
        monthly_compound = capital
    
    # 打印年度汇总
    print("\n📊 年度复利汇总")
    print("-"*80)
    print(f"{'年份':<8} {'年初资金':<15} {'年末资金':<15} {'年收益':<15} {'年收益率':<10}")
    print("-"*80)
    
    total_profit = 0
    for year in sorted(yearly_data.keys()):
        data = yearly_data[year]
        year_profit = data['end'] - data['start']
        year_return = year_profit / data['start'] * 100
        total_profit += year_profit
        
        print(f"{year:<8} ¥{data['start']:>12,.2f} ¥{data['end']:>12,.2f} ¥{year_profit:>12,.2f} {year_return:>9.2f}%")
    
    print("-"*80)
    print(f"{'总计':<8} ¥{initial_capital:>12,.2f} ¥{capital:>12,.2f} ¥{total_profit:>12,.2f} {(capital/initial_capital-1)*100:>9.2f}%")
    print()
    
    # 最终结果
    print("\n" + "="*80)
    print(" " * 35 + "最终结果")
    print("="*80)
    print(f"初始资金：     ¥{initial_capital:,.2f}")
    print(f"最终资金：     ¥{capital:,.2f}")
    print(f"累计收益：     ¥{total_profit:,.2f}")
    print(f"累计收益率：   {(capital/initial_capital-1)*100:,.2f}%")
    print(f"资金倍数：     {capital/initial_capital:,.2f} 倍")
    print(f"回测月数：     75 个月 (2020-01 至 2026-03)")
    print(f"年化收益率：   {(capital/initial_capital)**(12/75)-1:,.2f}%")
    print("="*80)
    
    # 里程碑
    print("\n📈 重要里程碑")
    print("-"*80)
    
    milestones = [
        (2, "翻倍"),
        (5, "5 倍"),
        (10, "10 倍"),
        (50, "50 倍"),
        (100, "100 倍"),
        (500, "500 倍"),
        (1000, "1000 倍"),
    ]
    
    compound = initial_capital
    achieved = []
    
    for month, (target_multiple, label) in zip(sorted(monthly_returns.keys()), 
                                                 [monthly_returns[k] for k in sorted(monthly_returns.keys())]):
        if target_multiple == 0:
            continue
        compound *= (1 + target_multiple)
        
        for multiple, milestone_label in milestones:
            if compound >= initial_capital * multiple and multiple not in [a[0] for a in achieved]:
                achieved.append((multiple, month, milestone_label))
    
    for multiple, month, label in achieved[:10]:  # 只显示前 10 个里程碑
        print(f"{label}: {month} (资金达到 ¥{initial_capital*multiple:,.0f})")
    
    return capital, total_profit


if __name__ == "__main__":
    calculate_compound()
