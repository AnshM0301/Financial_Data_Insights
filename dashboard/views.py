# dashboard/views.py

import decimal
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from .models import Portfolio, Holding, Watchlist
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')

    portfolio, created = Portfolio.objects.get_or_create(user=request.user)
    holdings = Holding.objects.filter(portfolio=portfolio)
    watchlist = Watchlist.objects.filter(user=request.user)

    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'watchlist': watchlist,
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
        current_price = decimal.Decimal(request.POST.get('price'))

        if not ticker or not quantity or not current_price:
            logger.error(f'Missing data: ticker={ticker}, quantity={quantity}, current_price={current_price}')
            return HttpResponseBadRequest('Missing data')

        try:
            quantity = int(quantity)
            current_price = current_price
        except ValueError as e:
            logger.error(f'Invalid data types: {e}')
            return HttpResponseBadRequest('Invalid data types')

        # Fetch the user's portfolio
        portfolio, created = Portfolio.objects.get_or_create(user=user)

        # Calculate total cost
        total_cost = quantity * current_price

        if portfolio.balance >= total_cost:
            # Deduct the total cost from the portfolio balance
            portfolio.balance -= total_cost
            portfolio.save()

            # Create a new holding or update the existing one
            holding, created = Holding.objects.get_or_create(
                portfolio=portfolio,
                ticker=ticker,
                defaults={'buy_date': datetime.now(), 'buy_price': current_price, 'quantity': quantity}
            )
            if not created:
                holding.quantity += quantity
                holding.buy_price = current_price  # Update the price to the latest purchase price
                holding.save()

            logger.info('Stock purchased successfully')

            return JsonResponse({'success': 'Stock purchased successfully'})
        else:
            logger.error('Insufficient funds')
            return JsonResponse({'error': 'Insufficient funds'}, status=400)

    logger.error('Invalid request method')
    return JsonResponse({'error': 'Invalid request method'}, status=405)
