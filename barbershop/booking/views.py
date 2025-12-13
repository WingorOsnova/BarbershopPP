from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST
import datetime
from .models import Barber, Service, Booking
from .forms import BookingForm, LoginForm, RegisterForm
from .utils import get_available_slots

def home(request):
  barbers = Barber.objects.filter(is_active=True)
  services = Service.objects.all()
  available_slots = None
  selected_barber = None
  selected_date = None

  # Определяем выбранные барбера и дату из GET/POST
  selected_barber_id = request.POST.get('barber') if request.method == 'POST' else request.GET.get('barber')
  selected_date_str = request.POST.get('booking_date') if request.method == 'POST' else request.GET.get('booking_date')

  if selected_barber_id and selected_date_str:
    selected_barber = Barber.objects.filter(id=selected_barber_id, is_active=True).first()
    try:
      selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
      selected_date = None

    if selected_barber and selected_date:
      available_slots = get_available_slots(selected_barber, selected_date)

  if request.method == 'POST':
    form = BookingForm(request.POST, available_slots=available_slots)
    if form.is_valid():
      form.save()
      return redirect('home')
  else:
    initial = {}
    if selected_barber:
      initial['barber'] = selected_barber.id
    if selected_date:
      initial['booking_date'] = selected_date

    form = BookingForm(initial=initial, available_slots=available_slots)

  context = {
    'barbers': barbers,
    'services': services,
    'form': form,
    'available_slots': available_slots,
  }

  return render(request, 'booking/home.html', context)

def booking_create(request):
  barbers = Barber.objects.filter(is_active=True)
  services = Service.objects.all()

  selected_barber = None
  selected_date = None
  available_slots = []

  if request.method == 'POST':
    barber_id = request.POST.get('barber')
    date_str = request.POST.get('booking_date')
    time_str = request.POST.get('booking_time')
    client_name = request.POST.get('client_name')
    client_phone = request.POST.get('client_phone')
    client_email = request.POST.get('client_email')
    service_id = request.POST.get('service')
    message = request.POST.get('message')

    if barber_id and date_str and time_str and client_name and client_phone and service_id:

      selected_barber = Barber.objects.get(id=barber_id)
      selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
      selected_time = datetime.datetime.strptime(time_str, '%H:%M').time()
      selected_service = Service.objects.get(id=service_id)

      Booking.objects.create(
        client_name=client_name,
        client_phone=client_phone,
        client_email=client_email,
        barber=selected_barber,
        service=selected_service,
        booking_date=selected_date,
        booking_time=selected_time,
        message=message,
        status=Booking.STATUS_PENDING,
      )

      return redirect('home')
  else:
    barber_id = request.GET.get('barber')
    date_str = request.GET.get('booking_date')

    if barber_id and date_str:
      selected_barber = Barber.objects.get(id=barber_id)
      selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
      available_slots = get_available_slots(selected_barber, selected_date)

  context = {
    'barbers': barbers,
    'services': services,
    'selected_barber': selected_barber,
    'selected_date': selected_date,
    'available_slots': available_slots,
  }
  return render(request, 'booking/booking_form.html', context)

@require_GET
def available_slots_api(request):
  barber_id = request.GET.get('barber')
  date_str = request.GET.get('booking_date')

  if not barber_id or not date_str:
    return JsonResponse({"slots": []})

  barber = Barber.objects.filter(id=barber_id, is_active=True).first()
  if not barber:
    return JsonResponse({"slots": []})

  try:
    selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
  except (ValueError, TypeError):
    return JsonResponse({"slots": []})

  slots = get_available_slots(barber, selected_date)
  return JsonResponse({"slots": [t.strftime('%H:%M') for t in slots]})


@require_POST
def booking_api(request):
  """
  AJAX бронирование без перезагрузки страницы.
  """
  # Подготовим available_slots для валидации формы
  available_slots = None
  barber_id = request.POST.get('barber')
  date_str = request.POST.get('booking_date')

  if barber_id and date_str:
    barber_obj = Barber.objects.filter(id=barber_id, is_active=True).first()
    try:
      selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
      selected_date = None

    if barber_obj and selected_date:
      available_slots = get_available_slots(barber_obj, selected_date)

  form = BookingForm(request.POST, available_slots=available_slots)

  if form.is_valid():
    booking = form.save()
    return JsonResponse({
      "ok": True,
      "message": "Запись создана, мы свяжемся с вами для подтверждения.",
      "id": booking.id,
    })

  # Ошибки по полям и общие
  errors = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
  return JsonResponse({"ok": False, "errors": errors}, status=400)


def register_view(request):
  if request.method == 'POST':
    form = RegisterForm(request.POST)
    if form.is_valid():
      user = form.save()
      auth_login(request, user)
      return redirect('dashboard')
  else:
    form = RegisterForm()
  return render(request, 'booking/register.html', {'form': form})

def login_view(request):
  # Показываем форму при GET и обрабатываем авторизацию при POST
  if request.method == 'POST':
    form = LoginForm(request, data=request.POST)
    if form.is_valid():
      auth_login(request, form.get_user())
      return redirect('dashboard')
  else:
    form = LoginForm(request)
  return render(request, 'booking/login.html', {'form': form})

def logout_view(request):
  auth_logout(request)
  return render(request, 'booking/logout.html')


@login_required
def dashboard_view(request):
  return render(request, 'booking/dashboard.html')
