# walkin/views.py - COPY TOÀN BỘ FILE NÀY

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from functools import wraps
from datetime import date
from .models import Location, User, Desk, WalkInQueue


# Decorator kiểm tra quyền admin
def admin_required(view_func):
    """Chỉ admin mới được truy cập"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_role():
            messages.error(request, 'Bạn không có quyền truy cập tính năng này. Chỉ người quản trị mới được phép.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@csrf_protect
@never_cache
def login_view(request):
    """
    Handle user login
    GET: Display login form
    POST: Authenticate and log in user
    """
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                # Check if user has a location (except superadmin)
                if not user.is_superuser and not user.location:
                    messages.error(request, 'Tài khoản của bạn chưa được gán vào địa điểm nào.')
                    return render(request, 'accounts/login.html')
                
                # Check if location is active
                if user.location and not user.location.active:
                    messages.error(request, 'Địa điểm của bạn hiện đang ngưng hoạt động.')
                    return render(request, 'accounts/login.html')
                
                # Log in user
                login(request, user)
                messages.success(request, f'Chào mừng trở lại, {user.first_name or user.username}!')
                
                # Redirect to next page or dashboard
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Tài khoản của bạn đã bị vô hiệu hóa.')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """
    Handle user logout
    """
    username = request.user.username
    logout(request)
    messages.success(request, f'{username} đã đăng xuất thành công.')
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Main dashboard view - shows location-specific data with desk list
    """
    user = request.user
    
    # Get accessible locations for the user
    accessible_locations = user.get_accessible_locations()
    
    # Get desks
    if user.is_superuser:
        desks = Desk.objects.all()
    else:
        desks = Desk.objects.filter(location=user.location)
    
    # Thống kê tổng quan
    if user.location:
        today_total = WalkInQueue.objects.filter(
            location=user.location,
            created_at__date=date.today()
        ).count()
        
        in_progress = WalkInQueue.objects.filter(
            location=user.location,
            status='in_progress',
            created_at__date=date.today()
        ).count()
        
        completed = WalkInQueue.objects.filter(
            location=user.location,
            status='completed',
            created_at__date=date.today()
        ).count()
        
        waiting = WalkInQueue.objects.filter(
            location=user.location,
            status='waiting',
            created_at__date=date.today()
        ).count()
    else:
        today_total = in_progress = completed = waiting = 0
    
    context = {
        'user': user,
        'location': user.location,
        'accessible_locations': accessible_locations,
        'is_superadmin': user.is_superuser,
        'desks': desks,
        'today_total': today_total,
        'in_progress': in_progress,
        'completed': completed,
        'waiting': waiting,
        'is_admin': user.is_admin_role(),
    }
    
    return render(request, 'dashboard/index.html', context)


@login_required
def desk_detail_view(request, desk_id):
    """Chi tiết bàn và hàng đợi - CẢ ADMIN VÀ USER ĐỀU XEM ĐƯỢC"""
    user = request.user
    desk = get_object_or_404(Desk, id=desk_id)
    
    # Kiểm tra quyền truy cập
    if not user.is_superuser and desk.location != user.location:
        messages.error(request, 'Bạn không có quyền truy cập bàn này.')
        return redirect('dashboard')
    
    # Khách đang được phục vụ
    current_serving = desk.queues.filter(
        status='in_progress',
        created_at__date=date.today()
    ).first()
    
    # Hàng đợi
    waiting_queue = desk.queues.filter(
        status='waiting',
        created_at__date=date.today()
    ).order_by('-is_priority', 'created_at')
    
    # Đã hoàn thành hôm nay
    completed_today = desk.queues.filter(
        status='completed',
        created_at__date=date.today()
    ).order_by('-completed_at')
    
    # Thống kê
    total_today = desk.get_today_total()
    
    # Thời gian phục vụ trung bình
    completed_queues = desk.queues.filter(
        status='completed',
        created_at__date=date.today()
    )
    
    avg_service_time = 0
    if completed_queues.exists():
        total_time = sum([q.get_service_time() for q in completed_queues])
        avg_service_time = total_time // completed_queues.count() if completed_queues.count() > 0 else 0
    
    context = {
        'user': user,
        'desk': desk,
        'current_serving': current_serving,
        'waiting_queue': waiting_queue,
        'completed_today': completed_today[:10],
        'total_today': total_today,
        'avg_service_time': avg_service_time,
        'waiting_count': waiting_queue.count(),
        'is_admin': user.is_admin_role(),
    }
    
    return render(request, 'queue/desk_detail.html', context)


