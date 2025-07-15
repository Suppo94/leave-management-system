from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from .models import (
    UserProfile, LeaveType, LeaveBalance, 
    LeaveRequest, LeaveHistory, CompanySettings
)

# Inline admin for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Employee Profile'
    fields = (
        'employee_id', 'position', 'department', 'starting_date',
        'mobile', 'birth_date', 'is_supervisor', 'supervisor',
        'country', 'gender', 'is_senior', 'is_active'
    )

# Extend User admin to include profile
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_employee_id', 'get_department')
    
    def get_employee_id(self, obj):
        try:
            return obj.userprofile.employee_id
        except:
            return '-'
    get_employee_id.short_description = 'Employee ID'
    
    def get_department(self, obj):
        try:
            return obj.userprofile.department
        except:
            return '-'
    get_department.short_description = 'Department'

# UserProfile resource for import/export
class UserProfileResource(resources.ModelResource):
    class Meta:
        model = UserProfile
        fields = ('employee_id', 'user__email', 'user__first_name', 'user__last_name', 
                 'position', 'department', 'starting_date', 'mobile', 'birth_date',
                 'is_supervisor', 'supervisor__employee_id', 'country', 'gender', 
                 'is_senior', 'is_active')

@admin.register(UserProfile)
class UserProfileAdmin(ImportExportModelAdmin):
    resource_class = UserProfileResource
    list_display = ('employee_id', 'get_full_name', 'position', 'department', 'supervisor', 'is_supervisor', 'is_senior', 'is_active')
    list_filter = ('department', 'is_supervisor', 'is_senior', 'is_active', 'country', 'gender')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__email', 'position', 'department')
    ordering = ('employee_id',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'employee_id')
        }),
        ('Job Information', {
            'fields': ('position', 'department', 'starting_date', 'is_supervisor', 'supervisor')
        }),
        ('Personal Information', {
            'fields': ('mobile', 'birth_date', 'country', 'gender')
        }),
        ('Status', {
            'fields': ('is_senior', 'is_active')
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Full Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'supervisor__user')

@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'requires_approval', 'requires_documentation', 'requires_reason', 'pay_percentage', 'is_active')
    list_filter = ('requires_approval', 'requires_documentation', 'requires_reason', 'is_active')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'year', 'allocated_days', 'used_days', 'available_days', 'used_percentage_display')
    list_filter = ('leave_type', 'year', 'user__department', 'user__is_senior')
    search_fields = ('user__user__first_name', 'user__user__last_name', 'user__employee_id')
    ordering = ('user__employee_id', 'leave_type__name', 'year')
    
    fieldsets = (
        ('Employee & Leave Type', {
            'fields': ('user', 'leave_type', 'year')
        }),
        ('Balance Details', {
            'fields': ('allocated_days', 'used_days', 'carry_over_days')
        }),
    )
    
    def used_percentage_display(self, obj):
        percentage = obj.used_percentage
        if percentage > 90:
            color = 'red'
        elif percentage > 75:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{:.1f}%</span>', color, percentage)
    used_percentage_display.short_description = 'Used %'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user__user', 'leave_type')

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'leave_type', 'start_date', 'end_date', 'total_days', 'status', 'created_at', 'approved_by')
    list_filter = ('status', 'leave_type', 'duration_type', 'created_at', 'user__department')
    search_fields = ('user__user__first_name', 'user__user__last_name', 'user__employee_id', 'reason')
    ordering = ('-created_at',)
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Employee & Leave Details', {
            'fields': ('user', 'leave_type', 'reason')
        }),
        ('Date & Duration', {
            'fields': ('start_date', 'end_date', 'start_time', 'end_time', 'duration_type', 'total_days')
        }),
        ('Status & Approval', {
            'fields': ('status', 'approved_by', 'approved_date', 'supervisor_comments')
        }),
        ('Document', {
            'fields': ('supporting_document',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user__user', 'leave_type', 'approved_by__user')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "approved_by":
            kwargs["queryset"] = UserProfile.objects.filter(is_supervisor=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(LeaveHistory)
class LeaveHistoryAdmin(admin.ModelAdmin):
    list_display = ('leave_request', 'action', 'performed_by', 'timestamp')
    list_filter = ('action', 'timestamp')
    search_fields = ('leave_request__user__user__first_name', 'leave_request__user__user__last_name', 'performed_by__user__first_name')
    ordering = ('-timestamp',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('leave_request__user__user', 'performed_by__user')

@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')
    search_fields = ('key', 'description')
    ordering = ('key',)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Customize admin site
admin.site.site_header = 'Leave Management System'
admin.site.site_title = 'Leave Management'
admin.site.index_title = 'Welcome to Leave Management System'
