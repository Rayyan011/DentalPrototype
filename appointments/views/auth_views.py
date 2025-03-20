from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm


class RoleBasedLoginView(View):
    """
    Custom login view that redirects users to their role-specific admin site
    """
    template_name = 'appointments/login.html'
    
    def get(self, request):
        # If user is already authenticated, redirect to appropriate dashboard
        if request.user.is_authenticated:
            return self._redirect_to_role_dashboard(request.user)
            
        form = AuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome, {user.first_name or username}!")
                return self._redirect_to_role_dashboard(user)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
            
        return render(request, self.template_name, {'form': form})
    
    def _redirect_to_role_dashboard(self, user):
        """Redirect user to appropriate dashboard based on role"""
        if user.is_superuser:
            return redirect(reverse('admin:index'))
        elif user.role == 'CUSTOMER':
            return redirect(reverse('customer_admin:index'))
        elif user.role == 'DOCTOR':
            return redirect(reverse('doctor_admin:index'))
        elif user.role == 'ADMIN_OFFICER':
            return redirect(reverse('admin_officer_admin:index'))
        elif user.role == 'MANAGER':
            return redirect(reverse('manager_admin:index'))
        else:
            # Default fallback
            return redirect('/')


class LogoutView(View):
    """Handle user logout"""
    
    def get(self, request):
        logout(request)
        messages.info(request, "You have successfully logged out.")
        return redirect('login') 