# dashboard/models.py

from django.db import models
from django.contrib.auth.models import User

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

    def current_value(self):
        # Placeholder for current value calculation, replace with actual logic
        return self.quantity * self.buy_price

    def __str__(self):
        return f"{self.ticker} - {self.quantity} shares"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.user.username} - {self.ticker}"
