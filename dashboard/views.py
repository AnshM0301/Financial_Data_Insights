# dashboard/views.py

import json
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, redirect
from .models import Portfolio, Holding, Watchlist, HoldingHistory
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import logging
import decimal

import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

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

        except Exception as e:
            logger.error(f"Error fetching current price for {holding.ticker}: {e}")

    # Create a pie chart for sector allocation
    fig_pie = px.pie(values=sector_values, names=sectors, title='Portfolio Allocation by Sector')
    pie_chart_json = json.loads(pio.to_json(fig_pie))

    # Create a bar chart for profit/loss distribution
    fig_bar = go.Figure(data=[
        # go.Bar(name = ['In Profit', 'In loss'], x = ['Holdings'], y = ['profit_count', 'loss_count'], marker_color = ['green', 'red'])
        go.Bar(name='In Profit', x=['Holdings'], y=[profit_count], marker_color='green'),
        go.Bar(name='In Loss', x=['Holdings'], y=[loss_count], marker_color='red')
    ])
    fig_bar.update_layout(barmode='stack', title='Number of Companies in Profit and Loss')
    bar_chart_json = json.loads(pio.to_json(fig_bar))

    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'total_investment': round(total_investment, 2),
        'unrealized_profit_loss': unrealized_profit_loss,
        'net_worth': round(net_worth, 2),
        'realized_profit_loss': round(portfolio.realized_profit_loss, 2),
        'watchlist': watchlist,
        'pie_chart_json': pie_chart_json,
        'bar_chart_json': bar_chart_json,
        'pie_chart_json': json.dumps(pie_chart_json),
        'bar_chart_json': json.dumps(bar_chart_json),
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