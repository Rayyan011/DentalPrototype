from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import uuid
import logging
from datetime import time
from appointments.utils.validators import (
    validate_not_friday,
    validate_surgery_room_not_in_evening,
    is_surgery_room_in_evening,
    check_clinic_shift_capacity,
    validate_doctor_clinic_limit
)
from appointments.utils.constants import SHIFT_TIMES
from appointments.utils.price_calculator import calculate_price

class UserRole(models.TextChoices):
    CUSTOMER = 'CUSTOMER', 'Customer'
    DOCTOR = 'DOCTOR', 'Doctor'
    ADMIN_OFFICER = 'ADMIN_OFFICER', 'Administrative Officer'
    MANAGER = 'MANAGER', 'Manager'
    SYSTEM_ADMIN = 'SYSTEM_ADMIN', 'System Admin'

class ShiftType(models.TextChoices):
    MORNING = 'MORNING', 'Morning (08:00 - 12:00)'
    AFTERNOON = 'AFTERNOON', 'Afternoon (13:00 - 17:00)'
    EVENING = 'EVENING', 'Evening (18:00 - 22:00)'

class RoomType(models.TextChoices):
    NORMAL = 'NORMAL', 'Normal Room'
    SURGERY = 'SURGERY', 'Surgery Room'

class ServiceType(models.TextChoices):
    PREVENTIVE_CARE = 'PREVENTIVE_CARE', 'Preventive Care'
    BASIC_RESTORATIVE = 'BASIC_RESTORATIVE', 'Basic Restorative'
    MAJOR_RESTORATIVE = 'MAJOR_RESTORATIVE', 'Major Restorative/Cosmetic'
    SPECIALTY_SERVICES = 'SPECIALTY_SERVICES', 'Specialty Services'

class CustomUser(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Clinic(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    def get_available_rooms(self, date, shift):
        # Implementation to get available rooms for a specific date and shift
        rooms = self.room_set.filter(is_active=True)
        available_rooms = []
        
        for room in rooms:
            if room.is_available(date, shift):
                # Surgery rooms are not available during evening shifts
                if not (room.type == RoomType.SURGERY and shift == ShiftType.EVENING):
                    available_rooms.append(room)
        
        return available_rooms

class Room(models.Model):
    number = models.CharField(max_length=10)
    type = models.CharField(
        max_length=20,
        choices=RoomType.choices,
        default=RoomType.NORMAL
    )
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.number} ({self.get_type_display()}) at {self.clinic.name}"

    def is_available(self, date, shift):
        # Check if room is available for a specific date and shift
        # Surgery rooms are not available during evening shifts
        if self.type == RoomType.SURGERY and shift == ShiftType.EVENING:
            return False
            
        # Check if there are any appointments for this room at the given date and shift
        appointments = Appointment.objects.filter(
            room=self, 
            date=date, 
            shift=shift, 
            status='CONFIRMED'
        )
        
        return appointments.count() == 0

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username} ({self.specialization})"

    def get_availability(self, date):
        # Get shifts where the doctor is available on the given date
        # This considers roster assignments and existing appointments
        
        # Get the doctor's roster for the specified date
        rosters = Roster.objects.filter(doctor=self, date=date, is_active=True)
        
        # Get all shifts from rosters
        available_shifts = [roster.shift for roster in rosters]
        
        return available_shifts

class Service(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=30,
        choices=ServiceType.choices
    )
    description = models.TextField()
    duration_minutes = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def get_price(self, shift):
        try:
            price = Price.objects.get(service=self, shift=shift, is_active=True)
            return price.amount
        except Price.DoesNotExist:
            return 0

