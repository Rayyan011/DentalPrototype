from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from appointments.models import Doctor

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates default users with appropriate roles for testing the system'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Creating user roles and permissions...')
        
        # Create superuser if not exists
        if not User.objects.filter(username='admin').exists():
            superuser = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_staff=True,
                role='SYSTEM_ADMIN'
            )
            self.stdout.write(self.style.SUCCESS(f'Created superuser: {superuser.username}'))
        
        # Create manager
        if not User.objects.filter(username='manager').exists():
            manager = User.objects.create_user(
                username='manager',
                email='manager@example.com',
                password='manager123',
                first_name='Manager',
                last_name='User',
                is_staff=True,
                role='MANAGER'
            )
            self.stdout.write(self.style.SUCCESS(f'Created manager: {manager.username}'))
        
        # Create administrative officer
        if not User.objects.filter(username='officer').exists():
            officer = User.objects.create_user(
                username='officer',
                email='officer@example.com',
                password='officer123',
                first_name='Admin',
                last_name='Officer',
                is_staff=True,
                role='ADMIN_OFFICER'
            )
            self.stdout.write(self.style.SUCCESS(f'Created officer: {officer.username}'))
        
        # Create customer
        if not User.objects.filter(username='customer').exists():
            customer = User.objects.create_user(
                username='customer',
                email='customer@example.com',
                password='customer123',
                first_name='Sample',
                last_name='Customer',
                role='CUSTOMER'
            )
            self.stdout.write(self.style.SUCCESS(f'Created customer: {customer.username}'))
        
        # Create doctors
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
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    role='DOCTOR'
                )
                
                # Check if doctor profile exists
                if not Doctor.objects.filter(user=user).exists():
                    doctor = Doctor.objects.create(
                        user=user,
                        specialization=data['specialization']
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created doctor: {doctor}'))
        
        self.stdout.write(self.style.SUCCESS('All roles created successfully!')) 