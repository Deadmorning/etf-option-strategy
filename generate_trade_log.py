#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细交易日志生成器 - 分析每笔交易

使用方法:
    python generate_trade_log.py --start 20260301 --end 20260331 --capital 100000
"""

import argparse
import logging
import sys
import pandas as pd
from datetime import datetime
from backtester import Backtester
from analyzer import PerformanceAnalyzer
import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


def generate_trade_log(start_date: str, end_date: str, capital: float):
    """生成详细交易日志"""
    
    # 创建回测引擎
    backtester = Backtester(
        start_date=start_date,
        end_date=end_date,
        initial_capital=capital
    )
    
    # 加载数据
    if not backtester.load_data():
        logger.error("数据加载失败")
        return
    
    # 执行回测
    daily_results = backtester.run_backtest()
    
    if daily_results.empty:
        logger.error("回测结果为空")
        return
    
    # 获取交易记录
    daily_df, trades_df = backtester.get_results()
    
    # 生成详细日志
    print("\n" + "="*100)
    print(" " * 30 + "2026 年 3 月 详细交易日志")
    print("="*100)
    
    # 月度汇总
    print(f"\n📊 月度概览")
    print(f"   回测区间：{start_date} 至 {end_date}")
    print(f"   初始资金：¥{capital:,.2f}")
    print(f"   最终资金：¥{daily_df.iloc[-1]['total_value']:,.2f}")
    print(f"   总收益：¥{daily_df.iloc[-1]['daily_pnl']:,.2f}")
    print(f"   总收益率：{daily_df.iloc[-1]['daily_return']*100:.2f}%")
    print(f"   交易天数：{len(daily_df)} 天")
    print(f"   总交易笔数：{len(trades_df)} 笔")
    
    # 按日期分组统计
    trades_df['date'] = pd.to_datetime(trades_df['datetime']).dt.strftime('%Y-%m-%d')
    daily_trades = trades_df.groupby('date')
    
    print("\n" + "="*100)
    print(" " * 35 + "每日交易明细")
    print("="*100)
    
    total_profit = 0
    total_loss = 0
    winning_trades = 0
    losing_trades = 0
    
    for date, group in daily_trades:
        # 获取当日 ETF 数据
        day_data = daily_df[daily_df['date'] == date]
        if not day_data.empty:
            open_price = day_data.iloc[0]['open_price']
            close_price = day_data.iloc[0]['close_price']
            daily_pnl = day_data.iloc[0]['daily_pnl']
            daily_return = day_data.iloc[0]['daily_return']
        else:
            open_price = 0
            close_price = 0
            daily_pnl = 0
            daily_return = 0
        
        print(f"\n📅 {date} (开盘：{open_price:.4f}, 收盘：{close_price:.4f}, 盈亏：¥{daily_pnl:,.2f}, 收益率：{daily_return*100:.2f}%)")
        print("-"*100)
        
        # 当日交易统计
        day_profit = group[group['pnl'] > 0]['pnl'].sum()
        day_loss = group[group['pnl'] < 0]['pnl'].sum()
        day_winning = len(group[group['pnl'] > 0])
        day_losing = len(group[group['pnl'] < 0])
        
        total_profit += day_profit
        total_loss += abs(day_loss)
        winning_trades += day_winning
        losing_trades += day_losing
        
        print(f"   交易笔数：{len(group)} | 盈利：{day_winning}笔 | 亏损：{day_losing}笔 | 胜率：{day_winning/len(group)*100:.1f}%")
        print(f"   盈利金额：¥{day_profit:,.2f} | 亏损金额：¥{abs(day_loss):,.2f} | 净盈亏：¥{day_profit + day_loss:,.2f}")
        print()
        
        # 逐笔交易详情
        print(f"   {'序号':<4} {'时间':<12} {'操作':<10} {'类型':<6} {'合约':<25} {'价格':<10} {'数量':<6} {'盈亏':<12} {'原因':<20}")
        print("   " + "-"*96)
        
        for idx, trade in group.iterrows():
            action_map = {
                'buy_open': '买入开仓',
                'sell_close': '卖出平仓',
                'sell_open': '卖出开仓',
                'buy_close': '买入平仓'
            }
            action_cn = action_map.get(trade['action'], trade['action'])
            option_type_cn = '看涨' if trade['option_type'] == 'call' else '看跌'
            pnl_text = f"¥{trade['pnl']:,.2f}" if trade['pnl'] != 0 else '-'
            pnl_style = '' if trade['pnl'] >= 0 else '(-)'
            
            print(f"   {idx+1:<4} {trade['datetime'].strftime('%H:%M'):<12} {action_cn:<10} {option_type_cn:<6} {trade['option_code']:<25} {trade['price']:<10.4f} {trade['quantity']:<6} {pnl_text:<12} {trade['reason']:<20}")
        
        print()
    
    # 月度交易汇总
    print("\n" + "="*100)
    print(" " * 35 + "月度交易汇总")
    print("="*100)
    
    print(f"\n📈 交易统计")
    print(f"   总交易笔数：{len(trades_df)} 笔")
    print(f"   盈利交易：{winning_trades} 笔 ({winning_trades/len(trades_df)*100:.2f}%)")
    print(f"   亏损交易：{losing_trades} 笔 ({losing_trades/len(trades_df)*100:.2f}%)")
    print(f"   胜率：{winning_trades/len(trades_df)*100:.2f}%")
    
    print(f"\n💰 盈亏统计")
    print(f"   总盈利：¥{total_profit:,.2f}")
    print(f"   总亏损：¥{total_loss:,.2f}")
    print(f"   净盈亏：¥{total_profit - total_loss:,.2f}")
    print(f"   盈亏比：{total_profit/total_loss:.2f}")
    print(f"   平均盈利：¥{total_profit/winning_trades:,.2f}" if winning_trades > 0 else "   平均盈利：N/A")
    print(f"   平均亏损：¥{total_loss/losing_trades:,.2f}" if losing_trades > 0 else "   平均亏损：N/A")
    
    # 按操作类型统计
    print(f"\n📝 操作类型统计")
    action_stats = trades_df.groupby('action').size()
    action_map_cn = {
        'buy_open': '买入开仓',
        'sell_close': '卖出平仓',
        'sell_open': '卖出开仓',
        'buy_close': '买入平仓'
    }
    for action, count in action_stats.items():
        action_cn = action_map_cn.get(action, action)
        print(f"   {action_cn}: {count} 笔")
    
    # 按期权类型统计
    print(f"\n📊 期权类型统计")
    type_stats = trades_df.groupby('option_type').size()
    for opt_type, count in type_stats.items():
        type_cn = '看涨期权 (Call)' if opt_type == 'call' else '看跌期权 (Put)'
        print(f"   {type_cn}: {count} 笔")
    
    # 按原因统计
    print(f"\n🔍 交易原因统计")
    reason_stats = trades_df.groupby('reason').size().sort_values(ascending=False)
    for reason, count in reason_stats.items():
        print(f"   {reason}: {count} 笔")
    
    # 最佳/最差交易日
    print(f"\n🏆 最佳/最差交易日")
    daily_df_sorted = daily_df.sort_values('daily_pnl', ascending=False)
    best_day = daily_df_sorted.iloc[0]
    worst_day = daily_df_sorted.iloc[-1]
    print(f"   最佳交易日：{best_day['date']} (盈亏：¥{best_day['daily_pnl']:,.2f}, 收益率：{best_day['daily_return']*100:.2f}%)")
    print(f"   最差交易日：{worst_day['date']} (盈亏：¥{worst_day['daily_pnl']:,.2f}, 收益率：{worst_day['daily_return']*100:.2f}%)")
    
    # 保存交易日志到文件
    output_file = f"reports/trade_log_{start_date.replace('-', '')}_{end_date.replace('-', '')}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 2026 年 3 月 详细交易日志\n\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## 月度概览\n\n")
        f.write(f"- 回测区间：{start_date} 至 {end_date}\n")
        f.write(f"- 初始资金：¥{capital:,.2f}\n")
        f.write(f"- 最终资金：¥{daily_df.iloc[-1]['total_value']:,.2f}\n")
        f.write(f"- 总收益：¥{daily_df.iloc[-1]['daily_pnl']:,.2f}\n")
        f.write(f"- 总收益率：{daily_df.iloc[-1]['daily_return']*100:.2f}%\n")
        f.write(f"- 交易天数：{len(daily_df)} 天\n")
        f.write(f"- 总交易笔数：{len(trades_df)} 笔\n")
        f.write(f"- 胜率：{winning_trades/len(trades_df)*100:.2f}%\n")
        f.write(f"- 盈亏比：{total_profit/total_loss:.2f}\n\n")
        
        f.write(f"## 交易统计\n\n")
        f.write(f"- 总盈利：¥{total_profit:,.2f}\n")
        f.write(f"- 总亏损：¥{total_loss:,.2f}\n")
        f.write(f"- 平均盈利：¥{total_profit/winning_trades:,.2f}\n")
        f.write(f"- 平均亏损：¥{total_loss/losing_trades:,.2f}\n\n")
        
        f.write(f"## 完整交易记录\n\n")
        f.write(trades_df.to_csv(index=False, sep='|'))
    
    print(f"\n✅ 交易日志已保存至：{output_file}")
    
    return trades_df


def main():
    parser = argparse.ArgumentParser(description="生成详细交易日志")
    parser.add_argument("--start", type=str, required=True, help="开始日期 (YYYYMMDD)")
    parser.add_argument("--end", type=str, required=True, help="结束日期 (YYYYMMDD)")
    parser.add_argument("--capital", type=float, default=100000, help="初始资金")
    
    args = parser.parse_args()
    
    start_date = args.start
    end_date = args.end
    
    if len(start_date) == 8:
        start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
    if len(end_date) == 8:
        end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
    
    generate_trade_log(start_date, end_date, args.capital)


if __name__ == "__main__":
    main()
