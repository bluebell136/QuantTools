from QUANTTOOLS.QAStockTradingDay.StockStrategySecond.trading_morning import trading
from QUANTAXIS.QAUtil import QA_util_today_str,QA_util_get_last_day
mark_day = QA_util_get_last_day(QA_util_today_str())
trading(mark_day)