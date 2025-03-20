from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from appointments.models import (
    CustomUser, Clinic, Room, Doctor, 
    Service, Price, Roster, Appointment, Report
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Assigns proper permissions to each user role'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Assigning permissions to user roles...')
        
        # Create or get role-based groups
        customer_group, _ = Group.objects.get_or_create(name='Customers')
        doctor_group, _ = Group.objects.get_or_create(name='Doctors')
        officer_group, _ = Group.objects.get_or_create(name='Admin Officers')
        manager_group, _ = Group.objects.get_or_create(name='Managers')
        
        # Clear any existing permissions
        customer_group.permissions.clear()
        doctor_group.permissions.clear()
        officer_group.permissions.clear()
        manager_group.permissions.clear()
        
        # Get content types for models
        appointment_ct = ContentType.objects.get_for_model(Appointment)
        clinic_ct = ContentType.objects.get_for_model(Clinic)
        room_ct = ContentType.objects.get_for_model(Room)
        doctor_ct = ContentType.objects.get_for_model(Doctor)
        service_ct = ContentType.objects.get_for_model(Service)
        price_ct = ContentType.objects.get_for_model(Price)
        roster_ct = ContentType.objects.get_for_model(Roster)
        report_ct = ContentType.objects.get_for_model(Report)
        user_ct = ContentType.objects.get_for_model(CustomUser)
        
        # Customer permissions
        customer_perms = [
            # Appointments - view and create own
            Permission.objects.get(codename='add_appointment', content_type=appointment_ct),
            Permission.objects.get(codename='change_appointment', content_type=appointment_ct),
            Permission.objects.get(codename='view_appointment', content_type=appointment_ct),
            
            # View-only permissions for clinics, doctors, services
            Permission.objects.get(codename='view_clinic', content_type=clinic_ct),
            Permission.objects.get(codename='view_doctor', content_type=doctor_ct),
            Permission.objects.get(codename='view_service', content_type=service_ct),
        ]
        customer_group.permissions.add(*customer_perms)
        
        # Doctor permissions
        doctor_perms = [
            # Appointments - view and update own
            Permission.objects.get(codename='view_appointment', content_type=appointment_ct),
            Permission.objects.get(codename='change_appointment', content_type=appointment_ct),
            
            # View roster
            Permission.objects.get(codename='view_roster', content_type=roster_ct),
            
            # View clinics, services
            Permission.objects.get(codename='view_clinic', content_type=clinic_ct),
            Permission.objects.get(codename='view_service', content_type=service_ct),
        ]
        doctor_group.permissions.add(*doctor_perms)
        
        # Officer permissions
        officer_perms = [
            # Full appointment management
            Permission.objects.get(codename='add_appointment', content_type=appointment_ct),
            Permission.objects.get(codename='change_appointment', content_type=appointment_ct),
            Permission.objects.get(codename='view_appointment', content_type=appointment_ct),
            Permission.objects.get(codename='delete_appointment', content_type=appointment_ct),
            
            # Roster management
            Permission.objects.get(codename='add_roster', content_type=roster_ct),
            Permission.objects.get(codename='change_roster', content_type=roster_ct),
            Permission.objects.get(codename='view_roster', content_type=roster_ct),
            Permission.objects.get(codename='delete_roster', content_type=roster_ct),
            
            # View doctors, clinics, rooms, services
            Permission.objects.get(codename='view_doctor', content_type=doctor_ct),
            Permission.objects.get(codename='view_clinic', content_type=clinic_ct),
            Permission.objects.get(codename='view_room', content_type=room_ct),
            Permission.objects.get(codename='view_service', content_type=service_ct),
        ]
        officer_group.permissions.add(*officer_perms)
        
        # Manager permissions (all permissions)
        manager_perms = []
        for model_ct in [appointment_ct, clinic_ct, room_ct, doctor_ct, service_ct, price_ct, roster_ct, report_ct, user_ct]:
            for perm in Permission.objects.filter(content_type=model_ct):
                manager_perms.append(perm)
        
        manager_group.permissions.add(*manager_perms)
        
        # Assign users to groups based on their role
        for user in User.objects.all():
            # Remove from all groups first
            user.groups.clear()
            
            # Add to appropriate group based on role
            if user.role == 'CUSTOMER':
                user.groups.add(customer_group)
            elif user.role == 'DOCTOR':
                user.groups.add(doctor_group)
            elif user.role == 'ADMIN_OFFICER':
                user.groups.add(officer_group)
            elif user.role == 'MANAGER':
                user.groups.add(manager_group)
            
            # Ensure staff permissions for admin roles
            if user.role in ['MANAGER', 'ADMIN_OFFICER', 'SYSTEM_ADMIN']:
                user.is_staff = True
                user.save()
        
        self.stdout.write(self.style.SUCCESS('All permissions assigned successfully!')) 