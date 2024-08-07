from django.shortcuts import render
from django.http import JsonResponse
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots 
import pandas as pd
from django.contrib.auth.decorators import login_required
import requests

import numpy as np
import json

NEWS_API_KEY = 'a99f21bd3dae43bc962eb23c86600461' 

@login_required(login_url="/UserAuth/login/")
def strategies(request):
    company_name = request.GET.get('company_name', 'GOOG')
    print(f"Company Name from query: {company_name}")  # Debug print statement
    news_articles = fetch_company_news(company_name)
    technical_chart, total_return, sharpe_ratio, max_drawdown, indicator_description = technical_analysis(request, company_name)
    context = {
        'company_name': company_name,
        'news_articles': news_articles,
        'technical_chart': technical_chart,
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'indicator_description': indicator_description
    }
    return render(request, 'strategies/strategies.html', context)

def search_company(request):
    if request.method == 'GET':
        company_name = request.GET.get('company_name', 'GOOG')
        ticker = company_name.upper()
        time_range = request.GET.get('time_range', '5y')
        if ticker:
            timeframe = request.GET.get('timeframe', '1d')
            hist_df, data = fetch_stock_data(ticker, timeframe, time_range)
            if hist_df is not None and data is not None:
                fig = create_candlestick_chart(hist_df, data, company_name)
                graph_div = fig.to_html(full_html=False)
                latest_price = data['Close'].iloc[-1]
                financial_details = fetch_financial_details(ticker)
                fig_performance, fig_debt, fig_conversion, fig_roe_roa = create_financial_charts(ticker, time_range)

                charts = {
                    'performance': fig_performance.to_html(full_html=False),
                    'debt': fig_debt.to_html(full_html=False),
                    'conversion': fig_conversion.to_html(full_html=False),
                    'roe_roa': fig_roe_roa.to_html(full_html=False)
                }

                return JsonResponse({
                    'graph_div': graph_div,
                    'company_name': company_name.capitalize(),
                    'latest_price': latest_price,
                    'financial_details': financial_details,
                    'charts': charts,
                }, status=200)
            else:
                print(f"No data available for {ticker} with time range {time_range} and timeframe {timeframe}")
                return JsonResponse({'error': 'Company not found or no data available'}, status=404)
        else:
            print("Ticker symbol not provided")
            return JsonResponse({'error': 'Ticker symbol not provided'}, status=400)
        
def technical_analysis_view(request, ticker):
    if request.method == 'GET':
        technical_chart, total_return, sharpe_ratio, max_drawdown, indicator_description = technical_analysis(request, ticker)
        return JsonResponse({
            'technical_chart': technical_chart,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'indicator_description': indicator_description
        }, status=200)
    
def fetch_company_news_view(request):
    company_name = request.GET.get('company_name', 'GOOG')
    news_articles = fetch_company_news(company_name)
    financial_details = fetch_financial_details(company_name)
    full_company_name = financial_details.get("Name", company_name)
    print(f"Full company name: {full_company_name}")  # Debug statement
    return JsonResponse({'news_articles': news_articles, 'full_company_name': full_company_name})

def fetch_stock_data(ticker, interval, time_range):
    try:
        data = yf.download(ticker, period=time_range, interval=interval)
        if data.empty:
            print(f"No data found for ticker: {ticker}, period: {time_range}, interval: {interval}")
            return None, None
        
         # Determine if the data is intraday or daily/weekly
        if interval in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h']:
            hist_df = data.reset_index()
            hist_df['Date'] = pd.to_datetime(hist_df['Datetime'])
        else:
            hist_df = data.reset_index()
            hist_df['Date'] = pd.to_datetime(hist_df['Date'])
        hist_df.set_index('Date', inplace=True)

        return hist_df, data 
    except Exception as e:
        print(f"Error fetching data: {e}")      
        return None, None