class Price(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    shift = models.CharField(
        max_length=20,
        choices=ShiftType.choices
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('service', 'shift')

    def __str__(self):
        return f"{self.service.name} - {self.get_shift_display()}: {self.amount}"

class Roster(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(
        max_length=20,
        choices=ShiftType.choices
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('doctor', 'date', 'shift')

    def __str__(self):
        return f"{self.doctor} at {self.clinic} on {self.date} ({self.get_shift_display()})"

    def clean(self):
        # Validate that no service is provided on Friday
        validate_not_friday(self.date)
        
        # Validate the doctor's clinic assignment limit
        validate_doctor_clinic_limit(self.doctor, self.clinic, self.date)
        
        # Check if this doctor already has a roster for this date and shift
        conflicting_roster = Roster.objects.filter(
            doctor=self.doctor,
            date=self.date,
            shift=self.shift
        ).exclude(pk=self.pk).first()
        
        if conflicting_roster:
            raise ValidationError(
                f"This doctor is already assigned to {conflicting_roster.clinic} during this time slot."
            )
        
        # Check if this clinic already has a doctor for this room, date, and shift
        conflicting_roster = Roster.objects.filter(
            clinic=self.clinic,
            date=self.date,
            shift=self.shift
        ).exclude(pk=self.pk).first()
        
        if conflicting_roster and conflicting_roster.doctor != self.doctor:
            raise ValidationError(
                f"This clinic already has a doctor ({conflicting_roster.doctor}) assigned during this time slot."
            )
            
        # Check how many doctors are scheduled for this clinic on this date and shift
        doctors_count = Roster.objects.filter(
            clinic=self.clinic,
            date=self.date,
            shift=self.shift
        ).exclude(pk=self.pk).count()
        
        # Each clinic can have at most 12 doctors
        if doctors_count >= 12:
            raise ValidationError("This clinic already has the maximum number of doctors (12) assigned.")

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'),
        ('NO_SHOW', 'No Show'),
    ]
    
    reference = models.CharField(max_length=10, unique=True, editable=False)
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(
        max_length=20,
        choices=ShiftType.choices
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='CONFIRMED'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.customer} with {self.doctor} on {self.date}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        
        # Always calculate price based on service and shift to ensure consistency
        if self.service and self.shift:
            self.price = self.service.get_price(self.shift)
            
        super().save(*args, **kwargs)

    def generate_reference(self):
        # Generate a unique reference number for the appointment
        return f"ID{uuid.uuid4().hex[:8].upper()}"

    def cancel(self):
        if self.status == 'CONFIRMED':
            self.status = 'CANCELLED'
            self.save()
            return True
        return False

    def generate_receipt(self):
        # Generate a receipt for the appointment
        shift_times = {
            'MORNING': '08:00 - 12:00',
            'AFTERNOON': '13:00 - 17:00',
            'EVENING': '18:00 - 22:00',
        }
        
        receipt = f"""
        BOOKING RECEIPT
        ===============
        Reference: {self.reference}
        Customer: {self.customer.get_full_name() or self.customer.username}
        Doctor: {self.doctor}
        Clinic: {self.clinic.name}
        Room: {self.room.number} ({self.room.get_type_display()})
        Service: {self.service.name}
        Date: {self.date}
        Shift: {self.get_shift_display()} ({shift_times[self.shift]})
        Price: {self.price} MVR
        Status: {self.get_status_display()}
        """
        return receipt

    def clean(self):
        # Validate that no appointment is made on Friday
        validate_not_friday(self.date)
            
        # Validate that surgery rooms are not booked during evening shifts
        validate_surgery_room_not_in_evening(self.room.type, self.shift)
        
        # Check clinic capacity (10 patients per shift)
        check_clinic_shift_capacity(self.clinic, self.date, self.shift)
        
        # Check if the doctor is assigned to this clinic on this date and shift
        roster_exists = Roster.objects.filter(
            doctor=self.doctor,
            clinic=self.clinic,
            date=self.date,
            shift=self.shift,
            is_active=True
        ).exists()
        
        if not roster_exists:
            raise ValidationError(
                "This doctor is not scheduled at this clinic for the selected date and shift."
            )

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('APPOINTMENT_UTILIZATION', 'Appointment Utilization'),
        ('REVENUE', 'Revenue Report'),
        ('DOCTOR_PERFORMANCE', 'Doctor Performance'),
        ('SERVICE_DEMAND', 'Service Demand'),
    ]
    
    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPE_CHOICES
    )
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.get_report_type_display()} ({self.date_range_start} to {self.date_range_end})"

# Define shift times directly in models.py until we fully refactor
SHIFT_TIMES = {
    'MORNING': '08:00 - 12:00',
    'AFTERNOON': '13:00 - 17:00',
    'EVENING': '18:00 - 22:00',
}

logger = logging.getLogger(__name__)
