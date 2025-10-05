# walkin/models.py - COPY TOÀN BỘ FILE NÀY

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import date


class Location(models.Model):
    """
    Public Administration Center Location
    Each location represents a physical center where walk-in services are provided
    """
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Name of the public administration center"
    )
    address = models.TextField(
        help_text="Full address of the location"
    )
    state = models.CharField(
        max_length=100,
        help_text="State/Province where the location is situated"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')],
        help_text="Contact phone number"
    )
    active = models.BooleanField(
        default=True,
        help_text="Whether this location is currently operational"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.name} - {self.state}"

    def get_active_status(self):
        return "Active" if self.active else "Inactive"


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Each user belongs to a specific location and can only see data from their location
    """
    ROLE_CHOICES = [
        ('user', 'Người dùng'),      # Chỉ xem
        ('admin', 'Người quản trị'), # Toàn quyền
    ]
    
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Location this user belongs to"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text="User role determining access level"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this user can log in"
    )

    class Meta:
        ordering = ['username']
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def can_access_location(self, location):
        """Check if user can access data from a specific location"""
        if self.is_superuser:
            return True
        return self.location == location

    def get_accessible_locations(self):
        """Get all locations this user can access"""
        if self.is_superuser:
            return Location.objects.filter(active=True)
        return Location.objects.filter(id=self.location.id, active=True) if self.location else Location.objects.none()
    
    def is_admin_role(self):
        """Kiểm tra có phải admin không"""
        return self.role == 'admin' or self.is_superuser
    
    def is_user_role(self):
        """Kiểm tra có phải user không"""
        return self.role == 'user'


class Desk(models.Model):
    """Bàn phục vụ tại trung tâm hành chính"""
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='desks',
        verbose_name='Địa điểm'
    )
    desk_number = models.CharField(
        max_length=10,
        verbose_name='Số bàn'
    )
    desk_name = models.CharField(
        max_length=100,
        verbose_name='Tên bàn'
    )
    service_type = models.TextField(
        verbose_name='Loại dịch vụ',
        help_text='Các loại dịch vụ được phục vụ tại bàn này'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Đang hoạt động'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['desk_number']
        verbose_name = 'Bàn phục vụ'
        verbose_name_plural = 'Các bàn phục vụ'
        unique_together = ['location', 'desk_number']

    def __str__(self):
        return f"{self.desk_number} - {self.desk_name}"

    def get_waiting_count(self):
        """Số khách đang chờ"""
        return self.queues.filter(
            status='waiting',
            created_at__date=date.today()
        ).count()

    def get_serving_count(self):
        """Số khách đang được phục vụ"""
        return self.queues.filter(
            status='in_progress',
            created_at__date=date.today()
        ).count()

    def get_today_total(self):
        """Tổng số khách hôm nay"""
        return self.queues.filter(
            created_at__date=date.today()
        ).count()

    def get_current_serving(self):
        """Khách đang được phục vụ"""
        return self.queues.filter(
            status='in_progress',
            created_at__date=date.today()
        ).first()


class WalkInQueue(models.Model):
    """Hàng đợi walk-in"""
    STATUS_CHOICES = [
        ('waiting', 'Đang chờ'),
        ('in_progress', 'Đang xử lý'),
        ('completed', 'Hoàn thành'),
        ('cancelled', 'Đã huỷ'),
    ]

    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='walk_in_queues',
        verbose_name='Địa điểm'
    )
    desk = models.ForeignKey(
        Desk,
        on_delete=models.CASCADE,
        related_name='queues',
        verbose_name='Bàn phục vụ'
    )

    # Thông tin khách hàng
    queue_number = models.CharField(
        max_length=20,
        verbose_name='Số thứ tự'
    )
    customer_name = models.CharField(
        max_length=200,
        verbose_name='Tên khách hàng'
    )
    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Số điện thoại'
    )
    service_type = models.CharField(
        max_length=100,
        verbose_name='Loại dịch vụ'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Ghi chú'
    )

    # Trạng thái
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting',
        verbose_name='Trạng thái'
    )
    is_priority = models.BooleanField(
        default=False,
        verbose_name='Ưu tiên',
        help_text='Người già, khuyết tật, phụ nữ mang thai'
    )

    # Thời gian
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Giờ vào hàng'
    )
    called_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Giờ gọi'
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Giờ bắt đầu phục vụ'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Giờ hoàn thành'
    )

    # Nhân viên xử lý
    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Nhân viên xử lý'
    )

    class Meta:
        ordering = ['-is_priority', 'created_at']
        verbose_name = 'Hàng đợi'
        verbose_name_plural = 'Hàng đợi'

    def __str__(self):
        return f"{self.queue_number} - {self.customer_name}"

    def call(self):
        """Gọi khách hàng"""
        self.called_at = timezone.now()
        self.save()

    def start_serving(self, user):
        """Bắt đầu phục vụ"""
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.handled_by = user
        self.save()

    def complete(self):
        """Hoàn thành phục vụ"""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def cancel(self):
        """Huỷ"""
        self.status = 'cancelled'
        self.save()

    def get_waiting_time(self):
        """Thời gian chờ (phút)"""
        if self.started_at:
            delta = self.started_at - self.created_at
            return int(delta.total_seconds() / 60)
        elif self.status == 'waiting':
            delta = timezone.now() - self.created_at
            return int(delta.total_seconds() / 60)
        return 0

    def get_service_time(self):
        """Thời gian phục vụ (phút)"""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return 0