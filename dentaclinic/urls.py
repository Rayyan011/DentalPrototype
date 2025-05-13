from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from appointments.views import router
from appointments.views import get_csrf_token

from appointments.views import (
    ClinicViewSet, RoomViewSet, DoctorViewSet, ServiceViewSet,
    PriceViewSet, RosterViewSet, AppointmentViewSet, ReportViewSet,
)

# Import the appointments views module (appointments/views.py)
from appointments import views # <-- Corrected import is now separate

from appointments.admin_sites import (
    customer_admin_site, doctor_admin_site,
    admin_officer_admin_site, manager_admin_site
)
from appointments.views.auth_views import RoleBasedLoginView, LogoutView
from django.views.generic import RedirectView

router = routers.DefaultRouter()
router.register(r'clinics', ClinicViewSet)
router.register(r'rooms', RoomViewSet)
router.register(r'doctors', DoctorViewSet)
router.register(r'services', ServiceViewSet)
router.register(r'prices', PriceViewSet)
router.register(r'rosters', RosterViewSet)
router.register(r'appointments', AppointmentViewSet)
router.register(r'reports', ReportViewSet)

urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),
    path('login/', RoleBasedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls, name='admin'),
    path('customer/', customer_admin_site.urls, name='customer_admin'),
    path('doctor/', doctor_admin_site.urls, name='doctor_admin'),
    path('officer/', admin_officer_admin_site.urls, name='officer_admin'),
    path('manager/', manager_admin_site.urls, name='manager_admin'),
    path('api/', include(router.urls)),
    path('csrf/', views.get_csrf_token, name='get_csrf_token'), 
]
