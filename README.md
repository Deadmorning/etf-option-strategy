# ETF 期权策略回测系统

## 目录结构

```
etf_option_strategy/
├── README.md                 # 使用说明
├── config.py                 # 配置文件
├── data_fetcher.py           # 数据获取模块（AkShare）
├── strategy.py               # 策略逻辑模块
├── backtester.py             # 回测引擎
├── analyzer.py               # 绩效分析模块
├── run_backtest.py           # 主程序入口
└── reports/                  # 回测报告输出目录
```

## 快速开始

```bash
# 1. 安装依赖
pip install akshare pandas numpy matplotlib

# 2. 运行回测
python run_backtest.py --start 20240101 --end 20241231

# 3. 查看报告
open reports/backtest_report.html
```

## 策略说明

详见策略文档：`../temp/etf-strategy-plan.md`
