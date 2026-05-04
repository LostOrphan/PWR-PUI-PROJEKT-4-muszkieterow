# api/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    RegisterView, UserProfileView, CurrencyListView, 
    LatestRatesView, RateHistoryView, FavoriteListView, FavoriteDetailView
)

urlpatterns = [
    # Grupa Kont
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserProfileView.as_view(), name='user_profile'),

    # Grupa Walut i Kursów
    path('currencies/', CurrencyListView.as_view(), name='currency_list'),
    path('rates/latest/', LatestRatesView.as_view(), name='latest_rates'),
    path('rates/<str:currency_code>/', RateHistoryView.as_view(), name='rate_history'),

    # Grupa Ulubionych
    path('favorites/', FavoriteListView.as_view(), name='favorite_list'),
    path('favorites/<str:currency_code>/', FavoriteDetailView.as_view(), name='favorite_delete'),
]