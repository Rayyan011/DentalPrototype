# appointments/tests.py

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient, APITestCase as DRF_APITestCase # Alias to avoid clash
from rest_framework import status
from datetime import date, timedelta, datetime

from .models import (
    Clinic, Room, Doctor, Service, Price,
    Roster, Appointment, Report,
    CustomUser, UserRole, ShiftType, RoomType, ServiceType
)
from .utils import validators
from .utils.constants import MAX_PATIENTS_PER_SHIFT, MAX_DOCTORS_PER_CLINIC_SHIFT

User = get_user_model()


# --- Utility Functions for Test Setup ---
def create_user_for_test(username, role, is_staff=None, is_superuser=False, password="password123", first_name=None, last_name=None):
    staff_roles_requiring_staff_true = [UserRole.ADMIN_OFFICER, UserRole.MANAGER, UserRole.SYSTEM_ADMIN, UserRole.CUSTOMER, UserRole.DOCTOR]
    effective_is_staff = is_staff if is_staff is not None else (role in staff_roles_requiring_staff_true)
    user_data = {
        'username': username, 'email': f'{username}@example.com', 'role': role,
        'is_staff': effective_is_staff, 'is_superuser': is_superuser,
        'first_name': first_name or username.capitalize(), 'last_name': last_name or 'User'
    }
    if is_superuser:
        user_data['role'] = role if role else UserRole.SYSTEM_ADMIN
        create_kwargs = {k:v for k,v in user_data.items() if k not in ['username', 'email', 'password']}
        return User.objects.create_superuser(username=username, email=user_data['email'], password=password, **create_kwargs)
    else:
        create_kwargs = {k:v for k,v in user_data.items() if k != 'password'}
        user = User.objects.create_user(**create_kwargs)
        user.set_password(password)
        user.save()
        return user

def create_doctor_profile_for_test(user, specialization="General Dentistry"):
    doctor_obj, created = Doctor.objects.get_or_create(user=user, defaults={'specialization': specialization})
    return doctor_obj

def create_clinic_for_test(name="Test Clinic"):
    clinic_obj, created = Clinic.objects.get_or_create(name=name, defaults={
        'location': "Test Location", 'address': "123 Test St", 'phone': "555-0101"
    })
    return clinic_obj

def create_room_for_test(clinic, number="101", room_type=RoomType.NORMAL):
    room_obj, created = Room.objects.get_or_create(clinic=clinic, number=number, defaults={'type': room_type})
    return room_obj

def create_service_for_test(name="Consultation", service_type=ServiceType.PREVENTIVE_CARE, duration=30):
    service_obj, created = Service.objects.get_or_create(name=name, defaults={
        'type': service_type, 'description': f"{name} service", 'duration_minutes': duration
    })
    return service_obj

def create_price_for_test(service, shift, amount=100.00):
    price_obj, created = Price.objects.get_or_create(service=service, shift=shift, defaults={'amount': amount})
    return price_obj

def create_roster_for_test(doctor, clinic, roster_date, shift):
    current_date = roster_date
    while current_date.weekday() == 4:
        current_date += timedelta(days=1)
    roster, created = Roster.objects.get_or_create(
        doctor=doctor, date=current_date, shift=shift, defaults={'clinic': clinic}
    )
    if not created and roster.clinic != clinic:
        roster.clinic = clinic
        roster.save()
    return roster

def get_valid_appointment_date_for_test():
    d = timezone.now().date() + timedelta(days=1)
    while d.weekday() == 4:
        d += timedelta(days=1)
    return d


