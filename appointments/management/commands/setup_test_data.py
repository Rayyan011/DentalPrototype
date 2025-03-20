from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from datetime import date, timedelta

from appointments.models import (
    Clinic, Room, Doctor, Service, Price,
    Roster, RoomType, ServiceType, ShiftType
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Sets up test data for Island Dental Booking System'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Setting up test data...')
        
        # Create users with different roles
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                role='SYSTEM_ADMIN',
                first_name='Admin',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin.username}'))
            
        if not User.objects.filter(username='manager').exists():
            manager = User.objects.create_user(
                username='manager',
                email='manager@example.com',
                password='manager123',
                role='MANAGER',
                first_name='Manager',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS(f'Created manager user: {manager.username}'))
            
        if not User.objects.filter(username='officer').exists():
            officer = User.objects.create_user(
                username='officer',
                email='officer@example.com',
                password='officer123',
                role='ADMIN_OFFICER',
                first_name='Admin',
                last_name='Officer'
            )
            self.stdout.write(self.style.SUCCESS(f'Created officer user: {officer.username}'))
            
        if not User.objects.filter(username='customer').exists():
            customer = User.objects.create_user(
                username='customer',
                email='customer@example.com',
                password='customer123',
                role='CUSTOMER',
                first_name='Test',
                last_name='Customer'
            )
            self.stdout.write(self.style.SUCCESS(f'Created customer user: {customer.username}'))
        
        # Create doctor users
        doctor_data = [
            {'username': 'doctor1', 'first_name': 'John', 'last_name': 'Doe', 'specialization': 'General Dentistry'},
            {'username': 'doctor2', 'first_name': 'Jane', 'last_name': 'Smith', 'specialization': 'Orthodontics'},
            {'username': 'doctor3', 'first_name': 'Mike', 'last_name': 'Johnson', 'specialization': 'Periodontics'},
        ]
        
        for data in doctor_data:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=f"{data['username']}@example.com",
                    password=f"{data['username']}123",
                    role='DOCTOR',
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )
                doctor = Doctor.objects.create(
                    user=user,
                    specialization=data['specialization']
                )
                self.stdout.write(self.style.SUCCESS(f'Created doctor: {doctor}'))
        
        # Create clinics
        clinic_data = [
            {'name': 'Male Clinic', 'location': 'Male', 'address': '123 Main St, Male', 'phone': '123-456-7890'},
            {'name': 'Kulhudhufushi Clinic', 'location': 'Kulhudhufushi', 'address': '456 Ocean Rd, Kulhudhufushi', 'phone': '234-567-8901'},
            {'name': 'Addu City Clinic', 'location': 'Addu City', 'address': '789 Palm Ave, Addu City', 'phone': '345-678-9012'},
        ]
        
        for data in clinic_data:
            clinic, created = Clinic.objects.get_or_create(
                name=data['name'],
                defaults={
                    'location': data['location'],
                    'address': data['address'],
                    'phone': data['phone']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created clinic: {clinic.name}'))
            
            # Create rooms for each clinic
            if Room.objects.filter(clinic=clinic).count() == 0:
                # Create 2 normal rooms
                for i in range(1, 3):
                    room = Room.objects.create(
                        number=f'{i}01',
                        type=RoomType.NORMAL,
                        clinic=clinic
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created normal room: {room.number} at {clinic.name}'))
                
                # Create 1 surgery room
                room = Room.objects.create(
                    number='301',
                    type=RoomType.SURGERY,
                    clinic=clinic
                )
                self.stdout.write(self.style.SUCCESS(f'Created surgery room: {room.number} at {clinic.name}'))
        
        # Create services
        service_data = [
            {'name': 'Teeth Cleaning', 'type': ServiceType.PREVENTIVE_CARE, 'description': 'Basic teeth cleaning service', 'duration': 30},
            {'name': 'Cavity Filling', 'type': ServiceType.BASIC_RESTORATIVE, 'description': 'Filling for minor cavities', 'duration': 45},
            {'name': 'Root Canal', 'type': ServiceType.MAJOR_RESTORATIVE, 'description': 'Root canal treatment', 'duration': 90},
            {'name': 'Dental Implant', 'type': ServiceType.SPECIALTY_SERVICES, 'description': 'Dental implant procedure', 'duration': 120},
        ]
        
        # Price mapping as per requirements
        price_mapping = {
            ServiceType.PREVENTIVE_CARE: {'MORNING': 150, 'AFTERNOON': 125, 'EVENING': 100},
            ServiceType.BASIC_RESTORATIVE: {'MORNING': 200, 'AFTERNOON': 250, 'EVENING': 150},
            ServiceType.MAJOR_RESTORATIVE: {'MORNING': 250, 'AFTERNOON': 400, 'EVENING': 600},
            ServiceType.SPECIALTY_SERVICES: {'MORNING': 350, 'AFTERNOON': 500, 'EVENING': 750},
        }
        
        for data in service_data:
            service, created = Service.objects.get_or_create(
                name=data['name'],
                defaults={
                    'type': data['type'],
                    'description': data['description'],
                    'duration_minutes': data['duration']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created service: {service.name}'))
                
                # Create prices for each shift
                for shift, amount in price_mapping[data['type']].items():
                    price, price_created = Price.objects.get_or_create(
                        service=service,
                        shift=shift,
                        defaults={'amount': amount}
                    )
                    if price_created:
                        self.stdout.write(self.style.SUCCESS(f'Created price: {service.name} - {shift}: {amount}'))
        
        # Create rosters for the next 7 days
        today = date.today()
        doctors = Doctor.objects.all()
        clinics = Clinic.objects.all()
        shifts = [ShiftType.MORNING, ShiftType.AFTERNOON, ShiftType.EVENING]
        
        # Clear existing future rosters
        Roster.objects.filter(date__gte=today).delete()
        
        for i in range(7):  # Next 7 days
            current_date = today + timedelta(days=i)
            
            # Skip Fridays (weekday 4)
            if current_date.weekday() == 4:
                continue
                
            # Assign each doctor to a different clinic for each shift
            for doc_index, doctor in enumerate(doctors):
                for shift_index, shift in enumerate(shifts):
                    # Rotate clinics for each doctor and shift
                    clinic_index = (doc_index + shift_index) % len(clinics)
                    clinic = clinics[clinic_index]
                    
                    roster = Roster.objects.create(
                        doctor=doctor,
                        clinic=clinic,
                        date=current_date,
                        shift=shift
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'Created roster: {doctor} at {clinic.name} on {current_date} ({shift})'
                    ))
        
        self.stdout.write(self.style.SUCCESS('Test data setup completed successfully!')) 