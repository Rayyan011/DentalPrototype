# appointments/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError as DjangoValidationError
import uuid
import logging

from appointments.utils.constants import MAX_DOCTORS_PER_CLINIC_SHIFT
from appointments.utils.validators import (
    validate_not_friday,
    validate_surgery_room_not_in_evening,
    check_clinic_shift_capacity,
    validate_doctor_clinic_limit # Assuming this is defined in your validators.py
)

logger = logging.getLogger(__name__)

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
        rooms = self.room_set.filter(is_active=True)
        available_rooms = []
        for room in rooms:
            if room.is_available(date, shift):
                available_rooms.append(room)
        return available_rooms

class Room(models.Model):
    number = models.CharField(max_length=10)
    type = models.CharField(max_length=20, choices=RoomType.choices, default=RoomType.NORMAL)
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.number} ({self.get_type_display()}) at {self.clinic.name}"
    def is_available(self, date, shift):
        if self.type == RoomType.SURGERY and shift == ShiftType.EVENING:
            return False
        return not Appointment.objects.filter(
            room=self, date=date, shift=shift, status='CONFIRMED'
        ).exists()

class Doctor(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    specialization = models.CharField(max_length=100)
    def __str__(self):
        full_name = self.user.get_full_name()
        return f"Dr. {full_name if full_name.strip() else self.user.username} ({self.specialization})"
    def get_availability(self, date):
        rosters = Roster.objects.filter(doctor=self, date=date, is_active=True)
        return [roster.shift for roster in rosters]

class Service(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=30, choices=ServiceType.choices)
    description = models.TextField()
    duration_minutes = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    def get_price(self, shift):
        try:
            price_obj = Price.objects.get(service=self, shift=shift, is_active=True)
            return price_obj.amount
        except Price.DoesNotExist:
            logger.warning(f"Price not found for service '{self.name}' and shift '{shift}'. Returning 0.")
            return 0

class Price(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    shift = models.CharField(max_length=20, choices=ShiftType.choices)
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
    shift = models.CharField(max_length=20, choices=ShiftType.choices)
    is_active = models.BooleanField(default=True)
    class Meta:
        unique_together = ('doctor', 'date', 'shift')
    def __str__(self):
        return f"{self.doctor} at {self.clinic} on {self.date} ({self.get_shift_display()})"

    def clean(self):
        # This is where the Roster.clean() logic from my previous comprehensive message should go.
        # Specifically the part that correctly handles MAX_DOCTORS_PER_CLINIC_SHIFT
        # and removes the erroneous "This clinic already has a doctor..." check.
        # For brevity here, I'll put the corrected capacity check.
        # Ensure other Roster validations (like Friday) are also here.

        validate_not_friday(self.date)
        # validate_doctor_clinic_limit(self.doctor, self.clinic, self.date) # Optional complex rule

        # Corrected capacity check:
        active_rosters_for_slot = Roster.objects.filter(
            clinic=self.clinic, date=self.date, shift=self.shift, is_active=True
        )
        if self.pk: # If updating an existing roster instance
            active_rosters_for_slot = active_rosters_for_slot.exclude(pk=self.pk)

        distinct_doctor_ids_in_slot = set(active_rosters_for_slot.values_list('doctor_id', flat=True))

        # If this new roster entry's doctor is not already in the slot for this clinic/date/shift
        # AND the number of distinct doctors already in the slot is at the limit, then raise error.
        if self.doctor_id not in distinct_doctor_ids_in_slot and \
           len(distinct_doctor_ids_in_slot) >= MAX_DOCTORS_PER_CLINIC_SHIFT:
            raise DjangoValidationError(
                f"This clinic ({self.clinic.name}) has reached its maximum capacity of "
                f"{MAX_DOCTORS_PER_CLINIC_SHIFT} doctors for the {self.get_shift_display()} shift on {self.date}."
            )


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('CONFIRMED', 'Confirmed'), ('CANCELLED', 'Cancelled'),
        ('COMPLETED', 'Completed'), ('NO_SHOW', 'No Show'),
    ]
    reference = models.CharField(max_length=10, unique=True, editable=False)
    customer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(max_length=20, choices=ShiftType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reference} - {self.customer.username} with {self.doctor} on {self.date}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        if self.service and self.shift:
            self.price = self.service.get_price(self.shift)
        
        # full_clean is not a kwarg for save(). Call it explicitly if needed.
        # For API/Form saves, validation happens before save.
        # For direct model saves, you might want to call it.
        if not (kwargs.get('force_insert', False) or kwargs.get('force_update', False) or kwargs.get('update_fields')):
            self.full_clean(exclude=['reference'] if self.pk else None) # Exclude reference on update

        super().save(*args, **kwargs) # Remove 'full_clean' from here

    def generate_reference(self):
        return f"ID{uuid.uuid4().hex[:8].upper()}"

    def cancel(self):
        if self.status == 'CONFIRMED':
            self.status = 'CANCELLED'
            # When cancelling, only update the status field and bypass full_clean
            # if other validations might prevent this specific status change.
            super().save(update_fields=['status']) # Use super().save to avoid recursion if overriding save
            return True
        return False

    def generate_receipt(self):
        return f"""
        BOOKING RECEIPT
        ===============
        Reference: {self.reference}
        Customer: {self.customer.get_full_name() or self.customer.username}
        Doctor: {self.doctor}
        Clinic: {self.clinic.name}
        Room: {self.room.number} ({self.room.get_type_display()})
        Service: {self.service.name}
        Date: {self.date}
        Shift: {self.get_shift_display()}
        Price: {self.price} MVR
        Status: {self.get_status_display()}
        """.strip()

    def clean(self):
        errors = {}
        if self.date:
            try: validate_not_friday(self.date)
            except DjangoValidationError as e: errors.setdefault('date', []).extend(e.messages)
        else:
             if not self.pk : errors.setdefault('date', []).append("Date is required.")
        
        if self.room and self.shift:
            try: validate_surgery_room_not_in_evening(self.room.type, self.shift)
            except DjangoValidationError as e: errors.setdefault('__all__', []).extend(e.messages if isinstance(e.messages, list) else [e.message])

        if self.status == 'CONFIRMED' and self.clinic and self.date and self.shift:
            try: check_clinic_shift_capacity(self.clinic, self.date, self.shift, exclude_appointment_pk=self.pk)
            except DjangoValidationError as e: errors.setdefault('__all__', []).extend(e.messages if isinstance(e.messages, list) else [e.message])
        
        if self.doctor and self.clinic and self.date and self.shift:
            if not Roster.objects.filter(doctor=self.doctor, clinic=self.clinic, date=self.date, shift=self.shift, is_active=True).exists():
                errors.setdefault('doctor', []).append("This doctor is not scheduled at this clinic for the selected date and shift.")
        
        if self.status == 'CONFIRMED' and self.room and self.date and self.shift:
            conflicting_query = Appointment.objects.filter(
                room=self.room, date=self.date, shift=self.shift, status='CONFIRMED'
            )
            if self.pk:
                conflicting_query = conflicting_query.exclude(pk=self.pk)
            if conflicting_query.exists():
                errors.setdefault('room', []).append(f"Room {self.room} is already booked and confirmed for this date and shift.")
        
        if errors:
            raise DjangoValidationError(errors)

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('APPOINTMENT_UTILIZATION', 'Appointment Utilization'),
        ('REVENUE', 'Revenue Report'),
        ('DOCTOR_PERFORMANCE', 'Doctor Performance'),
        ('SERVICE_DEMAND', 'Service Demand'),
    ]
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)
    def __str__(self):
        return f"{self.get_report_type_display()} ({self.date_range_start} to {self.date_range_end})"