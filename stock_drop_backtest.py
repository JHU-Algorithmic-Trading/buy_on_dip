import yfinance as yf
import numpy as np
from typing import List, Callable
from datetime import datetime



class PositionSet:
    def __init__(self, min_drop):
        self.pos_state = True
        self.min_drop = min_drop
        self.day_changes = []
        self.shares = []
        self.prices = []
        self.dates = []
        self.total_realized_gain = 0
        self.annualized_return = None
        self.sell_date = None
        self.sell_price = None
        self.day_duration = None

    def set_pos_state(self, pos_state):
        self.pos_state = pos_state

    def get_pos_state(self):
        """ True means open, False means closed """
        return self.pos_state

    def buy(self, shares: int, price: float, date: np.datetime64, day_change):
        self.day_changes.append(day_change)
        self.shares.append(shares)
        self.prices.append(price)
        self.dates.append(date)

    def get_num_drops(self):
        return len(self.day_changes)

    def get_avg_purchase_price(self, i=None):
        if i is None:
            return np.dot(self.shares, self.prices) / sum(self.shares)
        return np.dot(self.shares[:i+1], self.prices[:i+1]) / sum(self.shares[:i+1])

    def get_current_gain(self, current_price):
        pps = self.get_avg_purchase_price()
        return (current_price - pps) / pps

    def get_num_days_held_for(self, current_date: np.datetime64):
        return np.timedelta64(current_date - self.dates[0], 'D').astype(int)

    def sell_all_shares(self, price, date: np.datetime64, day_change):
        self.sell_day_change = day_change
        self.sell_date = date
        self.sell_price = price
        self.day_duration = int(self.get_num_days_held_for(date))
        self.total_realized_gain = float(self.get_current_gain(price))
        # self.annualized_return = (1 + self.total_percent_gain) ** (365/self.total_num_days_held) - 1
        self.annualized_return = float(self.total_realized_gain * (365 / self.day_duration))
        self.set_pos_state(False)
        
        
    def to_dict(self):            
        return {
            "entries": [
                {
                    "day_change_pct": round(drop_percent*100, 2),
                    "num_shares": shares,
                    "buy_price": round(price, 3),
                    "avg_purchase_price": round(self.get_avg_purchase_price(i), 3),
                    "date": date.astype('datetime64[ms]').astype(datetime).strftime("%m/%d/%Y")
                } for i, (drop_percent, shares, price, date) in enumerate(zip(self.day_changes,
                                                                self.shares,
                                                                self.prices,
                                                                self.dates))
            ],
            "exit": False if self.get_pos_state() else {
                "date": self.sell_date.astype('datetime64[ms]').astype(datetime).strftime("%m/%d/%Y"),
                "day_change_pct": round(self.sell_day_change * 100, 2),
                "investment_gain_pct": round(self.total_realized_gain * 100, 2),
                "day_duration": self.day_duration,
                "num_shares": sum(self.shares),
                "sell_price": round(self.sell_price, 3),
                "annualized_return_pct": round(self.annualized_return * 100, 2)
            }
        }
    
    def __str__(self):
        result_dict = self.to_dict()

        record0 = result_dict["entries"][0]
        string = f"{record0['date']}: Dropped {record0['day_change_pct']}% | Bought {record0['num_shares']} shares at ${record0['buy_price']} | Avg purchase price at {record0['avg_purchase_price']}\n"

        prev_record = record0
        for record in result_dict["entries"][1:]:
            pct_drop_from_prev_purchase_price = round((prev_record["buy_price"] - record["buy_price"]) / prev_record["buy_price"] * 100, 3)
            string += f"{record['date']}: Dropped {record['day_change_pct']}% | {pct_drop_from_prev_purchase_price}%>={round(self.min_drop * 100, 2)}% below last purchase price | Bought {record['num_shares']} shares at ${record['buy_price']} | Avg purchase price = ${record['avg_purchase_price']}\n"
            prev_record = record
        
        exit = result_dict["exit"]
        if exit:
            string += f"{exit['date']}: Gained {exit['day_change_pct']}% | Investment gained {exit['investment_gain_pct']}% | Span of {exit['day_duration']} days | Sold {exit['num_shares']} shares at ${exit['sell_price']}\n"
            string += f"Annualized return: {exit['annualized_return_pct']}%\n"
        
        return string

