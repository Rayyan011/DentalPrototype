from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Clinic, Room, Doctor, 
    Service, Price, Roster, Appointment, Report
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('phone', 'role')}),
    )
    list_filter = UserAdmin.list_filter + ('role',)

class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'phone', 'is_active')
    list_filter = ('is_active', 'location')
    search_fields = ('name', 'location', 'address', 'phone')

class RoomAdmin(admin.ModelAdmin):
    list_display = ('number', 'type', 'clinic', 'is_active')
    list_filter = ('type', 'clinic', 'is_active')
    search_fields = ('number',)

class DoctorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'specialization')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'duration_minutes', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name', 'description')

class PriceAdmin(admin.ModelAdmin):
    list_display = ('service', 'shift', 'amount', 'is_active')
    list_filter = ('shift', 'is_active')
    search_fields = ('service__name',)

class RosterAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'clinic', 'date', 'shift', 'is_active')
    list_filter = ('shift', 'clinic', 'is_active', 'date')
    search_fields = ('doctor__user__username', 'doctor__user__first_name', 'doctor__user__last_name')
    date_hierarchy = 'date'

class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('reference', 'customer', 'doctor', 'clinic', 'room', 'service', 'date', 'shift', 'price', 'status')
    list_filter = ('status', 'shift', 'clinic', 'date')
    search_fields = ('reference', 'customer__username', 'doctor__user__username', 'customer__first_name', 'customer__last_name')
    date_hierarchy = 'date'
    readonly_fields = ('reference', 'created_at', 'updated_at')

class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'date_range_start', 'date_range_end', 'clinic', 'created_by', 'created_at')
    list_filter = ('report_type', 'created_at')
    search_fields = ('report_type', 'created_by__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'data')

# Register models
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Clinic, ClinicAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Price, PriceAdmin)
admin.site.register(Roster, RosterAdmin)
admin.site.register(Appointment, AppointmentAdmin)
admin.site.register(Report, ReportAdmin)
