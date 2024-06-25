# dashboard/models.py

from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
import yfinance as yf
import decimal

class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00) 
    realized_profit_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Add this field

    def __str__(self):
        return f"{self.user.username}'s Portfolio"

class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    buy_date = models.DateField()
    buy_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    is_sold = models.BooleanField(default=False)
    sector = models.CharField(max_length=50, null=True, blank=True)  # New field

    def get_current_price(self):
        stock = yf.Ticker(self.ticker)
        current_price = stock.history(period="1d")['Close'].iloc[-1]  # Use iloc to avoid FutureWarning
        return round(current_price, 2)

    def current_value(self):
        return self.quantity * self.get_current_price()
    
    def fetch_sector(self):
        stock = yf.Ticker(self.ticker)
        return stock.info.get('sector', 'Unknown')

    def __str__(self):
        return f"{self.ticker} - {self.quantity} shares"

class HoldingHistory(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    quantity = models.PositiveIntegerField()
    buy_date = models.DateField(default=datetime.now)  # Set a default value
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Set a default value
    sell_date = models.DateField(default=datetime.now)  # Set a default value
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Set a default value
    profit_loss = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Set a default value

    def __str__(self):
        return f"{self.portfolio.user.username} - {self.ticker} - {self.sell_date} - {self.profit_loss}"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)

    def get_current_price(self):
        stock = yf.Ticker(self.ticker)
        current_price = stock.history(period="1d")['Close'].iloc[-1]  # Use iloc to avoid FutureWarning
        return round(current_price, 2)

    def __str__(self):
        return f"{self.user.username} - {self.ticker}"
