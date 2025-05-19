# DentalPrototype-main/appointments/views/main_views.py
from django.shortcuts import render

def landing_page(request):
    """
    Renders the public landing page.
    """
    context = {}
    # Ensure your template path is correct here.
    # If landing_page.html is in appointments/templates/appointments/
    return render(request, 'appointments/landing_page.html', context)
    # If landing_page.html is directly in appointments/templates/
    # return render(request, 'landing_page.html', context)