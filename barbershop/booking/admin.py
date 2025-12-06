from django.contrib import admin
from .models import Barber, Service, Booking

@admin.register(Barber)
class AdminBarber(admin.ModelAdmin):
  list_display = ('name', 'experience_years', 'is_active')
  list_filter = ('is_active',)
  search_fields = ('name',)

@admin.register(Service)
class AdminService(admin.ModelAdmin):
  list_display = ('name', 'price', 'duration_minutes')
  search_fields = ('name',)

@admin.register(Booking)
class AdminBooking(admin.ModelAdmin):
  list_display = (
    'client_name',
    'client_phone',
    'barber',
    'service',
    'booking_date',
    'booking_time',
    'status',
    'created_at'
  )
  list_filter = ('status', 'barber', 'service', 'booking_date')
  search_fields = ('client_name', 'client_phone','client_email')
  ordering = ('-booking_time', '-booking_date')
  
