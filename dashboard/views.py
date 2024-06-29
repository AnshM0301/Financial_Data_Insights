# dashboard/views.py

import json
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from .models import Portfolio, Holding, Watchlist, HoldingHistory
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import logging
import decimal
import yfinance as yf
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

def get_stock_beta(ticker):
    stock = yf.Ticker(ticker)
    return stock.info.get('beta', 0)

def calculate_portfolio_beta(holdings):
    total_value = sum(holding.current_price_value * holding.quantity for holding in holdings)
    portfolio_beta = sum(
        (holding.current_price_value * holding.quantity / total_value) * get_stock_beta(holding.ticker)
        for holding in holdings
    )
    return portfolio_beta

def get_historical_prices(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    hist = stock.history(start=start_date, end=end_date)
    return hist['Close'].tolist()

def calculate_daily_returns(prices):
    prices = np.array(prices)
    daily_returns = np.diff(prices) / prices[:-1]
    return daily_returns

def calculate_expected_return(daily_returns):
    return np.mean(daily_returns) * 252  # Annualize

def get_risk_free_rate():
    # Download 3-month US Treasury bills rates (IRX) and de-annualize
    t_bill = yf.download("^IRX")["Adj Close"]
    daily_risk_free_rate = (1 + t_bill / 100) ** (1/252) - 1
    return daily_risk_free_rate.mean()

# def calculate_sharpe_ratio(holdings):
#     end_date = datetime.now()
#     start_date = end_date - timedelta(days=365)  # For one year

#     all_daily_returns = []
#     total_value = sum(holding.current_price_value * holding.quantity for holding in holdings)
#     portfolio_weights = []

#     for holding in holdings:
#         try:
#             prices = get_historical_prices(holding.ticker, start_date, end_date)
#             daily_returns = calculate_daily_returns(prices)
#             all_daily_returns.append(daily_returns)
#             portfolio_weights.append((holding.current_price_value * holding.quantity) / total_value)
#         except Exception as e:
#             logger.error(f"Error fetching data for {holding.ticker}: {e}")

#     portfolio_daily_returns = np.dot(portfolio_weights, all_daily_returns)
#     expected_return = calculate_expected_return(portfolio_daily_returns)
#     risk_free_rate = get_risk_free_rate()
    
#     excess_returns = portfolio_daily_returns - risk_free_rate
#     sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)  # Annualize

#     return sharpe_ratio

def fetch_historical_data(ticker, date):
    stock = yf.Ticker(ticker)
    historical_data = stock.history(start=date, end=date + timedelta(days=1))
    if not historical_data.empty:
        return historical_data['Close'][0]
    return None

def generate_performance_chart(user):
    # ... (other code)

    # Daily investment and net worth calculations
    holdings = Holding.objects.filter(portfolio__user=user).order_by('buy_date')
    
    if not holdings:
        return json.loads(pio.to_json(go.Figure(), pretty=True))  # Return empty figure if no holdings

    start_date = holdings.first().buy_date
    end_date = datetime.now()
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Exclude weekends

    daily_investment = []
    daily_net_worth = []
    cumulative_investment = 0
    last_known_prices = {}

    for date in dates:
        daily_investment_value = 0
        net_worth = 0

        for holding in holdings:
            if holding.buy_date <= date.date():
                daily_investment_value += holding.buy_price * holding.quantity
                
                historical_price = fetch_historical_data(holding.ticker, date)
                if historical_price:
                    last_known_prices[holding.ticker] = historical_price
                else:
                    historical_price = last_known_prices.get(holding.ticker, 0)
                
                if historical_price:
                    current_value = historical_price * holding.quantity
                    net_worth += current_value

        cumulative_investment = daily_investment_value
        daily_investment.append(cumulative_investment)
        daily_net_worth.append(net_worth)

    # ... (code to calculate daily_investment and daily_net_worth)

    max_value = max(daily_net_worth + daily_investment)
    min_value = min(daily_net_worth + daily_investment)
    # Define maximum and minimum values for the y-axis


    fig = go.Figure()
    # Add traces for investment and net worth
    fig.add_trace(go.Scatter(x=dates, y=daily_investment, mode='lines+markers', name='Investment Value', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=dates, y=daily_net_worth, mode='lines+markers', name='Net Worth', line=dict(color='green')))

    fig.update_layout(
        title='Performance for Last 30 Days',
        xaxis_title='Date',
        yaxis_title='Value',
        yaxis=dict(range=[max(0, min_value - 5000), max_value + 5000]),
        template = 'plotly_dark'
    )
    # Convert figure to JSON for sending to the template
    graph_json = json.loads(pio.to_json(fig, pretty=True))

    return graph_json

@login_required(login_url="/UserAuth/login/")
def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    portfolio, created = Portfolio.objects.get_or_create(user=request.user)
    holdings = Holding.objects.filter(portfolio=portfolio)
    watchlist = Watchlist.objects.filter(user=request.user)

    total_investment = 0
    unrealized_profit_loss = 0
    
    net_worth = 0 #balance is not added here

    sectors = []
    sector_values = []

    profit_count = 0
    loss_count = 0

    
    for holding in holdings:
        try:
            current_price = holding.get_current_price()
            holding.current_price_value = current_price
            holding.profit_loss = round((decimal.Decimal(current_price) * holding.quantity) - (holding.buy_price * holding.quantity), 2)
            total_investment += holding.buy_price * holding.quantity
            unrealized_profit_loss += holding.profit_loss
            net_worth += holding.current_value()
            holding.sector = holding.fetch_sector()
            holding.save()

            sectors.append(holding.sector)
            sector_values.append(holding.current_value())

            if holding.profit_loss >= 0:
                profit_count += 1
            else:
                loss_count += 1

             # Fetch historical prices for the holding
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)  # For one year
            prices = get_historical_prices(holding.ticker, start_date, end_date)
            
            # # Calculate daily returns
            # daily_returns = calculate_daily_returns(prices)
            # daily_returns_all_stocks.extend(daily_returns)

        except Exception as e:
            logger.error(f"Error fetching current price for {holding.ticker}: {e}")

    # Create a pie chart for sector allocation
    fig_pie = px.pie(values=sector_values, names=sectors, title='Portfolio Allocation by Sector', template = 'plotly_dark')
    pie_chart_json = json.loads(pio.to_json(fig_pie))

    # Create a bar chart for profit/loss distribution
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        name='In Profit', x=[profit_count], y=['Holdings'], orientation='h', marker_color='green'
    ))
    fig_bar.add_trace(go.Bar(
        name='In Loss', x=[loss_count], y=['Holdings'], orientation='h', marker_color='red'
    ))

    # (data=[
    #     # go.Bar(name = ['In Profit', 'In loss'], x = ['Holdings'], y = ['profit_count', 'loss_count'], marker_color = ['green', 'red'])
    #     go.Bar(name='In Profit', x=['Holdings'], y=[profit_count], orientation='h', marker_color='green'),
    #     go.Bar(name='In Loss', x=['Holdings'], y=[loss_count], orientation='h', marker_color='red')
    # ])
    fig_bar.update_layout(barmode='group', title='Number of Companies in Profit and Loss',  
        xaxis=dict(title='Number of Companies'),
        yaxis=dict(title='',showticklabels=False, autorange='reversed'),
        legend=dict(x=0.8, y=1.2),
        template = 'plotly_dark'),
    bar_chart_json = json.loads(pio.to_json(fig_bar))


    # Fetch historical data and generate the performance chart
    # historical_data = fetch_historical_data(ticker, date)
    performance_chart_json = generate_performance_chart(request.user)



    #beta calculation
    portfolio_beta = calculate_portfolio_beta(holdings)

    # Calculate Sharpe Ratio
    # sharpe_ratio = calculate_sharpe_ratio(holdings)

     # Calculate expected one-year return for the portfolio
    all_daily_returns = []
    portfolio_weights = []

    for holding in holdings:
        try:
            prices = get_historical_prices(holding.ticker, start_date, end_date)
            daily_returns = calculate_daily_returns(prices)
            all_daily_returns.append(daily_returns)
            portfolio_weights.append((holding.current_price_value * holding.quantity) / net_worth)
        except Exception as e:
            logger.error(f"Error fetching data for {holding.ticker}: {e}")

    portfolio_daily_returns = np.dot(portfolio_weights, all_daily_returns)
    expected_return = calculate_expected_return(portfolio_daily_returns)

    risk_free_rate = get_risk_free_rate()
    risk_premium = expected_return - risk_free_rate
    std_deviation = np.std(portfolio_daily_returns) * np.sqrt(252)  # Annualized standard deviation
    sharpe_ratio = risk_premium / std_deviation

    # print("Expected One-Year Return:", round(expected_return * 100, 2), "%")
    # print("Risk-Free Rate:", round(risk_free_rate * 100, 2), "%")
    # print("Risk Premium:", round(risk_premium * 100, 2), "%")
    # print("Standard Deviation:", round(std_deviation * 100, 2), "%")
    
    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'total_investment': round(total_investment, 2),
        'unrealized_profit_loss': unrealized_profit_loss,
        'net_worth': round(net_worth, 2),
        'realized_profit_loss': round(portfolio.realized_profit_loss, 2),
        'portfolio_beta': round(portfolio_beta, 3),
        'watchlist': watchlist,
        'pie_chart_json': pie_chart_json,
        'bar_chart_json': bar_chart_json,
        'pie_chart_json': json.dumps(pie_chart_json),
        'bar_chart_json': json.dumps(bar_chart_json),
        'performance_chart_json': json.dumps(performance_chart_json),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'expected_one_year_return': round(expected_return * 100, 2),  # In percentage
    }

    return render(request, 'dashboard/dashboard.html', context)

