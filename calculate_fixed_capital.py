#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
固定本金复利计算 - 每月投入 10 万，利润取出，亏损补足
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


def calculate_fixed_capital():
    """
    计算固定本金模式下的总利润
    
    规则:
    - 每月固定投入 10 万元
    - 当月利润取出，不计入下月本金
    - 当月亏损，补足到 10 万
    - 始终维持 10 万/月的投入
    """
    monthly_capital = 100000  # 每月固定投入
    
    print("="*80)
    print(" " * 25 + "固定本金模式收益计算")
    print(" " * 20 + "(每月 10 万，利润取出，亏损补足)")
    print("="*80)
    print(f"每月投入：¥{monthly_capital:,.2f}")
    print(f"回测期间：2020-01 至 2026-03 (75 个月)")
    print(f"总投入本金：¥{monthly_capital * 75:,.2f}")
    print("="*80)
    print()
    
    total_profit = 0
    total_loss = 0
    profitable_months = 0
    losing_months = 0
    no_signal_months = 0
    
    yearly_summary = {}
    monthly_details = []
    
    for month, return_rate in sorted(monthly_returns.items()):
        year = month[:4]
        
        if return_rate == 0:
            # 无信号月份
            no_signal_months += 1
            profit = 0
            status = "无信号"
        elif return_rate > 0:
            # 盈利月份
            profitable_months += 1
            profit = monthly_capital * return_rate
            total_profit += profit
            status = "盈利"
        else:
            # 亏损月份
            losing_months += 1
            profit = monthly_capital * return_rate  # 负数
            total_loss += abs(profit)
            total_profit += profit  # 减去亏损
            status = "亏损"
        
        # 年度汇总
        if year not in yearly_summary:
            yearly_summary[year] = {
                'profit': 0,
                'months': 0,
                'profitable': 0,
                'losing': 0,
                'no_signal': 0
            }
        
        yearly_summary[year]['profit'] += profit
        yearly_summary[year]['months'] += 1
        if status == "盈利":
            yearly_summary[year]['profitable'] += 1
        elif status == "亏损":
            yearly_summary[year]['losing'] += 1
        else:
            yearly_summary[year]['no_signal'] += 1
        
        monthly_details.append({
            'month': month,
            'return': return_rate,
            'profit': profit,
            'status': status
        })
    
    # 打印年度汇总
    print("📊 年度收益汇总")
    print("-"*80)
    print(f"{'年份':<8} {'投入月数':<10} {'盈利月':<8} {'亏损月':<8} {'无信号':<8} {'年利润':<15}")
    print("-"*80)
    
    for year in sorted(yearly_summary.keys()):
        data = yearly_summary[year]
        print(f"{year:<8} {data['months']:<10} {data['profitable']:<8} {data['losing']:<8} "
              f"{data['no_signal']:<8} ¥{data['profit']:>12,.2f}")
    
    print("-"*80)
    
    # 总投入
    total_investment = monthly_capital * 75
    total_months = profitable_months + losing_months + no_signal_months
    
    # 最终结果
    print("\n" + "="*80)
    print(" " * 35 + "最终结果")
    print("="*80)
    print(f"回测期间：        2020-01 至 2026-03 (75 个月)")
    print(f"每月固定投入：    ¥{monthly_capital:,.2f}")
    print(f"总投入本金：      ¥{total_investment:,.2f}")
    print(f"累计总利润：      ¥{total_profit:,.2f}")
    print(f"净利润率：        {total_profit/total_investment*100:,.2f}%")
    print(f"平均月利润：      ¥{total_profit/75:,.2f}")
    print(f"投入产出比：      1:{total_profit/total_investment:.2f}")
    print("="*80)
    
    print("\n📈 交易统计")
    print("-"*80)
    print(f"总月份数：        {total_months} 个月")
    print(f"盈利月份：        {profitable_months} 个月 ({profitable_months/total_months*100:.1f}%)")
    print(f"亏损月份：        {losing_months} 个月 ({losing_months/total_months*100:.1f}%)")
    print(f"无信号月份：      {no_signal_months} 个月 ({no_signal_months/total_months*100:.1f}%)")
    print(f"总盈利：          ¥{total_profit:,.2f}")
    print(f"总亏损：          ¥{total_loss:,.2f}")
    print(f"净盈利：          ¥{total_profit:,.2f}")
    print("-"*80)
    
    # 最佳/最差月份
    print("\n🏆 最佳/最差月份")
    print("-"*80)
    
    best_month = max(monthly_details, key=lambda x: x['profit'])
    worst_month = min(monthly_details, key=lambda x: x['profit'])
    
    print(f"最佳月份：        {best_month['month']} (收益率 {best_month['return']*100:.2f}%, 利润 ¥{best_month['profit']:,.2f})")
    print(f"最差月份：        {worst_month['month']} (收益率 {worst_month['return']*100:.2f}%, 利润 ¥{worst_month['profit']:,.2f})")
    print("-"*80)
    
    # 年度最佳
    print("\n📊 年度排名")
    print("-"*80)
    sorted_years = sorted(yearly_summary.items(), key=lambda x: x[1]['profit'], reverse=True)
    
    for i, (year, data) in enumerate(sorted_years[:5], 1):
        print(f"{i}. {year}: ¥{data['profit']:,.2f} ({data['profitable']}盈/{data['losing']}亏/{data['no_signal']}无信号)")
    
    print("-"*80)
    
    # 如果利润再投资的对比
    print("\n💡 对比：如果利润再投资（复利模式）")
    print("-"*80)
    compound_capital = monthly_capital
    compound_profit = 0
    
    for month, return_rate in sorted(monthly_returns.items()):
        if return_rate == 0:
            continue
        month_profit = compound_capital * return_rate
        compound_capital += month_profit
        compound_profit += month_profit
    
    print(f"固定本金模式：    总利润 ¥{total_profit:,.2f}")
    print(f"复利模式：        最终资金 ¥{compound_capital:,.2f} (利润 ¥{compound_profit:,.2f})")
    print(f"差异：            复利多 ¥{compound_capital - total_profit - monthly_capital:,.2f}")
    print("-"*80)
    
    return total_profit, total_investment


if __name__ == "__main__":
    calculate_fixed_capital()
