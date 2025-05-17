from .clinic_views import ClinicViewSet, RoomViewSet
from .service_views import ServiceViewSet, PriceViewSet
from .doctor_views import DoctorViewSet, RosterViewSet
from .appointment_views import AppointmentViewSet
from .report_views import ReportViewSet
from rest_framework import routers

# Create a router for the API
router = routers.DefaultRouter()
router.register(r'clinics', ClinicViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'prices', PriceViewSet)
router.register(r'doctors', DoctorViewSet)
router.register(r'rosters', RosterViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'reports', ReportViewSet)
