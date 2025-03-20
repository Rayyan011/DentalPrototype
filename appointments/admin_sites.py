from django.contrib.admin import AdminSite
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from .models import (
    CustomUser, Clinic, Room, Doctor, 
    Service, Price, Roster, Appointment, Report
)

class BaseAdminSite(AdminSite):
    """Base admin site with common functionality"""
    
    def has_permission(self, request):
        """
        Check if the user has permission to access this admin site.
        """
        if not request.user.is_authenticated:
            return False
        
        # Additional role-specific checks should be implemented in subclasses
        return True
    
    def each_context(self, request):
        """
        Add common context variables to the admin site.
        """
        context = super().each_context(request)
        context.update({
            'role': request.user.role if hasattr(request.user, 'role') else None,
            'is_role_portal': True,  # Flag to indicate this is a role-specific portal
        })
        return context


class CustomerAdminSite(BaseAdminSite):
    """Admin site for customers"""
    site_header = _("Island Dental - Customer Portal")
    site_title = _("Customer Portal")
    index_title = _("Welcome to Island Dental Customer Portal")
    
    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        
        # Only allow customers
        return request.user.role == 'CUSTOMER'


class DoctorAdminSite(BaseAdminSite):
    """Admin site for doctors"""
    site_header = _("Island Dental - Doctor Portal")
    site_title = _("Doctor Portal")
    index_title = _("Welcome to Island Dental Doctor Portal")
    
    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        
        # Only allow doctors
        return request.user.role == 'DOCTOR'


class AdminOfficerAdminSite(BaseAdminSite):
    """Admin site for administrative officers"""
    site_header = _("Island Dental - Administrative Portal")
    site_title = _("Administrative Portal")
    index_title = _("Welcome to Island Dental Administrative Portal")
    
    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        
        # Only allow admin officers
        return request.user.role == 'ADMIN_OFFICER'


class ManagerAdminSite(BaseAdminSite):
    """Admin site for managers"""
    site_header = _("Island Dental - Management Portal")
    site_title = _("Management Portal")
    index_title = _("Welcome to Island Dental Management Portal")
    
    def has_permission(self, request):
        if not super().has_permission(request):
            return False
        
        # Only allow managers
        return request.user.role == 'MANAGER'


# Initialize admin sites
customer_admin_site = CustomerAdminSite(name='customer_admin')
doctor_admin_site = DoctorAdminSite(name='doctor_admin')
admin_officer_admin_site = AdminOfficerAdminSite(name='admin_officer_admin')
manager_admin_site = ManagerAdminSite(name='manager_admin')

# ----- Customer Admin -----
# Customize what customers can see/edit
class CustomerAppointmentAdmin(admin.ModelAdmin):
    """Admin for customers to view and manage their appointments"""
    list_display = ['reference', 'date', 'shift', 'clinic', 'doctor', 'service', 'price']
    list_filter = ['date', 'shift', 'clinic']
    readonly_fields = ['reference', 'price', 'created_at', 'updated_at', 'status']
    fields = ['date', 'shift', 'clinic', 'doctor', 'room', 'service', 'price', 'reference', 'created_at']
    
    def get_queryset(self, request):
        """Only show current customer's appointments"""
        qs = super().get_queryset(request)
        return qs.filter(customer=request.user)
    
    def save_model(self, request, obj, form, change):
        """Set customer to current user when creating appointment and calculate price"""
        if not change:  # Only when creating new appointments
            obj.customer = request.user
            
        # Always recalculate price based on service and shift to ensure consistency
        if obj.service and obj.shift:
            obj.price = obj.service.get_price(obj.shift)
            
        super().save_model(request, obj, form, change)
    
    def has_change_permission(self, request, obj=None):
        """Only allow customers to change appointments with CONFIRMED status"""
        if obj and obj.status != 'CONFIRMED':
            return False
        return super().has_change_permission(request, obj)

customer_admin_site.register(Appointment, CustomerAppointmentAdmin)

# Let customers view clinics, doctors, and services (read-only)
class ReadOnlyModelAdmin(admin.ModelAdmin):
    """Base admin for read-only models"""
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

class CustomerClinicAdmin(ReadOnlyModelAdmin):
    list_display = ['name', 'location', 'phone']
    list_filter = ['location']

class CustomerDoctorAdmin(ReadOnlyModelAdmin):
    list_display = ['__str__', 'specialization']

class CustomerServiceAdmin(ReadOnlyModelAdmin):
    list_display = ['name', 'type', 'duration_minutes']
    list_filter = ['type']

customer_admin_site.register(Clinic, CustomerClinicAdmin)
customer_admin_site.register(Doctor, CustomerDoctorAdmin)
customer_admin_site.register(Service, CustomerServiceAdmin)

