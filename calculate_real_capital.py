#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际本金投入计算 - 利润再投入模式

规则:
- 第 1 个月：投入 10 万本金
- 之后每月：优先使用上月利润投入，不足才追加本金
- 利润取出：指超过 10 万的部分
"""

monthly_returns = {
    '2020-01': 1.0533, '2020-02': 1.9403, '2020-03': 5.2981, '2020-04': 1.8983,
    '2020-05': 1.9573, '2020-06': 1.2305, '2020-07': 3.0441, '2020-08': 2.4921,
    '2020-09': 1.9128, '2020-10': 1.9804, '2020-11': 1.5648, '2020-12': 0.00,
    '2021-01': 2.2905, '2021-02': 1.1968, '2021-03': 2.4674, '2021-04': 1.0839,
    '2021-05': 1.4011, '2021-06': 1.8660, '2021-07': 5.1168, '2021-08': 0.5609,
    '2021-09': 1.7749, '2021-10': 0.6070, '2021-11': 0.6520, '2021-12': 1.2497,
    '2022-01': 1.6538, '2022-02': 1.0086, '2022-03': 4.9374, '2022-04': 2.6006,
    '2022-05': 3.0107, '2022-06': 2.9083, '2022-07': 1.5479, '2022-08': 0.4250,
    '2022-09': 1.5355, '2022-10': 3.4837, '2022-11': 1.7612, '2022-12': 1.0746,
    '2023-01': 0.4634, '2023-02': -0.0125, '2023-03': 0.4206, '2023-04': 0.2235,
    '2023-05': 0.00, '2023-06': -0.0108, '2023-07': 0.8517, '2023-08': 0.3850,
    '2023-09': 0.00, '2023-10': 1.0832, '2023-11': 1.1375, '2023-12': 0.3327,
    '2024-01': 1.2387, '2024-02': 1.9143, '2024-03': 0.7106, '2024-04': 0.4752,
    '2024-05': 0.3469, '2024-06': 0.9944, '2024-07': 1.2663, '2024-08': 0.8833,
    '2024-09': 1.9602, '2024-10': 2.0034, '2024-11': 1.7610, '2024-12': 0.3960,
    '2025-01': 3.4654, '2025-02': 0.8214, '2025-03': 1.6622, '2025-04': 2.4906,
    '2025-05': 1.1605, '2025-06': 0.00, '2025-07': 0.00, '2025-08': 2.5005,
    '2025-09': 1.7052, '2025-10': 5.9715, '2025-11': 3.4899, '2025-12': 1.1920,
    '2026-01': 3.1619, '2026-02': 3.1358, '2026-03': 6.3160,
}


def calculate_real_capital():
    """计算实际投入本金和真实收益"""
    
    print("="*80)
    print(" " * 25 + "实际本金投入收益计算")
    print(" " * 20 + "(利润再投入，不足才追加本金)")
    print("="*80)
    print()
    
    initial_capital = 100000  # 第 1 个月投入
    required_monthly = 100000  # 每月需要投入的固定金额
    
    total_capital_invested = initial_capital  # 实际投入的总本金
    total_profit_withdrawn = 0  # 累计取出的利润
    additional_capital = 0  # 额外追加的本金
    current_capital = initial_capital  # 当前可用资金
    
    monthly_details = []
    yearly_summary = {}
    
    for i, (month, return_rate) in enumerate(sorted(monthly_returns.items())):
        year = month[:4]
        
        if return_rate == 0:
            # 无信号月份
            profit = 0
            withdrawn = 0
            added = 0
            status = "无信号"
            # 仍需投入 10 万
            if current_capital < required_monthly:
                needed = required_monthly - current_capital
                additional_capital += needed
                total_capital_invested += needed
                current_capital = required_monthly
                added = needed
        else:
            # 计算当月收益
            profit = current_capital * return_rate
            end_capital = current_capital + profit
            
            # 取出利润（保留 10 万作为下月本金）
            if end_capital > required_monthly:
                withdrawn = end_capital - required_monthly
                current_capital = required_monthly
                status = "盈利"
            elif end_capital < required_monthly:
                # 亏损，需要补足
                needed = required_monthly - end_capital
                additional_capital += needed
                total_capital_invested += needed
                current_capital = required_monthly
                added = needed
                withdrawn = 0
                status = "亏损"
            else:
                withdrawn = 0
                status = "保本"
        
        total_profit_withdrawn += withdrawn
        
        # 年度汇总
        if year not in yearly_summary:
            yearly_summary[year] = {
                'profit': 0, 'withdrawn': 0, 'added': 0, 'months': 0
            }
        yearly_summary[year]['profit'] += profit
        yearly_summary[year]['withdrawn'] += withdrawn
        yearly_summary[year]['added'] += added if 'added' in dir() else 0
        yearly_summary[year]['months'] += 1
        
        monthly_details.append({
            'month': month,
            'return': return_rate,
            'profit': profit,
            'withdrawn': withdrawn,
            'added': added if 'added' in dir() else 0,
            'status': status
        })
        
        added = 0  # 重置
    
    # 打印年度汇总
    print("📊 年度资金汇总")
    print("-"*80)
    print(f"{'年份':<8} {'月数':<6} {'当月收益':<12} {'取出利润':<12} {'追加本金':<12}")
    print("-"*80)
    
    for year in sorted(yearly_summary.keys()):
        data = yearly_summary[year]
        print(f"{year:<8} {data['months']:<6} ¥{data['profit']:>10,.0f} ¥{data['withdrawn']:>10,.0f} ¥{data['added']:>10,.0f}")
    
    print("-"*80)
    
    # 最终结果
    months = len(monthly_details)
    years = months / 12
    
    print("\n" + "="*80)
    print(" " * 35 + "最终结果")
    print("="*80)
    print(f"回测期间：        {months} 个月 ({years:.1f} 年)")
    print(f"初始投入本金：    ¥{initial_capital:,.2f}")
    print(f"累计追加本金：    ¥{additional_capital:,.2f}")
    print(f"实际总投入：      ¥{total_capital_invested:,.2f}")
    print(f"累计取出利润：    ¥{total_profit_withdrawn:,.2f}")
    print(f"净利润：          ¥{total_profit_withdrawn - additional_capital:,.2f}")
    print(f"净利润率：        {(total_profit_withdrawn - additional_capital)/total_capital_invested*100:,.2f}%")
    print(f"年化收益率：      {((total_profit_withdrawn/total_capital_invested)**(1/years)-1)*100:,.2f}%")
    print(f"投入产出比：      1:{total_profit_withdrawn/total_capital_invested:.2f}")
    print("="*80)
    
    # 对比
    print("\n💡 两种计算方式对比")
    print("-"*80)
    print(f"{'':<20} {'固定投入模式':<20} {'利润再投模式':<20}")
    print("-"*80)
    print(f"{'总投入本金':<20} {'¥750 万':<20} {'¥{:.0f}万'.format(total_capital_invested/10000):<20}")
    print(f"{'总利润':<20} {'¥1,265 万':<20} {'¥{:.0f}万'.format(total_profit_withdrawn/10000):<20}")
    print(f"{'净利润':<20} {'¥1,265 万':<20} {'¥{:.0f}万'.format((total_profit_withdrawn-additional_capital)/10000):<20}")
    print(f"{'净利润率':<20} {'168.65%':<20} {'{:.2f}%'.format((total_profit_withdrawn-additional_capital)/total_capital_invested*100):<20}")
    print(f"{'年化收益率':<20} {'~24%':<20} {'{:.2f}%'.format(((total_profit_withdrawn/total_capital_invested)**(1/years)-1)*100):<20}")
    print("-"*80)
    
    return total_capital_invested, total_profit_withdrawn, additional_capital


if __name__ == "__main__":
    calculate_real_capital()
