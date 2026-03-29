# -*- coding: utf-8 -*-
"""
数据获取模块 - 使用 AkShare 获取 ETF 和期权历史数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """ETF 和期权数据获取器"""
    
    def __init__(self):
        self.etf_code = "159915"
    
    def get_etf_daily_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取 ETF 历史日线数据
        
        Args:
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            
        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        logger.info(f"获取 ETF {self.etf_code} 日线数据：{start_date} - {end_date}")
        
        try:
            # 获取 ETF 历史行情
            df = ak.fund_etf_hist_em(
                symbol=self.etf_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            # 重命名列
            df = df.rename(columns={
                "日期": "date",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume",
                "成交额": "turnover"
            })
            
            # 转换日期格式
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            
            logger.info(f"获取到 {len(df)} 条 ETF 数据")
            return df
            
        except Exception as e:
            logger.error(f"获取 ETF 数据失败：{e}")
            return pd.DataFrame()
    
    def get_etf_intraday_data(self, date: str, interval: str = "5") -> pd.DataFrame:
        """
        获取 ETF 日内分钟数据
        
        Args:
            date: 日期 YYYYMMDD
            interval: 分钟间隔 (1/5/15/30)
            
        Returns:
            DataFrame with intraday data
        """
        logger.info(f"获取 ETF {self.etf_code} 日内数据：{date}")
        
        try:
            # AkShare 获取 ETF 分钟数据
            df = ak.fund_etf_hist_min_em(
                symbol=self.etf_code,
                period=f"{interval}m",
                start_date=date,
                end_date=date,
                adjust=""
            )
            
            if df.empty:
                logger.warning(f"未获取到 {date} 的日内数据")
                return pd.DataFrame()
            
            # 重命名列
            df = df.rename(columns={
                "时间": "datetime",
                "开盘": "open",
                "最高": "high",
                "最低": "low",
                "收盘": "close",
                "成交量": "volume"
            })
            
            df["datetime"] = pd.to_datetime(df["datetime"])
            
            logger.info(f"获取到 {len(df)} 条日内数据")
            return df
            
        except Exception as e:
            logger.error(f"获取日内数据失败：{e}")
            return pd.DataFrame()
    
    def get_option_chain(self, date: str) -> pd.DataFrame:
        """
        获取 ETF 期权链数据
        
        Args:
            date: 日期 YYYYMMDD
            
        Returns:
            DataFrame with option chain data
        """
        logger.info(f"获取 ETF 期权链：{date}")
        
        try:
            # 获取创业板 ETF 期权数据
            df = ak.option_czb_em(symbol="创业板 ETF", exchange="深交所")
            
            if df.empty:
                logger.warning(f"未获取到 {date} 的期权链数据")
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条期权数据")
            return df
            
        except Exception as e:
            logger.error(f"获取期权链失败：{e}")
            return pd.DataFrame()
    
    def get_option_daily_data(self, option_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取单个期权合约历史数据
        
        Args:
            option_code: 期权合约代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
            
        Returns:
            DataFrame with option historical data
        """
        logger.info(f"获取期权 {option_code} 数据：{start_date} - {end_date}")
        
        try:
            # 获取期权历史行情
            df = ak.option_finance_current_sina(symbol=option_code)
            
            if df.empty:
                return pd.DataFrame()
            
            logger.info(f"获取到 {len(df)} 条期权数据")
            return df
            
        except Exception as e:
            logger.error(f"获取期权数据失败：{e}")
            return pd.DataFrame()
    
    def get_trading_calendar(self, start_date: str, end_date: str) -> List[str]:
        """
        获取交易日历
        
        Args:
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            List of trading days
        """
        try:
            # 获取 A 股交易日历
            df = ak.tool_trade_date_hist_sina()
            trade_days = df["trade_date"].tolist()
            
            # 过滤日期范围
            trade_days = [d for d in trade_days if start_date <= d <= end_date]
            
            return trade_days
            
        except Exception as e:
            logger.error(f"获取交易日历失败：{e}")
            return []
    
    def select_option_contract(self, date: datetime, option_type: str, 
                                underlying_price: float, 
                                option_chain: pd.DataFrame) -> Optional[str]:
        """
        根据规则选择期权合约
        
        Args:
            date: 当前日期
            option_type: 'call' 或 'put'
            underlying_price: 标的价格
            option_chain: 期权链数据
            
        Returns:
            期权合约代码
        """
        if option_chain.empty:
            return None
        
        # 根据日期选择月份
        day = date.day
        if day <= 10:
            month_type = "current"
        elif day <= 15:
            month_type = "both"
        else:
            month_type = "next"
        
        # 筛选期权类型
        if option_type == "call":
            option_chain = option_chain[option_chain["期权类型"].str.contains("购", na=False)]
        else:
            option_chain = option_chain[option_chain["期权类型"].str.contains("沽", na=False)]
        
        if option_chain.empty:
            return None
        
        # 选择平值期权（行权价最接近标的价格）
        option_chain["strike_diff"] = abs(option_chain["行权价"] - underlying_price)
        atm_option = option_chain.loc[option_chain["strike_diff"].idxmin()]
        
        return atm_option["期权代码"] if "期权代码" in atm_option.index else None
    
    def get_otm_option(self, option_type: str, underlying_price: float,
                       option_chain: pd.DataFrame, target_delta: float = 0.3) -> Optional[str]:
        """
        获取虚值期权（Delta 约 0.3）
        
        Args:
            option_type: 'call' 或 'put'
            underlying_price: 标的价格
            option_chain: 期权链数据
            target_delta: 目标 Delta
            
        Returns:
            期权合约代码
        """
        if option_chain.empty:
            return None
        
        # 筛选期权类型
        if option_type == "call":
            # 看涨虚值：行权价 > 标的价格
            option_chain = option_chain[
                (option_chain["期权类型"].str.contains("购", na=False)) &
                (option_chain["行权价"] > underlying_price)
            ]
        else:
            # 看跌虚值：行权价 < 标的价格
            option_chain = option_chain[
                (option_chain["期权类型"].str.contains("沽", na=False)) &
                (option_chain["行权价"] < underlying_price)
            ]
        
        if option_chain.empty:
            return None
        
        # 简化：选择行权价偏离度最接近 30% 的期权
        if option_type == "call":
            option_chain["delta_approx"] = (option_chain["行权价"] - underlying_price) / underlying_price
        else:
            option_chain["delta_approx"] = (underlying_price - option_chain["行权价"]) / underlying_price
        
        # 选择最接近目标 Delta 的期权
        option_chain["delta_diff"] = abs(option_chain["delta_approx"] - target_delta)
        otm_option = option_chain.loc[option_chain["delta_diff"].idxmin()]
        
        return otm_option["期权代码"] if "期权代码" in otm_option.index else None


# 测试
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fetcher = DataFetcher()
    
    # 测试获取 ETF 数据
    df = fetcher.get_etf_daily_data("20240101", "20241231")
    print(f"ETF 数据：{len(df)} 条")
    print(df.head())
    
    # 测试获取交易日历
    days = fetcher.get_trading_calendar("2024-01-01", "2024-12-31")
    print(f"交易日：{len(days)} 天")
