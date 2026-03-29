# -*- coding: utf-8 -*-
"""
ETF 期权策略配置文件
"""

# ==================== 策略参数 ====================

# 默认资金
DEFAULT_CAPITAL = 100000  # 元

# 开仓条件
OPEN_THRESHOLD = 0.005  # 开盘价 vs 昨收 ±0.5%

# 验证频率
CHECK_INTERVAL_MINUTES = 30  # 每 30 分钟确认一次

# 反手条件
REVERSE_THRESHOLD = 0.005  # 价格反向 > 开盘价 0.5%

# 交易数量
TRADE_SIZE = 1  # 每次 1 张

# 获利对冲阈值
PROFIT_THRESHOLD = 0.20  # >20% 获利时对冲

# 虚值期权 Delta
OTM_DELTA = 0.3  # Delta=0.3 的虚值期权

# 清仓时间
CLEAR_TIME = "14:45"  # 当天不过夜

# 期权月份选择规则
# 当月 10 号前=当月主力，10-15 号=当月 + 次月，15 号后=次月主力
OPTION_MONTH_RULE = {
    "before_10": "current",      # 1-10 号：当月
    "between_10_15": "both",     # 10-15 号：当月 + 次月
    "after_15": "next"           # 15 号后：次月
}

# ==================== 数据参数 ====================

# ETF 代码
ETF_CODE = "159915"
ETF_NAME = "易方达创业板 ETF"

# 交易所
EXCHANGE = "SZSE"

# ==================== 回测参数 ====================

# 手续费（估算）
COMMISSION_RATE = 0.0003  # 万分之三
SLIPPAGE = 0.001  # 滑点 0.1%

# 期权合约乘数（ETF 期权通常为 10000）
OPTION_MULTIPLIER = 10000

# 固定交易费用（元/张）
FIXED_COMMISSION_PER_CONTRACT = 5.0  # 每张 5 元

# ==================== 日志配置 ====================

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
