# Zeyn Schweyk

import numpy
import datetime
from dataclasses import dataclass
import yfinance as yf

#################### Input ####################

ticker = "GXO"
start_date = "1984-01-01"
end_date = "2025-02-12"
percent_drop_min = .05
percent_gain_min = .05

quantities = [1 for i in range(0, 100)]

#############################################

for name, _input in (("Ticker", ticker), ("Start Date", start_date), ("End Date", end_date), ("Min Percent Drop", percent_drop_min), ("Min Percent Gain", percent_gain_min), ("Share Quantities", quantities)):
    if name == "Min Percent Drop" or name == "Min Percent Gain":
        print(f"{name}: {round(_input * 100, 2)}%")
    else:
        print(f"{name}: {_input}")
print(f"{'-'*10}\n\n\n")


@dataclass
class Metrics:
    Mean: float = None
    Median: float = None
    Min: float  = None
    Mode: float = None
    Std: float = None


metrics = {
    "time": Metrics(),
    "gain": Metrics(),
    "num_purchases": Metrics()
}






def calc_mean_price(buy_prices: list, buy_quantities: list):
    return numpy.dot(buy_prices, buy_quantities) / sum(buy_quantities)

data = yf.download(ticker, start_date, end_date)
close_list = list(data["Close"][ticker])
dates_list = list(data.index.values)

prev_price = close_list[0]
buy_dates = []
buy_prices = []
buy_quantities = []
for price, date in zip(close_list, dates_list):
    if len(buy_prices) != 0:
        average_buy_price = calc_mean_price(buy_prices, buy_quantities)
        percent_gain = (price - average_buy_price) / average_buy_price
        if percent_gain >= percent_gain_min:
            num_days = numpy.timedelta64(date - buy_dates[0], 'D').astype(int)
            # annualized_return = (1 + percent_gain) ** (365/num_days) - 1
            annualized_return = percent_gain * (365/num_days)
            print(f"Investment gained {round(percent_gain * 100, 2)}% on {str(date)[:10]}. Span of {num_days} days. Sold {sum(buy_quantities)} shares at ${round(price, 2)}")
            print(f"Annualized return: {round(annualized_return * 100, 2)}%\n")
            buy_prices = []
            buy_dates = []
            buy_quantities = []

    
    percent_drop = (price - prev_price) / prev_price
    msg = None
    condition_satisfied = False
    if len(buy_prices) == 0:
        if percent_drop <= -percent_drop_min:
            msg = f"{ticker} dropped {round(percent_drop * 100, 2)}% on {str(date)[:10]}"
            condition_satisfied = True
    elif price <= calc_mean_price(buy_prices, buy_quantities) * (1-percent_drop_min) and price <= buy_prices[-1] * (1-percent_drop_min):
        msg = f"{ticker} is below the mean by {round((1 - price/calc_mean_price(buy_prices, buy_quantities)) * 100, 2)}%>={round(percent_drop_min * 100, 2)}% and significantly below last purchase price on {str(date)[:10]}"
        condition_satisfied = True
    
    if condition_satisfied:
        buy_prices.append(price)
        buy_dates.append(date)
        buy_quantities.append(quantities[len(buy_quantities)])
        print(f"{msg}. Bought {buy_quantities[-1]} shares at ${round(buy_prices[-1], 3)}. Average price at ${round(calc_mean_price(buy_prices, buy_quantities), 3)}.")

    prev_price = price


