from django.shortcuts import render
from .models import Barber, Service


def home(request):

  barbers = Barber.objects.filter(is_active=True)
  services = Service.objects.all()

  context = {
    'barbers': barbers,
    'services': services,
  }

  return render(request, 'booking/home.html', context)
