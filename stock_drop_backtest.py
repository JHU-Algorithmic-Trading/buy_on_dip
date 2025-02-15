import yfinance as yf
import numpy as np
from typing import List, Callable
from datetime import datetime



class Position:
    def __init__(self, drop_percent: float, shares: int, price: float, date: np.datetime64):
        self.set_is_invested(True)
        self.drop_percentages = []
        self.shares = []
        self.prices = []
        self.dates = []
        self.invest(drop_percent, shares, price, date)
        self.total_percent_gain = None
        self.annualized_return = None
        self.sell_date = None
        self.sell_price = None
        self.total_num_days_held = None

    def set_is_invested(self, _is_invested):
        self.is_invested = _is_invested

    def is_pos_open(self):
        return self.is_invested

    def invest(self, drop_percent, shares: int, price: float, date: np.datetime64):
        self.drop_percentages.append(drop_percent)
        self.shares.append(shares)
        self.prices.append(price)
        self.dates.append(date)

    def get_num_drops(self):
        return len(self.drop_percentages)

    def get_avg_purchase_price(self):
        return np.dot(self.shares, self.prices) / sum(self.shares)

    def get_percent_gain(self, current_price):
        pps = self.get_avg_purchase_price()
        return (current_price - pps) / pps

    def get_num_days_held_for(self, current_date: np.datetime64):
        return np.timedelta64(current_date - self.dates[0], 'D').astype(int)

    def sell_all_shares(self, price, date: np.datetime64):
        self.sell_date = date
        self.sell_price = price
        self.total_num_days_held = self.get_num_days_held_for(date)
        self.total_percent_gain = self.get_percent_gain(price)
        self.annualized_return = (1 + self.total_percent_gain) ** (365/self.total_num_days_held) - 1
        self.set_is_invested(False)

    def to_json(self):
        return {
            "entries": [
                {
                    "drop_percent": round(drop_percent*100, 2),
                    "shares": shares,
                    "price": round(price, 3),
                    "date": date.astype('datetime64[ms]').astype(datetime).strftime("%m/%d/%Y")
                } for drop_percent, shares, price, date in zip(self.drop_percentages,
                                                                self.shares,
                                                                self.prices,
                                                                self.dates)
            ],
            "exit": False if self.is_pos_open() else True
        }
    
    def __str__(self):
        string = ""

class StockDropBacktest:
    def __init__(self, ticker, start_date, end_date, pd_min, pg_min, next_quantity: Callable[[int], int]):
        self.ticker: str = ticker
        self.start_date: str = start_date
        self.end_date: str = end_date
        self.percent_drop_min: float = pd_min
        self.percent_gain_min: float = pg_min
        self.next_quantity: Callable[[int], int] = next_quantity
        self.investments = None

    def run(self):
        data = yf.download(self.ticker, self.start_date, self.end_date)
        close_list = list(data["Close"][self.ticker])  # need the [self.ticker] indexing to be compatible with updated yf library
        dates_list = list(data.index.values)

        prev_price = close_list[0]
        investments: List[Position] = []
        for price, date in zip(close_list, dates_list):
            if len(investments) != 0 and investments[-1].is_pos_open():
                percent_gain = investments[-1].get_percent_gain(price)
                if percent_gain >= self.percent_gain_min:
                    investments[-1].sell_all_shares(price, date)

            percent_drop = (price - prev_price) / prev_price
            if (len(investments) == 0 or not investments[-1].is_pos_open()):  # need to open a new position
                if percent_drop <= -self.percent_drop_min:
                    investments.append(Position(percent_drop, 1, price, date))  # always start with 1 share
            elif price <= investments[-1].get_avg_purchase_price() * (1 - self.percent_drop_min) and price <= investments[-1].prices[-1] * (1 - self.percent_drop_min):  # need to average down on previous position
                investments[-1].invest(percent_drop, self.next_quantity(investments[-1].shares[-1]), price, date)

            prev_price = price

        self.investments = investments

    def get_number_satisfied_conditions(self):
        return len(self.investments) if not self.investments[-1].is_pos_open() else len(self.investments) - 1

    def get_metrics(self):
        if self.investments is None:
            return None

        investments = self.investments
        if self.investments[-1].is_pos_open():
            print(f"In a drop as of {self.end_date}. Excluding this drop from metrics")
            investments = self.investments[:-1]

        metrics = {
            "satisfied": len(investments),
            "currently_in_drop": self.investments[-1].is_pos_open(),
            "percent_gain": {"mean": None, "median": None, "min": None, "max": None, "std": None},
            # "annualized_return": {"mean": None, "median": None, "std": None},
            "time_period": {"mean": None, "median": None, "min": None, "max": None, "std": None},
            "num_buys_per_investment": {"mean": None, "median": None, "min": None, "max": None, "std": None},
        }

        get_total_percent_gain = np.vectorize(lambda obj: float(obj.total_percent_gain))
        get_annualized_return = np.vectorize(lambda obj: float(obj.annualized_return))
        get_time_period = np.vectorize(lambda obj: float(obj.total_num_days_held))
        get_num_drops = np.vectorize(lambda obj: float(obj.get_num_drops()))

        metrics["percent_gain"]["mean"] = np.mean(get_total_percent_gain(investments))
        metrics["percent_gain"]["median"] = np.median(get_total_percent_gain(investments))
        metrics["percent_gain"]["std"] = np.std(get_total_percent_gain(investments))
        metrics["percent_gain"]["min"] = np.min(get_total_percent_gain(investments))
        metrics["percent_gain"]["max"] = np.max(get_total_percent_gain(investments))

        # metrics["annualized_return"]["mean"] = np.mean(get_annualized_return(investments))
        # metrics["annualized_return"]["median"] = np.median(get_annualized_return(investments))
        # metrics["annualized_return"]["std"] = np.std(get_annualized_return(investments))

        metrics["time_period"]["mean"] = np.mean(get_time_period(investments))
        metrics["time_period"]["median"] = np.median(get_time_period(investments))
        metrics["time_period"]["std"] = np.std(get_time_period(investments))
        metrics["time_period"]["min"] = np.min(get_time_period(investments))
        metrics["time_period"]["max"] = np.max(get_time_period(investments))

        metrics["num_buys_per_investment"]["mean"] = np.mean(get_num_drops(investments))
        metrics["num_buys_per_investment"]["median"] = np.median(get_num_drops(investments))
        metrics["num_buys_per_investment"]["std"] = np.std(get_num_drops(investments))
        metrics["num_buys_per_investment"]["min"] = np.min(get_num_drops(investments))
        metrics["num_buys_per_investment"]["max"] = np.max(get_num_drops(investments))

        return metrics