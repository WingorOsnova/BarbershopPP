from django.test import TestCase
from django.urls import reverse
from django.core.cache import cache

import datetime

from booking.models import Booking, Barber, Service
from booking.utils import get_available_slots


from .utils import generate_slot

class TimeSlotTest(TestCase):

  def test_generate_slot_count(self):
    date = datetime.date(2025, 1, 1)

    slots = generate_slot(date)
    self.assertEqual(len(slots), 18)

  def test_canceled_booking_does_not_block_slot(self):
        date = datetime.date(2026, 1, 1)

        barber = Barber.objects.create(
            name="Test Barber",
            experience_years=1,
            is_active=True
        )

        service = Service.objects.create(
            name="Haircut",
            price=20.00,
            duration_minutes=30
        )

        Booking.objects.create(
            client_name="Test",
            client_phone="+380501234567",
            barber=barber,
            service=service,
            booking_date=date,
            booking_time=datetime.time(10, 0),
            status=Booking.STATUS_CANCELED,
        )

        available = get_available_slots(barber, date)

        self.assertIn(datetime.time(10, 0), available)

class BookingApiTests(TestCase):
    def test_api_book_creates_booking_and_returns_json(self):
        barber = Barber.objects.create(
            name="Test Barber",
            experience_years=2,
            is_active=True
        )

        service = Service.objects.create(
            name="Haircut",
            price=25.00,
            duration_minutes=30
        )

        payload = {
            "client_name": "Kostya",
            "client_phone": "*380092123456",
            "client_email": "k@example.com",
            "barber": barber.id,
            "service": service.id,
            "booking_date": "2025-01-01",
            "booking_time": "10:00",
            "message": "Test booking",
        }

        url = reverse("booking_api")  # это name твоего endpoint
        response = self.client.post(url, data=payload)

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data.get("ok"))
        self.assertIn("id", data)

        self.assertEqual(Booking.objects.count(), 1)

        booking = Booking.objects.first()
        self.assertEqual(booking.client_name, "Kostya")
        self.assertEqual(booking.barber_id, barber.id)
        self.assertEqual(booking.service_id, service.id)
        self.assertEqual(str(booking.booking_date), "2025-01-01")
        self.assertEqual(booking.booking_time.strftime("%H:%M"), "10:00")
  
    def test_api_rate_limit_blocks_after_limit(self):
      cache.clear()
      self.client.defaults["REMOTE_ADDR"] = "10.0.0.123"  # изоляция по IP

      LIMIT = 3  # твой реальный лимит

      barber = Barber.objects.create(
          name="Test Barber",
          experience_years=2,
          is_active=True
      )

      service = Service.objects.create(
          name="Haircut",
          price=25.00,
          duration_minutes=30
      )

      payload = {
          "client_name": "Kostya",
          "client_phone": "+380501234567",
          "client_email": "k@example.com",
          "barber": barber.id,
          "service": service.id,
          "booking_date": "2025-01-01",
          "booking_time": "10:00",
          "message": "Test booking",
      }

      url = reverse("booking_api")

      # первые LIMIT запросов должны пройти
      for i in range(LIMIT):
          payload["booking_time"] = f"{9 + i:02d}:00"
          response = self.client.post(url, data=payload)
          self.assertEqual(response.status_code, 200)
          self.assertTrue(response.json().get("ok"))

      # следующий запрос должен быть заблокирован
      payload["booking_time"] = "15:00"
      response = self.client.post(url, data=payload)
      self.assertEqual(response.status_code, 429)
      self.assertFalse(response.json().get("ok"))

      # в БД должно быть ровно LIMIT записей
      self.assertEqual(Booking.objects.count(), LIMIT)

    def test_cannot_double_book_same_slot(self):
      barber = Barber.objects.create(
          name="Test Barber",
          experience_years=2,
          is_active=True
      )

      service = Service.objects.create(
          name="Haircut",
          price=25.00,
          duration_minutes=30
      )

      payload = {
          "client_name": "Kostya",
          "client_phone": "+380501234567",
          "client_email": "k@example.com",
          "barber": barber.id,
          "service": service.id,
          "booking_date": "2025-01-01",
          "booking_time": "10:00",
          "message": "Test booking",
      }

      url = reverse("booking_api")

      # первый запрос проходит
      response1 = self.client.post(url, data=payload)
      self.assertEqual(response1.status_code, 200)
      self.assertTrue(response1.json().get("ok"))

      # второй на тот же слот должен упасть
      response2 = self.client.post(url, data=payload)
      self.assertIn(response2.status_code, (400, 409))
      self.assertFalse(response2.json().get("ok"))

      # в базе только одна бронь на этот слот
      self.assertEqual(Booking.objects.count(), 1)
