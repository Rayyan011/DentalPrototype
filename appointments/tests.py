from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date, timedelta
import json

from .models import (
    Clinic, Room, Doctor, Service, Price, 
    Roster, Appointment, ShiftType, RoomType, ServiceType
)

User = get_user_model()

class ModelTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='password123', 
            email='admin@example.com',
            role='SYSTEM_ADMIN'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager', 
            password='password123', 
            email='manager@example.com',
            role='MANAGER'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor', 
            password='password123', 
            email='doctor@example.com',
            role='DOCTOR'
        )
        
        self.customer_user = User.objects.create_user(
            username='customer', 
            password='password123', 
            email='customer@example.com',
            role='CUSTOMER'
        )
        
        # Create test clinic
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            location='Male',
            address='Test Address',
            phone='1234567890'
        )
        
        # Create test rooms
        self.normal_room = Room.objects.create(
            number='101',
            type=RoomType.NORMAL,
            clinic=self.clinic
        )
        
        self.surgery_room = Room.objects.create(
            number='102',
            type=RoomType.SURGERY,
            clinic=self.clinic
        )
        
        # Create test doctor
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='General Dentistry'
        )
        
        # Create test service
        self.service = Service.objects.create(
            name='Teeth Cleaning',
            type=ServiceType.PREVENTIVE_CARE,
            description='Basic teeth cleaning service',
            duration_minutes=30
        )
        
        # Create test prices
        self.morning_price = Price.objects.create(
            service=self.service,
            shift=ShiftType.MORNING,
            amount=150.00
        )
        
        self.afternoon_price = Price.objects.create(
            service=self.service,
            shift=ShiftType.AFTERNOON,
            amount=125.00
        )
        
        self.evening_price = Price.objects.create(
            service=self.service,
            shift=ShiftType.EVENING,
            amount=100.00
        )
        
        # Create test roster
        today = date.today()
        self.today = today
        
        # Make sure it's not a Friday (weekday 4)
        if today.weekday() == 4:  # Friday
            today = today + timedelta(days=1)  # Move to Saturday
        
        self.roster = Roster.objects.create(
            doctor=self.doctor,
            clinic=self.clinic,
            date=today,
            shift=ShiftType.MORNING
        )

    def test_clinic_model(self):
        """Test the clinic model"""
        self.assertEqual(str(self.clinic), 'Test Clinic')
        self.assertTrue(self.clinic.is_active)

    def test_room_model(self):
        """Test the room model"""
        self.assertEqual(str(self.normal_room), f"101 (Normal Room) at {self.clinic.name}")
        self.assertTrue(self.normal_room.is_active)
        
        # Test room availability
        self.assertTrue(self.normal_room.is_available(self.today, ShiftType.MORNING))
        self.assertTrue(self.normal_room.is_available(self.today, ShiftType.EVENING))
        
        # Surgery room should not be available in evening
        self.assertFalse(self.surgery_room.is_available(self.today, ShiftType.EVENING))

    def test_doctor_model(self):
        """Test the doctor model"""
        expected_str = f"Dr. {self.doctor_user.username} (General Dentistry)"
        self.assertEqual(str(self.doctor), expected_str)
        
        # Test doctor availability
        available_shifts = self.doctor.get_availability(self.today)
        self.assertEqual(len(available_shifts), 1)
        self.assertEqual(available_shifts[0], ShiftType.MORNING)

    def test_service_model(self):
        """Test the service model"""
        self.assertEqual(str(self.service), "Teeth Cleaning (Preventive Care)")
        self.assertTrue(self.service.is_active)
        
        # Test price retrieval
        self.assertEqual(self.service.get_price(ShiftType.MORNING), 150.00)
        self.assertEqual(self.service.get_price(ShiftType.AFTERNOON), 125.00)
        self.assertEqual(self.service.get_price(ShiftType.EVENING), 100.00)

    def test_appointment_model(self):
        """Test the appointment model"""
        # Create a test appointment
        appointment = Appointment.objects.create(
            customer=self.customer_user,
            doctor=self.doctor,
            clinic=self.clinic,
            room=self.normal_room,
            service=self.service,
            date=self.today,
            shift=ShiftType.MORNING,
            price=150.00
        )
        
        # Test appointment reference generation
        self.assertIsNotNone(appointment.reference)
        self.assertEqual(len(appointment.reference), 10)  # ID + 8 chars
        
        # Test appointment cancellation
        self.assertEqual(appointment.status, 'CONFIRMED')
        success = appointment.cancel()
        self.assertTrue(success)
        self.assertEqual(appointment.status, 'CANCELLED')
        
        # Test receipt generation
        receipt = appointment.generate_receipt()
        self.assertIn(appointment.reference, receipt)
        self.assertIn(self.customer_user.username, receipt)
        self.assertIn(str(self.doctor), receipt)
        self.assertIn(self.clinic.name, receipt)
        self.assertIn(self.normal_room.number, receipt)
        self.assertIn(self.service.name, receipt)
        self.assertIn("CANCELLED", receipt)