# --- Validator Tests ---
class ValidatorTests(TestCase):
    def test_is_friday(self):
        today = date.today()
        days_until_friday = (4 - today.weekday() + 7) % 7
        friday = today + timedelta(days=days_until_friday)
        saturday = friday + timedelta(days=1)
        self.assertTrue(validators.is_friday(friday))
        self.assertFalse(validators.is_friday(saturday))

    def test_is_surgery_room_in_evening(self):
        self.assertTrue(validators.is_surgery_room_in_evening(RoomType.SURGERY, ShiftType.EVENING))
        self.assertFalse(validators.is_surgery_room_in_evening(RoomType.SURGERY, ShiftType.MORNING))
        self.assertFalse(validators.is_surgery_room_in_evening(RoomType.NORMAL, ShiftType.EVENING))

    def test_validate_not_friday(self):
        today = date.today()
        days_until_friday = (4 - today.weekday() + 7) % 7
        friday = today + timedelta(days=days_until_friday)
        saturday = friday + timedelta(days=1)
        with self.assertRaises(ValidationError):
            validators.validate_not_friday(friday)
        try:
            validators.validate_not_friday(saturday)
        except ValidationError:
            self.fail("validate_not_friday raised ValidationError unexpectedly for a Saturday")

    def test_validate_surgery_room_not_in_evening(self):
        with self.assertRaises(ValidationError):
            validators.validate_surgery_room_not_in_evening(RoomType.SURGERY, ShiftType.EVENING)
        try:
            validators.validate_surgery_room_not_in_evening(RoomType.SURGERY, ShiftType.MORNING)
            validators.validate_surgery_room_not_in_evening(RoomType.NORMAL, ShiftType.EVENING)
        except ValidationError:
            self.fail("validate_surgery_room_not_in_evening raised ValidationError unexpectedly")

    def test_check_clinic_shift_capacity(self):
        clinic = create_clinic_for_test("Capacity Clinic")
        valid_date = get_valid_appointment_date_for_test()
        doctor_user = create_user_for_test("testdoc_cap", UserRole.DOCTOR)
        doctor = create_doctor_profile_for_test(doctor_user)
        room = create_room_for_test(clinic, "CapRoom")
        service = create_service_for_test("CapService")
        create_price_for_test(service, ShiftType.MORNING)
        create_roster_for_test(doctor, clinic, valid_date, ShiftType.MORNING)
        for i in range(MAX_PATIENTS_PER_SHIFT):
            customer = create_user_for_test(f"cust_cap_{i}", UserRole.CUSTOMER)
            Appointment.objects.create(
                customer=customer, doctor=doctor, clinic=clinic, room=room, service=service,
                date=valid_date, shift=ShiftType.MORNING, status='CONFIRMED'
            )
        with self.assertRaisesRegex(ValidationError, "This clinic has reached its capacity"):
            validators.check_clinic_shift_capacity(clinic, valid_date, ShiftType.MORNING)
        try:
            validators.check_clinic_shift_capacity(clinic, valid_date, ShiftType.AFTERNOON)
        except ValidationError:
            self.fail("check_clinic_shift_capacity raised ValidationError for an empty shift.")


