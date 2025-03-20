from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import datetime

from ..models import Clinic, Room, ShiftType
from ..serializers import ClinicSerializer, RoomSerializer

class IsAdminOrManagerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins and managers to edit objects.
    Others can only read.
    """
    def has_permission(self, request, view):
        # Allow read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admins and managers
        return request.user.is_authenticated and request.user.role in ['MANAGER', 'SYSTEM_ADMIN']

class ClinicViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Clinics.
    """
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    @action(detail=True, methods=['get'])
    def rooms(self, request, pk=None):
        """
        Get all rooms for a specific clinic
        """
        clinic = self.get_object()
        rooms = Room.objects.filter(clinic=clinic)
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def available_rooms(self, request, pk=None):
        """
        Get available rooms for a specific clinic on a specific date and shift
        """
        clinic = self.get_object()
        date_str = request.query_params.get('date', None)
        shift = request.query_params.get('shift', None)
        
        if not date_str or not shift:
            return Response(
                {"error": "Please provide date and shift parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if shift not in [choice[0] for choice in ShiftType.choices]:
            return Response(
                {"error": f"Invalid shift. Choose from {[choice[0] for choice in ShiftType.choices]}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        available_rooms = clinic.get_available_rooms(date, shift)
        serializer = RoomSerializer(available_rooms, many=True)
        return Response(serializer.data)

class RoomViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Rooms.
    """
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Check if a room is available on a specific date and shift
        """
        room = self.get_object()
        date_str = request.query_params.get('date', None)
        shift = request.query_params.get('shift', None)
        
        if not date_str or not shift:
            return Response(
                {"error": "Please provide date and shift parameters"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if shift not in [choice[0] for choice in ShiftType.choices]:
            return Response(
                {"error": f"Invalid shift. Choose from {[choice[0] for choice in ShiftType.choices]}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        is_available = room.is_available(date, shift)
        
        # Also check if it's a surgery room in the evening shift
        if room.type == 'SURGERY' and shift == 'EVENING':
            is_available = False
            message = "Surgery rooms are not available during evening shifts."
        else:
            message = "Room is available" if is_available else "Room is already booked"
            
        return Response({
            "is_available": is_available,
            "message": message
        }) 