#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETF 期权策略回测系统 - 主程序入口

使用方法:
    python run_backtest.py --start 20240101 --end 20241231
    python run_backtest.py --start 20240101 --end 20241231 --capital 100000
"""

import argparse
import logging
import sys
from datetime import datetime
from backtester import Backtester
from analyzer import PerformanceAnalyzer
import config

# 配置日志
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("backtest.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ETF 期权策略回测系统")
    parser.add_argument("--start", type=str, required=True, help="开始日期 (YYYYMMDD)")
    parser.add_argument("--end", type=str, required=True, help="结束日期 (YYYYMMDD)")
    parser.add_argument("--capital", type=float, default=config.DEFAULT_CAPITAL, help="初始资金")
    parser.add_argument("--output", type=str, default="reports", help="报告输出目录")
    
    args = parser.parse_args()
    
    # 格式化日期
    start_date = args.start
    end_date = args.end
    
    if len(start_date) == 8:
        start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
    if len(end_date) == 8:
        end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"
    
    logger.info("="*60)
    logger.info("ETF 期权策略回测系统")
    logger.info("="*60)
    logger.info(f"回测区间：{start_date} 至 {end_date}")
    logger.info(f"初始资金：¥{args.capital:,.2f}")
    logger.info(f"策略参数:")
    logger.info(f"  - 开仓阈值：{config.OPEN_THRESHOLD*100:.2f}%")
    logger.info(f"  - 反手阈值：{config.REVERSE_THRESHOLD*100:.2f}%")
    logger.info(f"  - 获利对冲：>{config.PROFIT_THRESHOLD*100:.2f}%")
    logger.info(f"  - 虚值 Delta: {config.OTM_DELTA}")
    logger.info(f"  - 清仓时间：{config.CLEAR_TIME}")
    logger.info("="*60)
    
    try:
        # 创建回测引擎
        backtester = Backtester(
            start_date=start_date,
            end_date=end_date,
            initial_capital=args.capital
        )
        
        # 加载数据
        if not backtester.load_data():
            logger.error("数据加载失败")
            return 1
        
        # 执行回测
        daily_results = backtester.run_backtest()
        
        if daily_results.empty:
            logger.error("回测结果为空")
            return 1
        
        # 获取交易记录
        daily_results, trades = backtester.get_results()
        
        # 绩效分析
        analyzer = PerformanceAnalyzer(daily_results, trades)
        
        # 打印摘要
        analyzer.print_summary()
        
        # 生成报告
        report_path = analyzer.generate_report(args.output)
        logger.info(f"\n✅ 回测完成！报告已保存至：{report_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"回测失败：{e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
