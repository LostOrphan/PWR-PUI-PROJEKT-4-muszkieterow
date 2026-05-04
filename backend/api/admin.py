from django.contrib import admin
from .models import User, Currency, ExchangeRate, FavCurrency

admin.site.register(User)
admin.site.register(Currency)
admin.site.register(ExchangeRate)
admin.site.register(FavCurrency)