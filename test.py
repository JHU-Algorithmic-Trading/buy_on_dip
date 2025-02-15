from stock_drop_backtest import StockDropBacktest
from pprint import pprint
from datetime import datetime
import sys
# import matplotlib.pyplot as plt


def main(ticker, min_drop, min_gain):
    stock_drop = StockDropBacktest(
        ticker,
        "1984-01-01",
        datetime.today().strftime("%Y-%m-%d"),
        min_drop,
        min_gain,
        lambda prev_qty: prev_qty
    )
    stock_drop.run()
    metrics = stock_drop.get_metrics()
    pprint(metrics)

    for investment in stock_drop.investments:
        pprint(investment.to_json())

    # Time period bar chart





if __name__ == "__main__":
    if len(sys.argv) == 4:
        main(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]))
    else:
        print("Pass in ticker symbol")