# dashboard/urls.py

from django.urls import path
from .views import dashboard, buy_stock

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('buy_stock/', buy_stock, name='buy_stock'),
]
