from django.urls import path
from . import views

urlpatterns = [
  path('', views.home, name='home'),
  path('api/book/', views.booking_api, name='booking_api'),
  path('api/available-slots/', views.available_slots_api, name='available_slots_api'),
  path('login/', views.login_view, name='login'),
  path('register/', views.register_view, name='register'),
  path('dashboard/', views.dashboard_view, name='dashboard'),
  path('logout/', views.logout_view, name='logout'),
]