# --- Model Tests ---
class ModelTestCase(TestCase):
    def setUp(self):
        self.admin_user = create_user_for_test('admin_model', UserRole.SYSTEM_ADMIN, is_superuser=True, first_name="Admin", last_name="Model")
        self.manager_user = create_user_for_test('manager_model', UserRole.MANAGER, first_name="Manager", last_name="Model")
        self.doctor_user = create_user_for_test('doctor_model', UserRole.DOCTOR, first_name="Doctor", last_name="Model")
        self.customer_user = create_user_for_test('customer_model', UserRole.CUSTOMER, first_name="Customer", last_name="Model")

        self.clinic = create_clinic_for_test('Test Clinic Model')
        self.normal_room = create_room_for_test(self.clinic, 'N101M', RoomType.NORMAL)
        self.surgery_room = create_room_for_test(self.clinic, 'S101M', RoomType.SURGERY)
        self.doctor = create_doctor_profile_for_test(self.doctor_user, 'Model Dentistry')
        self.service = create_service_for_test('Model Cleaning', ServiceType.PREVENTIVE_CARE)

        self.morning_price = create_price_for_test(self.service, ShiftType.MORNING, 150.00)
        self.afternoon_price = create_price_for_test(self.service, ShiftType.AFTERNOON, 125.00)
        self.evening_price = create_price_for_test(self.service, ShiftType.EVENING, 100.00)

        self.today_model = get_valid_appointment_date_for_test()
        self.roster = create_roster_for_test(self.doctor, self.clinic, self.today_model, ShiftType.MORNING)

    def test_user_str(self):
        self.assertEqual(str(self.customer_user), "customer_model (Customer)")
        self.assertEqual(str(self.doctor_user), "doctor_model (Doctor)")

    def test_clinic_model(self):
        self.assertEqual(str(self.clinic), 'Test Clinic Model')
        self.assertTrue(self.clinic.is_active)

    def test_room_model(self):
        self.assertEqual(str(self.normal_room), f"N101M (Normal Room) at {self.clinic.name}")
        self.assertTrue(self.normal_room.is_active)
        self.assertTrue(self.normal_room.is_available(self.today_model, ShiftType.MORNING))
        self.assertTrue(self.normal_room.is_available(self.today_model, ShiftType.EVENING))
        self.assertFalse(self.surgery_room.is_available(self.today_model, ShiftType.EVENING))
        self.assertTrue(self.surgery_room.is_available(self.today_model, ShiftType.MORNING))

    def test_doctor_model(self):
        expected_str = f"Dr. Doctor Model (Model Dentistry)"
        self.assertEqual(str(self.doctor), expected_str)
        available_shifts = self.doctor.get_availability(self.today_model)
        self.assertCountEqual(available_shifts, [ShiftType.MORNING])

    def test_service_model(self):
        self.assertEqual(str(self.service), "Model Cleaning (Preventive Care)")
        self.assertTrue(self.service.is_active)
        self.assertEqual(self.service.get_price(ShiftType.MORNING), 150.00)
        self.assertEqual(self.service.get_price(ShiftType.AFTERNOON), 125.00)
        self.assertEqual(self.service.get_price(ShiftType.EVENING), 100.00)

    def test_appointment_model(self):
        appointment = Appointment.objects.create(
            customer=self.customer_user, doctor=self.doctor, clinic=self.clinic,
            room=self.normal_room, service=self.service, date=self.today_model,
            shift=ShiftType.MORNING
        )
        self.assertIsNotNone(appointment.reference)
        self.assertEqual(len(appointment.reference), 10)
        self.assertEqual(appointment.price, 150.00)
        self.assertEqual(appointment.status, 'CONFIRMED')
        self.assertTrue(appointment.cancel())
        self.assertEqual(appointment.status, 'CANCELLED')
        receipt = appointment.generate_receipt()
        self.assertIn(appointment.reference, receipt)
        self.assertIn(self.customer_user.get_full_name(), receipt)
        self.assertIn(str(self.doctor), receipt)
        self.assertIn(self.clinic.name, receipt)
        self.assertIn(self.normal_room.number, receipt)
        self.assertIn(self.service.name, receipt)
        self.assertIn("Cancelled", receipt)

    def test_roster_friday_validation(self):
        friday = self.today_model
        while friday.weekday() != 4:
            friday += timedelta(days=1)
        with self.assertRaisesRegex(ValidationError, "No service is available on Fridays."):
            Roster(doctor=self.doctor, clinic=self.clinic, date=friday, shift=ShiftType.MORNING).clean()

    def test_roster_doctor_capacity_validation(self):
        shift_for_capacity_test = ShiftType.AFTERNOON
        capacity_test_clinic = create_clinic_for_test("Roster Capacity Clinic")
        for i in range(MAX_DOCTORS_PER_CLINIC_SHIFT):
            doc_user = create_user_for_test(f"doc_cap_m_{i}", UserRole.DOCTOR)
            doc_profile = create_doctor_profile_for_test(doc_user, f"Spec_m_{i}")
            create_roster_for_test(doc_profile, capacity_test_clinic, self.today_model, shift_for_capacity_test)
        another_doc_user = create_user_for_test("another_doc_cap_m", UserRole.DOCTOR)
        another_doc_profile = create_doctor_profile_for_test(another_doc_user, "ExtraSpec_m")
        with self.assertRaisesRegex(ValidationError, f"{capacity_test_clinic.name}.*has reached its maximum capacity"):
            Roster(doctor=another_doc_profile, clinic=capacity_test_clinic, date=self.today_model, shift=shift_for_capacity_test).clean()

    def test_appointment_friday_validation(self):
        friday = self.today_model
        while friday.weekday() != 4:
            friday += timedelta(days=1)
        with self.assertRaisesRegex(ValidationError, "No service is available on Fridays."):
            Appointment(
                customer=self.customer_user, doctor=self.doctor, clinic=self.clinic, room=self.normal_room,
                service=self.service, date=friday, shift=ShiftType.MORNING
            ).clean()

    def test_appointment_surgery_evening_validation(self):
        create_roster_for_test(self.doctor, self.clinic, self.today_model, ShiftType.EVENING)
        with self.assertRaisesRegex(ValidationError, "Surgery rooms are not available during evening shifts."):
            Appointment(
                customer=self.customer_user, doctor=self.doctor, clinic=self.clinic, room=self.surgery_room,
                service=self.service, date=self.today_model, shift=ShiftType.EVENING
            ).clean()

    def test_appointment_doctor_not_on_roster_validation(self):
        other_doctor_user = create_user_for_test("otherdoc_model", UserRole.DOCTOR)
        other_doctor = create_doctor_profile_for_test(other_doctor_user, "Cardiology")
        expected_error_message = "This doctor is not scheduled at this clinic for the selected date and shift."
        with self.assertRaises(ValidationError) as cm:
            Appointment(
                customer=self.customer_user, doctor=other_doctor, clinic=self.clinic, room=self.normal_room,
                service=self.service, date=self.today_model, shift=ShiftType.MORNING
            ).clean()
        self.assertIn('doctor', cm.exception.message_dict) 
        self.assertIn(expected_error_message, cm.exception.message_dict['doctor'])


    def test_appointment_room_availability_validation(self):
        Appointment.objects.create(
            customer=self.customer_user, doctor=self.doctor, clinic=self.clinic, room=self.normal_room,
            service=self.service, date=self.today_model, shift=ShiftType.MORNING, status='CONFIRMED'
        )
        new_appointment_to_clean = Appointment(
            customer=create_user_for_test("another_cust_room_m", UserRole.CUSTOMER),
            doctor=self.doctor, clinic=self.clinic, room=self.normal_room,
            service=self.service, date=self.today_model, shift=ShiftType.MORNING, status='CONFIRMED'
        )
        expected_error_message_part = f"Room {self.normal_room} is already booked and confirmed"
        with self.assertRaises(ValidationError) as cm:
            new_appointment_to_clean.clean()
        self.assertIn('room', cm.exception.message_dict)
        self.assertIn(expected_error_message_part, cm.exception.message_dict['room'][0])


