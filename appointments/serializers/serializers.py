from rest_framework import serializers
from django.contrib.auth import get_user_model
import logging
from ..models import (
    Clinic, Room, Doctor, Service, Price, 
    Roster, Appointment, Report
)
from ..utils.validators import (
    validate_not_friday, 
    validate_surgery_room_not_in_evening,
    check_clinic_shift_capacity
)

logger = logging.getLogger(__name__)
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role']
        read_only_fields = ['id']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = '__all__'

class RoomSerializer(serializers.ModelSerializer):
    clinic_name = serializers.ReadOnlyField(source='clinic.name')
    
    class Meta:
        model = Room
        fields = ['id', 'number', 'type', 'clinic', 'clinic_name', 'is_active']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='DOCTOR'),
        source='user',
        write_only=True
    )
    
    class Meta:
        model = Doctor
        fields = ['id', 'user', 'user_id', 'specialization']

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

class PriceSerializer(serializers.ModelSerializer):
    service_name = serializers.ReadOnlyField(source='service.name')
    
    class Meta:
        model = Price
        fields = ['id', 'service', 'service_name', 'shift', 'amount', 'is_active']

class RosterSerializer(serializers.ModelSerializer):
    doctor_name = serializers.ReadOnlyField(source='doctor.__str__')
    clinic_name = serializers.ReadOnlyField(source='clinic.name')
    
    class Meta:
        model = Roster
        fields = ['id', 'doctor', 'doctor_name', 'clinic', 'clinic_name', 'date', 'shift', 'is_active']
    
    def validate(self, data):
        # Ensure doctor doesn't have another roster at the same time
        existing_roster = Roster.objects.filter(
            doctor=data['doctor'],
            date=data['date'],
            shift=data['shift']
        ).exists()
        
        if existing_roster and not data.get('id'):
            raise serializers.ValidationError(
                "This doctor already has a roster assignment for this date and shift."
            )
        
        # Check Friday validation
        if data['date'].weekday() == 4:  # 4 corresponds to Friday
            raise serializers.ValidationError("No service is available on Fridays.")
            
        return data

class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.__str__')
    doctor_name = serializers.ReadOnlyField(source='doctor.__str__')
    clinic_name = serializers.ReadOnlyField(source='clinic.name')
    room_info = serializers.ReadOnlyField(source='room.__str__')
    service_name = serializers.ReadOnlyField(source='service.name')
    receipt = serializers.SerializerMethodField()
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'reference', 'customer', 'customer_name', 'doctor', 'doctor_name',
            'clinic', 'clinic_name', 'room', 'room_info', 'service', 'service_name',
            'date', 'shift', 'price', 'status', 'receipt', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reference', 'price', 'status', 'created_at', 'updated_at']
    
    def get_receipt(self, obj):
        if obj.status == 'CONFIRMED':
            return obj.generate_receipt()
        return None
    
    def validate(self, data):
        # Friday validation using our utility function
        try:
            validate_not_friday(data['date'])
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        # Surgery room not available in evening using our utility function
        try:
            validate_surgery_room_not_in_evening(data['room'].type, data['shift'])
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        # Check if the clinic has reached the capacity of 10 patients per shift
        try:
            check_clinic_shift_capacity(data['clinic'], data['date'], data['shift'])
        except Exception as e:
            raise serializers.ValidationError(str(e))
        
        # Check if doctor is on roster for this clinic, date and shift
        try:
            roster_exists = Roster.objects.filter(
                doctor=data['doctor'],
                clinic=data['clinic'],
                date=data['date'],
                shift=data['shift'],
                is_active=True
            ).exists()
            
            if not roster_exists:
                raise serializers.ValidationError(
                    "This doctor is not scheduled at this clinic for the selected date and shift."
                )
        except Exception as e:
            logger.error(f"Error checking doctor roster: {e}")
            raise serializers.ValidationError(
                "Error checking doctor roster: please ensure all data is valid."
            )
        
        # Check if room is available
        try:
            room_available = data['room'].is_available(data['date'], data['shift'])
            if not room_available:
                raise serializers.ValidationError(
                    "This room is not available for the selected date and shift."
                )
        except Exception as e:
            logger.error(f"Error checking room availability: {e}")
            raise serializers.ValidationError(
                "Error checking room availability: please ensure all data is valid."
            )
            
        return data

class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    clinic_name = serializers.ReadOnlyField(source='clinic.name', default=None)
    
    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'date_range_start', 'date_range_end',
            'clinic', 'clinic_name', 'created_by', 'created_by_name', 
            'created_at', 'data'
        ]
        read_only_fields = ['created_at', 'data']
    
    def validate(self, data):
        if data['date_range_end'] < data['date_range_start']:
            raise serializers.ValidationError("End date must be after start date.")
        return data 