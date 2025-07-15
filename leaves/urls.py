from django.urls import path
from . import views

app_name = 'leaves'

urlpatterns = [
    # Dashboard views
    path('', views.dashboard, name='dashboard'),
    path('employee/', views.employee_dashboard, name='employee_dashboard'),
    path('supervisor/', views.supervisor_dashboard, name='supervisor_dashboard'),
    
    # Leave request views
    path('request/', views.create_leave_request, name='create_leave_request'),
    path('request/<int:request_id>/', views.leave_request_detail, name='leave_request_detail'),
    path('request/<int:request_id>/approve/', views.approve_leave_request, name='approve_leave_request'),
    path('request/<int:request_id>/reject/', views.reject_leave_request, name='reject_leave_request'),
    path('request/<int:request_id>/cancel/', views.cancel_leave_request, name='cancel_leave_request'),
    
    # Profile and settings
    path('profile/', views.profile, name='profile'),
    path('balance/', views.leave_balance, name='leave_balance'),
    
    # Admin views
    path('admin/import-employees/', views.import_employees, name='import_employees'),
    path('admin/export-template/', views.export_template, name='export_template'),
    
    # Authentication helper
    path('auth/complete/', views.auth_complete, name='auth_complete'),
] 