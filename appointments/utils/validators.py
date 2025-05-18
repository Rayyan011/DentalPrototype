"""
Validation functions for appointments.
"""
from django.core.exceptions import ValidationError
from datetime import date

def is_friday(check_date):
    """
    Check if the given date is a Friday.
    
    Args:
        check_date: A date object to check.
    
    Returns:
        True if the date is a Friday, False otherwise.
    """
    return check_date.weekday() == 4  # 4 corresponds to Friday


def is_surgery_room_in_evening(room_type, shift):
    """
    Check if the room is a surgery room and the shift is evening.
    
    Args:
        room_type: The type of room.
        shift: The shift value.
    
    Returns:
        True if the room is a surgery room and the shift is evening, False otherwise.
    """
    return room_type == 'SURGERY' and shift == 'EVENING'


def validate_not_friday(check_date):
    """
    Validate that the given date is not a Friday.
    
    Args:
        check_date: A date object to check.
    
    Raises:
        ValidationError: If the date is a Friday.
    """
    if is_friday(check_date):
        raise ValidationError("No service is available on Fridays.")


def validate_surgery_room_not_in_evening(room_type, shift):
    """
    Validate that surgery rooms are not booked during evening shifts.
    
    Args:
        room_type: The type of room.
        shift: The shift value.
    
    Raises:
        ValidationError: If the room is a surgery room and the shift is evening.
    """
    if is_surgery_room_in_evening(room_type, shift):
        raise ValidationError("Surgery rooms are not available during evening shifts.")


def check_clinic_shift_capacity(clinic, date, shift):
    """
    Check if a clinic has reached its capacity of 10 patients per shift.
    
    Args:
        clinic: The clinic to check.
        date: The date to check.
        shift: The shift to check.
        
    Returns:
        int: The number of appointments already booked for this clinic, date, and shift.
        
    Raises:
        ValidationError: If the clinic has reached its capacity for the shift.
    """
    from ..models import Appointment
    
    # Count confirmed appointments for this clinic, date, and shift
    appointment_count = Appointment.objects.filter(
        clinic=clinic,
        date=date,
        shift=shift,
        status='CONFIRMED'
    ).count()
    
    # Check if the clinic has reached its capacity
    if appointment_count >= 10:
        raise ValidationError(
            f"This clinic has reached its capacity of 10 patients for {shift} on {date}."
        )
    
    return appointment_count


def validate_doctor_clinic_limit(doctor, clinic, date):
    """
    Validates that a doctor is not assigned to more than 12 distinct clinics in rotation.
    
    This enforces the business rule that doctors should rotate among no more than 12 clinics.
    
    Args:
        doctor: The doctor to check.
        clinic: The clinic being assigned to.
        date: The date of the assignment.
        
    Raises:
        ValidationError: If the doctor would exceed the limit of 12 distinct clinics.
    """
    from ..models import Roster
    
    # Get all distinct clinics assigned to this doctor in the future
    # (including the current date but excluding current assignment if it exists)
    future_clinics = Roster.objects.filter(
        doctor=doctor,
        date__gte=date
    ).exclude(
        clinic=clinic,
        date=date
    ).values_list('clinic', flat=True).distinct()
    
    # Count the unique clinics
    distinct_clinic_count = len(set(future_clinics))
    
    # If adding this clinic would exceed 12 total clinics
    if clinic.id not in future_clinics and distinct_clinic_count >= 12:
        raise ValidationError(
            f"Doctor {doctor} cannot be assigned to more than 12 distinct clinics in rotation."
        ) 
