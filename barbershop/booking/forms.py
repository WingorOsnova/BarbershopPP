from django import forms
import datetime
from .models import Booking

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
      }),
      'client_phone' : forms.TextInput(attrs={
        'id': 'phone',
        'placeholder' : '+380',
        'data-lang-key': 'form-phone',
      }),
      'client_email' : forms.EmailInput(attrs={
        'id': 'email',
        'placeholder': '',
        'data-lang-key': 'form-email',
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
    super().__init__(*args, **kwargs)

    # Запрещаем выбор прошедшей даты
    self.fields['booking_date'].widget.attrs.setdefault('min', datetime.date.today().isoformat())

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
