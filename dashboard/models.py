# dashboard/models.py

from django.db import models
from django.contrib.auth.models import User
import yfinance as yf
import decimal

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00) 

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    buy_date = models.DateField()
    buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def get_current_price(self):
        stock = yf.Ticker(self.ticker)
        current_price = stock.history(period="1d")['Close'].iloc[-1]  # Use iloc to avoid FutureWarning
        return round(current_price, 2)

    def current_value(self):
        return self.quantity * self.get_current_price()

    def __str__(self):
        return f"{self.ticker} - {self.quantity} shares"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.username} - {self.ticker}"
