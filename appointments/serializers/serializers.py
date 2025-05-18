# appointments/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
import logging
from django.db import models  # <--- IMPORTED models
from ..models import (
    Clinic, Room, Doctor, Service, Price,
    Roster, Appointment, Report, UserRole, ShiftType, RoomType, ServiceType
)
from ..utils import validators as app_validators
from django.core.exceptions import ValidationError as DjangoValidationError

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
        role = validated_data.get('role')
        if role and role not in UserRole.values: # Use .values for choices
            raise serializers.ValidationError({"role": f"Invalid role '{role}'. Valid roles are {UserRole.labels}."})
        
        user_obj = User.objects.create_user(**validated_data)
        # create_user hashes password if provided in validated_data.
        # If popped, set it explicitly.
        if password and 'password' not in validated_data: # Check if password was in original validated_data
             user_obj.set_password(password)
             user_obj.save() # Save again if password was set separately
        return user_obj

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
        queryset=User.objects.filter(role=UserRole.DOCTOR),
        source='user', write_only=True, label="User ID (Must have DOCTOR role)"
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
        # To properly call model.clean(), we need a model instance with all its fields.
        # Start with existing instance data if updating, then overlay with new data.
        instance_data = {}
        if self.instance:
            for field in Roster._meta.fields:
                if field.name != 'id' and hasattr(self.instance, field.name): # Exclude 'id'
                    instance_data[field.name] = getattr(self.instance, field.name)
        
        instance_data.update(data) # Overlay/add new data

        # Resolve ForeignKey PKs in instance_data to actual model instances for .clean()
        # This is a simplified version; a more robust one would iterate model fields.
        if 'doctor' in instance_data and not isinstance(instance_data['doctor'], Doctor) and instance_data['doctor'] is not None:
            try: instance_data['doctor'] = Doctor.objects.get(pk=instance_data['doctor'].pk if hasattr(instance_data['doctor'], 'pk') else instance_data['doctor'])
            except Doctor.DoesNotExist: raise serializers.ValidationError({"doctor": "Invalid doctor."})
        if 'clinic' in instance_data and not isinstance(instance_data['clinic'], Clinic) and instance_data['clinic'] is not None:
            try: instance_data['clinic'] = Clinic.objects.get(pk=instance_data['clinic'].pk if hasattr(instance_data['clinic'], 'pk') else instance_data['clinic'])
            except Clinic.DoesNotExist: raise serializers.ValidationError({"clinic": "Invalid clinic."})

        # Ensure all required fields for Roster model are present before creating an instance
        # 'doctor', 'clinic', 'date', 'shift' are mandatory from model definition
        required_model_fields = {f.name for f in Roster._meta.get_fields() if not f.blank and not f.null and not f.is_relation}
        missing_fields = [rf for rf in required_model_fields if rf not in instance_data or instance_data[rf] is None]
        if missing_fields and self.instance is None: # Only enforce for creation here, updates are partial
             raise serializers.ValidationError({mf: "This field is required." for mf in missing_fields})


        # Create a temporary model instance to call its clean method
        # Only pass fields that are actual model fields for Roster
        roster_model_fields = {f.name for f in Roster._meta.fields}
        clean_data = {k: v for k, v in instance_data.items() if k in roster_model_fields}

        # Ensure all required fields (non-nullable, non-blank without defaults) are in clean_data for instance creation
        for f_name in ['doctor', 'clinic', 'date', 'shift']: # Core fields for Roster
            if f_name not in clean_data or clean_data[f_name] is None:
                 if self.instance is None: # If creating, these are essential
                     raise serializers.ValidationError({f_name: "This field is required for Roster validation."})
                 # If updating and not provided, it's fine, clean() will use existing instance value
                 # but instance_data should already have it from self.instance.

        roster_instance = Roster(**clean_data)
        if self.instance and self.instance.pk: # If updating, set the pk for .clean()
            roster_instance.pk = self.instance.pk
        
        try:
            # Exclude 'id' as it's auto-generated and not part of user input fields for validation
            roster_instance.clean_fields(exclude=['id'] if roster_instance.pk else None) 
            roster_instance.clean() # Your custom model-wide validation
        except DjangoValidationError as e:
            # Convert Django's ValidationError to DRF's ValidationError
            raise serializers.ValidationError(serializers.as_serializer_error(e))
        return data


class AppointmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.__str__')
    doctor_name = serializers.ReadOnlyField(source='doctor.__str__')
    clinic_name = serializers.ReadOnlyField(source='clinic.name')
    room_info = serializers.ReadOnlyField(source='room.__str__')
    service_name = serializers.ReadOnlyField(source='service.name')
    receipt = serializers.SerializerMethodField()

    customer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=UserRole.CUSTOMER),
        required=False, allow_null=True
    )
    status = serializers.ChoiceField(choices=Appointment.STATUS_CHOICES, required=False)

    class Meta:
        model = Appointment
        fields = [
            'id', 'reference', 'customer', 'customer_name', 'doctor', 'doctor_name',
            'clinic', 'clinic_name', 'room', 'room_info', 'service', 'service_name',
            'date', 'shift', 'price', 'status', 'receipt', 'created_at', 'updated_at'
        ]
        read_only_fields = ['reference', 'price', 'created_at', 'updated_at']

    def get_receipt(self, obj):
        if obj.status == 'CONFIRMED':
            return obj.generate_receipt()
        return None

    def validate_customer(self, value):
        if value and value.role != UserRole.CUSTOMER:
            raise serializers.ValidationError("The assigned user must have a 'CUSTOMER' role.")
        return value

    def validate(self, data):
        request = self.context.get('request')
        is_creating = self.instance is None
        current_user = request.user if request else None

        # Handle customer field assignment logic
        if is_creating and current_user:
            if current_user.role == UserRole.CUSTOMER:
                if 'customer' in data and data.get('customer') != current_user:
                    # Customers cannot book for others if 'customer' field is sent by them
                    raise serializers.ValidationError({"customer": "Customers can only book appointments for themselves."})
                # Actual assignment of request.user to customer happens in perform_create
            elif current_user.role in [UserRole.ADMIN_OFFICER, UserRole.MANAGER]:
                if not data.get('customer'): # If officer/manager is creating, customer must be in payload
                    raise serializers.ValidationError({"customer": "Customer is required when an Officer or Manager creates an appointment."})
                # validate_customer (called automatically if customer field is present) will check role.
        
        # --- Individual validations using resolved/current values ---
        # For updates, get current value from instance if not in `data`
        _date = data.get('date', getattr(self.instance, 'date', None))
        _room_payload = data.get('room', getattr(self.instance, 'room', None))
        _shift = data.get('shift', getattr(self.instance, 'shift', None))
        _clinic_payload = data.get('clinic', getattr(self.instance, 'clinic', None))
        _doctor_payload = data.get('doctor', getattr(self.instance, 'doctor', None))
        _service_payload = data.get('service', getattr(self.instance, 'service', None))
        _status_to_check = data.get('status', getattr(self.instance, 'status', 'CONFIRMED' if is_creating else None)) # Default to CONFIRMED for new

        # Resolve FKs if they are PKs
        _room = _room_payload
        if _room_payload and not isinstance(_room_payload, Room):
            try: _room = Room.objects.get(pk=_room_payload.pk if hasattr(_room_payload, 'pk') else _room_payload)
            except Room.DoesNotExist: raise serializers.ValidationError({"room": "Invalid Room."})
        
        _clinic = _clinic_payload
        if _clinic_payload and not isinstance(_clinic_payload, Clinic):
            try: _clinic = Clinic.objects.get(pk=_clinic_payload.pk if hasattr(_clinic_payload, 'pk') else _clinic_payload)
            except Clinic.DoesNotExist: raise serializers.ValidationError({"clinic": "Invalid Clinic."})

        _doctor = _doctor_payload
        if _doctor_payload and not isinstance(_doctor_payload, Doctor):
            try: _doctor = Doctor.objects.get(pk=_doctor_payload.pk if hasattr(_doctor_payload, 'pk') else _doctor_payload)
            except Doctor.DoesNotExist: raise serializers.ValidationError({"doctor": "Invalid Doctor."})
        
        _service = _service_payload
        if _service_payload and not isinstance(_service_payload, Service):
            try: _service = Service.objects.get(pk=_service_payload.pk if hasattr(_service_payload, 'pk') else _service_payload)
            except Service.DoesNotExist: raise serializers.ValidationError({"service": "Invalid Service."})


        # Basic presence check for creation - ensure all resolved values are not None
        if is_creating and not all([_date, _room, _shift, _clinic, _doctor, _service]):
             # Identify which resolved value is None
            missing_resolved = []
            if not _date: missing_resolved.append('date')
            if not _room: missing_resolved.append('room')
            # ... and so on for other fields
            # This indicates an issue either in payload or test setup if creating
            raise serializers.ValidationError(f"Essential appointment details (date, room, shift, clinic, doctor, service) must be provided for creation.")


        if _date:
            try: app_validators.validate_not_friday(_date)
            except DjangoValidationError as e: raise serializers.ValidationError({"date": e.messages})

        if _room and _shift: # Ensure _room is resolved Room instance
            try: app_validators.validate_surgery_room_not_in_evening(_room.type, _shift)
            except DjangoValidationError as e: raise serializers.ValidationError({"non_field_errors": e.messages})
        
        is_becoming_confirmed = (_status_to_check == 'CONFIRMED')

        if is_becoming_confirmed and _clinic and _date and _shift:
            try:
                exclude_pk = self.instance.pk if self.instance else None
                app_validators.check_clinic_shift_capacity(_clinic, _date, _shift, exclude_appointment_pk=exclude_pk)
            except DjangoValidationError as e: raise serializers.ValidationError({"non_field_errors": e.messages})

        if _doctor and _clinic and _date and _shift:
            if not Roster.objects.filter(doctor=_doctor, clinic=_clinic, date=_date, shift=_shift, is_active=True).exists():
                raise serializers.ValidationError(
                    {"doctor": "This doctor is not scheduled at this clinic for the selected date and shift."}
                )

        if is_becoming_confirmed and _room and _date and _shift:
            query = Appointment.objects.filter(room=_room, date=_date, shift=_shift, status='CONFIRMED')
            if self.instance: query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError(
                    # Using _room directly which should be the Room instance now
                    {"room": f"This room ({_room}) is not available for the selected date and shift (already booked and confirmed)."}
                )
        
        return data


class ReportSerializer(serializers.ModelSerializer):
    created_by_name = serializers.ReadOnlyField(source='created_by.username')
    clinic_name = serializers.ReadOnlyField(source='clinic.name', allow_null=True)
    # For output only, set in perform_create
    created_by = UserSerializer(read_only=True, required=False, allow_null=True) 

    class Meta:
        model = Report
        fields = [
            'id', 'report_type', 'date_range_start', 'date_range_end',
            'clinic', 'clinic_name', 'created_by', 'created_by_name', 
            'created_at', 'data'
        ]
        read_only_fields = ['created_at', 'data', 'created_by_name']
        # 'created_by' field itself should not be writable from client payload
        # The UserSerializer(read_only=True) makes it non-writable for input.

    def validate(self, data):
        if data.get('date_range_end') and data.get('date_range_start') and \
           data['date_range_end'] < data['date_range_start']:
            raise serializers.ValidationError({"date_range_end": "End date must be after or the same as start date."})
        return data