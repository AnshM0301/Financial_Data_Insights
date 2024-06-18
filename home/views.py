from django.shortcuts import render, redirect
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.io import to_html
import requests


tickers = ['^GSPC', '^NSEI', '^BSESN', '^NSEBANK', '^NDX', '^DJI', '^FTSE']
names = ['S&P 500', 'NIFTY 50', 'BSE', 'BANK NIFTY', 'Nasdaq', 'Dow Jones', 'UK 100']
countries = ['USA', 'India', 'India', 'India', 'USA', 'USA', 'UK']

NEWS_API_KEY = 'a99f21bd3dae43bc962eb23c86600461' 

def fetch_news():
    url = f'https://newsapi.org/v2/top-headlines?category=business&language=en&pageSize=20&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    articles = response.json().get('articles', [])
    
    # Fallback image URL
    default_image_url = '/static/home/css/default_news_image.png'
    
    # Add fallback image if the article has no image
    for article in articles:
        if not article.get('urlToImage'):
            article['urlToImage'] = default_image_url

    return articles

def index(request):
    return redirect("home:display_ticker", ticker="^GSPC")

def retrieve_data(ticker: str):
    ticker_obj = yf.Ticker(ticker)
    ticker_info = ticker_obj.info

    hist_df = ticker_obj.history(period="5y")
    hist_df = hist_df.reset_index()
    
    return hist_df, ticker_info

def create_candlestick_chart(hist_df: pd.DataFrame):
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=hist_df.index,
            open=hist_df['Open'],
            high=hist_df['High'],
            low=hist_df['Low'],
            close=hist_df['Close'],
            name='Price'
        ))
        

        fig.update_layout(
            # title=f'{company_name.capitalize()} Stock Price and Volume',
            yaxis_title='Stock Price',
            xaxis_rangeslider_visible=False,
            xaxis=dict(type='category', tickangle=-45, tickmode='auto', nticks=20),
            margin=dict(l=0, r=0, t=30, b=20),
            height=600,
            width=1200
        )
        return fig



def home(request, ticker="^GSPC"):
    # Retrieving the latest close prices for the indices
    try:
        sp500 = yf.Ticker("^GSPC").history(period="1d")['Close'].iloc[-1]
    except IndexError:
        sp500 = None
    try:
        nifty = yf.Ticker("^NSEI").history(period="1d")['Close'].iloc[-1]
    except IndexError:  
        nifty = None
    try:
        banknifty = yf.Ticker("^NSEBANK").history(period="1d")['Close'].iloc[-1]
    except IndexError:
        banknifty = None

    news_articles = fetch_news()    

    context = {
        'sp500': "{:,.2f}".format(sp500) if sp500 else "N/A",
        'nifty': "{:,.2f}".format(nifty) if nifty else "N/A",
        'banknifty': "{:,.2f}".format(banknifty) if banknifty else "N/A",
        'news_articles': news_articles,
    }

    hist_df, info = retrieve_data(ticker)

    if hist_df.empty:
        context.update({
            "tickers": zip(tickers, names),
            "ticker": ticker,
            "chart_div": "No data available for this ticker.",
            "close": "N/A",
            "change": "N/A",
            "pct_change": "N/A",
            "last_close": "N/A",
            "high_52wk": "N/A",
            "low_52wk": "N/A"
        })
        return render(request, 'home/home.html', context)

    candlestick_fig = create_candlestick_chart(hist_df)
    chart_div = to_html(candlestick_fig, full_html=False, include_plotlyjs="cdn", div_id="overview")

    last_close = hist_df['Close'].iloc[-1]
    high_52wk = hist_df['High'].max()
    low_52wk = hist_df['Low'].min()
    p1, p2 = hist_df["Close"].values[-1], hist_df["Close"].values[-2]
    change, prcnt_change = (p2 - p1), (p2 - p1) / p1

    context.update({
        "tickers": zip(tickers, names, countries),
        "ticker": ticker,
        "chart_div": chart_div,
        "name": info.get("longName", ""),
        "close": f"{p1:.2f}",
        "change": f"{change:.2f}",
        "pct_change": f"{prcnt_change * 100:.2f}%",
        "last_close": f"{last_close:.2f}",
        "high_52wk": f"{high_52wk:.2f}",
        "low_52wk": f"{low_52wk:.2f}",
    
    })

    return render(request, 'home/home.html', context)

