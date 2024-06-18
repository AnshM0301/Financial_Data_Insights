# # # home/services.py

# # import requests
# # from django.conf import settings

# # def fetch_market_performance():
# #     indices = ['SPY', 'DJI', 'IXIC']
# #     data = []
# #     for index in indices:
# #         url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={index}&apikey={settings.ALPHA_VANTAGE_API_KEY}'
# #         response = requests.get(url).json()
# #         if "Global Quote" in response:
# #             data.append({
# #                 'name': index,
# #                 'value': response['Global Quote']['05. price'],
# #                 'change': response['Global Quote']['10. change percent']
# #             })
# #     return data

# # def fetch_top_gainers_and_losers():
# #     url = f'https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={settings.ALPHA_VANTAGE_API_KEY}'
# #     response = requests.get(url).json()
# #     top_gainers = response.get('top_gainers', [])
# #     top_losers = response.get('top_losers', [])
# #     return top_gainers, top_losers

# # def fetch_featured_news():
# #     url = f'https://newsapi.org/v2/top-headlines?category=business&apiKey={settings.NEWS_API_KEY}'
# #     response = requests.get(url).json()
# #     articles = response.get('articles', [])
# #     return articles

# # def fetch_historical_data(symbol):
# #     url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={settings.ALPHA_VANTAGE_API_KEY}'
# #     response = requests.get(url).json()
# #     time_series = response.get('Time Series (Daily)', {})
# #     dates = list(time_series.keys())
# #     prices = [float(time_series[date]['4. close']) for date in dates]
# #     return dates, prices

# # def fetch_market_analysis():
# #     # Placeholder for market analysis. You might want to write your custom logic here.
# #     return "The market is experiencing significant volatility due to recent economic events."


# from alpha_vantage.timeseries import TimeSeries

# def fetch_real_time_price(symbol, api_key):
#     """Fetches real-time price for a given symbol using Alpha Vantage.

#     Args:
#         symbol (str): The stock symbol (e.g., ".INX").
#         api_key (str): Your Alpha Vantage API key.

#     Returns:
#         float: The real-time price if successful, None otherwise.
#     """

#     try:
#         # Create Alpha Vantage TimeSeries object
#         ts = TimeSeries(key=api_key, outputsize='compact')

#         # Fetch real-time intraday data for the symbol
#         data, meta_info = ts.get_intraday(symbol, interval='1min', outputsize='compact')

#         if 'Realtime Stock Quote' in meta_info:
#             # Extract the latest price (assuming success)
#             return float(data['Realtime Stock Quote']['5. price'])
#         else:
#             print(f"Error fetching data for {symbol}")
#             return None

#     except Exception as e:
#         print(f"Error fetching real-time price: {e}")
#         return None