# --- API Tests ---
class MyGeneralAPITestCase(DRF_APITestCase): # Renamed for clarity
    def setUp(self):
        print("--- Running MyGeneralAPITestCase.setUp ---") # DEBUG PRINT
        self.admin_user = create_user_for_test('admin_api_gen', UserRole.SYSTEM_ADMIN, is_superuser=True)
        self.manager_user = create_user_for_test('manager_api_gen', UserRole.MANAGER)
        self.officer_user = create_user_for_test('officer_api_gen', UserRole.ADMIN_OFFICER)
        self.doctor_user = create_user_for_test('doctor_api_gen', UserRole.DOCTOR)
        self.customer_user = create_user_for_test('customer_api_gen', UserRole.CUSTOMER)
        
        self.clinic = create_clinic_for_test('API Test Clinic Gen')
        self.normal_room = create_room_for_test(self.clinic, 'GEN101N', RoomType.NORMAL)
        self.surgery_room = create_room_for_test(self.clinic, 'GEN101S', RoomType.SURGERY)
        self.doctor = create_doctor_profile_for_test(self.doctor_user, 'API Gen Dentistry')
        self.service = create_service_for_test('API Gen Cleaning', ServiceType.PREVENTIVE_CARE)
        self.price = create_price_for_test(self.service, ShiftType.MORNING, 150.00)
        
        self.today_api = get_valid_appointment_date_for_test()
        self.roster = create_roster_for_test(self.doctor, self.clinic, self.today_api, ShiftType.MORNING)
        
        self.client = APIClient()

    def test_clinic_list_api_unauthenticated(self):
        print("--- Running MyGeneralAPITestCase.test_clinic_list_api_unauthenticated ---") # DEBUG
        response = self.client.get(reverse('clinic-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_clinic_list_api_customer(self):
        print("--- Running MyGeneralAPITestCase.test_clinic_list_api_customer ---") # DEBUG
        self.client.force_authenticate(user=self.customer_user) 
        response = self.client.get(reverse('clinic-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 1)
        if response.data['results']: 
            self.assertEqual(response.data['results'][0]['name'], 'API Test Clinic Gen')

    def test_create_clinic_customer_permission_denied(self):
        print("--- Running MyGeneralAPITestCase.test_create_clinic_customer_permission_denied ---") # DEBUG
        self.client.force_authenticate(user=self.customer_user) 
        data = {"name": "New Clinic by Cust", "location": "CustLoc", "address": "CustAddr", "phone": "111"}
        response = self.client.post(reverse('clinic-list'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_clinic_manager_success(self):
        print("--- Running MyGeneralAPITestCase.test_create_clinic_manager_success ---") # DEBUG
        self.client.force_authenticate(user=self.manager_user)
        data = {"name": "New Clinic by Mgr Gen", "location": "MgrLoc", "address": "MgrAddr", "phone": "222"}
        response = self.client.post(reverse('clinic-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Clinic.objects.filter(name="New Clinic by Mgr Gen").exists())

    def test_doctor_availability_api(self):
        print("--- Running MyGeneralAPITestCase.test_doctor_availability_api ---") # DEBUG
        self.client.force_authenticate(user=self.customer_user) 
        url = reverse('doctor-availability', args=[self.doctor.id]) 
        response = self.client.get(url, {'date': self.today_api.strftime('%Y-%m-%d')}) 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(response.data['available_shifts'], [ShiftType.MORNING])

    def test_appointment_booking_api_customer(self):
        print("--- Running MyGeneralAPITestCase.test_appointment_booking_api_customer ---") # DEBUG
        self.client.force_authenticate(user=self.customer_user) 
        url_check = reverse('appointment-check-availability')
        check_params = {
            'clinic': self.clinic.id, 'date': self.today_api.strftime('%Y-%m-%d'),
            'service': self.service.id, 'shift': ShiftType.MORNING
        }
        response_check = self.client.get(url_check, check_params)
        self.assertEqual(response_check.status_code, status.HTTP_200_OK, response_check.data)
        
        book_data = {
            'doctor': self.doctor.id, 'clinic': self.clinic.id, 'room': self.normal_room.id, 
            'service': self.service.id, 'date': self.today_api.strftime('%Y-%m-%d'), 'shift': ShiftType.MORNING
        }
        response_book = self.client.post(reverse('appointment-list'), book_data, format='json')
        self.assertEqual(response_book.status_code, status.HTTP_201_CREATED, response_book.data)
        self.assertEqual(float(response_book.data['price']), 150.00)
        self.assertEqual(response_book.data['status'], 'CONFIRMED')
        self.assertEqual(response_book.data['customer'], self.customer_user.id)

        response_fail = self.client.post(reverse('appointment-list'), book_data, format='json')
        self.assertEqual(response_fail.status_code, status.HTTP_400_BAD_REQUEST, response_fail.data)
        error_str = str(response_fail.data).lower()
        self.assertIn("this room", error_str)
        self.assertIn("is not available", error_str)
        self.assertIn("already booked and confirmed", error_str)

    def test_appointment_booking_api_officer(self):
        print("--- Running MyGeneralAPITestCase.test_appointment_booking_api_officer ---") # DEBUG
        other_customer = create_user_for_test("other_cust_api_gen", UserRole.CUSTOMER)
        self.client.force_authenticate(user=self.officer_user) 
        book_data = {
            'customer': other_customer.id, 
            'doctor': self.doctor.id, 'clinic': self.clinic.id, 'room': self.normal_room.id, 
            'service': self.service.id, 'date': self.today_api.strftime('%Y-%m-%d'), 'shift': ShiftType.MORNING
        }
        response_book = self.client.post(reverse('appointment-list'), book_data, format='json')
        self.assertEqual(response_book.status_code, status.HTTP_201_CREATED, response_book.data)
        self.assertEqual(response_book.data['customer'], other_customer.id)

    def test_appointment_cancel_api_customer_own(self):
        print("--- Running MyGeneralAPITestCase.test_appointment_cancel_api_customer_own ---") # DEBUG
        self.client.force_authenticate(user=self.customer_user) 
        appointment = Appointment.objects.create(
            customer=self.customer_user, doctor=self.doctor, clinic=self.clinic, 
            room=self.normal_room, service=self.service, date=self.today_api,
            shift=ShiftType.MORNING
        )
        url = reverse('appointment-cancel', args=[appointment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['appointment']['status'], 'CANCELLED')

    def test_surgery_room_evening_restriction_api(self):
        print("--- Running MyGeneralAPITestCase.test_surgery_room_evening_restriction_api ---") # DEBUG
        create_roster_for_test(self.doctor, self.clinic, self.today_api, ShiftType.EVENING) 
        self.client.force_authenticate(user=self.customer_user) 
        book_data = {
            'doctor': self.doctor.id, 'clinic': self.clinic.id, 'room': self.surgery_room.id, 
            'service': self.service.id, 'date': self.today_api.strftime('%Y-%m-%d'), 'shift': ShiftType.EVENING
        }
        response = self.client.post(reverse('appointment-list'), book_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
        error_message = str(response.data).lower()
        self.assertIn('surgery rooms are not available during evening shifts', error_message)

    def test_list_appointments_customer_own(self):
        print("--- Running MyGeneralAPITestCase.test_list_appointments_customer_own ---") # DEBUG
        self.client.force_authenticate(user=self.customer_user) 
        Appointment.objects.create(
            customer=self.customer_user, doctor=self.doctor, clinic=self.clinic, room=self.normal_room, 
            service=self.service, date=self.today_api, shift=ShiftType.MORNING
        )
        customer2 = create_user_for_test("api_customer2_gen", UserRole.CUSTOMER)
        another_room = create_room_for_test(self.clinic, "API_OTHER_ROOM_GEN")
        Appointment.objects.create(
            customer=customer2, doctor=self.doctor, clinic=self.clinic, room=another_room,
            service=self.service, date=self.today_api, shift=ShiftType.MORNING
        )
        response = self.client.get(reverse('appointment-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['customer'], self.customer_user.id)

    def test_list_appointments_manager_all(self):
        print("--- Running MyGeneralAPITestCase.test_list_appointments_manager_all ---") # DEBUG
        Appointment.objects.create(customer=self.customer_user, doctor=self.doctor, clinic=self.clinic, room=self.normal_room, service=self.service, date=self.today_api, shift=ShiftType.MORNING) 
        customer2 = create_user_for_test("api_customer3_gen", UserRole.CUSTOMER)
        Appointment.objects.create(customer=customer2, doctor=self.doctor, clinic=self.clinic, room=create_room_for_test(self.clinic, "MGR02_GEN"), service=self.service, date=self.today_api, shift=ShiftType.MORNING)
        self.client.force_authenticate(user=self.manager_user) 
        response = self.client.get(reverse('appointment-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) >= 2)

    def test_update_appointment_status_manager(self):
        print("--- Running MyGeneralAPITestCase.test_update_appointment_status_manager ---") # DEBUG
        appointment = Appointment.objects.create(
            customer=self.customer_user, doctor=self.doctor, clinic=self.clinic, 
            room=self.normal_room, service=self.service, date=self.today_api,
            shift=ShiftType.MORNING
        )
        self.client.force_authenticate(user=self.manager_user) 
        url_detail = reverse('appointment-detail', kwargs={'pk': appointment.id})
        update_data = {"status": "COMPLETED"}
        response = self.client.patch(url_detail, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['status'], 'COMPLETED')
# --- END OF MyGeneralAPITestCase CLASS ---


# --- Report API Tests ---
class MyReportSpecificAPITests(DRF_APITestCase): # Renamed and inherits from DRF_APITestCase
    def setUp(self):
        print("--- Running MyReportSpecificAPITests.setUp ---") # DEBUG PRINT
        self.report_manager_user = create_user_for_test('report_mgr_api_spec', UserRole.MANAGER)
        self.report_officer_user = create_user_for_test('report_officer_api_spec', UserRole.ADMIN_OFFICER)
        self.test_customer_for_reports = create_user_for_test('report_cust_api_spec', UserRole.CUSTOMER)

        self.clinic_for_reports = create_clinic_for_test('Report Clinic Specific')
        doctor_user_for_reports = create_user_for_test('report_doc_api_spec', UserRole.DOCTOR)
        self.doctor_for_reports = create_doctor_profile_for_test(doctor_user_for_reports, 'Reporting Doc Spec')
        self.room_for_reports = create_room_for_test(self.clinic_for_reports, 'RPT101_SPEC')
        self.service_for_reports = create_service_for_test('Report Test Service Spec')
        
        self.report_valid_date_start = get_valid_appointment_date_for_test()
        
        create_price_for_test(self.service_for_reports, ShiftType.MORNING, 100.00)
        create_price_for_test(self.service_for_reports, ShiftType.AFTERNOON, 120.00)

        create_roster_for_test(self.doctor_for_reports, self.clinic_for_reports, self.report_valid_date_start, ShiftType.MORNING)
        
        self.report_valid_date_next = self.report_valid_date_start + timedelta(days=1)
        while self.report_valid_date_next.weekday() == 4: self.report_valid_date_next += timedelta(days=1)
        create_roster_for_test(self.doctor_for_reports, self.clinic_for_reports, self.report_valid_date_next, ShiftType.AFTERNOON)

        self.appointment1 = Appointment.objects.create(
            customer=self.test_customer_for_reports, doctor=self.doctor_for_reports, 
            clinic=self.clinic_for_reports, room=self.room_for_reports,
            service=self.service_for_reports, date=self.report_valid_date_start, 
            shift=ShiftType.MORNING, status='COMPLETED'
        )
        self.appointment2 = Appointment.objects.create(
            customer=self.test_customer_for_reports, doctor=self.doctor_for_reports, 
            clinic=self.clinic_for_reports, room=self.room_for_reports, 
            service=self.service_for_reports, date=self.report_valid_date_next, 
            shift=ShiftType.AFTERNOON, status='CONFIRMED'
        )
        self.client = APIClient()

    def test_create_revenue_report_manager(self):
        print("--- Running MyReportSpecificAPITests.test_create_revenue_report_manager ---") # DEBUG
        self.client.force_authenticate(user=self.report_manager_user)
        data = {
            "report_type": "REVENUE",
            "date_range_start": self.report_valid_date_start.strftime('%Y-%m-%d'),
            "date_range_end": (self.report_valid_date_start + timedelta(days=2)).strftime('%Y-%m-%d'),
            "clinic": self.clinic_for_reports.id
        }
        response = self.client.post(reverse('report-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['report_type'], 'REVENUE')
        self.assertIn('total_revenue', response.data['data'])
        self.assertEqual(float(response.data['data']['total_revenue']), 100.00 + 120.00)

    def test_create_appointment_utilization_report_officer(self):
        print("--- Running MyReportSpecificAPITests.test_create_appointment_utilization_report_officer ---") # DEBUG
        self.client.force_authenticate(user=self.report_officer_user)
        data = {
            "report_type": "APPOINTMENT_UTILIZATION",
            "date_range_start": self.report_valid_date_start.strftime('%Y-%m-%d'),
            "date_range_end": (self.report_valid_date_start + timedelta(days=2)).strftime('%Y-%m-%d'),
        }
        response = self.client.post(reverse('report-list'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn('total_appointments', response.data['data'])
        self.assertEqual(response.data['data']['total_appointments'], 2)
        self.assertEqual(response.data['data']['completed_appointments'], 1)
        self.assertEqual(response.data['data']['confirmed_appointments'], 1)

    def test_ad_hoc_revenue_report_manager(self):
        print("--- Running MyReportSpecificAPITests.test_ad_hoc_revenue_report_manager ---") # DEBUG
        self.client.force_authenticate(user=self.report_manager_user)
        url = reverse('report-revenue')
        params = {
            "start_date": self.report_valid_date_start.strftime('%Y-%m-%d'),
            "end_date": (self.report_valid_date_start + timedelta(days=2)).strftime('%Y-%m-%d'),
        }
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(float(response.data['total_revenue']), 100.00 + 120.00)

# --- END OF MyReportSpecificAPITests CLASS ---