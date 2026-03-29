# -*- coding: utf-8 -*-
"""
绩效分析模块 - 生成回测报告
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """策略绩效分析器"""
    
    def __init__(self, daily_results: pd.DataFrame, trades: pd.DataFrame):
        self.daily_results = daily_results
        self.trades = trades
        
        if daily_results.empty:
            logger.warning("每日结果为空，无法分析")
            self.metrics = {}
            return
        
        self.metrics = self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict:
        """计算绩效指标"""
        daily_returns = self.daily_results["daily_return"]
        
        metrics = {}
        
        # 基础指标
        metrics["total_days"] = len(self.daily_results)
        metrics["total_trades"] = len(self.trades)
        metrics["initial_capital"] = self.daily_results.iloc[0]["total_value"] - self.daily_results.iloc[0]["daily_pnl"]
        metrics["final_capital"] = self.daily_results.iloc[-1]["total_value"]
        metrics["total_pnl"] = self.daily_results.iloc[-1]["daily_pnl"]
        metrics["total_return"] = (metrics["final_capital"] - metrics["initial_capital"]) / metrics["initial_capital"]
        
        # 收益率指标
        metrics["avg_daily_return"] = daily_returns.mean()
        metrics["std_daily_return"] = daily_returns.std()
        
        # 年化收益率（假设 250 个交易日）
        metrics["annual_return"] = (1 + metrics["total_return"]) ** (250 / metrics["total_days"]) - 1
        
        # 夏普比率（假设无风险利率 3%）
        risk_free_rate = 0.03 / 250
        if metrics["std_daily_return"] > 0:
            metrics["sharpe_ratio"] = (metrics["avg_daily_return"] - risk_free_rate) / metrics["std_daily_return"] * np.sqrt(250)
        else:
            metrics["sharpe_ratio"] = 0
        
        # 最大回撤
        cumulative = (1 + daily_returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        metrics["max_drawdown"] = drawdown.min()
        
        # 胜率
        winning_days = (daily_returns > 0).sum()
        metrics["win_rate"] = winning_days / len(daily_returns) if len(daily_returns) > 0 else 0
        
        # 盈亏比
        winning_returns = daily_returns[daily_returns > 0]
        losing_returns = daily_returns[daily_returns < 0]
        
        avg_win = winning_returns.mean() if len(winning_returns) > 0 else 0
        avg_loss = abs(losing_returns.mean()) if len(losing_returns) > 0 else 0
        
        metrics["profit_loss_ratio"] = avg_win / avg_loss if avg_loss > 0 else 0
        
        # 交易统计
        if len(self.trades) > 0:
            winning_trades = self.trades[self.trades["pnl"] > 0]
            losing_trades = self.trades[self.trades["pnl"] < 0]
            
            metrics["winning_trades"] = len(winning_trades)
            metrics["losing_trades"] = len(losing_trades)
            metrics["avg_win_per_trade"] = winning_trades["pnl"].mean() if len(winning_trades) > 0 else 0
            metrics["avg_loss_per_trade"] = abs(losing_trades["pnl"].mean()) if len(losing_trades) > 0 else 0
        
        # 开仓统计
        long_trades = self.trades[self.trades["action"] == "buy_open"]
        metrics["call_trades"] = len(self.trades[self.trades["option_type"] == "call"])
        metrics["put_trades"] = len(self.trades[self.trades["option_type"] == "put"])
        
        return metrics
    
    def generate_report(self, output_dir: str = "reports") -> str:
        """生成 HTML 报告"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(output_dir, f"backtest_report_{timestamp}.html")
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>ETF 期权策略回测报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50; }}
        .metric-label {{ font-size: 14px; color: #666; margin-bottom: 5px; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #333; }}
        .positive {{ color: #4CAF50; }}
        .negative {{ color: #f44336; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #4CAF50; color: white; }}
        tr:hover {{ background: #f5f5f5; }}
        .summary {{ background: #e8f5e9; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 ETF 期权策略回测报告</h1>
        <p>生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <h2>📈 策略概要</h2>
            <p><strong>策略类型：</strong>ETF 期权三阶段策略（探索 + 验证 + 对冲）</p>
            <p><strong>回测区间：</strong>{self.daily_results["date"].iloc[0]} 至 {self.daily_results["date"].iloc[-1]}</p>
            <p><strong>初始资金：</strong>¥{self.metrics.get("initial_capital", 0):,.2f}</p>
        </div>
        
        <h2>💰 核心绩效指标</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">总收益率</div>
                <div class="metric-value {'positive' if self.metrics.get('total_return', 0) >= 0 else 'negative'}">{self.metrics.get('total_return', 0)*100:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">年化收益率</div>
                <div class="metric-value {'positive' if self.metrics.get('annual_return', 0) >= 0 else 'negative'}">{self.metrics.get('annual_return', 0)*100:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">夏普比率</div>
                <div class="metric-value">{self.metrics.get('sharpe_ratio', 0):.2f}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">最大回撤</div>
                <div class="metric-value negative">{self.metrics.get('max_drawdown', 0)*100:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">胜率</div>
                <div class="metric-value {'positive' if self.metrics.get('win_rate', 0) >= 0.5 else 'negative'}">{self.metrics.get('win_rate', 0)*100:.2f}%</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">盈亏比</div>
                <div class="metric-value">{self.metrics.get('profit_loss_ratio', 0):.2f}</div>
            </div>
        </div>
        
        <h2>📊 资金曲线</h2>
        <p>总交易日：<strong>{self.metrics.get('total_days', 0)}</strong> | 总交易笔数：<strong>{self.metrics.get('total_trades', 0)}</strong></p>
        <p>最终资金：<strong class="{'positive' if self.metrics.get('final_capital', 0) >= self.metrics.get('initial_capital', 0) else 'negative'}">¥{self.metrics.get('final_capital', 0):,.2f}</strong></p>
        <p>总盈亏：<strong class="{'positive' if self.metrics.get('total_pnl', 0) >= 0 else 'negative'}">¥{self.metrics.get('total_pnl', 0):,.2f}</strong></p>
        
        <h2>📝 交易统计</h2>
        <table>
            <tr>
                <th>指标</th>
                <th>数值</th>
            </tr>
            <tr>
                <td>看涨期权交易</td>
                <td>{self.metrics.get('call_trades', 0)} 笔</td>
            </tr>
            <tr>
                <td>看跌期权交易</td>
                <td>{self.metrics.get('put_trades', 0)} 笔</td>
            </tr>
            <tr>
                <td>盈利交易</td>
                <td>{self.metrics.get('winning_trades', 0)} 笔</td>
            </tr>
            <tr>
                <td>亏损交易</td>
                <td>{self.metrics.get('losing_trades', 0)} 笔</td>
            </tr>
            <tr>
                <td>平均盈利</td>
                <td class="positive">¥{self.metrics.get('avg_win_per_trade', 0):,.2f}</td>
            </tr>
            <tr>
                <td>平均亏损</td>
                <td class="negative">¥{self.metrics.get('avg_loss_per_trade', 0):,.2f}</td>
            </tr>
        </table>
        
        <h2>📅 每日收益明细</h2>
        <table>
            <tr>
                <th>日期</th>
                <th>开盘价</th>
                <th>收盘价</th>
                <th>交易笔数</th>
                <th>当日盈亏</th>
                <th>收益率</th>
            </tr>
"""
        
        # 添加每日数据（最多显示 50 天）
        for idx, row in self.daily_results.head(50).iterrows():
            pnl_class = "positive" if row["daily_pnl"] >= 0 else "negative"
            return_class = "positive" if row["daily_return"] >= 0 else "negative"
            html_content += f"""
            <tr>
                <td>{row['date']}</td>
                <td>{row['open_price']:.4f}</td>
                <td>{row['close_price']:.4f}</td>
                <td>{row['trades']}</td>
                <td class="{pnl_class}">¥{row['daily_pnl']:,.2f}</td>
                <td class="{return_class}">{row['daily_return']*100:.2f}%</td>
            </tr>
"""
        
        html_content += """
        </table>
        
        <h2>⚠️ 风险提示</h2>
        <div style="background: #fff3cd; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">
            <p>1. 本回测使用简化模型估算期权价格，实际交易可能存在偏差</p>
            <p>2. 未考虑交易手续费、滑点等实际成本</p>
            <p>3. 历史业绩不代表未来表现</p>
            <p>4. 期权交易具有高风险，请谨慎投资</p>
        </div>
    </div>
</body>
</html>
"""
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"报告已生成：{report_path}")
        return report_path
    
    def print_summary(self):
        """打印绩效摘要"""
        print("\n" + "="*60)
        print("📊 策略回测绩效摘要")
        print("="*60)
        print(f"回测天数：      {self.metrics.get('total_days', 0)} 天")
        print(f"总交易笔数：    {self.metrics.get('total_trades', 0)} 笔")
        print(f"初始资金：      ¥{self.metrics.get('initial_capital', 0):,.2f}")
        print(f"最终资金：      ¥{self.metrics.get('final_capital', 0):,.2f}")
        print(f"总盈亏：        ¥{self.metrics.get('total_pnl', 0):,.2f}")
        print(f"总收益率：      {self.metrics.get('total_return', 0)*100:.2f}%")
        print(f"年化收益率：    {self.metrics.get('annual_return', 0)*100:.2f}%")
        print(f"夏普比率：      {self.metrics.get('sharpe_ratio', 0):.2f}")
        print(f"最大回撤：      {self.metrics.get('max_drawdown', 0)*100:.2f}%")
        print(f"胜率：          {self.metrics.get('win_rate', 0)*100:.2f}%")
        print(f"盈亏比：        {self.metrics.get('profit_loss_ratio', 0):.2f}")
        print("="*60)