# ----- Doctor Admin -----
class DoctorAppointmentAdmin(admin.ModelAdmin):
    """Admin for doctors to view their appointments"""
    list_display = ['reference', 'date', 'shift', 'clinic', 'customer', 'service', 'price', 'status_display']
    list_filter = ['date', 'shift', 'clinic', 'status']
    readonly_fields = ['reference', 'customer', 'clinic', 'room', 'service', 'price', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Only show current doctor's appointments"""
        qs = super().get_queryset(request)
        try:
            doctor = Doctor.objects.get(user=request.user)
            return qs.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            return qs.none()
    
    def save_model(self, request, obj, form, change):
        """Calculate price based on service and shift to ensure consistency"""
        if obj.service and obj.shift:
            obj.price = obj.service.get_price(obj.shift)
        super().save_model(request, obj, form, change)
    
    def status_display(self, obj):
        """Display status with a colored badge"""
        status_map = {
            'CONFIRMED': '<span class="status-badge confirmed">Confirmed</span>',
            'CANCELLED': '<span class="status-badge cancelled">Cancelled</span>',
            'COMPLETED': '<span class="status-badge completed">Completed</span>',
            'NO_SHOW': '<span class="status-badge no-show">No Show</span>',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'
    status_display.allow_tags = True

class DoctorRosterAdmin(ReadOnlyModelAdmin):
    """Admin for doctors to view their roster"""
    list_display = ['date', 'shift', 'clinic']
    list_filter = ['date', 'shift', 'clinic']
    
    def get_queryset(self, request):
        """Only show current doctor's roster"""
        qs = super().get_queryset(request)
        try:
            doctor = Doctor.objects.get(user=request.user)
            return qs.filter(doctor=doctor)
        except Doctor.DoesNotExist:
            return qs.none()

doctor_admin_site.register(Appointment, DoctorAppointmentAdmin)
doctor_admin_site.register(Roster, DoctorRosterAdmin)
doctor_admin_site.register(Clinic, CustomerClinicAdmin)  # Reuse the read-only admin

# ----- Admin Officer Admin -----
class OfficerAppointmentAdmin(admin.ModelAdmin):
    """Admin for officers to manage all appointments"""
    list_display = ['reference', 'date', 'shift', 'clinic', 'room', 'doctor', 'customer', 'service', 'price', 'status_display']
    list_filter = ['date', 'shift', 'clinic', 'doctor', 'status']
    search_fields = ['reference', 'customer__user__username', 'doctor__user__username']
    
    def save_model(self, request, obj, form, change):
        """Calculate price based on service and shift to ensure consistency"""
        if obj.service and obj.shift:
            obj.price = obj.service.get_price(obj.shift)
        super().save_model(request, obj, form, change)
    
    def status_display(self, obj):
        """Display status with a colored badge"""
        status_map = {
            'CONFIRMED': '<span class="status-badge confirmed">Confirmed</span>',
            'CANCELLED': '<span class="status-badge cancelled">Cancelled</span>',
            'COMPLETED': '<span class="status-badge completed">Completed</span>',
            'NO_SHOW': '<span class="status-badge no-show">No Show</span>',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'
    status_display.allow_tags = True

class AdminOfficerRosterAdmin(admin.ModelAdmin):
    """Admin for officers to manage rosters"""
    list_display = ['doctor', 'clinic', 'date', 'shift']
    list_filter = ['clinic', 'date', 'shift']
    search_fields = ['doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name']

admin_officer_admin_site.register(Appointment, OfficerAppointmentAdmin)
admin_officer_admin_site.register(Roster, AdminOfficerRosterAdmin)
admin_officer_admin_site.register(Doctor)
admin_officer_admin_site.register(Clinic)
admin_officer_admin_site.register(Room)
admin_officer_admin_site.register(Service)

# ----- Manager Admin -----
class ManagerAppointmentAdmin(admin.ModelAdmin):
    """Admin for managers to manage all appointments with additional options"""
    list_display = ['reference', 'date', 'shift', 'clinic', 'room', 'doctor', 'customer', 'service', 'price', 'status_display']
    list_filter = ['date', 'shift', 'clinic', 'doctor', 'status']
    search_fields = ['reference', 'customer__user__username', 'doctor__user__username']
    
    def save_model(self, request, obj, form, change):
        """Calculate price based on service and shift to ensure consistency"""
        if obj.service and obj.shift:
            obj.price = obj.service.get_price(obj.shift)
        super().save_model(request, obj, form, change)
    
    def status_display(self, obj):
        """Display status with a colored badge"""
        status_map = {
            'CONFIRMED': '<span class="status-badge confirmed">Confirmed</span>',
            'CANCELLED': '<span class="status-badge cancelled">Cancelled</span>',
            'COMPLETED': '<span class="status-badge completed">Completed</span>',
            'NO_SHOW': '<span class="status-badge no-show">No Show</span>',
        }
        return status_map.get(obj.status, obj.get_status_display())
    status_display.short_description = 'Status'
    status_display.allow_tags = True

# Managers can access everything
manager_admin_site.register(CustomUser)
manager_admin_site.register(Clinic)
manager_admin_site.register(Room)
manager_admin_site.register(Doctor)
manager_admin_site.register(Service)
manager_admin_site.register(Price)
manager_admin_site.register(Roster, AdminOfficerRosterAdmin)
manager_admin_site.register(Appointment, ManagerAppointmentAdmin)
manager_admin_site.register(Report) 