class StockDropBacktest:
    def __init__(self, ticker, start_date, end_date, min_drop, min_gain, next_quantity: Callable[[int], int]):
        self.ticker: str = ticker
        self.start_date: str = start_date
        self.end_date: str = end_date
        self.min_drop: float = min_drop
        self.min_gain: float = min_gain
        self.next_quantity: Callable[[int], int] = next_quantity
        self.position_sets = None

    def run(self):
        data = yf.download(self.ticker, self.start_date, self.end_date)
        close_list = list(data["Close"][self.ticker])  # need the [self.ticker] indexing to be compatible with updated yf library
        dates_list = list(data.index.values)

        prev_price = close_list[0]
        position_sets: List[PositionSet] = []
        for price, date in zip(close_list, dates_list):
            day_change = (price - prev_price) / prev_price
            
            if len(position_sets) != 0 and position_sets[-1].get_pos_state():
                gain = position_sets[-1].get_current_gain(price)
                if gain >= self.min_gain:
                    position_sets[-1].sell_all_shares(price, date, day_change)
            
            if len(position_sets) == 0 or not position_sets[-1].get_pos_state():  # need to open a new position
                if day_change <= -self.min_drop:
                    ps = PositionSet(self.min_drop)
                    ps.buy(1, price, date, day_change)
                    position_sets.append(ps)  # always start with 1 share
            elif price <= position_sets[-1].get_avg_purchase_price() * (1 - self.min_drop) and \
                 price <= position_sets[-1].prices[-1] * (1 - self.min_drop):  # only this condition matters
                position_sets[-1].buy(self.next_quantity(position_sets[-1].shares[-1]), price, date, day_change)

            prev_price = price

        self.position_sets = position_sets


    def get_number_satisfied_conditions(self):
        return len(self.position_sets) if not self.position_sets[-1].get_pos_state() else len(self.position_sets) - 1

    def get_metrics(self):
        if self.position_sets is None:
            return None

        position_sets = self.position_sets
        if self.position_sets[-1].get_pos_state():
            # print(f"Currently in a drop and excluding this drop from metrics")
            position_sets = self.position_sets[:-1]

        metrics = {
            "num_occurrences": len(position_sets),
            "currently_in_drop": self.position_sets[-1].get_pos_state(),
            "percent_gain": {"mean": None, "median": None, "min": None, "max": None, "std": None},
            # "annualized_return": {"mean": None, "median": None, "std": None},
            "time_period": {"mean": None, "median": None, "min": None, "max": None, "std": None},
            "num_buys_per_investment": {"mean": None, "median": None, "min": None, "max": None, "std": None},
        }

        get_total_percent_gain = np.vectorize(lambda obj: obj.total_realized_gain * 100)
        # get_annualized_return = np.vectorize(lambda obj: float(obj.annualized_return))
        get_time_period = np.vectorize(lambda obj: obj.day_duration)
        get_num_drops = np.vectorize(lambda obj: obj.get_num_drops())
        rounding_dec_places = 3

        tot_pct_gains = get_total_percent_gain(position_sets)
        metrics["percent_gain"]["mean"] = round(float(np.mean(tot_pct_gains)), rounding_dec_places)
        metrics["percent_gain"]["median"] = round(float(np.median(tot_pct_gains)), rounding_dec_places)
        metrics["percent_gain"]["std"] = round(float(np.std(tot_pct_gains)), rounding_dec_places)
        metrics["percent_gain"]["min"] = round(float(np.min(tot_pct_gains)), rounding_dec_places)
        metrics["percent_gain"]["max"] = round(float(np.max(tot_pct_gains)), rounding_dec_places)

        # metrics["annualized_return"]["mean"] = np.mean(get_annualized_return(investments))
        # metrics["annualized_return"]["median"] = np.median(get_annualized_return(investments))
        # metrics["annualized_return"]["std"] = np.std(get_annualized_return(investments))

        time_periods = get_time_period(position_sets)
        metrics["time_period"]["mean"] = round(float(np.mean(time_periods)), rounding_dec_places)
        metrics["time_period"]["median"] = round(float(np.median(time_periods)), rounding_dec_places)
        metrics["time_period"]["std"] = round(float(np.std(time_periods)), rounding_dec_places)
        metrics["time_period"]["min"] = round(float(np.min(time_periods)), rounding_dec_places)
        metrics["time_period"]["max"] = round(float(np.max(time_periods)), rounding_dec_places)

        num_drops = get_num_drops(position_sets)
        metrics["num_buys_per_investment"]["mean"] = round(float(np.mean(num_drops)), rounding_dec_places)
        metrics["num_buys_per_investment"]["median"] = round(float(np.median(num_drops)), rounding_dec_places)
        metrics["num_buys_per_investment"]["std"] = round(float(np.std(num_drops)), rounding_dec_places)
        metrics["num_buys_per_investment"]["min"] = round(float(np.min(num_drops)), rounding_dec_places)
        metrics["num_buys_per_investment"]["max"] = round(float(np.max(num_drops)), rounding_dec_places)

        return metrics