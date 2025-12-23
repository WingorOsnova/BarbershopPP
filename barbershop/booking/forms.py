import datetime
import re

from django import forms
from django.core.exceptions import ValidationError

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Booking, UserProfile
from .utils import get_available_slots


class BookingForm(forms.ModelForm):
  hp_field = forms.CharField(
    required=False,
    widget=forms.TextInput(attrs={
      'autocomplete': 'off',
      'tabindex': '-1',
      'aria-hidden': 'true',
      'style': 'position:absolute; left:-9999px; opacity:0; height:1px; width:1px;'
    })
  )
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
      'hp_field',
    ]

    widgets = {
      'client_name' : forms.TextInput(attrs={
        'id': 'name',
        'placeholder': _('Имя и фамилия'),
        'data-lang-key': 'form-name',
        'autocomplete': 'off',
      }),
      'client_phone' : forms.TextInput(attrs={
        'id': 'phone',
        'placeholder' : '+380',
        'data-lang-key': 'form-phone',
        'autocomplete': 'off',
        'inputmode': 'tel',
        'pattern': r'\+?[0-9\s\-\(\)]{10,20}',
      }),
      'client_email' : forms.EmailInput(attrs={
        'id': 'email',
        'placeholder': 'email@example.com',
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
          'placeholder': 'YYYY-MM-DD',
          'data-lang-key': 'form-date',
      }),
      'message': forms.Textarea(attrs={
          'id': 'comment',
          'rows': 3,
          'placeholder': _('Комментарий (необязательно)'),
          'data-lang-key': 'form-comment',
      }),
    }

    labels = {
      'client_name': _('Ваше имя *'),
      'client_phone': _('Телефон *'),
      'client_email': 'Email',
      'barber': _('Выберите барбера *'),
      'service': _('Выберите услугу *'),
      'booking_date': _('Дата *'),
      'booking_time': _('Время сеанса *'),
      'message': _('Комментарий'),
      'hp_field': '',
    }

    error_messages = {
      'client_name': {
        'required': _('Введите ваше имя, чтобы мы смогли подтвердить запись.'),
      },
      'client_phone': {
        'required': _('Укажите номер телефона для связи.'),
      },
      'client_email': {
        'invalid': _('Введите корректный email или оставьте поле пустым.'),
      },
      'barber': {
        'required': _('Выберите барбера, к которому хотите записаться.'),
      },
      'service': {
        'required': _('Выберите услугу, которую хотите получить.'),
      },
      'booking_date': {
        'required': _('Укажите дату визита.'),
        'invalid': _('Введите дату в корректном формате.'),
      },
      'booking_time': {
        'required': _('Укажите удобное время.'),
        'invalid': _('Введите время в корректном формате.'),
      },
      'message': {
        'max_length': _('Сообщение слишком длинное.'),
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
      slot_choices = [('', _('Сначала выберите барбера и дату'))]
    elif available_slots:
      slot_choices = [('', _('Выберите время'))] + [
        (slot.strftime('%H:%M'), slot.strftime('%H:%M')) for slot in available_slots
      ]
    else:
      slot_choices = [('', _('Нет свободных слотов на выбранную дату'))]

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
        raise ValidationError(_("Это время уже занято. Выберите другое."))

    # Проверяем, что у пользователя нет другой записи в это же время
    if self.user and self.user.is_authenticated:
      conflict = Booking.objects.filter(
        user=self.user,
        booking_date=booking_date,
        booking_time=booking_time,
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
      ).exists()
      if conflict:
        raise ValidationError(_("У вас уже есть запись на это время."))

    # Honeypot: если поле заполнено — считаем спамом
    if self.cleaned_data.get('hp_field'):
      raise ValidationError(_("Спам-фильтр: отправка отклонена."))

    return cleaned_data

  def clean_client_phone(self):
    phone = (self.cleaned_data.get('client_phone') or '').strip()
    digits = re.sub(r'\D', '', phone)

    if len(digits) < 10 or len(digits) > 15:
      raise ValidationError(_("Введите телефон в формате +380501234567 (10–15 цифр)."))

    if len(digits) == 10 and digits.startswith('0'):
      digits = f"38{digits}"

    formatted = digits if phone.startswith('+') else f"+{digits}"
    pure_digits = re.sub(r'\D', '', formatted)
    if len(pure_digits) < 10 or len(pure_digits) > 15:
      raise ValidationError(_("Введите телефон в формате +380501234567 (10–15 цифр)."))

    return formatted


class ProfileForm(forms.ModelForm):
  first_name = forms.CharField(label=_('Имя'), required=False)
  last_name = forms.CharField(label=_('Фамилия'), required=False)
  email = forms.EmailField(label='Email', required=False)

  class Meta:
    model = UserProfile
    fields = ['phone']
    labels = {'phone': _('Телефон')}
    widgets = {
      'phone': forms.TextInput(attrs={
        'placeholder': '+380XXXXXXXXX',
        'autocomplete': 'off',
        'inputmode': 'tel',
        'pattern': r'\+?[0-9\s\-\(\)]{10,20}',
      })
    }

  def __init__(self, *args, **kwargs):
    self.user = kwargs.pop('user')
    super().__init__(*args, **kwargs)
    if self.user:
      self.fields['first_name'].initial = self.user.first_name
      self.fields['last_name'].initial = self.user.last_name
      self.fields['email'].initial = self.user.email
    self.fields['first_name'].widget.attrs.setdefault('placeholder', _('Имя'))
    self.fields['last_name'].widget.attrs.setdefault('placeholder', _('Фамилия'))
    self.fields['email'].widget.attrs.setdefault('placeholder', 'email@example.com')

  def save(self, commit=True):
    profile = super().save(commit=False)
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

  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['username'].widget.attrs.update({
      'placeholder': _('Придумайте логин'),
      'autocomplete': 'off'
    })
    self.fields['password1'].widget.attrs.update({
      'placeholder': _('Придумайте пароль'),
      'autocomplete': 'new-password'
    })
    self.fields['password2'].widget.attrs.update({
      'placeholder': _('Повторите пароль'),
      'autocomplete': 'new-password'
    })


class LoginForm(AuthenticationForm):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['username'].widget.attrs.update({
      'placeholder': _('Ваш логин'),
      'autocomplete': 'off'
    })
    self.fields['password'].widget.attrs.update({
      'placeholder': _('Ваш пароль'),
      'autocomplete': 'off'
    })
