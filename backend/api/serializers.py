from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Currency, ExchangeRate, FavCurrency

# -------------------------------------------------------------------
#                       GRUPA UŻYTKOWNIKA
# -------------------------------------------------------------------

class UserRegistrationSerializer(serializers.ModelSerializer):
    """ Używany tylko podczas tworzenia konta (wymusza walidację hasła) """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """ Używany do pobierania i aktualizacji danych zalogowanego użytkownika """
    class Meta:
        model = User
        fields = ('id', 'username', 'email','used_theme') 
        read_only_fields = ('id', 'username', 'email')


# -------------------------------------------------------------------
#                           GRUPA WALUT I KURSÓW
# -------------------------------------------------------------------

class CurrencySerializer(serializers.ModelSerializer):
    """ Zwraca podstawowe informacje o walucie"""
    class Meta:
        model = Currency
        fields = ('code', 'name', 'table_type')


class ExchangeRateSerializer(serializers.ModelSerializer):
    """ Zwraca szczegóły kursu. Zamiast ID waluty, podaje od razu jej kod """
    currency_code = serializers.CharField(source='currency.code', read_only=True)

    class Meta:
        model = ExchangeRate
        fields = ('currency_code', 'effective_date', 'average_rate', 'buy_rate', 'sell_rate')


# -------------------------------------------------------------------
#                       GRUPA ULUBIONYCH
# -------------------------------------------------------------------

class FavCurrencySerializer(serializers.ModelSerializer):
    """ 
    - Przy wysyłaniu na frontend (GET): zwraca pełne dane o walucie (kod, nazwa).
    - Przy odbieraniu z frontendu (POST): oczekuje tylko kodu waluty (np. "USD").
    """
    currency_details = CurrencySerializer(source='currency', read_only=True)
    
    currency_code = serializers.SlugRelatedField(
        queryset=Currency.objects.all(),
        slug_field='code',
        source='currency',
        write_only=True
    )

    class Meta:
        model = FavCurrency
        fields = ('id', 'currency_details', 'currency_code')