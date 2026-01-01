# bookingservices-telegram-bot

Готовое решение для онлайн-записи в салон/барбершоп: веб-интерфейс для клиентов, личный кабинет с переносами/отменой и отдельная админ-панель. Проект используется как демо и шаблон — адаптируйте тексты/брендинг под свой бизнес.

## Возможности
- Клиент: выбор барбера/услуги/даты/времени, показ только свободных слотов; личный кабинет с предстоящими/прошедшими визитами, перенос и отмена с ограничением по времени; профиль с сохранением контактов; i18n (RU/UA/EN); защита от спама (honeypot + лимит 3 запроса/10 минут).
- Админ: панель `/adminbr/` с управлением услугами, барберами, бронированиями и статусов «не явился»; загрузка фото барберов и героев раздела «О нас»; ручное подтверждение/закрытие записей.

## Технологии
- Python 3.13, Django 6, Gunicorn + WhiteNoise
- Postgres через `DATABASE_URL` (для локалки — SQLite по умолчанию)
- Чистый HTML/CSS/JS без тяжёлых фронтенд-фреймворков
- i18n (ru/uk/en), кеш для rate-limit, медиа-хранилище для фото барберов

## Скриншоты
| Файл | Описание |
| --- | --- |
| `cover.png` | Обложка с буллитами: онлайн-запись, админ-панель, антиспам, i18n |
| `01_start.png` | Стартовый экран и выбор услуги/барбера |
| `02_flow_service.png` | Шаг выбора услуги и стоимости |
| `03_flow_datetime.png` | Календарь и время с фильтром свободных слотов |
| `04_flow_confirm.png` | Подтверждение записи и уведомление пользователю |
| `05_admin_orders.png` | Админ: список заказов, статусы, поиск |
| `06_admin_admins.png` | Админ: управление услугами/барберами/контентом |
Файлы лежат в корне репозитория (исходники — в `docs/`).

## Статус проекта
Готово для демо/портфолио: основной пользовательский поток и админ-панель работают, антиспам и i18n включены. Под конкретный бизнес требуется базовая настройка контента и домена.

## Быстрый старт (локально)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env  # задайте ключ, DEBUG, ALLOWED_HOSTS, DATABASE_URL (опционально)
cd barbershop
python manage.py migrate
python manage.py runserver
```
- Админка: `/adminbr/` (создайте суперпользователя `python manage.py createsuperuser`).
- Демо-данные: создайте услуги/барберов в админке, затем оформите пару бронирований на главной.

## FAQ/Деплой
- **Деплой на Render/аналог:** Procfile уже настроен под Gunicorn + WhiteNoise. Настройте `DATABASE_URL` на Postgres и добавьте переменные из `.env.example`.
- **Статика и медиа:** при прод-выкате запустите `python manage.py collectstatic`; медиа (фото барберов, обложки) храните во внешнем бакете или на диске.
- **Антиспам:** включён honeypot-поле и rate-limit (3 запроса / 10 минут) для форм записи.
- **Локализация:** языки ru/uk/en переключаются через стандартные Django i18n URL (`/i18n/`).


## Контакты
- Email: kostiantyn.lk22@gmail.com
- Telegram: @WinGor0
- Telegram-канал: https://t.me/kostiantyn_dev0
- WhatsApp: +4916096584651
- Freelancehunt: https://freelancehunt.com/my

## Admin demo
- URL: `/adminbr/`
- Login: `adminbr2007`
- Password: `adminbr2007`
How to verify quickly: log in, create one booking (service + barber + date/time), then check the main page — the slot is shown once and cannot be double-booked.

