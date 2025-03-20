from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import Service, Price, ShiftType
from ..serializers import ServiceSerializer, PriceSerializer
from .clinic_views import IsAdminOrManagerOrReadOnly

class ServiceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Services.
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]

    @action(detail=True, methods=['get'])
    def prices(self, request, pk=None):
        """
        Get all prices for a specific service
        """
        service = self.get_object()
        prices = Price.objects.filter(service=service, is_active=True)
        serializer = PriceSerializer(prices, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def price_by_shift(self, request, pk=None):
        """
        Get price for a specific service and shift
        """
        service = self.get_object()
        shift = request.query_params.get('shift', None)
        
        if not shift:
            return Response(
                {"error": "Please provide shift parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if shift not in [choice[0] for choice in ShiftType.choices]:
            return Response(
                {"error": f"Invalid shift. Choose from {[choice[0] for choice in ShiftType.choices]}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        price = service.get_price(shift)
        
        return Response({
            "service": service.name,
            "shift": shift,
            "price": price
        })

class PriceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Prices.
    """
    queryset = Price.objects.filter(is_active=True)
    serializer_class = PriceSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly] 