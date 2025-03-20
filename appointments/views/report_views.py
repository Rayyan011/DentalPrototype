from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta

from ..models import Report, Appointment, Doctor, Service, Clinic, ShiftType
from ..serializers import ReportSerializer

class IsAdminOrManager(permissions.BasePermission):
    """
    Custom permission to only allow admins and managers to access reports.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['MANAGER', 'SYSTEM_ADMIN', 'ADMIN_OFFICER']

class ReportViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Reports.
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAdminOrManager]

    def perform_create(self, serializer):
        """
        Set the created_by field to the current user and generate report data
        """
        report = serializer.save(created_by=self.request.user)
        
        # Generate report data based on type
        if report.report_type == 'APPOINTMENT_UTILIZATION':
            data = self.generate_appointment_utilization(report)
        elif report.report_type == 'REVENUE':
            data = self.generate_revenue_report(report)
        elif report.report_type == 'DOCTOR_PERFORMANCE':
            data = self.generate_doctor_performance(report)
        elif report.report_type == 'SERVICE_DEMAND':
            data = self.generate_service_demand(report)
        else:
            data = {}
            
        # Update report with generated data
        report.data = data
        report.save()

    def generate_appointment_utilization(self, report):
        """
        Generate appointment utilization report
        """
        # Base queryset
        appointments = Appointment.objects.filter(
            date__gte=report.date_range_start,
            date__lte=report.date_range_end
        )
        
        # Filter by clinic if specified
        if report.clinic:
            appointments = appointments.filter(clinic=report.clinic)
            
        # Group by shift
        shift_counts = appointments.values('shift').annotate(
            total=Count('id'),
            confirmed=Count('id', filter=Q(status='CONFIRMED')),
            cancelled=Count('id', filter=Q(status='CANCELLED')),
            completed=Count('id', filter=Q(status='COMPLETED')),
            no_show=Count('id', filter=Q(status='NO_SHOW'))
        )
        
        shift_data = {shift['shift']: {
            'total': shift['total'],
            'confirmed': shift['confirmed'],
            'cancelled': shift['cancelled'],
            'completed': shift['completed'],
            'no_show': shift['no_show']
        } for shift in shift_counts}
        
        # Group by date
        date_counts = appointments.values('date').annotate(
            total=Count('id'),
            confirmed=Count('id', filter=Q(status='CONFIRMED')),
            cancelled=Count('id', filter=Q(status='CANCELLED')),
            completed=Count('id', filter=Q(status='COMPLETED')),
            no_show=Count('id', filter=Q(status='NO_SHOW'))
        ).order_by('date')
        
        date_data = {str(date['date']): {
            'total': date['total'],
            'confirmed': date['confirmed'],
            'cancelled': date['cancelled'],
            'completed': date['completed'],
            'no_show': date['no_show']
        } for date in date_counts}
        
        # Calculate total utilization
        total_appointments = appointments.count()
        confirmed_appointments = appointments.filter(status='CONFIRMED').count()
        cancelled_appointments = appointments.filter(status='CANCELLED').count()
        completed_appointments = appointments.filter(status='COMPLETED').count()
        no_show_appointments = appointments.filter(status='NO_SHOW').count()
        
        return {
            'total_appointments': total_appointments,
            'confirmed_appointments': confirmed_appointments,
            'cancelled_appointments': cancelled_appointments,
            'completed_appointments': completed_appointments,
            'no_show_appointments': no_show_appointments,
            'utilization_by_shift': shift_data,
            'utilization_by_date': date_data
        }

    def generate_revenue_report(self, report):
        """
        Generate revenue report
        """
        # Base queryset
        appointments = Appointment.objects.filter(
            date__gte=report.date_range_start,
            date__lte=report.date_range_end,
            status__in=['CONFIRMED', 'COMPLETED']  # Only count confirmed and completed appointments
        )
        
        # Filter by clinic if specified
        if report.clinic:
            appointments = appointments.filter(clinic=report.clinic)
            
        # Group by shift
        shift_revenue = appointments.values('shift').annotate(
            total_revenue=Sum('price'),
            appointment_count=Count('id')
        )
        
        shift_data = {shift['shift']: {
            'total_revenue': float(shift['total_revenue']) if shift['total_revenue'] else 0,
            'appointment_count': shift['appointment_count'],
            'average_revenue': float(shift['total_revenue'] / shift['appointment_count']) if shift['appointment_count'] > 0 else 0
        } for shift in shift_revenue}
        
        # Group by clinic
        clinic_revenue = appointments.values('clinic__name').annotate(
            total_revenue=Sum('price'),
            appointment_count=Count('id')
        )
        
        clinic_data = {clinic['clinic__name']: {
            'total_revenue': float(clinic['total_revenue']) if clinic['total_revenue'] else 0,
            'appointment_count': clinic['appointment_count'],
            'average_revenue': float(clinic['total_revenue'] / clinic['appointment_count']) if clinic['appointment_count'] > 0 else 0
        } for clinic in clinic_revenue}
        
        # Calculate total revenue
        total_revenue = appointments.aggregate(total=Sum('price'))['total'] or 0
        total_appointments = appointments.count()
        
        return {
            'total_revenue': float(total_revenue),
            'total_appointments': total_appointments,
            'average_revenue_per_appointment': float(total_revenue / total_appointments) if total_appointments > 0 else 0,
            'revenue_by_shift': shift_data,
            'revenue_by_clinic': clinic_data
        }

    def generate_doctor_performance(self, report):
        """
        Generate doctor performance report
        """
        # Base queryset
        appointments = Appointment.objects.filter(
            date__gte=report.date_range_start,
            date__lte=report.date_range_end
        )
        
        # Filter by clinic if specified
        if report.clinic:
            appointments = appointments.filter(clinic=report.clinic)
            
        # Group by doctor
        doctor_performance = appointments.values('doctor__user__first_name', 'doctor__user__last_name', 'doctor_id').annotate(
            total_appointments=Count('id'),
            confirmed_appointments=Count('id', filter=Q(status='CONFIRMED')),
            completed_appointments=Count('id', filter=Q(status='COMPLETED')),
            cancelled_appointments=Count('id', filter=Q(status='CANCELLED')),
            no_show_appointments=Count('id', filter=Q(status='NO_SHOW')),
            total_revenue=Sum('price', filter=Q(status__in=['CONFIRMED', 'COMPLETED']))
        ).order_by('-total_appointments')
        
        # Find top doctor by appointments
        top_doctor_by_appointments = None
        if doctor_performance:
            top_doctor_by_appointments = doctor_performance[0]
            
        # Find top doctor by revenue
        doctor_performance_by_revenue = sorted(doctor_performance, key=lambda x: x['total_revenue'] or 0, reverse=True)
        top_doctor_by_revenue = None
        if doctor_performance_by_revenue:
            top_doctor_by_revenue = doctor_performance_by_revenue[0]
        
        # Format doctor data
        doctor_data = {}
        for doctor in doctor_performance:
            name = f"Dr. {doctor['doctor__user__first_name']} {doctor['doctor__user__last_name']}".strip()
            if not name or name == "Dr. ":
                # Try to get doctor object for better name
                try:
                    doctor_obj = Doctor.objects.get(id=doctor['doctor_id'])
                    name = str(doctor_obj)
                except Doctor.DoesNotExist:
                    name = f"Doctor #{doctor['doctor_id']}"
                    
            doctor_data[str(doctor['doctor_id'])] = {
                'name': name,
                'total_appointments': doctor['total_appointments'],
                'confirmed_appointments': doctor['confirmed_appointments'],
                'completed_appointments': doctor['completed_appointments'],
                'cancelled_appointments': doctor['cancelled_appointments'],
                'no_show_appointments': doctor['no_show_appointments'],
                'total_revenue': float(doctor['total_revenue']) if doctor['total_revenue'] else 0
            }
            
        return {
            'doctor_performance': doctor_data,
            'top_doctor_by_appointments': {
                'id': top_doctor_by_appointments['doctor_id'],
                'name': f"Dr. {top_doctor_by_appointments['doctor__user__first_name']} {top_doctor_by_appointments['doctor__user__last_name']}".strip(),
                'total_appointments': top_doctor_by_appointments['total_appointments']
            } if top_doctor_by_appointments else None,
            'top_doctor_by_revenue': {
                'id': top_doctor_by_revenue['doctor_id'],
                'name': f"Dr. {top_doctor_by_revenue['doctor__user__first_name']} {top_doctor_by_revenue['doctor__user__last_name']}".strip(),
                'total_revenue': float(top_doctor_by_revenue['total_revenue']) if top_doctor_by_revenue['total_revenue'] else 0
            } if top_doctor_by_revenue else None
        }

    def generate_service_demand(self, report):
        """
        Generate service demand report
        """
        # Base queryset
        appointments = Appointment.objects.filter(
            date__gte=report.date_range_start,
            date__lte=report.date_range_end
        )
        
        # Filter by clinic if specified
        if report.clinic:
            appointments = appointments.filter(clinic=report.clinic)
            
        # Group by service
        service_demand = appointments.values('service__name', 'service__type', 'service_id').annotate(
            total_appointments=Count('id'),
            confirmed_appointments=Count('id', filter=Q(status='CONFIRMED')),
            completed_appointments=Count('id', filter=Q(status='COMPLETED')),
            cancelled_appointments=Count('id', filter=Q(status='CANCELLED')),
            no_show_appointments=Count('id', filter=Q(status='NO_SHOW')),
            total_revenue=Sum('price', filter=Q(status__in=['CONFIRMED', 'COMPLETED']))
        ).order_by('-total_appointments')
        
        # Find most demanded service
        most_demanded_service = None
        if service_demand:
            most_demanded_service = service_demand[0]
            
        # Format service data
        service_data = {}
        for service in service_demand:
            service_data[str(service['service_id'])] = {
                'name': service['service__name'],
                'type': service['service__type'],
                'total_appointments': service['total_appointments'],
                'confirmed_appointments': service['confirmed_appointments'],
                'completed_appointments': service['completed_appointments'],
                'cancelled_appointments': service['cancelled_appointments'],
                'no_show_appointments': service['no_show_appointments'],
                'total_revenue': float(service['total_revenue']) if service['total_revenue'] else 0
            }
            
        return {
            'service_demand': service_data,
            'most_demanded_service': {
                'id': most_demanded_service['service_id'],
                'name': most_demanded_service['service__name'],
                'type': most_demanded_service['service__type'],
                'total_appointments': most_demanded_service['total_appointments']
            } if most_demanded_service else None
        }

    @action(detail=False, methods=['get'])
    def appointment_utilization(self, request):
        """
        Generate ad-hoc appointment utilization report
        """
        date_range_start_str = request.query_params.get('start_date', None)
        date_range_end_str = request.query_params.get('end_date', None)
        clinic_id = request.query_params.get('clinic', None)
        
        # If dates not provided, use last 30 days
        if not date_range_start_str or not date_range_end_str:
            date_range_end = timezone.now().date()
            date_range_start = date_range_end - timedelta(days=30)
        else:
            try:
                date_range_start = datetime.strptime(date_range_start_str, '%Y-%m-%d').date()
                date_range_end = datetime.strptime(date_range_end_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        # Create temporary report object
        report = Report(
            report_type='APPOINTMENT_UTILIZATION',
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            created_by=request.user
        )
        
        if clinic_id:
            try:
                clinic = Clinic.objects.get(id=clinic_id)
                report.clinic = clinic
            except Clinic.DoesNotExist:
                pass
                
        data = self.generate_appointment_utilization(report)
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def revenue(self, request):
        """
        Generate ad-hoc revenue report
        """
        date_range_start_str = request.query_params.get('start_date', None)
        date_range_end_str = request.query_params.get('end_date', None)
        clinic_id = request.query_params.get('clinic', None)
        
        # If dates not provided, use last 30 days
        if not date_range_start_str or not date_range_end_str:
            date_range_end = timezone.now().date()
            date_range_start = date_range_end - timedelta(days=30)
        else:
            try:
                date_range_start = datetime.strptime(date_range_start_str, '%Y-%m-%d').date()
                date_range_end = datetime.strptime(date_range_end_str, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        # Create temporary report object
        report = Report(
            report_type='REVENUE',
            date_range_start=date_range_start,
            date_range_end=date_range_end,
            created_by=request.user
        )
        
        if clinic_id:
            try:
                clinic = Clinic.objects.get(id=clinic_id)
                report.clinic = clinic
            except Clinic.DoesNotExist:
                pass
                
        data = self.generate_revenue_report(report)
        
        return Response(data) 