@csrf_exempt
def buy_stock(request):
    if request.method == 'POST':
        user = request.user
        if not user.is_authenticated:
            logger.error('User not authenticated')
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        ticker = request.POST.get('ticker')
        quantity = request.POST.get('quantity')
        current_price = request.POST.get('price')

        if not ticker or not quantity or not current_price:
            logger.error(f'Missing data: ticker={ticker}, quantity={quantity}, current_price={current_price}')
            return HttpResponseBadRequest('Missing data')

        try:
            quantity = int(quantity)
            current_price = decimal.Decimal(current_price)
        except ValueError as e: 
            logger.error(f'Invalid data types: {e}')
            return HttpResponseBadRequest('Invalid data types')

        portfolio, created = Portfolio.objects.get_or_create(user=user)

        total_cost = quantity * current_price

        if portfolio.balance >= total_cost:
            portfolio.balance -= total_cost
            portfolio.save()

            holding, created = Holding.objects.get_or_create(
                portfolio=portfolio,
                ticker=ticker,
                defaults={'buy_date': datetime.now(), 'buy_price': current_price, 'quantity': quantity}
            )
            if not created:
                holding.quantity += quantity
                holding.buy_price = current_price
                holding.save()

            logger.info('Stock purchased successfully')
            return JsonResponse({'success': 'Stock purchased successfully'})
        else:
            logger.error('Insufficient funds')
            return JsonResponse({'error': 'Insufficient funds'}, status=400)

    logger.error('Invalid request method')
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def sell_stock(request):
    if request.method == 'POST':
        user = request.user
        if not user.is_authenticated:
            logger.error('User not authenticated')
            return JsonResponse({'error': 'User not authenticated'}, status=401)

        data = json.loads(request.body)
        ticker = data.get('ticker')
        quantity = data.get('quantity')
        current_price = data.get('current_price')

        if not ticker or not quantity or not current_price:
            logger.error(f'Missing data: ticker={ticker}, quantity={quantity}, current_price={current_price}')
            return HttpResponseBadRequest('Missing data')

        try:
            quantity = int(quantity)
            current_price = decimal.Decimal(current_price)
        except ValueError as e:
            logger.error(f'Invalid data types: {e}')
            return HttpResponseBadRequest('Invalid data types')

        portfolio = Portfolio.objects.get(user=user)
        holding = Holding.objects.get(portfolio=portfolio, ticker=ticker)

        if holding.quantity < quantity:
            logger.error('Not enough shares to sell')
            return JsonResponse({'error': 'Not enough shares to sell'}, status=400)

        total_value = quantity * current_price
        profit_loss = total_value - (quantity * holding.buy_price)

        portfolio.balance += total_value
        portfolio.realized_profit_loss += profit_loss
        portfolio.save()

        HoldingHistory.objects.create(
            portfolio=portfolio,
            ticker=ticker,
            quantity=quantity,
            buy_date=holding.buy_date,
            buy_price=holding.buy_price,
            sell_date=datetime.now(),
            sell_price=current_price,
            profit_loss=profit_loss
        )

        holding.quantity -= quantity

        if holding.quantity == 0:
            holding.delete()
        else:
            holding.save()

        logger.info('Stock sold successfully')
        return JsonResponse({'success': 'Stock sold successfully'})

    logger.error('Invalid request method')
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def add_to_watchlist(request):
    if request.method == 'POST':
        user = request.user
        ticker = request.POST.get('ticker')

        if not ticker:
            return JsonResponse({'error': 'Missing ticker'}, status=400)
        
        watchlist, created = Watchlist.objects.get_or_create(user=user, ticker=ticker)

        if created:
            return JsonResponse({'success':'Stock added to the watchlst'})
        else:
            return JsonResponse({'info':'Stock already in watchlist'})
    
    return JsonResponse({'error' : 'Invalid request method'}, status=405)

@csrf_exempt
def get_watchlist(request):
    user_watchlist = Watchlist.objects.filter(user=request.user)
    data = []
    for item in user_watchlist:
        current_price = item.get_current_price()
        data.append({
            'ticker': item.ticker,
            'current_price': current_price  
        })
    return JsonResponse(data, safe=False)

@csrf_exempt
def remove_from_watchlist(request):
    if request.method == 'POST':
        user = request.user
    
        ticker = request.POST.get('ticker')
        Watchlist.objects.filter(user=user, ticker=ticker).delete()
        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

