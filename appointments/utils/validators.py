# appointments/utils/validators.py
"""
Validation functions for appointments.
"""
from django.core.exceptions import ValidationError

def is_friday(check_date):
    return check_date.weekday() == 4

def is_surgery_room_in_evening(room_type, shift):
    from ..models import RoomType, ShiftType # Local import for type safety
    return room_type == RoomType.SURGERY and shift == ShiftType.EVENING

def validate_not_friday(check_date):
    if is_friday(check_date):
        raise ValidationError("No service is available on Fridays.")

def validate_surgery_room_not_in_evening(room_type, shift):
    if is_surgery_room_in_evening(room_type, shift):
        raise ValidationError("Surgery rooms are not available during evening shifts.")

def check_clinic_shift_capacity(clinic, date, shift, exclude_appointment_pk=None):
    from ..models import Appointment # Local import to avoid circularity
    from .constants import MAX_PATIENTS_PER_SHIFT

    appointments_query = Appointment.objects.filter(
        clinic=clinic,
        date=date,
        shift=shift,
        status='CONFIRMED'
    )
    if exclude_appointment_pk:
        appointments_query = appointments_query.exclude(pk=exclude_appointment_pk)
    
    appointment_count = appointments_query.count()
    if appointment_count >= MAX_PATIENTS_PER_SHIFT:
        raise ValidationError(
            f"This clinic has reached its capacity of {MAX_PATIENTS_PER_SHIFT} confirmed patients for {shift} on {date}."
        )
    return appointment_count

def validate_doctor_clinic_limit(doctor, clinic, date):
    # Placeholder - implement actual logic if this rule is needed for individual roster saves
    pass