def fetch_financial_details(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        financial_details = {
            'Name': info.get('shortName', 'N/A'),
            'Market Capitalization': info.get('marketCap', 'N/A'),
            'Dividend Yield': info.get('dividendYield', 'N/A'),
            'PE Ratio': info.get('trailingPE', 'N/A'),
            'EPS': info.get('trailingEps', 'N/A'),
            'Net Income': info.get('netIncomeToCommon', 'N/A'),
            'Revenue': info.get('totalRevenue', 'N/A'),
            'Shares Float': info.get('sharesOutstanding', 'N/A'),
            'Beta': info.get('beta', 'N/A'),
            'Sector': info.get('sector', 'N/A'),
            'Industry': info.get('industry', 'N/A'),
            'Headquarters': info.get('country','N/A'),
            'Summary' : info.get('longBusinessSummary', 'N/A'),
            'Total Employees' : info.get('fullTimeEmployees', 'N/A'),
            'Website' : info.get('website', 'N/A'),
        }
        return financial_details
    except Exception as e:
        print(f"Error fetching financial details: {e}")
        return {}

def create_candlestick_chart(hist_df, data, company_name):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', yaxis='y2'))

    num_dates = len(hist_df.index)
    step = max(1, round(num_dates / 20))  # Ensure the step is at least 1

    fig.update_layout(
        title=f'{company_name.capitalize()} Stock Price and Volume',
        yaxis_title='Stock Price',
        xaxis_rangeslider_visible=False,
        yaxis2=dict(title='Volume', overlaying='y', side='right',position=1.0, range=[0, 300_000_000]),
        xaxis=dict(type='category', tickangle=-45, tickmode='array', 
                        tickvals=hist_df.index[::step],  # Adjust this to get 2-3 months interval
                        ticktext=[date.strftime('%Y-%m-%d') for date in hist_df.index[::step]],
                        tickformat='%Y-%m-%d',nticks=20),
        margin=dict(l=0, r=0, t=30, b=20),
        height=600,
        width=1200
    )
    return fig


def get_company_data(ticker):
    company = yf.Ticker(ticker)
    financial_data = company.financials.transpose()
    balance_sheet = company.balance_sheet.transpose()
    cash_flow = company.cashflow.transpose()
    earnings = company.quarterly_financials.transpose()

    return financial_data, balance_sheet, cash_flow, earnings

def create_financial_charts(ticker, time_range):
    financial_data, balance_sheet, cash_flow, earnings = get_company_data(ticker)

    if time_range == '5y':
        financial_data = financial_data.tail(5)
        balance_sheet = balance_sheet.tail(5)
        cash_flow = cash_flow.tail(5)
        earnings = earnings.tail(5)
    elif time_range == '5q':
        financial_data = financial_data.tail(5)
        balance_sheet = balance_sheet.tail(5)
        cash_flow = cash_flow.tail(5)
        earnings = earnings.tail(5)



    # # Find the maximum length among the DataFrames
    # max_length = max(len(financial_data), len(balance_sheet), len(cash_flow), len(earnings))

    # # Pad shorter DataFrames with NaNs or zeros to match the max_length
    # def pad_dataframe(df, length):
    #     if len(df) < length:
    #         padding_length = length - len(df)
    #         padding = pd.DataFrame(index=[None]*padding_length, columns=df.columns)
    #         df = pd.concat([padding, df])
    #     return df

    # financial_data = pad_dataframe(financial_data, max_length)
    # balance_sheet = pad_dataframe(balance_sheet, max_length)
    # cash_flow = pad_dataframe(cash_flow, max_length)
    # earnings = pad_dataframe(earnings, max_length)

    # # Define and fill missing data with zeros if necessary
    # revenue = financial_data.get('Total Revenue', pd.Series([0] * max_length, index=financial_data.index)).astype(float)
    # net_income = financial_data.get('Net Income', pd.Series([0] * max_length, index=financial_data.index)).astype(float)


    # Ensure lengths match
    min_length = min(len(financial_data), len(balance_sheet), len(cash_flow), len(earnings))

    financial_data = financial_data.tail(min_length)
    balance_sheet = balance_sheet.tail(min_length)
    cash_flow = cash_flow.tail(min_length)
    earnings = earnings.tail(min_length)

    revenue = financial_data.get('Total Revenue', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)
    cogs = financial_data.get('Cost Of Revenue', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)
    gross_profit = financial_data.get('Gross Profit', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)
    operating_expenses = financial_data.get('Operating Expense', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)
    operating_income = financial_data.get('Operating Income', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)
    non_op_expenses = financial_data.get('Other Non Operating Income Expenses', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)
    taxes = financial_data.get('Tax Provision', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)
    net_income = financial_data.get('Net Income', pd.Series([0]*len(financial_data), index=financial_data.index)).astype(float)

    fig_performance = go.Figure()
    fig_performance.add_trace(go.Bar(x=financial_data.index, y=revenue, name='Revenue'))
    fig_performance.add_trace(go.Bar(x=financial_data.index, y=net_income, name='Net Income'))
    fig_performance.add_trace(go.Scatter(x=financial_data.index, y=(net_income / revenue) * 100, name='Net Margin %', yaxis='y2'))

    fig_performance.update_layout(
        title='Performance',
        xaxis_title='Year',
        yaxis_title='Revenue & Net Income',
        yaxis2=dict(title='Net Margin %', overlaying='y', side='right'),
        barmode='group'
    )

    fig_debt = go.Figure()
    fig_debt.add_trace(go.Bar(x=cash_flow.index, y=balance_sheet.get('Long Term Debt', pd.Series([0]*len(balance_sheet), index=balance_sheet.index)).astype(float), name='Debt'))
    fig_debt.add_trace(go.Bar(x=cash_flow.index, y=cash_flow.get('Free Cash Flow', pd.Series([0]*len(cash_flow), index=cash_flow.index)).astype(float), name='Free Cash Flow'))
    fig_debt.add_trace(go.Bar(x=cash_flow.index, y=balance_sheet.get('Cash And Cash Equivalents', pd.Series([0]*len(balance_sheet), index=balance_sheet.index)).astype(float), name='Cash & Equivalents'))

    fig_debt.update_layout(
        title='Debt Level and Coverage',
        xaxis_title='Year',
        yaxis_title='Amount',
        barmode='group'
    )

    fig_conversion = go.Figure()
    fig_conversion.add_trace(go.Waterfall(
        name="Revenue Conversion",
        orientation="v",
        measure=["relative", "relative", "total", "relative", "total", "relative", "relative", "total"],
        x=["Revenue", "COGS", "Gross Profit", "Operating Expenses", "Operating Income", "Non-Operating Expenses", "Taxes", "Net Income"],
        textposition="outside",
        text=[f"{value:,}" for value in [revenue.sum(), -cogs.sum(), gross_profit.sum(), -operating_expenses.sum(), operating_income.sum(), -non_op_expenses.sum(), -taxes.sum(), net_income.sum()]],
        y=[revenue.sum(), -cogs.sum(), gross_profit.sum(), -operating_expenses.sum(), operating_income.sum(), -non_op_expenses.sum(), -taxes.sum(), net_income.sum()],
        connector={"line": {"color": "rgb(63, 63, 63)"}}
    ))

    fig_conversion.update_layout(
        title="Revenue Conversion to Profit",
        showlegend=True
    )

    total_assets = balance_sheet.get('Total Assets', pd.Series([0]* min_length, index = balance_sheet.index)).astype(float)
    total_equity = balance_sheet.get('Stockholders Equity', pd.Series([0] * min_length, index = balance_sheet.index)).astype(float)


    roe = (net_income / total_equity) * 100
    roa = (net_income / total_assets) * 100
    # except KeyError as e:
    #     print(f"Error calculating ROE and ROA: {e}")
        

    fig_roe_roa = go.Figure()
    fig_roe_roa.add_trace(go.Bar(
        x=roe.index,
        y=roe,
        name='ROE',
        marker_color='indianred'
    ))

    fig_roe_roa.add_trace(go.Bar(
        x=roa.index,
        y=roa,
        name='ROA',
        marker_color='lightsalmon'
    ))

    fig_roe_roa.update_layout(
        title='ROE and ROA',
        xaxis_title='Date',
        yaxis_title='Percentage',
        barmode='group'
    )

    return fig_performance, fig_debt, fig_conversion, fig_roe_roa


def technical_analysis(request, ticker):
    data = yf.download(tickers=ticker, period='1y', interval='1d')
    hist_df = data.reset_index()
    hist_df['Date'] = pd.to_datetime(hist_df['Date'])
    hist_df.set_index('Date', inplace=True)

                       
    indicators = request.GET.getlist('indicators', 'VWAP')

    print("Indicators:", indicators)  # Debug statement

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price'
    ))
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='Volume', yaxis='y2'))


    indicator_description = ""

    total_return = ""
    sharpe_ratio = ""
    max_drawdown = ""


    # Trend status
    # trend_status = "Neutral"
    # if data['Close'].iloc[-1] > data['Close'].iloc[-2]:
    #     trend_status = "Bullish"
    #  elif data['Close'].iloc[-1] < data['Close'].iloc[-2]:
