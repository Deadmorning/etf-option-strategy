#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量回测脚本 - 按年/月批量回测

使用方法:
    python batch_backtest.py --year 2025 --capital 100000
"""

import subprocess
import sys
import pandas as pd
from datetime import datetime
import os

def backtest_month(year: int, month: int, capital: float):
    """回测单个月份"""
    start_date = f"{year}{month:02d}01"
    
    # 计算月末
    if month == 12:
        end_date = f"{year}1231"
    else:
        # 下个月 1 日减 1 天
        import calendar
        _, last_day = calendar.monthrange(year, month)
        end_date = f"{year}{month:02d}{last_day:02d}"
    
    print(f"\n{'='*60}")
    print(f"回测 {year}年{month}月：{start_date} - {end_date}")
    print(f"{'='*60}")
    
    cmd = [
        sys.executable, "run_backtest.py",
        "--start", start_date,
        "--end", end_date,
        "--capital", str(capital),
        "--output", "reports/batch"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 解析结果
    output = result.stdout + result.stderr
    lines = output.split('\n')
    
    metrics = {}
    for line in lines:
        if '总收益率:' in line:
            metrics['total_return'] = line.split(':')[1].strip().replace('%', '')
        elif '最终资金:' in line:
            metrics['final_capital'] = line.split(':')[1].strip().replace('¥', '').replace(',', '')
        elif '总交易笔数:' in line:
            metrics['total_trades'] = line.split(':')[1].strip()
        elif '胜率:' in line and '盈亏比' not in line:
            metrics['win_rate'] = line.split(':')[1].strip().replace('%', '')
        elif '盈亏比:' in line:
            metrics['profit_loss_ratio'] = line.split(':')[1].strip()
        elif '最大回撤:' in line:
            metrics['max_drawdown'] = line.split(':')[1].strip().replace('%', '')
        elif '夏普比率:' in line:
            metrics['sharpe_ratio'] = line.split(':')[1].strip()
    
    return metrics


def main():
    import argparse
    parser = argparse.ArgumentParser(description="批量回测")
    parser.add_argument("--year", type=int, default=2025, help="回测年份")
    parser.add_argument("--capital", type=float, default=100000, help="初始资金")
    
    args = parser.parse_args()
    
    print(f"\n{'='*80}")
    print(f" " * 30 + f"{args.year}年 全年回测")
    print(f"{'='*80}")
    print(f"初始资金：¥{args.capital:,.2f}")
    print(f"交易费用：¥5 元/张")
    print(f"{'='*80}")
    
    # 创建输出目录
    os.makedirs("reports/batch", exist_ok=True)
    
    all_results = []
    
    for month in range(1, 13):
        metrics = backtest_month(args.year, month, args.capital)
        
        result = {
            'month': f"{args.year}-{month:02d}",
            **metrics
        }
        all_results.append(result)
        
        # 打印月度结果
        print(f"\n{args.year}-{month:02d}: "
              f"收益率={metrics.get('total_return', 'N/A')}%, "
              f"资金=¥{metrics.get('final_capital', 'N/A')}, "
              f"交易={metrics.get('total_trades', 'N/A')}笔，"
              f"胜率={metrics.get('win_rate', 'N/A')}%")
    
    # 汇总结果
    print(f"\n{'='*80}")
    print(f" " * 35 + f"{args.year}年 全年汇总")
    print(f"{'='*80}")
    
    df = pd.DataFrame(all_results)
    
    # 保存 CSV
    output_file = f"reports/batch/{args.year}_full_year.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 打印汇总表
    print(f"\n{df.to_string(index=False)}")
    print(f"\n✅ 汇总报告已保存至：{output_file}")
    
    # 计算全年总计
    if not df.empty:
        print(f"\n📊 全年统计:")
        
        # 有数据的月份
        months_with_data = len(df[df['total_return'].notna()])
        print(f"   回测月份：{months_with_data}/12")
        
        # 平均收益率（仅正收益月份）
        positive_months = df[df['total_return'].notna()]['total_return'].astype(float)
        if len(positive_months) > 0:
            avg_return = positive_months.mean()
            print(f"   平均月收益率：{avg_return:.2f}%")
        
        # 胜率统计
        win_rate = df[df['win_rate'].notna()]['win_rate'].astype(float)
        if len(win_rate) > 0:
            avg_win_rate = win_rate.mean()
            print(f"   平均胜率：{avg_win_rate:.2f}%")


if __name__ == "__main__":
    main()
