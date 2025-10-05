from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Location, User

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'state', 'phone', 'active', 'created_at']
    list_filter = ['active', 'state']
    search_fields = ['name', 'address', 'state']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'location', 'role', 'is_active']
    list_filter = ['role', 'is_active', 'location']
    
    fieldsets = (
        ('Login Info', {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Location & Role', {'fields': ('location', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    
    add_fieldsets = (
        ('Login Info', {'fields': ('username', 'password1', 'password2')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Location & Role', {'fields': ('location', 'role')}),
    )

from .models import Location, User, Desk, WalkInQueue

@admin.register(Desk)
class DeskAdmin(admin.ModelAdmin):
    list_display = ['desk_number', 'desk_name', 'location', 'is_active', 'created_at']
    list_filter = ['is_active', 'location', 'created_at']
    search_fields = ['desk_number', 'desk_name', 'service_type']
    ordering = ['location', 'desk_number']