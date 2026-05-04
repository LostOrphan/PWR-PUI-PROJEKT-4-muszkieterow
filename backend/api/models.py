from django.db import models
from django.contrib.auth.models import AbstractUser

# Modele utworzone na podstawie skryptu SQL Michała

# Tabela Użytkowników 
class User(AbstractUser):
    # Dodanie do defaultowego modelu django pól
    email = models.EmailField(unique=True)
    used_theme = models.CharField(max_length=10, default='light')

# Tabela Walut
class Currency(models.Model):
    TABLE_TYPES = [
        ('A', 'Table A'),
        ('B', 'Table B'),
        ('C', 'Table C'),
    ]
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100)
    table_type = models.CharField(max_length=1, choices=TABLE_TYPES)

    def __str__(self):
        return f"{self.code} - {self.name}"

# Tabela Kursów
class ExchangeRate(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    effective_date = models.DateField()
    average_rate = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    buy_rate = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    sell_rate = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)

    class Meta:
        unique_together = ('currency', 'effective_date')
        indexes = [
            models.Index(fields=['currency']),
            models.Index(fields=['effective_date']),
        ]

# Tabela Ulubionych Walut
class FavCurrency(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    added_at = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'currency')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['currency']),
        ]