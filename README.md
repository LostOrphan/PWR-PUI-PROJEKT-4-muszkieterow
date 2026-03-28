"# PWR-PUI-PROJEKT-4-muszkieterow" 

Backend setup:
0. Posiadanie zainstalowanego PSQL 17.9 oraz utworzenie bazy danych
1. python -m venv venv
2. pip install -r requirements.txt
3. Utworzenie pliku .env zgodnie z .env_example
z venv
4. python manage.py migrate
5. python manage.py runserver