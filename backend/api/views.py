from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Max
from datetime import date, timedelta

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

from .models import User, Currency, ExchangeRate, FavCurrency
from .serializers import (
    UserRegistrationSerializer, 
    UserProfileSerializer, 
    CurrencySerializer, 
    ExchangeRateSerializer, 
    FavCurrencySerializer
)

# -------------------------------------------------------------------
#                       GRUPA UŻYTKOWNIKA
# -------------------------------------------------------------------

@extend_schema(
    tags=['Autoryzacja'],
    summary="Rejestracja nowego użytkownika",
    description="Tworzy nowe konto użytkownika w systemie. Zwraca utworzone dane (bez hasła)."
)
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer


@extend_schema_view(
    get=extend_schema(
        tags=['Użytkownik'], 
        summary="Pobierz profil", 
        description="Pobiera dane zalogowanego użytkownika (wymaga tokena JWT)."
    ),
    put=extend_schema(
        tags=['Użytkownik'], 
        summary="Aktualizuj profil (całkowicie)", 
        description="Nadpisuje wszystkie dane w profilu użytkownika."
    ),
    patch=extend_schema(
        tags=['Użytkownik'], 
        summary="Aktualizuj profil (częściowo)", 
        description="Pozwala na zmianę pojedynczych pól, np. samego motywu (used_theme)."
    )
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return self.request.user


# -------------------------------------------------------------------
# 2. GRUPA WALUT I KURSÓW (Otwarte endpointy)
# -------------------------------------------------------------------

@extend_schema(
    tags=['Waluty i Kursy'],
    summary="Lista dostępnych walut",
    description="Zwraca listę wszystkich obsługiwanych przez system walut (kod, nazwa, typ tabeli)."
)
class CurrencyListView(generics.ListAPIView):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = (AllowAny,)


@extend_schema(
    tags=['Waluty i Kursy'],
    summary="Najnowsze kursy",
    description="Zwraca najświeższe notowania walut (z ostatniego dnia dostępnego w bazie)."
)
class LatestRatesView(generics.ListAPIView):
    serializer_class = ExchangeRateSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        latest_date = ExchangeRate.objects.aggregate(Max('effective_date'))['effective_date__max']
        if latest_date:
            return ExchangeRate.objects.filter(effective_date=latest_date)
        return ExchangeRate.objects.none()


@extend_schema(
    tags=['Waluty i Kursy'],
    summary="Historia kursów dla wybranej waluty",
    description="Zwraca chronologicznie ułożoną historię kursów. Użyj parametrów, by zawęzić przedział czasowy.",
    parameters=[
        OpenApiParameter(name='days', description='Liczba ostatnich dni (np. 30)', required=False, type=OpenApiTypes.INT),
        OpenApiParameter(name='start', description='Data początkowa (format YYYY-MM-DD)', required=False, type=OpenApiTypes.DATE),
        OpenApiParameter(name='end', description='Data końcowa (format YYYY-MM-DD)', required=False, type=OpenApiTypes.DATE),
    ]
)
class RateHistoryView(generics.ListAPIView):
    serializer_class = ExchangeRateSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        currency_code = self.kwargs.get('currency_code')
        queryset = ExchangeRate.objects.filter(currency__code=currency_code).order_by('effective_date')

        days = self.request.query_params.get('days')
        start_date = self.request.query_params.get('start')
        end_date = self.request.query_params.get('end')

        if days:
            try:
                cutoff_date = date.today() - timedelta(days=int(days))
                queryset = queryset.filter(effective_date__gte=cutoff_date)
            except ValueError:
                pass
        else:
            if start_date:
                queryset = queryset.filter(effective_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(effective_date__lte=end_date)

        return queryset


# -------------------------------------------------------------------
#               GRUPA ULUBIONYCH (Wymaga tokena JWT)
# -------------------------------------------------------------------

@extend_schema_view(
    get=extend_schema(
        tags=['Ulubione'], 
        summary="Pobierz listę ulubionych", 
        description="Zwraca wszystkie waluty dodane do ulubionych przez zalogowanego użytkownika."
    ),
    post=extend_schema(
        tags=['Ulubione'], 
        summary="Dodaj do ulubionych", 
        description="Przypisuje nową walutę do ulubionych użytkownika."
    )
)
class FavoriteListView(generics.ListCreateAPIView):
    serializer_class = FavCurrencySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return FavCurrency.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    tags=['Ulubione'],
    summary="Usuń z ulubionych",
    description="Usuwa konkretną walutę (po kodzie np. USD) z listy ulubionych zalogowanego użytkownika."
)
class FavoriteDetailView(generics.DestroyAPIView):
    serializer_class = FavCurrencySerializer
    permission_classes = (IsAuthenticated,)
    
    lookup_field = 'currency__code'
    lookup_url_kwarg = 'currency_code'

    def get_queryset(self):
        return FavCurrency.objects.filter(user=self.request.user)