# appointments/views/appointment_views.py
from rest_framework import viewsets, permissions, status, serializers as drf_serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from datetime import datetime
from django.core.exceptions import PermissionDenied

from ..models import Appointment, Service, Doctor, Room, Clinic, ShiftType, UserRole
from ..serializers import (
    AppointmentSerializer,
    ClinicSerializer,
    RoomSerializer,
    DoctorSerializer,
    ServiceSerializer
)

class IsCustomerOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if view.action == 'list':
            return True
        if view.action == 'create':
            return request.user.role in [UserRole.CUSTOMER, UserRole.ADMIN_OFFICER, UserRole.MANAGER]
        return True # Default to True, let has_object_permission handle object-specifics

    def has_object_permission(self, request, view, obj):
        if request.user.role in [UserRole.MANAGER, UserRole.SYSTEM_ADMIN]:
            return True
        if request.user.role == UserRole.ADMIN_OFFICER:
            return True # Officers can manage appointments
        if request.user.role == UserRole.CUSTOMER:
            if obj.customer == request.user:
                if request.method in permissions.SAFE_METHODS: return True # Can view own
                if view.action == 'cancel' and (request.method == 'POST' or request.method == 'PATCH'): return True # Can cancel own
            return False
        if request.user.role == UserRole.DOCTOR and hasattr(request.user, 'doctor'):
            if obj.doctor == request.user.doctor:
                if request.method in permissions.SAFE_METHODS: return True # Can view assigned
                # Doctors can update status of their appointments
                if view.action in ['update', 'partial_update'] and (request.method == 'PUT' or request.method == 'PATCH'): return True
            return False
        return False

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all().order_by('-date', '-created_at')
    serializer_class = AppointmentSerializer
    permission_classes = [IsCustomerOwnerOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated: return queryset.none()
        if user.role == UserRole.CUSTOMER: queryset = queryset.filter(customer=user)
        elif user.role == UserRole.DOCTOR and hasattr(user, 'doctor'): queryset = queryset.filter(doctor=user.doctor)
        
        date_str = self.request.query_params.get('date', None)
        clinic_id = self.request.query_params.get('clinic', None)
        doctor_id = self.request.query_params.get('doctor', None)
        status_param = self.request.query_params.get('status', None)
        shift = self.request.query_params.get('shift', None)
        
        if date_str:
            try: parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date(); queryset = queryset.filter(date=parsed_date)
            except ValueError: pass
        if clinic_id: queryset = queryset.filter(clinic_id=clinic_id)
        if doctor_id: queryset = queryset.filter(doctor_id=doctor_id)
        if status_param: queryset = queryset.filter(status=status_param)
        if shift and shift in ShiftType.values: queryset = queryset.filter(shift=shift)
        return queryset

    def perform_create(self, serializer):
        service = serializer.validated_data.get('service')
        shift = serializer.validated_data.get('shift')
        if not service or not shift: raise drf_serializers.ValidationError("Service and shift are fundamental.")
        price = service.get_price(shift)
        user = self.request.user
        
        with transaction.atomic():
            if user.role == UserRole.CUSTOMER:
                # Serializer validation should ensure customer is not in payload or matches request.user
                serializer.save(customer=user, price=price)
            elif user.role in [UserRole.ADMIN_OFFICER, UserRole.MANAGER]:
                # Serializer validation ensures 'customer' is in validated_data from payload
                if not serializer.validated_data.get('customer'):
                     raise drf_serializers.ValidationError({"customer": "Customer is required for this role."})
                serializer.save(price=price)
            else:
                raise PermissionDenied("This user role cannot create appointments.")

    def perform_update(self, serializer):
        # Recalculate price if service or shift potentially changes
        # Ensure validated_data is used for potentially changed fields, else use instance's current value
        instance = self.get_object()
        service = serializer.validated_data.get('service', instance.service)
        shift = serializer.validated_data.get('shift', instance.shift)
        
        new_price = service.get_price(shift)
        serializer.save(price=new_price)


    @action(detail=True, methods=['post', 'patch'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status != 'CONFIRMED':
            return Response({"error": f"Cannot cancel appointment with status {appointment.get_status_display()}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # has_object_permission in IsCustomerOwnerOrAdmin already verified user can cancel this obj
        success = appointment.cancel()
        
        if success:
            return Response({"message": "Appointment cancelled successfully.", "appointment": self.get_serializer(appointment).data})
        else:
            return Response({"error": "Failed to cancel appointment internally."}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        clinic_id = request.query_params.get('clinic', None)
        date_str = request.query_params.get('date', None)
        service_id = request.query_params.get('service', None)
        shift = request.query_params.get('shift', None)
        if not all([clinic_id, date_str, service_id, shift]):
            return Response({"error": "Clinic, date, service, and shift parameters are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        if parsed_date.weekday() == 4:
            return Response({"error": "No service is available on Fridays."}, status=status.HTTP_400_BAD_REQUEST)
        if shift not in ShiftType.values:
            return Response({"error": f"Invalid shift. Choose from {ShiftType.labels}."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            clinic = Clinic.objects.get(id=clinic_id)
            service = Service.objects.get(id=service_id)
        except (Clinic.DoesNotExist, Service.DoesNotExist):
            return Response({"error": "Invalid clinic or service ID."}, status=status.HTTP_400_BAD_REQUEST)
        available_rooms = clinic.get_available_rooms(parsed_date, shift)
        rostered_doctors = Doctor.objects.filter(
            roster__clinic=clinic, roster__date=parsed_date, roster__shift=shift, roster__is_active=True
        ).distinct()
        price = service.get_price(shift)
        context = {'request': request}
        return Response({
            "clinic": ClinicSerializer(clinic, context=context).data,
            "date": date_str, "shift": shift,
            "service": ServiceSerializer(service, context=context).data,
            "price": price,
            "available_rooms": RoomSerializer(available_rooms, many=True, context=context).data,
            "available_doctors": DoctorSerializer(rostered_doctors, many=True, context=context).data
        })