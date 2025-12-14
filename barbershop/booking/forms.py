import datetime

from django import forms
from django.core.exceptions import ValidationError

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import Booking, UserProfile
from .utils import get_available_slots


class BookingForm(forms.ModelForm):
  booking_time = forms.TimeField(
    input_formats=['%H:%M'],
    widget=forms.Select(attrs={
      'id': 'time',
      'data-lang-key': 'form-time',
    })
  )

  class Meta:
    model = Booking

    fields = [
      'client_name',
      'client_phone',
      'client_email',
      'barber',
      'service',
      'booking_date',
      'booking_time',
      'message',
    ]

    widgets = {
      'client_name' : forms.TextInput(attrs={
        'id': 'name',
        'placeholder': '',
        'data-lang-key': 'form-name',
        'autocomplete': 'off',
      }),
      'client_phone' : forms.TextInput(attrs={
        'id': 'phone',
        'placeholder' : '+380',
        'data-lang-key': 'form-phone',
        'autocomplete': 'off',
      }),
      'client_email' : forms.EmailInput(attrs={
        'id': 'email',
        'placeholder': '',
        'data-lang-key': 'form-email',
        'autocomplete': 'off',
      }),
      'barber': forms.Select(attrs={
          'id': 'barber',
          'data-lang-key': 'form-barber',
      }),
      'service': forms.Select(attrs={
          'id': 'service',
          'data-lang-key': 'form-service',
      }),
      'booking_date': forms.DateInput(attrs={
          'id': 'date',
          'type': 'date',
          'data-lang-key': 'form-date',
      }),
      'message': forms.Textarea(attrs={
          'id': 'comment',
          'rows': 3,
          'placeholder': '',
          'data-lang-key': 'form-comment',
      }),
    }

    labels = {
      'client_name': 'Ваше имя *',
      'client_phone': 'Телефон *',
      'client_email': 'Email',
      'barber': 'Выберите барбера *',
      'service': 'Выберите услугу *',
      'booking_date': 'Дата *',
      'booking_time': 'Время *',
      'message': 'Комментарий',
    }

    error_messages = {
      'client_name': {
        'required': 'Введите ваше имя, чтобы мы смогли подтвердить запись.',
      },
      'client_phone': {
        'required': 'Укажите номер телефона для связи.',
      },
      'client_email': {
        'invalid': 'Введите корректный email или оставьте поле пустым.',
      },
      'barber': {
        'required': 'Выберите барбера, к которому хотите записаться.',
      },
      'service': {
        'required': 'Выберите услугу, которую хотите получить.',
      },
      'booking_date': {
        'required': 'Укажите дату визита.',
        'invalid': 'Введите дату в корректном формате.',
      },
      'booking_time': {
        'required': 'Укажите удобное время.',
        'invalid': 'Введите время в корректном формате.',
      },
      'message': {
        'max_length': 'Сообщение слишком длинное.',
      },
    }

  def __init__(self, *args, **kwargs):
    available_slots = kwargs.pop('available_slots', None)
    self.user = kwargs.pop('user', None)
    super().__init__(*args, **kwargs)

    # Запрещаем выбор прошедшей даты
    self.fields['booking_date'].widget.attrs.setdefault('min', datetime.date.today().isoformat())

    # Подставляем данные профиля
    if not self.is_bound and self.user and self.user.is_authenticated:
      profile = getattr(self.user, 'profile', None)
      full_name = f"{self.user.first_name} {self.user.last_name}".strip() or self.user.username
      if full_name and not self.initial.get('client_name'):
        self.initial['client_name'] = full_name
      if profile and profile.phone and not self.initial.get('client_phone'):
        self.initial['client_phone'] = profile.phone
      if self.user.email and not self.initial.get('client_email'):
        self.initial['client_email'] = self.user.email

    # Настраиваем выпадающий список времени
    if available_slots is None:
      slot_choices = [('', 'Сначала выберите барбера и дату')]
    elif available_slots:
      slot_choices = [('', 'Выберите время')] + [
        (slot.strftime('%H:%M'), slot.strftime('%H:%M')) for slot in available_slots
      ]
    else:
      slot_choices = [('', 'Нет свободных слотов на выбранную дату')]

    self.fields['booking_time'].widget.choices = slot_choices
  
  def clean(self):
    cleaned_data = super().clean()
    barber = cleaned_data.get('barber')
    booking_date = cleaned_data.get('booking_date')
    booking_time = cleaned_data.get('booking_time')

    if not barber or not booking_date or not booking_time:
        return cleaned_data

    available = get_available_slots(barber, booking_date)
    if booking_time not in available:
        raise ValidationError("Это время уже занято. Выберите другое.")

    # Проверяем, что у пользователя нет другой записи в это же время
    if self.user and self.user.is_authenticated:
      conflict = Booking.objects.filter(
        user=self.user,
        booking_date=booking_date,
        booking_time=booking_time,
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
      ).exists()
      if conflict:
        raise ValidationError("У вас уже есть запись на это время.")

    return cleaned_data


class ProfileForm(forms.ModelForm):
  first_name = forms.CharField(label='Имя', required=False)
  last_name = forms.CharField(label='Фамилия', required=False)
  email = forms.EmailField(label='Email', required=False)

  class Meta:
    model = UserProfile
    fields = ['phone']
    labels = {'phone': 'Телефон'}
    widgets = {
      'phone': forms.TextInput(attrs={'placeholder': '+380...', 'autocomplete': 'off'})
    }

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user')
    super().__init__(*args, **kwargs)
    if self.user:
      self.fields['first_name'].initial = self.user.first_name
      self.fields['last_name'].initial = self.user.last_name
      self.fields['email'].initial = self.user.email

  def save(self, commit=True):
    profile = super().save(commit=False)
    # Сохраняем данные пользователя
    self.user.first_name = self.cleaned_data.get('first_name', '')
    self.user.last_name = self.cleaned_data.get('last_name', '')
    self.user.email = self.cleaned_data.get('email', '')
    if commit:
      self.user.save(update_fields=['first_name', 'last_name', 'email'])
      profile.user = self.user
      profile.save()
    return profile

class RegisterForm(UserCreationForm):
  class Meta:
    model = User
    fields = ['username', 'password1', 'password2']


class LoginForm(AuthenticationForm):
  pass
