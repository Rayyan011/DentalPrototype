"""
URL configuration for dentaclinic project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from appointments.views import (
    ClinicViewSet, RoomViewSet, DoctorViewSet, ServiceViewSet, 
    PriceViewSet, RosterViewSet, AppointmentViewSet, ReportViewSet
)
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
    # Auth views
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),
    path('login/', RoleBasedLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Default admin
    path('admin/', admin.site.urls, name='admin'),
    
    # Role-specific admin interfaces
    path('customer/', customer_admin_site.urls, name='customer_admin'),
    path('doctor/', doctor_admin_site.urls, name='doctor_admin'),
    path('officer/', admin_officer_admin_site.urls, name='officer_admin'),
    path('manager/', manager_admin_site.urls, name='manager_admin'),
    
    # API endpoints
    path('api/', include(router.urls)),
]
