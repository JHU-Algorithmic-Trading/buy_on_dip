from datetime import datetime, timedelta
import os
from pathlib import Path
import json

from strategy_backtester import StockDropBacktest, PositionSet
from yf_scraper import get_top_losers





# directory = "C:\\Users\\ZSchw\\Documents\\MyProjects\\buy_on_dip\\backtests"
directory = Path("C:\\Users\\ZSchw\\Documents\\MyProjects\\buy_on_dip\\backtests")
# Create the directory if it doesn't exist
directory.mkdir(parents=True, exist_ok=True)

backtest_txt_file_name = "backtest.txt"
backtest_jsn_file_name = "backtest.json"
metrics_jsn_file_name = "metrics.json"
inputs_jsn_file_name = "inputs.json"

MIN_DROP_STOCK_FILTER = .07
MIN_DROP = .05
MIN_GAIN = .05




def main():
	losers = get_top_losers(count=50)
	for loser in losers:
		change = loser["change"] / 100
		if change < 0 and abs(change) >= MIN_DROP_STOCK_FILTER:
			today_str = datetime.today().strftime("%Y-%m-%d")
			strategy = StockDropBacktest(
				loser["symbol"],
				"1984-01-01",
				today_str,
				MIN_DROP,
				MIN_GAIN,
				lambda prev_qty: prev_qty
			)
			strategy.run()
			backtest_str = "\n".join([position_set.__str__() for position_set in strategy.position_sets])
			backtest_json = json.dumps([position_set.to_dict() for position_set in strategy.position_sets])
			metrics_json = json.dumps(strategy.get_metrics())

			sub_dir = directory / Path(f"{today_str}/{loser['symbol']}")
			sub_dir.mkdir(parents=True, exist_ok=True)

			backtest_txt_file = sub_dir / backtest_txt_file_name
			backtest_jsn_file = sub_dir / backtest_jsn_file_name
			metrics_jsn_file = sub_dir / metrics_jsn_file_name

			with backtest_txt_file.open("w") as file:
				file.write(backtest_str)

			with backtest_jsn_file.open("w") as file:
				json.dump(backtest_json, file, indent=4)
			
			with metrics_jsn_file.open("w") as file:
				json.dump(metrics_json, file, indent=4)










if __name__ == "__main__":
	main()