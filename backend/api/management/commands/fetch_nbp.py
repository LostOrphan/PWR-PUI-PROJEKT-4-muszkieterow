import requests
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Max
from api.models import Currency, ExchangeRate
class Command(BaseCommand):
    help = 'Pobiera brakujące kursy walut z API NBP (Tabele A, B i C) i usuwa dane starsze niż 365 dni'
    def handle(self, *args, **kwargs):
        today = date.today()
        
        # Czyszczenie starych danych (starszych niż 365 dni)
        cutoff_date = today - timedelta(days=365)
        deleted_count, _ = ExchangeRate.objects.filter(effective_date__lt=cutoff_date).delete()
        
        if deleted_count > 0:
            self.stdout.write(self.style.WARNING(f"Usunięto {deleted_count} starych rekordów (sprzed {cutoff_date})."))
        else:
            self.stdout.write("Brak starych rekordów do usunięcia.")
        
        # Sprawdzenie najmłodszego wpisu
        latest_record = ExchangeRate.objects.aggregate(Max('effective_date'))['effective_date__max']
        if latest_record:
            start_date = latest_record + timedelta(days=1)
            self.stdout.write(f"Ostatnie dane w bazie są z: {latest_record}")
        else:
            start_date = today - timedelta(days=365)
            self.stdout.write("Baza jest pusta. Pobieram dane z ostatnich 365 dni...")
        if start_date > today:
            self.stdout.write(self.style.SUCCESS("Baza danych jest już w pełni aktualna!"))
            return
        current_start = start_date
        
        # Podzielenie zapytań na 90-dniowe bloki
        while current_start <= today:
            current_end = current_start + timedelta(days=90)
            if current_end > today:
                current_end = today
                
            self.stdout.write(f"\nPobieram okres: {current_start} - {current_end}...")
            
            # Pobieramy po kolei wszystkie 3 tabele dla danego okienka
            for table_letter in ['A', 'B', 'C']:
                self.fetch_and_save(table_letter, current_start, current_end)
            
            current_start = current_end + timedelta(days=1)
        self.stdout.write(self.style.SUCCESS("\nZakończono aktualizację bazy danych!"))
    def fetch_and_save(self, table_letter, start_date, end_date):
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        url = f"http://api.nbp.pl/api/exchangerates/tables/{table_letter}/{start_str}/{end_str}/?format=json"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 404:
                # Pominięcie 404 - Tabela B nie jest aktualizowana codziennie
                return
            
            response.raise_for_status()
            data = response.json()
            
            for table in data:
                effective_date = table['effectiveDate']
                rates = table['rates']
                
                for rate in rates:
                    # Dodanie waluty, jeśli jeszcze nie istnieje
                    currency, created = Currency.objects.get_or_create(
                        code=rate['code'],
                        defaults={
                            'name': rate['currency'],
                            'table_type': table_letter
                        }
                    )
                    
                    defaults = {}
                    if table_letter in ['A', 'B']:
                        defaults['average_rate'] = rate['mid']
                    elif table_letter == 'C':
                        defaults['buy_rate'] = rate['bid']
                        defaults['sell_rate'] = rate['ask']
                    
                    # Aktualizacja danych lub utworzenie nowego wpisu
                    ExchangeRate.objects.update_or_create(
                        currency=currency,
                        effective_date=effective_date,
                        defaults=defaults
                    )
            self.stdout.write(self.style.SUCCESS(f" -> Tabela {table_letter}: POBRANO"))
                    
        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f"Błąd połączenia z API NBP dla tabeli {table_letter}: {e}"))