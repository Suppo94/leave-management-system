from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

class UserProfile(models.Model):
    """Extended user profile for employee information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=10, unique=True)
    position = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    starting_date = models.DateField()
    mobile = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    is_supervisor = models.BooleanField(default=False)
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    country = models.CharField(max_length=50, default='Egypt')
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')])
    is_senior = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"
    
    def get_subordinates(self):
        """Get all employees reporting to this supervisor"""
        return UserProfile.objects.filter(supervisor=self, is_active=True)
    
    def years_of_service(self):
        """Calculate years of service"""
        return (timezone.now().date() - self.starting_date).days / 365.25

class LeaveType(models.Model):
    """Different types of leaves available"""
    name = models.CharField(max_length=50, unique=True)
    requires_approval = models.BooleanField(default=True)
    requires_documentation = models.BooleanField(default=False)
    requires_reason = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # For paid leaves, percentage of salary paid
    pay_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=Decimal('100.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    def __str__(self):
        return self.name

class LeaveBalance(models.Model):
    """Employee's leave balance for each leave type"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    allocated_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    used_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carry_over_days = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    year = models.IntegerField(default=timezone.now().year)
    
    class Meta:
        unique_together = ['user', 'leave_type', 'year']
    
    def __str__(self):
        return f"{self.user.user.get_full_name()} - {self.leave_type.name} ({self.year})"
    
    @property
    def available_days(self):
        """Calculate available days"""
        return self.allocated_days + self.carry_over_days - self.used_days
    
    @property
    def used_percentage(self):
        """Calculate percentage of used days"""
        total_allocated = self.allocated_days + self.carry_over_days
        if total_allocated > 0:
            return (self.used_days / total_allocated) * 100
        return 0

class LeaveRequest(models.Model):
    """Leave request submitted by employees"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    DURATION_CHOICES = [
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
        ('hours', 'Hours'),
    ]
    
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    duration_type = models.CharField(max_length=10, choices=DURATION_CHOICES, default='full_day')
    total_days = models.DecimalField(max_digits=6, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    
    # Approval fields
    approved_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_requests')
    approved_date = models.DateTimeField(null=True, blank=True)
    supervisor_comments = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Document upload
    supporting_document = models.FileField(upload_to='leave_documents/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.user.get_full_name()} - {self.leave_type.name} ({self.start_date} to {self.end_date})"
    
    def can_be_approved_by(self, supervisor):
        """Check if a supervisor can approve this request"""
        return self.user.supervisor == supervisor
    
    def is_past_due(self):
        """Check if the leave request is for past dates"""
        return self.start_date < timezone.now().date()
    
    def get_duration_display_text(self):
        """Get human-readable duration"""
        if self.duration_type == 'full_day':
            if self.total_days == 1:
                return "1 day"
            return f"{self.total_days} days"
        elif self.duration_type == 'half_day':
            return "Half day"
        else:
            return f"{self.total_days * 8} hours"

class LeaveHistory(models.Model):
    """History of leave request changes"""
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # 'created', 'approved', 'rejected', 'cancelled'
    performed_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    comments = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.leave_request} - {self.action} by {self.performed_by}"

class CompanySettings(models.Model):
    """Company-wide settings for leave management"""
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    class Meta:
        verbose_name = "Company Setting"
        verbose_name_plural = "Company Settings"
