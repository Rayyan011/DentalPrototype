"""
Constants used throughout the application.
"""

# Shift times definitions
SHIFT_TIMES = {
    'MORNING': '08:00 - 12:00',
    'AFTERNOON': '13:00 - 17:00',
    'EVENING': '18:00 - 22:00',
}

# Appointment status choices
STATUS_CHOICES = {
    'PENDING': 'Pending',
    'CONFIRMED': 'Confirmed',
    'CANCELLED': 'Cancelled',
    'COMPLETED': 'Completed',
}

# Room types
ROOM_TYPES = {
    'NORMAL': 'Normal',
    'SURGERY': 'Surgery',
}

# Maximum number of patients per shift
MAX_PATIENTS_PER_SHIFT = 10

# Maximum number of doctors per clinic in rotation
MAX_DOCTORS_PER_CLINIC = 12

MAX_DOCTORS_PER_CLINIC_SHIFT = 4

# Service categories
SERVICE_CATEGORIES = {
    'GENERAL': 'General',
    'SPECIALTY': 'Specialty',
    'COSMETIC': 'Cosmetic',
    'EMERGENCY': 'Emergency',
} 
