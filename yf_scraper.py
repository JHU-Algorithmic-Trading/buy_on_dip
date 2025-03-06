from yahooquery import Screener, Ticker
from pprint import pprint



def get_top_losers(count=50):
	screener = Screener()
	data = screener.get_screeners("day_losers", count)

	if "day_losers" in data and "quotes" in data["day_losers"]:
		losers = data["day_losers"]["quotes"]
		symbols = [stock['symbol'] for stock in losers]
		ticker_data = Ticker(symbols).asset_profile
		return [{
            'symbol': stock['symbol'],
            'name': stock.get('shortName', 'N/A'),
            'price': stock.get('regularMarketPrice', 'N/A'),
            'change': stock.get('regularMarketChangePercent', 'N/A'),
            'sector': ticker_data.get(stock['symbol'], {}).get('sector', 'N/A'),
            'market_cap': stock.get('marketCap', 'N/A'),
						'52_week_range': [float(elem) for elem in stock.get('fiftyTwoWeekRange', 'N/A').split(" - ")]
		} for stock in losers] 
	else:
		return []

if __name__ == "__main__":
    top_losers = get_top_losers()
    pprint(top_losers)