from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import random
import logging

from appointments.models import Clinic, Room, Doctor, Roster, UserRole
from appointments.utils.constants import MAX_DOCTORS_PER_CLINIC

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Set up clinics with rooms and doctor rotations'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=30, help='Number of days to generate roster for')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before setup')

    def handle(self, *args, **options):
        days = options['days']
        clear = options.get('clear', False)
        
        with transaction.atomic():
            if clear:
                self.stdout.write(self.style.WARNING('Clearing existing rosters...'))
                Roster.objects.all().delete()
                
                self.stdout.write(self.style.WARNING('Clearing existing rooms...'))
                Room.objects.all().delete()
                
                self.stdout.write(self.style.WARNING('Clearing existing clinics...'))
                Clinic.objects.all().delete()
                
                self.stdout.write(self.style.WARNING('Clearing existing doctors...'))
                Doctor.objects.all().delete()
                
                # We don't delete users as they might be referenced elsewhere
            
            # Create clinics
            self.stdout.write(self.style.SUCCESS('Creating clinics...'))
            clinic_data = [
                {
                    'name': 'Male Clinic',
                    'location': 'Male City',
                    'address': 'Orchid Magu, Male 20095',
                    'phone': '+960 333-1234'
                },
                {
                    'name': 'Kulhudhufushi Clinic',
                    'location': 'Kulhudhufushi',
                    'address': 'Main Street, Kulhudhufushi 03000',
                    'phone': '+960 333-5678'
                },
                {
                    'name': 'Addu City Clinic',
                    'location': 'Addu City',
                    'address': 'Hithadhoo, Addu City 19020',
                    'phone': '+960 333-9012'
                }
            ]
            
            clinics = []
            for data in clinic_data:
                clinic, created = Clinic.objects.get_or_create(
                    name=data['name'],
                    defaults={
                        'location': data['location'],
                        'address': data['address'],
                        'phone': data['phone'],
                        'is_active': True
                    }
                )
                clinics.append(clinic)
                action = 'Created' if created else 'Found existing'
                self.stdout.write(self.style.SUCCESS(f'{action} clinic: {clinic.name}'))
            
            # Create rooms for each clinic (2 normal, 1 surgery)
            self.stdout.write(self.style.SUCCESS('Creating rooms...'))
            for clinic in clinics:
                # Check if rooms already exist
                existing_rooms = Room.objects.filter(clinic=clinic)
                if existing_rooms.count() >= 3:
                    self.stdout.write(self.style.SUCCESS(f'Clinic {clinic.name} already has {existing_rooms.count()} rooms'))
                    continue
                
                # Create 2 normal rooms
                for i in range(1, 3):
                    room, created = Room.objects.get_or_create(
                        clinic=clinic,
                        number=f'N{i}',
                        defaults={
                            'type': 'NORMAL',
                            'is_active': True
                        }
                    )
                    action = 'Created' if created else 'Found existing'
                    self.stdout.write(self.style.SUCCESS(f'{action} normal room: {room.number} at {clinic.name}'))
                
                # Create 1 surgery room
                room, created = Room.objects.get_or_create(
                    clinic=clinic,
                    number='S1',
                    defaults={
                        'type': 'SURGERY',
                        'is_active': True
                    }
                )
                action = 'Created' if created else 'Found existing'
                self.stdout.write(self.style.SUCCESS(f'{action} surgery room: {room.number} at {clinic.name}'))
            
            # Create doctors (12 per clinic, 36 total)
            self.stdout.write(self.style.SUCCESS('Creating doctors...'))
            specializations = [
                'General Dentistry', 'Orthodontics', 'Pediatric Dentistry', 
                'Endodontics', 'Periodontics', 'Oral Surgery', 'Prosthodontics'
            ]
            
            all_doctors = []
            doctor_credentials = []
            
            # Generate unique doctor credentials
            for i in range(1, 37):
                suffix = str(i).zfill(2)
                username = f'doctor{suffix}'
                email = f'doctor{suffix}@islanddental.mv'
                doctor_credentials.append((username, email, f'Dr. Name {suffix}'))
            
            # Create doctors
            for username, email, name in doctor_credentials:
                # Check if user exists, create if not
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': name.split()[1],
                        'last_name': name.split()[2],
                        'role': UserRole.DOCTOR,
                        'is_active': True
                    }
                )
                
                # Check if doctor exists, create if not
                doctor, doctor_created = Doctor.objects.get_or_create(
                    user=user,
                    defaults={
                        'specialization': random.choice(specializations)
                    }
                )
                
                all_doctors.append(doctor)
                action = 'Created' if doctor_created else 'Found existing'
                self.stdout.write(self.style.SUCCESS(f'{action} doctor: {name}'))
            
            # Set up doctor rotations
            self.stdout.write(self.style.SUCCESS('Setting up doctor rotations...'))
            
            # Divide doctors into 3 groups (one per clinic)
            doctor_groups = [all_doctors[i:i+12] for i in range(0, len(all_doctors), 12)]
            
            # Get current date
            start_date = datetime.now().date()
            
            # Create roster for each day
            for day in range(days):
                current_date = start_date + timedelta(days=day)
                
                # Skip Fridays (5 is Friday in Python's datetime, where Monday is 0)
                if current_date.weekday() == 4:  # Friday
                    self.stdout.write(self.style.WARNING(f'Skipping Friday: {current_date}'))
                    continue
                
                # Every 5 days, rotate the doctor groups between clinics
                rotation_index = (day // 5) % 3
                
                # Assign doctors to clinics based on rotation
                for clinic_index, clinic in enumerate(clinics):
                    # Get the doctor group for this clinic in this rotation
                    doctor_group_index = (clinic_index + rotation_index) % 3
                    doctors_for_clinic = doctor_groups[doctor_group_index]
                    
                    # Create rosters for each shift
                    for shift in ['MORNING', 'AFTERNOON', 'EVENING']:
                        # Skip evening shift for Fridays
                        if current_date.weekday() == 4 and shift == 'EVENING':
                            continue
                        
                        # Select 4 doctors for this shift (out of the 12 assigned to this clinic)
                        shift_doctors = random.sample(doctors_for_clinic, 4)
                        
                        for doctor in shift_doctors:
                            try:
                                roster, created = Roster.objects.get_or_create(
                                    doctor=doctor,
                                    clinic=clinic,
                                    date=current_date,
                                    shift=shift
                                )
                                if created:
                                    self.stdout.write(f'Created roster: {doctor.user.get_full_name()} at {clinic.name} on {current_date} ({shift})')
                            except ValidationError as e:
                                self.stdout.write(self.style.ERROR(f'Error creating roster: {e}'))
            
            self.stdout.write(self.style.SUCCESS('Clinic rotation setup completed successfully!')) 