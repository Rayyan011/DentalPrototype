from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Sum, Q

from ..models import Appointment, Service, Doctor, Room, Clinic, ShiftType
from ..serializers import AppointmentSerializer

class IsCustomerOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow customers to view and edit their own appointments,
    and admins/managers to view and edit any appointment.
    """
    def has_permission(self, request, view):
        # Anyone authenticated can create a new appointment
        if request.method == 'POST':
            return request.user.is_authenticated and request.user.role == 'CUSTOMER'
            
        # Only admins, managers, or admin officers can list all appointments
        if request.method == 'GET' and view.action == 'list':
            return request.user.is_authenticated and request.user.role in ['MANAGER', 'SYSTEM_ADMIN', 'ADMIN_OFFICER', 'DOCTOR']
            
        # For other requests, check in has_object_permission
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Doctors can view their own appointments
        if request.user.role == 'DOCTOR' and hasattr(request.user, 'doctor'):
            if obj.doctor.user == request.user:
                return True
                
        # Customers can only view and cancel their own appointments
        if request.user.role == 'CUSTOMER':
            if obj.customer == request.user:
                # Customers can only cancel appointments, not update them
                if request.method in ['GET', 'DELETE'] or (request.method == 'PATCH' and view.action == 'cancel'):
                    return True
            return False
            
        # Admin, manager, or admin officer can do anything
        return request.user.role in ['MANAGER', 'SYSTEM_ADMIN', 'ADMIN_OFFICER']

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Appointments.
    """
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsCustomerOwnerOrAdmin]

    def get_queryset(self):
        """
        Optionally restricts the returned appointments by filtering
        based on query parameters in the URL and user role.
        """
        queryset = Appointment.objects.all()
        
        # Filter by user role
        if self.request.user.role == 'CUSTOMER':
            queryset = queryset.filter(customer=self.request.user)
        elif self.request.user.role == 'DOCTOR' and hasattr(self.request.user, 'doctor'):
            queryset = queryset.filter(doctor=self.request.user.doctor)
            
        # Apply additional filters
        date_str = self.request.query_params.get('date', None)
        clinic_id = self.request.query_params.get('clinic', None)
        doctor_id = self.request.query_params.get('doctor', None)
        status = self.request.query_params.get('status', None)
        shift = self.request.query_params.get('shift', None)
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                queryset = queryset.filter(date=date)
            except ValueError:
                pass  # If date format is invalid, ignore the filter
                
        if clinic_id:
            queryset = queryset.filter(clinic_id=clinic_id)
            
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
            
        if status:
            queryset = queryset.filter(status=status)
            
        if shift and shift in [choice[0] for choice in ShiftType.choices]:
            queryset = queryset.filter(shift=shift)
            
        return queryset

    def perform_create(self, serializer):
        """
        Set the customer as the current user when creating an appointment
        and calculate the price based on service and shift.
        """
        service = serializer.validated_data.get('service')
        shift = serializer.validated_data.get('shift')
        
        # Calculate price based on service and shift
        price = service.get_price(shift)
        
        # Save with the calculated price and current user as customer
        with transaction.atomic():
            serializer.save(customer=self.request.user, price=price)

    @action(detail=True, methods=['post', 'patch'])
    def cancel(self, request, pk=None):
        """
        Cancel an appointment
        """
        appointment = self.get_object()
        
        if appointment.status != 'CONFIRMED':
            return Response(
                {"error": f"Cannot cancel appointment with status {appointment.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        success = appointment.cancel()
        
        if success:
            return Response({
                "message": "Appointment cancelled successfully",
                "appointment": AppointmentSerializer(appointment).data
            })
        else:
            return Response(
                {"error": "Failed to cancel appointment"},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        """
        Check availability for booking based on clinic, date, service, and shift
        """
        clinic_id = request.query_params.get('clinic', None)
        date_str = request.query_params.get('date', None)
        service_id = request.query_params.get('service', None)
        shift = request.query_params.get('shift', None)
        
        # Validate parameters
        if not clinic_id or not date_str or not service_id or not shift:
            return Response(
                {"error": "Please provide clinic, date, service, and shift parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if date is not Friday
        if date.weekday() == 4:  # 4 corresponds to Friday
            return Response(
                {"error": "No service is available on Fridays"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if shift not in [choice[0] for choice in ShiftType.choices]:
            return Response(
                {"error": f"Invalid shift. Choose from {[choice[0] for choice in ShiftType.choices]}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            clinic = Clinic.objects.get(id=clinic_id)
            service = Service.objects.get(id=service_id)
        except (Clinic.DoesNotExist, Service.DoesNotExist):
            return Response(
                {"error": "Invalid clinic or service ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get available rooms in the clinic
        available_rooms = clinic.get_available_rooms(date, shift)
        
        # Find doctors on roster for this clinic, date, and shift
        available_doctors = Doctor.objects.filter(
            roster__clinic=clinic,
            roster__date=date,
            roster__shift=shift,
            roster__is_active=True
        )
        
        # Check if any doctors are already booked for this shift
        booked_doctors = Doctor.objects.filter(
            appointments__clinic=clinic,
            appointments__date=date,
            appointments__shift=shift,
            appointments__status='CONFIRMED'
        )
        
        # Remove booked doctors from available doctors
        available_doctors = available_doctors.exclude(id__in=booked_doctors.values_list('id', flat=True))
        
        price = service.get_price(shift)
        
        return Response({
            "clinic": {
                "id": clinic.id,
                "name": clinic.name
            },
            "date": date_str,
            "shift": shift,
            "service": {
                "id": service.id,
                "name": service.name
            },
            "price": price,
            "available_rooms": [
                {
                    "id": room.id,
                    "number": room.number,
                    "type": room.type
                } for room in available_rooms
            ],
            "available_doctors": [
                {
                    "id": doctor.id,
                    "name": str(doctor)
                } for doctor in available_doctors
            ]
        }) 