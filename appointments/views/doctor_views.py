from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime

from ..models import Doctor, Roster, UserRole, ShiftType
from ..serializers import DoctorSerializer, RosterSerializer
from .clinic_views import IsAdminOrManagerOrReadOnly

class IsDoctorOrAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow doctors to edit their own data,
    and admins to edit any doctor data.
    """
    def has_permission(self, request, view):
        # Allow read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the doctor themselves or admin/manager
        return request.user.is_authenticated and (
            request.user.role in ['MANAGER', 'SYSTEM_ADMIN', 'ADMIN_OFFICER'] or 
            (request.user.role == 'DOCTOR' and hasattr(request.user, 'doctor'))
        )

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the doctor themselves or admin/manager
        return (
            request.user.role in ['MANAGER', 'SYSTEM_ADMIN', 'ADMIN_OFFICER'] or
            (request.user.role == 'DOCTOR' and hasattr(request.user, 'doctor') and request.user.doctor == obj)
        )

class DoctorViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Doctors.
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsDoctorOrAdminOrReadOnly]

    @action(detail=True, methods=['get'])
    def roster(self, request, pk=None):
        """
        Get roster for a specific doctor
        """
        doctor = self.get_object()
        date_str = request.query_params.get('date', None)
        
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                rosters = Roster.objects.filter(doctor=doctor, date=date, is_active=True)
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            rosters = Roster.objects.filter(doctor=doctor, is_active=True)
            
        serializer = RosterSerializer(rosters, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Get availability for a specific doctor on a specific date
        """
        doctor = self.get_object()
        date_str = request.query_params.get('date', None)
        
        if not date_str:
            return Response(
                {"error": "Please provide date parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        available_shifts = doctor.get_availability(date)
        
        return Response({
            "doctor": str(doctor),
            "date": date_str,
            "available_shifts": available_shifts
        })

class IsAdminOrManager(permissions.BasePermission):
    """
    Custom permission to only allow admins and managers to manage rosters.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['MANAGER', 'SYSTEM_ADMIN', 'ADMIN_OFFICER']

class RosterViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Rosters.
    """
    queryset = Roster.objects.filter(is_active=True)
    serializer_class = RosterSerializer
    permission_classes = [IsAdminOrManager]

    def get_queryset(self):
        """
        Optionally restricts the returned rosters by filtering
        based on query parameters in the URL.
        """
        queryset = Roster.objects.filter(is_active=True)
        
        date_str = self.request.query_params.get('date', None)
        clinic_id = self.request.query_params.get('clinic', None)
        doctor_id = self.request.query_params.get('doctor', None)
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
            
        if shift and shift in [choice[0] for choice in ShiftType.choices]:
            queryset = queryset.filter(shift=shift)
            
        return queryset 