#         trend_status = "Bearish"
    #     indicator_description += f"Trend Status: {trend_status}\n"
    #     
    # else:
    #   indicator_description += f"Trend Status: Neutral\n"

    confirmation_period=20
   
    if 'vwap' in indicators:
        vwap = (data['Volume'] * (data['High'] + data['Low'] + data['Close']) / 3).cumsum() / data['Volume'].cumsum()
        print("VWAP calculated")  # Debug statement
        indicator_description += "<p>VWAP is the Volume Weighted Average Price. It provides insight into the average price a security has traded at throughout the day, based on both volume and price. It is calculated by dividing the sum of the product of the price and volume for each transaction by the total volume for the period.</p>"

        data['vwap'] = vwap

        short_window = 20
        data['short_mavg'] = data['Close'].rolling(window=short_window, min_periods=1).mean()

        # Generate buy signals
        data['Buy_Signal'] = np.where((data['short_mavg'] > data['vwap']) & (data['short_mavg'].shift(1) <= data['vwap'].shift(1)), 1, 0)
        # Generate sell signals
        data['Sell_Signal'] = np.where((data['short_mavg'] < data['vwap']) & (data['short_mavg'].shift(1) >= data['vwap'].shift(1)), -1, 0)

        # Combine buy and sell signals into a single signal column
        data['Confirmed_Signal'] = data['Buy_Signal'] + data['Sell_Signal']

        # Debug output to inspect signals
        print(data[['Close', 'vwap', 'short_mavg', 'Buy_Signal', 'Sell_Signal', 'Confirmed_Signal']].tail(30))

        # Calculate returns based on the confirmed signals
        data['Returns'] = data['Close'].pct_change()
        data['Strategy_Returns'] = data['Returns'] * data['Confirmed_Signal'].shift(1)
        data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()

        # Performance metrics
        total_return = data['Cumulative_Returns'].iloc[-1] - 1
        sharpe_ratio = data['Strategy_Returns'].mean() / data['Strategy_Returns'].std() * (252**0.5)  # Annualized Sharpe ratio
        max_drawdown = (data['Cumulative_Returns'].cummax() - data['Cumulative_Returns']).max()

        fig.add_trace(go.Scatter(x=data.index, y=data['vwap'], mode='lines', name='VWAP'))
        fig.add_trace(go.Scatter(x=data.index, y=data['short_mavg'], mode='lines', name='Short-term Moving Average'))

        buy_signals = data[data['Buy_Signal'] == 1]
        sell_signals = data[data['Sell_Signal'] == -1]

        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['Close'],
            mode='markers',
            marker=dict(color='green', symbol='triangle-up', size=10),
            name='Buy Signal'
        ))

        fig.add_trace(go.Scatter(
            x=sell_signals.index,
            y=sell_signals['Close'],
            mode='markers',
            marker=dict(color='red', symbol='triangle-down', size=10),
            name='Sell Signal'
        ))

        fig.update_layout(title='Backtesting Results with VWAP and Short-term Moving Average', xaxis_title='Date', yaxis_title='Price')



    if 'ema50' in indicators:
        ema50 = data['Close'].ewm(span=50, adjust=False).mean()
        print("EMA50 calculated")  # Debug statement
        fig.add_trace(go.Scatter(x=data.index, y=ema50, mode='lines', name='50-Day EMA'))
        indicator_description += "<p>The 50-Day EMA (Exponential Moving Average) is a popular technical indicator used to smooth price data and identify trends over a medium-term period.</p>"

    if 'ema200' in indicators:
        ema200 = data['Close'].ewm(span=200, adjust=False).mean()
        print("EMA200 calculated")  # Debug statement
        fig.add_trace(go.Scatter(x=data.index, y=ema200, mode='lines', name='200-Day EMA'))
        indicator_description += "<p>The 200-Day EMA is a long-term trend indicator.</p>"

    if 'bollinger_bands' in indicators:
        # Calculate Bollinger Bands
        rolling_mean = data['Close'].rolling(window=20).mean()
        rolling_std = data['Close'].rolling(window=20).std()
        upper_band = rolling_mean + (rolling_std * 2)
        lower_band = rolling_mean - (rolling_std * 2)
        print("Bollinger Bands calculated")
        
        indicator_description += "<p>Bollinger Bands are a volatility indicator that consists of a set of three lines drawn in relation to securities prices. The middle line is usually a simple moving average, and the upper and lower lines are derived by adding and subtracting a standard deviation (usually two) from the middle line.</p>"

        # Detect Bollinger Band Squeeze
        data['BandWidth'] = (upper_band - lower_band) / rolling_mean
        squeeze_threshold = data['BandWidth'].rolling(window=120).min()
        data['Squeeze'] = data['BandWidth'] == squeeze_threshold

        # Reversal signals
        data['Buy_Signal'] = ((data['Close'] < lower_band) & (data['Close'].shift(1) < data['Open'].shift(1)) & (data['Close'] > data['Open'])).astype(int)
        data['Sell_Signal'] = ((data['Close'] > upper_band) & (data['Close'].shift(1) > data['Open'].shift(1)) & (data['Close'] < data['Open'])).astype(int)

        # Use middle band as support/resistance
        data['Middle_Band_Buy'] = ((data['Close'] > rolling_mean) & (data['Close'].shift(1) < rolling_mean)).astype(int)
        data['Middle_Band_Sell'] = ((data['Close'] < rolling_mean) & (data['Close'].shift(1) > rolling_mean)).astype(int)

        # Combine all signals
        data['Buy_Signal'] = data[['Buy_Signal', 'Middle_Band_Buy']].max(axis=1)
        data['Sell_Signal'] = data[['Sell_Signal', 'Middle_Band_Sell']].max(axis=1)
        data['Confirmed_Signal'] = data['Buy_Signal'] - data['Sell_Signal']

        # Debug output to inspect signals
        # print(data[['Close', 'upper_band', 'lower_band', 'Buy_Signal', 'Sell_Signal', 'Confirmed_Signal']].tail(30))

        # Calculate returns based on the confirmed signals
        data['Returns'] = data['Close'].pct_change()
        data['Strategy_Returns'] = data['Returns'] * data['Confirmed_Signal'].shift(1)
        data['Cumulative_Returns'] = (1 + data['Strategy_Returns']).cumprod()

        # Performance metrics
        total_return = data['Cumulative_Returns'].iloc[-1] - 1
        sharpe_ratio = data['Strategy_Returns'].mean() / data['Strategy_Returns'].std() * (252**0.5)  # Annualized Sharpe ratio
        max_drawdown = (data['Cumulative_Returns'].cummax() - data['Cumulative_Returns']).max()

        fig.add_trace(go.Scatter(x=data.index, y=upper_band, mode='lines', name='Upper Bollinger Band'))
        fig.add_trace(go.Scatter(x=data.index, y=lower_band, mode='lines', name='Lower Bollinger Band'))
        fig.add_trace(go.Scatter(x=data.index, y=rolling_mean, mode='lines', name='Middle Bollinger Band'))

        buy_signals = data[data['Buy_Signal'] == 1]
        sell_signals = data[data['Sell_Signal'] == 1]
        
        fig.add_trace(go.Scatter(
            x=buy_signals.index,
            y=buy_signals['Close'],
            mode='markers',
            marker=dict(color='green', symbol='triangle-up', size=10),
            name='Buy Signal'
        ))

        fig.add_trace(go.Scatter(
            x=sell_signals.index,
            y=sell_signals['Close'],
            mode='markers',
            marker=dict(color='red', symbol='triangle-down', size=10),
            name='Sell Signal'
        ))

        fig.update_layout(title='Backtesting Results with Bollinger Bands', xaxis_title='Date', yaxis_title='Price')

    if 'rsi' in indicators:
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).ewm(span=14, adjust=False).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(span=14, adjust=False).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        print("RSI calculated")  # Debug statement
        fig.add_trace(go.Scatter(x=data.index, y=rsi, mode='lines', name='RSI'))
        # fig.add_hline(y=70, line_width=1, line_color='red', line_dash='dash', name='Overbought (70)')
        # fig.add_hline(y=30, line_width=1, line_color='green', line_dash='dash', name='Oversold (30)')
        indicator_description += "<p>RSI (Relative Strength Index) is a momentum oscillator that measures the speed and change of price movements. It oscillates between zero and 100. Traditionally, and according to Wilder, RSI is considered overbought when above 70 and oversold when below 30.</p>"

    if 'macd' in indicators:
        ema12 = data['Close'].ewm(span=12, adjust=False).mean()
        ema26 = data['Close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        print("MACD calculated")  # Debug statement
        fig.add_trace(go.Scatter(x=data.index, y=macd, mode='lines', name='MACD'))
        fig.add_trace(go.Scatter(x=data.index, y=signal, mode='lines', name='MACD Signal Line'))
        indicator_description += "<p>MACD (Moving Average Convergence Divergence) is a trend-following momentum indicator that shows the relationship between two moving averages of a security’s price.</p>"

    if 'fibonacci' in indicators:
        max_price = data['Close'].max()
        min_price = data['Close'].min()
        diff = max_price - min_price
        levels = [max_price - diff * level for level in [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]]
        print("Fibonacci levels calculated")  # Debug statement
        for level in levels:
            fig.add_trace(go.Scatter(x=[data.index[0], data.index[-1]], y=[level, level], mode='lines', name=f'Fib Level {level:.2f}'))
        indicator_description += "<p>Fibonacci retracement levels are horizontal lines that indicate where support and resistance are likely to occur.</p>"

    if 'support_resistance' in indicators:
        support = data['Low'].rolling(window=50).min()
        resistance = data['High'].rolling(window=50).max()
        print("Support and Resistance calculated")  # Debug statement
        fig.add_trace(go.Scatter(x=data.index, y=support, mode='lines', name='Support'))
        fig.add_trace(go.Scatter(x=data.index, y=resistance, mode='lines', name='Resistance'))
        indicator_description += "<p>Support and resistance are levels where the price tends to find support as it falls and resistance as it rises.</p>"

    fig.update_layout(
        title=f'Technical Analysis for {ticker}',
        yaxis_title='Stock Price',
        xaxis_rangeslider_visible=False,
        yaxis2=dict(title='Volume', overlaying='y', side='right', position=1.0, range=[0, 300_000_000]),
         xaxis=dict(type='category', tickangle=-45, tickmode='array', 
                        tickvals=hist_df.index[::round(len(hist_df.index) / 20)],  # Adjust this to get 2-3 months interval
                        ticktext=[date.strftime('%Y-%m-%d') for date in hist_df.index[::round(len(hist_df.index) / 20)]],
                        tickformat='%Y-%m-%d',nticks=20),
        margin=dict(l=0, r=0, t=30, b=20),
        height=600,
        width=1200
    )
    technical_chart = fig.to_html(full_html=False)

    return technical_chart, total_return, sharpe_ratio, max_drawdown, indicator_description

def fetch_company_news(company_name):
#  url = f'https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=20&apiKey={NEWS_API_KEY}'

    url = f'https://newsapi.org/v2/everything?q={company_name}&language=en&sortBy=relevancy&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json()
        articles = news_data['articles']
        default_image_url = '/static/home/css/default_news_image.png'
        valid_articles = []
        for article in articles:
            if article.get('title') and article.get('description') and article.get('url'):
                if not article.get('urlToImage'):
                    article['urlToImage'] = default_image_url
                valid_articles.append(article)
        return valid_articles[:9]
    else:
        return []