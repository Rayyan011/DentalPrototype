from django.shortcuts import render
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

# This file is here for backward compatibility and general views.
# All main API ViewSets and role-based admin views are in views/ directory.


@ensure_csrf_cookie # Ensure the csrftoken cookie is set on this response
def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)})

