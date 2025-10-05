from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

@csrf_protect
@never_cache
def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                if user.role != 'superadmin' and not user.location:
                    messages.error(request, 'Your account is not assigned to any location.')
                    return render(request, 'accounts/login.html')
                
                if user.location and not user.location.active:
                    messages.error(request, 'Your location is currently inactive.')
                    return render(request, 'accounts/login.html')
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Your account is inactive.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Handle user logout"""
    username = request.user.username
    logout(request)
    messages.success(request, f'{username} has been logged out successfully.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """Main dashboard view"""
    user = request.user
    accessible_locations = user.get_accessible_locations()
    
    context = {
        'user': user,
        'location': user.location,
        'accessible_locations': accessible_locations,
        'is_superadmin': user.role == 'superadmin',
    }
    
    return render(request, 'dashboard/index.html', context)