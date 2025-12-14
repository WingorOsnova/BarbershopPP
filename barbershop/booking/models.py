from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

class Barber(models.Model):
  name = models.CharField(max_length=100)
  photo = models.ImageField(
    upload_to='barbers/',
    blank=True,
    null=True,
    validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
  )
  experience_years = models.PositiveIntegerField(default=0)
  description = models.TextField(blank=True)
  is_active = models.BooleanField(default=True)
  
  def __str__(self):
    return self.name

  def save(self, *args, **kwargs):
    if self.pk:
      old = Barber.objects.filter(pk=self.pk).first()
      if old and old.photo and old.photo != self.photo:
        old.photo.delete(save=False)
    super().save(*args, **kwargs)

  def delete(self, *args, **kwargs):
    if self.photo:
      self.photo.delete(save=False)
    super().delete(*args, **kwargs)

class Service(models.Model):
  icon = models.CharField(max_length=10)
  name = models.CharField(max_length=100)
  description = models.TextField(blank=True)
  price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='PRICE ₴')
  duration_minutes = models.PositiveIntegerField(default=30)

  def __str__(self):
    return self.name

class Booking(models.Model):
  client_name = models.CharField(max_length=100)
  client_phone = models.CharField(max_length=20)
  client_email = models.EmailField(blank=True)
  user = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    blank=True,
    on_delete=models.SET_NULL,
    related_name='bookings',
  )
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
  STATUS_NO_SHOW = 'no_show'

  STATUS_CHOICES = [
    (STATUS_PENDING, _('В ожидание')),
    (STATUS_CONFIRMED, _('Подтверждено')),
    (STATUS_CANCELED, _('Отменено')),
    (STATUS_COMPLETED, _('Выполнено')),
    (STATUS_NO_SHOW, _('Не явился')),
  ]

  status = models.CharField(
    max_length=20,
    choices=STATUS_CHOICES,
    default=STATUS_PENDING,
    verbose_name=_('Статус')
  )

  def __str__(self):
    return f"{self.client_name} - {self.barber.name} - {self.service.name} - {self.booking_date}"


class UserProfile(models.Model):
  user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='profile')
  phone = models.CharField(max_length=20, blank=True)

  def __str__(self):
    return f"Профиль {self.user.username}"
