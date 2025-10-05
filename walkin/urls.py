# walkin/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Desk Detail (Cả admin và user đều xem được)
    path('desks/<int:desk_id>/', views.desk_detail_view, name='desk_detail'),
    
    # Desk Management (Chỉ admin)
    path('desks/management/', views.desk_management_view, name='desk_management'),
    path('desks/create/', views.create_desk, name='create_desk'),
    path('desks/<int:desk_id>/delete/', views.delete_desk, name='delete_desk'),
    
    # Queue Management (Chỉ admin)
    path('queue/add/<int:desk_id>/', views.add_to_queue, name='add_to_queue'),
    path('queue/<int:queue_id>/call/', views.call_queue, name='call_queue'),
    path('queue/<int:queue_id>/complete/', views.complete_queue, name='complete_queue'),
    path('queue/<int:queue_id>/cancel/', views.cancel_queue, name='cancel_queue'),
]