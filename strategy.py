# -*- coding: utf-8 -*-
"""
策略逻辑模块 - 实现 ETF 期权三阶段策略
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PositionType(Enum):
    """持仓类型"""
    CALL_LONG = "call_long"      # 买入看涨
    PUT_LONG = "put_long"        # 买入看跌
    CALL_SHORT = "call_short"    # 卖出看涨
    PUT_SHORT = "put_short"      # 卖出看跌


class MarketState(Enum):
    """市场状态"""
    BULLISH = "bullish"      # 看涨
    BEARISH = "bearish"      # 看跌
    NEUTRAL = "neutral"      # 震荡


@dataclass
class OptionContract:
    """期权合约信息"""
    code: str
    option_type: str  # 'call' or 'put'
    strike_price: float
    expiry_date: str
    premium: float  # 权利金
    position_type: PositionType
    open_price: float  # 开仓价格
    open_datetime: datetime
    quantity: int = 1
    current_value: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0


@dataclass
class Trade:
    """交易记录"""
    datetime: datetime
    action: str  # 'buy_open', 'sell_close', 'sell_open', 'buy_close'
    option_code: str
    option_type: str
    price: float
    quantity: int
    premium: float
    pnl: float = 0.0
    reason: str = ""


@dataclass
class DailyPosition:
    """每日持仓状态"""
    date: str
    positions: List[OptionContract] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    cash: float = 100000.0
    total_value: float = 100000.0
    daily_pnl: float = 0.0


class ETFOptionStrategy:
    """
    ETF 期权三阶段策略
    
    阶段 1: 探索阶段 - 9:30 开盘判断方向，买入平值期权
    阶段 2: 验证阶段 - 每 30 分钟确认，反向则反手
    阶段 3: 对冲阶段 - 获利>20% 时卖出虚值期权对冲
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.open_threshold = config.get("open_threshold", 0.005)
        self.check_interval = config.get("check_interval", 30)  # 分钟
        self.reverse_threshold = config.get("reverse_threshold", 0.005)
        self.trade_size = config.get("trade_size", 1)
        self.profit_threshold = config.get("profit_threshold", 0.20)
        self.otm_delta = config.get("otm_delta", 0.3)
        self.clear_time = config.get("clear_time", "14:45")
        self.initial_capital = config.get("initial_capital", 100000)
        
        self.positions: List[OptionContract] = []
        self.trades: List[Trade] = []
        self.cash = self.initial_capital
        self.current_date = None
        self.open_price = None  # 当日开盘价
        self.prev_close = None  # 昨日收盘价
        
    def reset_daily(self, date: str, prev_close: float, open_price: float):
        """每日重置"""
        self.current_date = date
        self.prev_close = prev_close
        self.open_price = open_price
        self.positions = []
        self.cash = self.initial_capital
        logger.info(f"=== {date} 策略重置 ===")
        logger.info(f"昨收：{prev_close:.4f}, 开盘：{open_price:.4f}")
    
    def check_open_signal(self, open_price: float, prev_close: float) -> Optional[str]:
        """
        阶段 1: 探索阶段 - 检查开盘信号
        
        Returns:
            'call' / 'put' / None
        """
        change_rate = (open_price - prev_close) / prev_close
        
        if change_rate > self.open_threshold:
            logger.info(f"开盘上涨 {change_rate*100:.2f}% > {self.open_threshold*100:.2f}% → 买入看涨期权")
            return "call"
        elif change_rate < -self.open_threshold:
            logger.info(f"开盘下跌 {change_rate*100:.2f}% < {-self.open_threshold*100:.2f}% → 买入看跌期权")
            return "put"
        else:
            logger.info(f"开盘震荡 {change_rate*100:.2f}% → 观望")
            return None
    
    def open_position(self, option_code: str, option_type: str, 
                      premium: float, strike_price: float,
                      expiry_date: str, current_time: datetime):
        """开仓"""
        position = OptionContract(
            code=option_code,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            position_type=PositionType.CALL_LONG if option_type == "call" else PositionType.PUT_LONG,
            open_price=premium,
            open_datetime=current_time,
            quantity=self.trade_size,
            current_value=premium
        )
        
        self.positions.append(position)
        self.cash -= premium * 10000  # 期权合约乘数 10000
        
        trade = Trade(
            datetime=current_time,
            action="buy_open",
            option_code=option_code,
            option_type=option_type,
            price=premium,
            quantity=self.trade_size,
            premium=premium * 10000,
            reason="开仓"
        )
        self.trades.append(trade)
        
        logger.info(f"开仓：{option_type} {option_code} @ {premium:.4f}")
    
    def check_reverse_signal(self, current_price: float) -> Optional[str]:
        """
        阶段 2: 验证阶段 - 检查是否需要反手
        
        Returns:
            'reverse' / 'hold' / None
        """
        if not self.positions:
            return None
        
        # 检查价格是否反向
        change_from_open = (current_price - self.open_price) / self.open_price
        
        current_position = self.positions[0]
        
        if current_position.option_type == "call":
            # 持有多头看涨，价格下跌超过阈值 → 反手
            if change_from_open < -self.reverse_threshold:
                logger.info(f"价格反向：下跌 {change_from_open*100:.2f}% < {-self.reverse_threshold*100:.2f}% → 反手")
                return "reverse_to_put"
        else:
            # 持有多头看跌，价格上涨超过阈值 → 反手
            if change_from_open > self.reverse_threshold:
                logger.info(f"价格反向：上涨 {change_from_open*100:.2f}% > {self.reverse_threshold*100:.2f}% → 反手")
                return "reverse_to_call"
        
        return "hold"
    
    def reverse_position(self, new_option_code: str, new_option_type: str,
                         new_premium: float, strike_price: float,
                         expiry_date: str, current_time: datetime,
                         current_price: float):
        """反手操作：平仓原合约，开新合约"""
        # 平仓原合约
        for pos in self.positions:
            self.close_position(pos, current_price, current_time, "反手平仓")
        
        # 开新合约
        self.open_position(new_option_code, new_option_type, new_premium,
                          strike_price, expiry_date, current_time)
    
    def close_position(self, position: OptionContract, current_price: float,
                       current_time: datetime, reason: str):
        """平仓"""
        # 估算平仓价格（简化：假设当前价格=权利金）
        close_premium = max(0.0001, position.current_value)
        
        self.cash += close_premium * 10000
        
        pnl = (close_premium - position.open_price) * 10000 * position.quantity
        
        trade = Trade(
            datetime=current_time,
            action="sell_close" if position.option_type == "call" else "buy_close",
            option_code=position.code,
            option_type=position.option_type,
            price=close_premium,
            quantity=position.quantity,
            premium=close_premium * 10000,
            pnl=pnl,
            reason=reason
        )
        self.trades.append(trade)
        
        logger.info(f"平仓：{position.code} @ {close_premium:.4f}, 盈亏：{pnl:.2f} 元，原因：{reason}")
        
        self.positions.remove(position)
    
    def check_hedge_signal(self, current_time: datetime) -> List[Tuple[OptionContract, str]]:
        """
        阶段 3: 对冲阶段 - 检查哪些持仓需要对冲
        
        Returns:
            List of (position, hedge_type)
        """
        hedge_list = []
        
        for pos in self.positions:
            pnl_percent = (pos.current_value - pos.open_price) / pos.open_price
            
            if pnl_percent > self.profit_threshold:
                logger.info(f"持仓 {pos.code} 盈利 {pnl_percent*100:.2f}% > {self.profit_threshold*100:.2f}% → 可以对冲")
                hedge_type = "call" if pos.option_type == "call" else "put"
                hedge_list.append((pos, hedge_type))
        
        return hedge_list
    
    def open_hedge(self, option_code: str, option_type: str,
                   premium: float, strike_price: float,
                   expiry_date: str, current_time: datetime):
        """开对冲仓位（卖出虚值期权）"""
        position = OptionContract(
            code=option_code,
            option_type=option_type,
            strike_price=strike_price,
            expiry_date=expiry_date,
            premium=premium,
            position_type=PositionType.CALL_SHORT if option_type == "call" else PositionType.PUT_SHORT,
            open_price=premium,
            open_datetime=current_time,
            quantity=self.trade_size,
            current_value=premium
        )
        
        self.positions.append(position)
        self.cash += premium * 10000  # 卖出期权收取权利金
        
        trade = Trade(
            datetime=current_time,
            action="sell_open",
            option_code=option_code,
            option_type=option_type,
            price=premium,
            quantity=self.trade_size,
            premium=premium * 10000,
            reason="对冲"
        )
        self.trades.append(trade)
        
        logger.info(f"对冲：卖出 {option_type} {option_code} @ {premium:.4f}")
    
    def clear_all_positions(self, current_time: datetime, current_prices: dict):
        """14:45 清仓所有持仓"""
        logger.info(f"=== 14:45 清仓 ===")
        
        for pos in self.positions[:]:  # 复制列表避免迭代中修改
            current_price = current_prices.get(pos.code, pos.current_value)
            self.close_position(pos, current_price, current_time, "日终清仓")
    
    def update_position_value(self, option_code: str, current_value: float):
        """更新持仓市值"""
        for pos in self.positions:
            if pos.code == option_code:
                pos.current_value = current_value
                pos.pnl = (current_value - pos.open_price) * 10000 * pos.quantity
                pos.pnl_percent = (current_value - pos.open_price) / pos.open_price
    
    def get_total_value(self) -> float:
        """计算总资产"""
        position_value = sum(pos.current_value * 10000 * pos.quantity for pos in self.positions)
        return self.cash + position_value
    
    def get_daily_pnl(self) -> float:
        """计算当日盈亏"""
        return sum(t.pnl for t in self.trades if t.datetime.date() == datetime.strptime(self.current_date, "%Y-%m-%d").date())
