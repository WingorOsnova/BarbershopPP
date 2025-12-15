from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Q
import datetime
from .models import Barber, Service, Booking, UserProfile, SiteContent
from .forms import BookingForm, LoginForm, RegisterForm, ProfileForm
from .utils import get_available_slots
from django.utils import timezone
from django.utils.translation import gettext as _

CANCEL_LIMIT_HOURS = 3

def home(request):
  barbers = Barber.objects.filter(is_active=True)
  services = Service.objects.all()
  site_content = SiteContent.objects.first()
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
    form = BookingForm(request.POST, available_slots=available_slots, user=request.user)
    if form.is_valid():
      booking = form.save(commit=False)
      if request.user.is_authenticated:
        booking.user = request.user
      booking.save()
      messages.success(request, _("Запись создана, мы свяжемся с вами для подтверждения."))
      return redirect('home')
  else:
    initial = {}
    if selected_barber:
      initial['barber'] = selected_barber.id
    if selected_date:
      initial['booking_date'] = selected_date

    form = BookingForm(initial=initial, available_slots=available_slots, user=request.user)

  context = {
    'barbers': barbers,
    'services': services,
    'form': form,
    'available_slots': available_slots,
    'site_content': site_content,
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

      if request.user.is_authenticated:
        conflict = Booking.objects.filter(
          user=request.user,
          booking_date=selected_date,
          booking_time=selected_time,
          status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
        ).exists()
        if conflict:
          messages.error(request, _("У вас уже есть запись на это время."))
          return redirect('dashboard')

      Booking.objects.create(
        client_name=client_name,
        client_phone=client_phone,
        client_email=client_email,
        user=request.user if request.user.is_authenticated else None,
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

  form = BookingForm(request.POST, available_slots=available_slots, user=request.user)

  if form.is_valid():
    booking = form.save(commit=False)
    if request.user.is_authenticated:
      booking.user = request.user
    booking.save()
    return JsonResponse({
      "ok": True,
      "message": _("Запись создана, мы свяжемся с вами для подтверждения."),
      "id": booking.id,
    })

  # Ошибки по полям и общие
  errors = {field: [str(err) for err in errs] for field, errs in form.errors.items()}
  return JsonResponse({"ok": False, "errors": errors}, status=400)

def cancel_booking(request, booking_id):
  booking = get_object_or_404(Booking, id=booking_id, user=request.user)

  # Нельзя отменять выполненную
  if booking.status == Booking.STATUS_COMPLETED:
    messages.error(request, _('Вы не можете отменить выполненную запись.'))
    return redirect('dashboard')
  
  appointment_dt = datetime.datetime.combine(booking.booking_date, booking.booking_time)
  appointment_dt = timezone.make_aware(appointment_dt)
  
  if appointment_dt <= timezone.now():
    messages.error(request, _('Вы не можете отменить прошедшую запись.'))
    return redirect('dashboard')

  diff = appointment_dt - timezone.now()
  if diff< datetime.timedelta(hours=CANCEL_LIMIT_HOURS):
    messages.error(request, _('Отмена возможна минимум за %(hours)s часа до визита.') % {'hours': CANCEL_LIMIT_HOURS})
    return redirect('dashboard')

  booking.status = Booking.STATUS_CANCELED
  booking.save(update_fields=['status'])

  messages.success(request, _('Запись успешно отменена. Мы будем рады видеть вас снова!'))
  return redirect('dashboard')


@login_required
def reschedule_booking(request, booking_id):
  booking = get_object_or_404(Booking, id=booking_id, user=request.user)

  # Запреты
  if booking.status in [Booking.STATUS_CANCELED, Booking.STATUS_COMPLETED, Booking.STATUS_NO_SHOW]:
    messages.error(request, _("Эту запись нельзя перенести."))
    return redirect('dashboard')

  appointment_dt = datetime.datetime.combine(booking.booking_date, booking.booking_time)
  appointment_dt = timezone.make_aware(appointment_dt)

  if appointment_dt <= timezone.now():
    messages.error(request, _("Прошедшую запись нельзя перенести."))
    return redirect('dashboard')

  if appointment_dt - timezone.now() < datetime.timedelta(hours=CANCEL_LIMIT_HOURS):
    messages.error(request, _("Перенос возможен минимум за %(hours)s часа до визита.") % {'hours': CANCEL_LIMIT_HOURS})
    return redirect('dashboard')

  # Выбор даты/барбера (барбер фиксирован — переносим к тому же)
  selected_date_str = request.POST.get('booking_date') if request.method == 'POST' else request.GET.get('booking_date')
  selected_date = None
  available_slots = None

  if selected_date_str:
    try:
      selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
      available_slots = get_available_slots(booking.barber, selected_date)
    except ValueError:
      selected_date = None

  if request.method == 'POST':
    time_str = request.POST.get('booking_time')
    if selected_date and time_str:
      selected_time = datetime.datetime.strptime(time_str, '%H:%M').time()

      # Проверим что слот реально свободен
      if available_slots and selected_time in available_slots:
        # Проверим, что нет другой активной записи пользователя в это же время
        conflict = Booking.objects.filter(
          user=request.user,
          booking_date=selected_date,
          booking_time=selected_time,
          status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
        ).exclude(id=booking.id).exists()
        if conflict:
          messages.error(request, _("У вас уже есть запись на это время."))
          return redirect('dashboard')

        booking.booking_date = selected_date
        booking.booking_time = selected_time
        booking.status = Booking.STATUS_PENDING  # после переноса снова "ожидает"
        booking.save(update_fields=['booking_date', 'booking_time', 'status'])

        messages.success(request, _("Запись перенесена! Мы свяжемся для подтверждения."))
        return redirect('dashboard')

      messages.error(request, _("Этот слот уже занят. Выберите другое время."))

  context = {
    'booking': booking,
    'selected_date': selected_date,
    'available_slots': available_slots,
    'min_date': datetime.date.today().isoformat(),
  }
  return render(request, 'booking/reschedule.html', context)


@login_required
def edit_profile(request):
  profile, _ = UserProfile.objects.get_or_create(user=request.user)

  if request.method == 'POST':
    form = ProfileForm(request.POST, instance=profile, user=request.user)
    if form.is_valid():
      form.save()
      messages.success(request, _("Профиль обновлён."))
      return redirect('dashboard')
  else:
    form = ProfileForm(instance=profile, user=request.user)

  return render(request, 'booking/profile_edit.html', {'form': form})



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
  now = timezone.localtime()
  today = now.date()
  current_time = now.time()

  base_qs = Booking.objects.filter(
    user=request.user
  ).select_related('barber', 'service')

  # Отмечаем как "не явился" все просроченные (ожидаемые/подтвержденные) записи
  missed_qs = base_qs.filter(
    status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED]
  ).filter(
    Q(booking_date__lt=today) |
    Q(booking_date=today, booking_time__lt=current_time)
  )
  if missed_qs.exists():
    missed_qs.update(status=Booking.STATUS_NO_SHOW)

  upcoming_bookings = base_qs.filter(
    Q(booking_date__gt=today) |
    Q(booking_date=today, booking_time__gte=current_time)
  ).exclude(status__in=[Booking.STATUS_CANCELED, Booking.STATUS_COMPLETED, Booking.STATUS_NO_SHOW]) \
   .order_by('booking_date', 'booking_time')

  past_bookings = base_qs.exclude(
    id__in=upcoming_bookings.values('id')
  ).order_by('-booking_date', '-booking_time')

  bookings = base_qs.order_by('-booking_date', '-booking_time')

  context = {
    'bookings': bookings,
    'upcoming_bookings': upcoming_bookings,
    'past_bookings': past_bookings,
    'today': today,
  }

  return render(request, 'booking/dashboard.html', context)
