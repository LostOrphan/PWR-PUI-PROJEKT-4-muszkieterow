from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from .models import Currency, ExchangeRate, FavCurrency

User = get_user_model()

class BaseApiTestCase(APITestCase):
    """ Klasa bazowa przygotowująca dane testowe dla wszystkich testów """
    def setUp(self):
        # 1. Tworzenie użytkownika testowego
        self.user = User.objects.create_user(
            username='testuser', 
            email='test@test.pl', 
            password='TestPassword123!'
        )

        # 2. Tworzenie testowych walut
        self.currency_usd = Currency.objects.create(code='USD', name='dolar amerykański', table_type='A')
        self.currency_eur = Currency.objects.create(code='EUR', name='euro', table_type='A')

        # 3. Tworzenie testowych kursów (dla dzisiaj i wczoraj)
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)

        ExchangeRate.objects.create(
            currency=self.currency_usd, effective_date=self.yesterday, average_rate=3.90
        )
        ExchangeRate.objects.create(
            currency=self.currency_usd, effective_date=self.today, average_rate=4.00, buy_rate=3.95, sell_rate=4.05
        )
        ExchangeRate.objects.create(
            currency=self.currency_eur, effective_date=self.today, average_rate=4.30
        )


# -------------------------------------------------------------------
# 1. TESTY KONT I AUTORYZACJI
# -------------------------------------------------------------------
class UserAuthTests(BaseApiTestCase):
    
    def test_user_registration(self):
        """ Testuje poprawną rejestrację nowego użytkownika """
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'new@test.pl',
            'password': 'StrongPassword123!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2) # Zwiększyło się z 1 do 2

    def test_get_user_profile_authenticated(self):
        """ Testuje pobieranie profilu przez zalogowanego użytkownika """
        url = reverse('user_profile')
        self.client.force_authenticate(user=self.user) # Symulacja tokena JWT
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_get_user_profile_unauthenticated(self):
        """ Testuje czy niezalogowany użytkownik dostanie błąd 401 """
        url = reverse('user_profile')
        response = self.client.get(url) # Brak force_authenticate
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# -------------------------------------------------------------------
# 2. TESTY OTWARTYCH ENDPOINTÓW (Waluty i Kursy)
# -------------------------------------------------------------------
class PublicDataTests(BaseApiTestCase):

    def test_get_currency_list(self):
        """ Testuje pobieranie listy wszystkich walut """
        url = reverse('currency_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # Stworzyliśmy USD i EUR w setUp
        self.assertEqual(response.data[0]['code'], 'USD')

    def test_get_latest_rates(self):
        """ Testuje pobieranie najświeższych kursów (tylko z najnowszej daty) """
        url = reverse('latest_rates')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Zwraca 2, bo USD i EUR mają wpisy na 'today', a wpis USD z 'yesterday' jest ignorowany
        self.assertEqual(len(response.data), 2) 

    def test_get_rate_history(self):
        """ Testuje pobieranie historii dla konkretnej waluty """
        url = reverse('rate_history', kwargs={'currency_code': 'USD'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2) # USD ma dwa wpisy (dzisiaj i wczoraj)
        self.assertEqual(response.data[0]['currency_code'], 'USD')


# -------------------------------------------------------------------
# 3. TESTY CHRONIONYCH ENDPOINTÓW (Ulubione)
# -------------------------------------------------------------------
class FavoriteTests(BaseApiTestCase):

    def test_add_favorite_authenticated(self):
        """ Testuje dodawanie waluty do ulubionych """
        url = reverse('favorite_list')
        data = {'currency_code': 'USD'}
        
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(FavCurrency.objects.count(), 1)
        self.assertEqual(FavCurrency.objects.first().user, self.user)

    def test_get_favorites(self):
        """ Testuje pobieranie listy ulubionych użytkownika """
        FavCurrency.objects.create(user=self.user, currency=self.currency_usd)
        
        url = reverse('favorite_list')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # Weryfikacja czy 'currency_details' działa poprawnie (według naszego serializatora)
        self.assertEqual(response.data[0]['currency_details']['code'], 'USD')

    def test_delete_favorite(self):
        """ Testuje usuwanie waluty z ulubionych """
        FavCurrency.objects.create(user=self.user, currency=self.currency_usd)
        
        url = reverse('favorite_delete', kwargs={'currency_code': 'USD'})
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(FavCurrency.objects.count(), 0)

    def test_favorites_unauthenticated(self):
        """ Testuje zablokowanie dostępu do ulubionych bez tokena """
        url = reverse('favorite_list')
        response = self.client.post(url, {'currency_code': 'USD'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)