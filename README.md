# Barbershop Booking

Conversion-focused SPA for a barbershop: service/barber showcase, frictionless booking flow, multilingual UX (EN/UA/RU), and built-in anti-spam/rate-limit protection. Ready for production on Render (Gunicorn + WhiteNoise + Postgres).

## Highlights (why it sells)
- Booking that converts: pick barber/service/date/time with only free slots shown.
- Retention-ready dashboard: upcoming/past visits, cancel/reschedule, auto no-show mark.
- Lead quality: honeypot + rate-limit (3 req / 10 min) to cut bots and noise.
- Multilingual (EN/UA/RU) switcher, status badges, polished notifications.
- Content control: barber photos + about-page hero uploaded via admin.

## Tech Stack
- Python 3.13, Django 6, Gunicorn, WhiteNoise
- Postgres via `DATABASE_URL` (SQLite fallback for local dev)
- Plain HTML/CSS/JS (no heavy frontend frameworks)

## Quickstart (local)
```bash
git clone https://github.com/WingorOsnova/BarbershopPP
cd BarbershopPP/barbershop
python3 -m venv .venv && source .venv/bin/activate
pip install -r ../requirements.txt
cp ../.env.example .env  # set DJANGO_SECRET_KEY, DATABASE_URL (optional), hosts
python manage.py migrate
python manage.py runserver
```

## Tests
```bash
python manage.py test
```

## Admin demo
- URL: `/adminbr/`
- Login: `adminbr2007`
- Password: `adminbr2007`
How to verify quickly: log in, create one booking (service + barber + date/time), then check the main page — the slot is shown once and cannot be double-booked.

## Screenshots
(Add 2–4 visuals in `media/screenshots` when publishing: home/booking flow, dashboard, profile/edit)

---

## Українською (коротко)
SPA для запису в барбершоп: послуги/барбери, кабінет (перенос/скасування), профіль, i18n (EN/UA/RU). Антиспам: honeypot + rate-limit 3/10хв. Адмін: `/adminbr/`, логін/пароль `adminbr2007`. Стек: Django 6, Postgres, Gunicorn, WhiteNoise.

## Русский (коротко)
SPA для онлайн-записи: услуги/барберы, кабинет (перенос/отмена), профиль, i18n (EN/UA/RU), антиспам (honeypot + лимит 3/10мин). Админка `/adminbr/`, логин/пароль `adminbr2007`. Стек: Django 6, Postgres, Gunicorn, WhiteNoise.
