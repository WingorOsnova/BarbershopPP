import datetime
from .models import Booking

BASE_SLOT_MINUTES = 30
WORK_DAY_START = datetime.time(hour=9, minute=0)
WORK_DAY_END = datetime.time(hour=18, minute=0)

def generate_slot(date, start=WORK_DAY_START, end=WORK_DAY_END, step=BASE_SLOT_MINUTES):
    slots = []
    current = datetime.datetime.combine(date, start)
    end_dt = datetime.datetime.combine(date, end)
    step_dt = datetime.timedelta(minutes=step)

    while current < end_dt:
        slots.append(current.time())
        current += step_dt

    return slots


def get_available_slots(barber, date):
    all_slots = generate_slot(date)

    booked_times_qs = Booking.objects.filter(
        barber=barber,
        booking_date=date,
        status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED],
    ).values_list('booking_time', flat=True)

    booked_times = set(booked_times_qs)
    return [t for t in all_slots if t not in booked_times]
