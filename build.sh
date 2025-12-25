#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

cd "$(dirname "$0")/barbershop"

python manage.py collectstatic --no-input
python manage.py migrate

# Опционально создать суперюзера из переменных окружения (без хардкода пароля)
if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  python manage.py shell <<'PYCODE' || true
import os
from django.contrib.auth import get_user_model

User = get_user_model()
username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

if username and password and not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superuser '{username}' created.")
else:
    print("Superuser creation skipped (exists or creds not provided).")
PYCODE
fi