class APITestCase(TestCase):
    def setUp(self):
        # Create test data similar to ModelTestCase
        self.admin_user = User.objects.create_user(
            username='admin', 
            password='password123', 
            email='admin@example.com',
            role='SYSTEM_ADMIN'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager', 
            password='password123', 
            email='manager@example.com',
            role='MANAGER'
        )
        
        self.doctor_user = User.objects.create_user(
            username='doctor', 
            password='password123', 
            email='doctor@example.com',
            role='DOCTOR'
        )
        
        self.customer_user = User.objects.create_user(
            username='customer', 
            password='password123', 
            email='customer@example.com',
            role='CUSTOMER'
        )
        
        self.clinic = Clinic.objects.create(
            name='Test Clinic',
            location='Male',
            address='Test Address',
            phone='1234567890'
        )
        
        self.normal_room = Room.objects.create(
            number='101',
            type=RoomType.NORMAL,
            clinic=self.clinic
        )
        
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization='General Dentistry'
        )
        
        self.service = Service.objects.create(
            name='Teeth Cleaning',
            type=ServiceType.PREVENTIVE_CARE,
            description='Basic teeth cleaning service',
            duration_minutes=30
        )
        
        self.price = Price.objects.create(
            service=self.service,
            shift=ShiftType.MORNING,
            amount=150.00
        )
        
        # Make sure it's not a Friday (weekday 4)
        today = date.today()
        if today.weekday() == 4:  # Friday
            today = today + timedelta(days=1)  # Move to Saturday
        self.today = today
        
        self.roster = Roster.objects.create(
            doctor=self.doctor,
            clinic=self.clinic,
            date=today,
            shift=ShiftType.MORNING
        )
        
        # Create API client
        self.client = APIClient()

    def test_clinic_list_api(self):
        """Test the clinic list API endpoint"""
        # Login as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Get clinics
        response = self.client.get(reverse('clinic-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Clinic')

    def test_doctor_availability_api(self):
        """Test the doctor availability API endpoint"""
        # Login as customer
        self.client.force_authenticate(user=self.customer_user)
        
        # Get doctor availability
        url = reverse('doctor-availability', args=[self.doctor.id])
        response = self.client.get(url, {'date': self.today.strftime('%Y-%m-%d')})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['available_shifts'], [ShiftType.MORNING])

    def test_appointment_booking_api(self):
        """Test the appointment booking API endpoint"""
        # Login as customer
        self.client.force_authenticate(user=self.customer_user)
        
        # Check availability
        url = reverse('appointment-check-availability')
        response = self.client.get(url, {
            'clinic': self.clinic.id,
            'date': self.today.strftime('%Y-%m-%d'),
            'service': self.service.id,
            'shift': ShiftType.MORNING
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['price'], 150.00)
        self.assertEqual(len(response.data['available_rooms']), 2)
        self.assertEqual(len(response.data['available_doctors']), 1)
        
        # Book appointment
        response = self.client.post(reverse('appointment-list'), {
            'doctor': self.doctor.id,
            'clinic': self.clinic.id,
            'room': self.normal_room.id,
            'service': self.service.id,
            'date': self.today.strftime('%Y-%m-%d'),
            'shift': ShiftType.MORNING
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['price'], 150.00)
        self.assertEqual(response.data['status'], 'CONFIRMED')
        self.assertIsNotNone(response.data['reference'])
        
        # Try to book same room and shift (should fail due to availability)
        response = self.client.post(reverse('appointment-list'), {
            'doctor': self.doctor.id,
            'clinic': self.clinic.id,
            'room': self.normal_room.id,
            'service': self.service.id,
            'date': self.today.strftime('%Y-%m-%d'),
            'shift': ShiftType.MORNING
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_appointment_cancel_api(self):
        """Test the appointment cancellation API endpoint"""
        # Create an appointment
        appointment = Appointment.objects.create(
            customer=self.customer_user,
            doctor=self.doctor,
            clinic=self.clinic,
            room=self.normal_room,
            service=self.service,
            date=self.today,
            shift=ShiftType.MORNING,
            price=150.00
        )
        
        # Login as customer
        self.client.force_authenticate(user=self.customer_user)
        
        # Cancel appointment
        url = reverse('appointment-cancel', args=[appointment.id])
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['appointment']['status'], 'CANCELLED')

    def test_surgery_room_evening_restriction(self):
        """Test that surgery rooms cannot be booked in the evening"""
        surgery_room = Room.objects.create(
            number='103',
            type=RoomType.SURGERY,
            clinic=self.clinic
        )
        
        # Create evening roster
        Roster.objects.create(
            doctor=self.doctor,
            clinic=self.clinic,
            date=self.today,
            shift=ShiftType.EVENING
        )
        
        # Login as customer
        self.client.force_authenticate(user=self.customer_user)
        
        # Try to book surgery room in the evening (should fail)
        response = self.client.post(reverse('appointment-list'), {
            'doctor': self.doctor.id,
            'clinic': self.clinic.id,
            'room': surgery_room.id,
            'service': self.service.id,
            'date': self.today.strftime('%Y-%m-%d'),
            'shift': ShiftType.EVENING
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Surgery rooms are not available during evening shifts', str(response.data))
