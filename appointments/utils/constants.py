# appointments/utils/constants.py
"""
Constants used throughout the application.
"""

# Shift times definitions (already available in model choices, but can be useful here)
SHIFT_TIMES = {
    'MORNING': '08:00 - 12:00',
    'AFTERNOON': '13:00 - 17:00',
    'EVENING': '18:00 - 22:00',
}

# Maximum number of patients per shift (for appointments in a clinic)
MAX_PATIENTS_PER_SHIFT = 10

# Maximum number of doctors per clinic in rotation roster (for a specific shift)
MAX_DOCTORS_PER_CLINIC_SHIFT = 12