# -*- coding: utf-8 -*-
"""
回测引擎 - 执行策略回测
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Optional
import logging
from data_fetcher import DataFetcher
from strategy import ETFOptionStrategy, DailyPosition
import config

logger = logging.getLogger(__name__)


class Backtester:
    """ETF 期权策略回测引擎"""
    
    def __init__(self, start_date: str, end_date: str, initial_capital: float = 100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.current_capital = initial_capital  # 累加资金
        
        self.data_fetcher = DataFetcher()
        self.strategy = ETFOptionStrategy({
            "open_threshold": config.OPEN_THRESHOLD,
            "check_interval": config.CHECK_INTERVAL_MINUTES,
            "reverse_threshold": config.REVERSE_THRESHOLD,
            "trade_size": config.TRADE_SIZE,
            "profit_threshold": config.PROFIT_THRESHOLD,
            "otm_delta": config.OTM_DELTA,
            "clear_time": config.CLEAR_TIME,
            "initial_capital": initial_capital
        })
        
        self.etf_data = None
        self.daily_results = []
        self.all_trades = []
        self.hedge_count_per_day = 0  # 每日对冲次数计数
        
    def load_data(self):
        """加载 ETF 历史数据"""
        logger.info(f"加载数据：{self.start_date} - {self.end_date}")
        
        # 获取 ETF 日线数据
        self.etf_data = self.data_fetcher.get_etf_daily_data(
            self.start_date.replace("-", ""),
            self.end_date.replace("-", "")
        )
        
        if self.etf_data.empty:
            logger.error("未获取到 ETF 数据")
            return False
        
        logger.info(f"加载完成：{len(self.etf_data)} 个交易日")
        return True
    
    def generate_intraday_prices(self, daily_bar: pd.Series) -> pd.DataFrame:
        """
        根据日线数据生成模拟的日内价格（每 30 分钟）
        
        简化假设：
        - 9:30 开盘价 = 日线开盘
        - 15:00 收盘价 = 日线收盘
        - 中间价格线性插值 + 随机波动
        """
        timestamps = [
            "09:30", "10:00", "10:30", "11:00", "11:30",
            "13:00", "13:30", "14:00", "14:30", "14:45", "15:00"
        ]
        
        open_price = daily_bar["open"]
        close_price = daily_bar["close"]
        high_price = daily_bar["high"]
        low_price = daily_bar["low"]
        
        prices = []
        
        for i, ts in enumerate(timestamps):
            hour, minute = map(int, ts.split(":"))
            
            if i == 0:
                # 开盘
                price = open_price
            elif i == len(timestamps) - 1:
                # 收盘
                price = close_price
            else:
                # 中间时间：线性插值 + 随机波动
                progress = i / (len(timestamps) - 1)
                base_price = open_price + (close_price - open_price) * progress
                
                # 添加波动（在高低点范围内）
                range_size = high_price - low_price
                noise = np.random.uniform(-0.3, 0.3) * range_size
                price = base_price + noise
                
                # 确保在高低点范围内
                price = max(low_price, min(high_price, price))
            
            prices.append({
                "datetime": f"{daily_bar['date'].strftime('%Y-%m-%d')} {ts}",
                "price": price
            })
        
        return pd.DataFrame(prices)
    
    def estimate_option_premium(self, underlying_price: float, strike_price: float,
                                 option_type: str, days_to_expiry: int = 30) -> float:
        """
        估算期权权利金（保守模型 - 修正版）
        
        使用更保守的参数，避免过度放大
        """
        # 内在价值
        if option_type == "call":
            intrinsic_value = max(0, underlying_price - strike_price)
            moneyness = underlying_price / strike_price
        else:
            intrinsic_value = max(0, strike_price - underlying_price)
            moneyness = strike_price / underlying_price
        
        # 时间价值（保守估计）
        # 假设隐含波动率 25-35%
        implied_vol = 0.30
        time_factor = np.sqrt(days_to_expiry / 365)
        
        # 简化的时间价值
        time_value = underlying_price * implied_vol * time_factor * 0.2
        
        # 虚值程度调整
        otm_factor = max(0.2, 1 - abs(moneyness - 1) * 3)
        
        premium = intrinsic_value + time_value * otm_factor
        
        return max(0.0001, premium)
    
    def run_backtest(self):
        """执行回测"""
        logger.info("开始回测...")
        
        for idx, daily_bar in self.etf_data.iterrows():
            if idx == 0:
                continue  # 跳过第一天（需要昨日收盘价）
            
            date = daily_bar["date"].strftime("%Y-%m-%d")
            prev_close = self.etf_data.iloc[idx - 1]["close"]
            open_price = daily_bar["open"]
            
            logger.info(f"\n{'='*60}")
            logger.info(f"交易日期：{date}")
            logger.info(f"{'='*60}")
            
            # 每日重置（保留累计资金）
            self.strategy.reset_daily(date, prev_close, open_price)
            self.strategy.cash = self.current_capital  # 使用累计资金
            self.hedge_count_per_day = 0  # 重置对冲计数
            
            # 生成日内价格
            intraday_df = self.generate_intraday_prices(daily_bar)
            
            # 阶段 1: 探索阶段（9:30）
            open_signal = self.strategy.check_open_signal(open_price, prev_close)
            
            if open_signal:
                # 选择期权合约（简化：假设平值期权）
                strike_price = round(open_price, 3)  # 平值行权价
                premium = self.estimate_option_premium(open_price, strike_price, open_signal)
                
                self.strategy.open_position(
                    option_code=f"{open_signal}_{date}",
                    option_type=open_signal,
                    premium=premium,
                    strike_price=strike_price,
                    expiry_date=date,
                    current_time=pd.to_datetime(f"{date} 09:30")
                )
            
            # 阶段 2: 验证阶段（每 30 分钟）
            for intraday_idx, intraday_row in intraday_df.iterrows():
                if intraday_row["datetime"].endswith("09:30"):
                    continue  # 已处理
                
                current_time = pd.to_datetime(intraday_row["datetime"])
                current_price = intraday_row["price"]
                
                # 检查是否到清仓时间
                if current_time.strftime("%H:%M") >= "14:45":
                    if self.strategy.positions:
                        current_prices = {p.code: p.current_value for p in self.strategy.positions}
                        self.strategy.clear_all_positions(current_time, current_prices)
                    break
                
                # 检查是否需要反手
                if self.strategy.positions:
                    reverse_signal = self.strategy.check_reverse_signal(current_price)
                    
                    if reverse_signal and reverse_signal != "hold":
                        # 反手操作
                        new_type = "call" if reverse_signal == "reverse_to_call" else "put"
                        strike_price = round(current_price, 3)
                        premium = self.estimate_option_premium(current_price, strike_price, new_type)
                        
                        self.strategy.reverse_position(
                            new_option_code=f"{new_type}_{date}_{intraday_idx}",
                            new_option_type=new_type,
                            new_premium=premium,
                            strike_price=strike_price,
                            expiry_date=date,
                            current_time=current_time,
                            current_price=current_price
                        )
                    
                    # 更新持仓市值（限制涨跌幅）
                    for pos in self.strategy.positions:
                        # 计算 ETF 涨跌幅
                        if pos.option_type == "call":
                            etf_change = (current_price - pos.open_price) / pos.open_price
                        else:
                            etf_change = (pos.open_price - current_price) / pos.open_price
                        
                        # 期权杠杆放大（3-5 倍，而非之前的 20 倍+）
                        leverage = 4.0
                        option_change = etf_change * leverage
                        
                        # 限制单日最大涨跌幅
                        option_change = max(-0.50, min(2.0, option_change))  # -50% 到 +200%
                        
                        pos.current_value = pos.open_price * (1 + option_change)
                    
                    # 阶段 3: 对冲阶段（每天最多对冲 1 次）
                    if self.hedge_count_per_day < 1:
                        hedge_list = self.strategy.check_hedge_signal(current_time)
                        
                        for pos, hedge_type in hedge_list:
                            # 检查是否已对冲
                            already_hedged = any(
                                p.position_type.name.endswith("SHORT") and p.option_type == hedge_type
                                for p in self.strategy.positions
                            )
                            
                            if not already_hedged:
                                # 开虚值期权对冲
                                if hedge_type == "call":
                                    strike_price = round(current_price * 1.03, 3)  # 虚值 3%
                                else:
                                    strike_price = round(current_price * 0.97, 3)  # 虚值 3%
                                
                                premium = self.estimate_option_premium(current_price, strike_price, hedge_type) * 0.5  # 虚值便宜些
                                
                                self.strategy.open_hedge(
                                    option_code=f"hedge_{hedge_type}_{date}",
                                    option_type=hedge_type,
                                    premium=premium,
                                    strike_price=strike_price,
                                    expiry_date=date,
                                    current_time=current_time
                                )
                                self.hedge_count_per_day += 1
                                break  # 每天只对冲一次
            
            # 记录每日结果
            total_value = self.strategy.get_total_value()
            daily_pnl = total_value - self.current_capital
            daily_return = daily_pnl / self.current_capital if self.current_capital > 0 else 0
            
            daily_result = {
                "date": date,
                "open_price": open_price,
                "close_price": daily_bar["close"],
                "trades": len(self.strategy.trades),
                "total_value": total_value,
                "cash": self.strategy.cash,
                "daily_pnl": daily_pnl,
                "daily_return": daily_return
            }
            self.daily_results.append(daily_result)
            self.all_trades.extend(self.strategy.trades)
            
            # 更新累计资金
            self.current_capital = total_value
            
            logger.info(f"当日盈亏：{daily_result['daily_pnl']:.2f} 元，收益率：{daily_result['daily_return']*100:.2f}%")
        
        logger.info(f"\n回测完成！共 {len(self.daily_results)} 个交易日，{len(self.all_trades)} 笔交易")
        
        return pd.DataFrame(self.daily_results)
    
    def get_results(self) -> tuple:
        """获取回测结果"""
        return pd.DataFrame(self.daily_results), pd.DataFrame(self.all_trades)
