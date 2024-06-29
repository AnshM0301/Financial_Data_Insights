from django.contrib import admin
from .models import Portfolio, Holding, HoldingHistory, Watchlist

admin.site.register(Portfolio)
admin.site.register(Holding)
admin.site.register(HoldingHistory)
admin.site.register(Watchlist)
