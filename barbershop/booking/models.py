from django.db import models

class Barber(models.Model):
  name = models.CharField(max_length=100)
  photo_url = models.URLField(blank=True)
  experience_years = models.PositiveIntegerField(default=0)
  description = models.TextField(blank=True)
  is_active = models.BooleanField(default=True)
  
  def __str__(self):
    return self.name

class Service(models.Model):
  name = models.CharField(max_length=100)
  description = models.TextField(blank=True)
  price = models.DecimalField(max_digits=10, decimal_places=2)
  duration_minutes = models.PositiveIntegerField(default=30)

  def __str__(self):
    return self.name

class Booking(models.Model):
  client_name = models.CharField(max_length=100)
  client_phone = models.CharField(max_length=20)
  client_email = models.EmailField(blank=True)
  barber = models.ForeignKey(Barber, on_delete=models.CASCADE)
  service = models.ForeignKey(Service, on_delete=models.CASCADE)
  booking_date = models.DateField()
  booking_time = models.TimeField()
  message = models.TextField(blank=True)
  created_at = models.DateTimeField(auto_now_add=True)

  STATUS_PENDING = 'pending'
  STATUS_CONFIRMED = 'confirmed'
  STATUS_CANCELED = 'canceled'
  STATUS_COMPLETED = 'completed'

  STATUS_CHOICES = [
    (STATUS_PENDING, 'В ожидание'),
    (STATUS_CONFIRMED, 'Подтвержденно'),
    (STATUS_CANCELED, 'Отмененно'),
    (STATUS_COMPLETED, 'Выполненно'),
  ]

  status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default=STATUS_PENDING,
    verbose_name='Статус'
  )

  def __str__(self):
    return f"{self.client_name} - {self.barber.name} - {self.service.name} - {self.booking_date}"