@login_required
@admin_required
def add_to_queue(request, desk_id):
    """Thêm khách vào hàng đợi - CHỈ ADMIN"""
    if request.method == 'POST':
        desk = get_object_or_404(Desk, id=desk_id)
        
        # Kiểm tra quyền
        if not request.user.is_superuser and desk.location != request.user.location:
            return JsonResponse({'success': False, 'error': 'Không có quyền'})
        
        # Tạo số thứ tự tự động
        today_count = WalkInQueue.objects.filter(
            desk=desk,
            created_at__date=date.today()
        ).count()
        
        queue_number = f"{desk.desk_number.replace('Bàn ', '')}{today_count + 1:03d}"
        
        # Tạo hàng đợi mới
        queue = WalkInQueue.objects.create(
            location=desk.location,
            desk=desk,
            queue_number=queue_number,
            customer_name=request.POST.get('customer_name'),
            customer_phone=request.POST.get('customer_phone', ''),
            service_type=request.POST.get('service_type'),
            notes=request.POST.get('notes', ''),
            is_priority=request.POST.get('is_priority') == 'on',
        )
        
        messages.success(request, f'Đã thêm {queue.customer_name} vào hàng đợi với số {queue_number}')
        return redirect('desk_detail', desk_id=desk.id)
    
    return redirect('dashboard')


@login_required
@admin_required
def call_queue(request, queue_id):
    """Gọi khách hàng - CHỈ ADMIN"""
    queue = get_object_or_404(WalkInQueue, id=queue_id)
    
    # Kiểm tra quyền
    if not request.user.is_superuser and queue.location != request.user.location:
        messages.error(request, 'Không có quyền')
        return redirect('dashboard')
    
    queue.call()
    queue.start_serving(request.user)
    
    messages.success(request, f'Đã gọi số {queue.queue_number} - {queue.customer_name}')
    return redirect('desk_detail', desk_id=queue.desk.id)


@login_required
@admin_required
def complete_queue(request, queue_id):
    """Hoàn thành phục vụ - CHỈ ADMIN"""
    queue = get_object_or_404(WalkInQueue, id=queue_id)
    
    # Kiểm tra quyền
    if not request.user.is_superuser and queue.location != request.user.location:
        messages.error(request, 'Không có quyền')
        return redirect('dashboard')
    
    queue.complete()
    
    messages.success(request, f'Đã hoàn thành phục vụ {queue.queue_number} - {queue.customer_name}')
    return redirect('desk_detail', desk_id=queue.desk.id)


@login_required
@admin_required
def cancel_queue(request, queue_id):
    """Huỷ hàng đợi - CHỈ ADMIN"""
    queue = get_object_or_404(WalkInQueue, id=queue_id)
    
    # Kiểm tra quyền
    if not request.user.is_superuser and queue.location != request.user.location:
        messages.error(request, 'Không có quyền')
        return redirect('dashboard')
    
    queue.cancel()
    
    messages.success(request, f'Đã huỷ {queue.queue_number} - {queue.customer_name}')
    return redirect('desk_detail', desk_id=queue.desk.id)


@login_required
@admin_required
def desk_management_view(request):
    """Quản lý bàn - CHỈ ADMIN"""
    user = request.user
    
    if user.is_superuser:
        desks = Desk.objects.all()
    else:
        desks = Desk.objects.filter(location=user.location)
    
    context = {
        'user': user,
        'desks': desks,
    }
    
    return render(request, 'queue/desk_management.html', context)


@login_required
@admin_required
def create_desk(request):
    """Tạo bàn mới - CHỈ ADMIN"""
    if request.method == 'POST':
        location = request.user.location if not request.user.is_superuser else get_object_or_404(Location, id=request.POST.get('location_id'))
        
        Desk.objects.create(
            location=location,
            desk_number=request.POST.get('desk_number'),
            desk_name=request.POST.get('desk_name'),
            service_type=request.POST.get('service_type'),
            is_active=request.POST.get('is_active') == 'on'
        )
        
        messages.success(request, 'Đã tạo bàn mới thành công!')
        return redirect('desk_management')
    
    return redirect('dashboard')


@login_required
@admin_required
def delete_desk(request, desk_id):
    """Xoá bàn - CHỈ ADMIN"""
    desk = get_object_or_404(Desk, id=desk_id)
    
    # Kiểm tra quyền
    if not request.user.is_superuser and desk.location != request.user.location:
        messages.error(request, 'Không có quyền xoá bàn này.')
        return redirect('desk_management')
    
    desk_number = desk.desk_number
    desk.delete()
    
    messages.success(request, f'Đã xoá {desk_number} thành công!')
    return redirect('desk_management')


@login_required
def profile_view(request):
    """User profile view"""
    context = {
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
@admin_required
def desk_management_view(request):
    """Quản lý bàn - CHỈ ADMIN"""
    user = request.user
    
    if user.is_superuser:
        desks = Desk.objects.all()
    else:
        desks = Desk.objects.filter(location=user.location)
    
    context = {
        'user': user,
        'desks': desks,
    }
    
    return render(request, 'queue/desk_management.html', context)