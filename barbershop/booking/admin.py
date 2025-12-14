from django.contrib import admin
from django.utils.html import format_html
from .models import Barber, Service, Booking

@admin.register(Barber)
class AdminBarber(admin.ModelAdmin):
  list_display = ('name', 'experience_years', 'is_active', 'photo_preview')
  list_filter = ('is_active',)
  search_fields = ('name',)
  readonly_fields = ('photo_preview',)
  fields = ('name', 'photo', 'photo_preview', 'experience_years', 'description', 'is_active')

  def photo_preview(self, obj):
    if obj.photo:
      return format_html('<img src="{}" style="max-height:120px;border-radius:8px;" />', obj.photo.url)
    return "—"

  photo_preview.short_description = "Фото"

@admin.register(Service)
class AdminService(admin.ModelAdmin):
  list_display = ('icon', 'name', 'price', 'duration_minutes')
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
    'created_at',
    'user'
  )
  list_filter = ('status', 'barber', 'service', 'booking_date')
  search_fields = ('client_name', 'client_phone','client_email')
  ordering = ('-booking_time', '-booking_date')
  
