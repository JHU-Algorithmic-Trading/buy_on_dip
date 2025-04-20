# region imports
from AlgorithmImports import *
# endregion

from Selection.FundamentalUniverseSelectionModel import FundamentalUniverseSelectionModel
 
class RevisedBuyOnDip(QCAlgorithm):
    def initialize(self):
        self.set_start_date(2000, 1, 1)
        self.set_end_date(2025, 1, 1)
        self.set_cash(100_000)

        self.spy = self.add_equity("SPY", Resolution.DAILY).Symbol
        self.biggest_stock = None
        self.invested_stock = None
        self.entry_price = None
        self.total_allocated = 0
        
        self.universe_settings.resolution = Resolution.DAILY
        self._universe = BiggestMarketCapUniverse(self)
        self.set_universe_selection(self._universe)

        self.schedule.on(self.date_rules.every_day(), self.time_rules.after_market_open("SPY", 1), self.rebalance)

    def rebalance(self):
        if not self._universe.last_selected_symbol:
            return

        if self.biggest_stock != self._universe.last_selected_symbol:
            self.biggest_stock = self._universe.last_selected_symbol
            self.AddEquity(self.biggest_stock, Resolution.DAILY)

        history = self.history(self.biggest_stock, 2, Resolution.DAILY)
        if len(history) < 2:
            return
        
        prev_close = history.iloc[-2]['close']
        curr_close = history.iloc[-1]['close']
        price_drop = (prev_close - curr_close) / prev_close

        # Check if we need to sell due to profit-taking
        if self.invested_stock:
            avg_entry_price = self.entry_price
            current_return = (curr_close - avg_entry_price) / avg_entry_price
            if current_return >= 0.05:
                self.liquidate(self.invested_stock)
                self.invested_stock = None
                self.entry_price = None
                self.total_allocated = 0
                self.set_holdings(self.spy, 1)
                return

        # If price drops more than 5%, buy 9% more of the biggest stock
        if price_drop >= 0.05 and self.total_allocated + 0.09 <= 0.99:
            self.set_holdings(self.spy, -.1)  # Sell 10% of SPY
            self.set_holdings(self.biggest_stock, self.total_allocated + 0.09)
            self.total_allocated += 0.09

            # Update entry price as a weighted average
            if not self.invested_stock:
                self.invested_stock = self.biggest_stock
                self.entry_price = curr_close
            else:
                self.entry_price = (self.entry_price * (self.total_allocated - 0.09) + curr_close * 0.09) / self.total_allocated






class BiggestMarketCapUniverse(FundamentalUniverseSelectionModel):
    def __init__(self, algorithm):
        super().__init__(True)  # True = use dynamic universe selection
        self.algorithm = algorithm
        self.last_selected_symbol = None
    
    def SelectCoarse(self, algorithm, coarse):
        filtered = [x for x in coarse if x.HasFundamentalData and x.Market == Market.USA]
        return [x.Symbol for x in filtered]
    
    def SelectFine(self, algorithm, fine):
        if not fine:
            return []
        fine = sorted(fine, key=lambda x: x.MarketCap, reverse=True)
        self.last_selected_symbol = fine[0].Symbol
        return [self.last_selected_symbol]