# dashboard/urls.py

from django.urls import path
from .views import dashboard, buy_stock, sell_stock, add_to_watchlist, remove_from_watchlist, get_watchlist

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('buy_stock/', buy_stock, name='buy_stock'),
    path('sell_stock/', sell_stock, name = 'sell_stock'),
    path('add_to_watchlist/', add_to_watchlist, name='add_to_watchlist'),
    path('get_watchlist/', get_watchlist, name='get_watchlist'),
    path('remove_from_watchlist/', remove_from_watchlist, name='remove_from_watchlist'),
]
