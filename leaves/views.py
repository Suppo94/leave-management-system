from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Q, Sum
from decimal import Decimal
import csv
import io
from datetime import datetime, timedelta

from .models import UserProfile, LeaveType, LeaveBalance, LeaveRequest, LeaveHistory
from .forms import LeaveRequestForm, EmployeeImportForm

def dashboard(request):
    """Main dashboard that redirects based on user type"""
    if not request.user.is_authenticated:
        return redirect('/accounts/google/login/')
    
    try:
        user_profile = request.user.userprofile
        if user_profile.is_supervisor:
            return redirect('leaves:supervisor_dashboard')
        else:
            return redirect('leaves:employee_dashboard')
    except UserProfile.DoesNotExist:
        # User doesn't have a profile, redirect to auth completion
        return redirect('leaves:auth_complete')

@login_required
def employee_dashboard(request):
    """Employee dashboard showing leave balances and request history"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    # Get current year leave balances
    current_year = timezone.now().year
    leave_balances = LeaveBalance.objects.filter(
        user=user_profile, 
        year=current_year
    ).select_related('leave_type')
    
    # Get recent leave requests
    recent_requests = LeaveRequest.objects.filter(
        user=user_profile
    ).order_by('-created_at')[:10]
    
    # Get pending requests count
    pending_requests = LeaveRequest.objects.filter(
        user=user_profile,
        status='pending'
    ).count()
    
    context = {
        'user_profile': user_profile,
        'leave_balances': leave_balances,
        'recent_requests': recent_requests,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'leaves/employee_dashboard.html', context)

@login_required
def supervisor_dashboard(request):
    """Supervisor dashboard showing team members and pending requests"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    if not user_profile.is_supervisor:
        return redirect('leaves:employee_dashboard')
    
    # Get all subordinates
    subordinates = user_profile.get_subordinates()
    
    # Get pending requests from subordinates
    pending_requests = LeaveRequest.objects.filter(
        user__in=subordinates,
        status='pending'
    ).order_by('-created_at')
    
    # Get all requests from subordinates (recent)
    all_requests = LeaveRequest.objects.filter(
        user__in=subordinates
    ).order_by('-created_at')[:20]
    
    # Get team leave summary
    team_summary = []
    for subordinate in subordinates:
        current_year = timezone.now().year
        balances = LeaveBalance.objects.filter(
            user=subordinate,
            year=current_year
        ).select_related('leave_type')
        
        team_summary.append({
            'employee': subordinate,
            'balances': balances,
            'pending_requests': pending_requests.filter(user=subordinate).count()
        })
    
    context = {
        'user_profile': user_profile,
        'subordinates': subordinates,
        'pending_requests': pending_requests,
        'all_requests': all_requests,
        'team_summary': team_summary,
    }
    
    return render(request, 'leaves/supervisor_dashboard.html', context)

@login_required
def create_leave_request(request):
    """Create a new leave request"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST, request.FILES, user=user_profile)
        if form.is_valid():
            leave_request = form.save(commit=False)
            leave_request.user = user_profile
            leave_request.save()
            
            # Create history entry
            LeaveHistory.objects.create(
                leave_request=leave_request,
                action='created',
                performed_by=user_profile,
                comments=f'Leave request created for {leave_request.total_days} days'
            )
            
            # Send email notification to supervisor
            if user_profile.supervisor:
                send_leave_request_notification(leave_request)
            
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('leaves:employee_dashboard')
    else:
        form = LeaveRequestForm(user=user_profile)
    
    return render(request, 'leaves/create_request.html', {'form': form})

@login_required
def leave_request_detail(request, request_id):
    """View details of a leave request"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    # Check permissions
    if not (leave_request.user == user_profile or 
            (user_profile.is_supervisor and leave_request.can_be_approved_by(user_profile))):
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('leaves:dashboard')
    
    # Get request history
    history = LeaveHistory.objects.filter(leave_request=leave_request)
    
    context = {
        'leave_request': leave_request,
        'history': history,
        'can_approve': user_profile.is_supervisor and leave_request.can_be_approved_by(user_profile) and leave_request.status == 'pending',
    }
    
    return render(request, 'leaves/request_detail.html', context)

@login_required
def approve_leave_request(request, request_id):
    """Approve a leave request"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    if not user_profile.is_supervisor:
        messages.error(request, 'You do not have permission to approve requests.')
        return redirect('leaves:dashboard')
    
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    if not leave_request.can_be_approved_by(user_profile):
        messages.error(request, 'You cannot approve this request.')
        return redirect('leaves:supervisor_dashboard')
    
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        
        with transaction.atomic():
            # Update request status
            leave_request.status = 'approved'
            leave_request.approved_by = user_profile
            leave_request.approved_date = timezone.now()
            leave_request.supervisor_comments = comments
            leave_request.save()
            
            # Update leave balance
            leave_balance, created = LeaveBalance.objects.get_or_create(
                user=leave_request.user,
                leave_type=leave_request.leave_type,
                year=timezone.now().year,
                defaults={'allocated_days': get_default_allocation(leave_request.user, leave_request.leave_type)}
            )
            leave_balance.used_days += leave_request.total_days
            leave_balance.save()
            
            # Create history entry
            LeaveHistory.objects.create(
                leave_request=leave_request,
                action='approved',
                performed_by=user_profile,
                comments=comments
            )
        
        # Send notification email
        send_leave_status_notification(leave_request, 'approved')
        
        messages.success(request, 'Leave request approved successfully!')
        return redirect('leaves:supervisor_dashboard')
    
    return render(request, 'leaves/approve_request.html', {'leave_request': leave_request})

@login_required
def reject_leave_request(request, request_id):
    """Reject a leave request"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    if not user_profile.is_supervisor:
        messages.error(request, 'You do not have permission to reject requests.')
        return redirect('leaves:dashboard')
    
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    if not leave_request.can_be_approved_by(user_profile):
        messages.error(request, 'You cannot reject this request.')
        return redirect('leaves:supervisor_dashboard')
    
    if request.method == 'POST':
        comments = request.POST.get('comments', '')
        
        leave_request.status = 'rejected'
        leave_request.approved_by = user_profile
        leave_request.approved_date = timezone.now()
        leave_request.supervisor_comments = comments
        leave_request.save()
        
        # Create history entry
        LeaveHistory.objects.create(
            leave_request=leave_request,
            action='rejected',
            performed_by=user_profile,
            comments=comments
        )
        
        # Send notification email
        send_leave_status_notification(leave_request, 'rejected')
        
        messages.success(request, 'Leave request rejected.')
        return redirect('leaves:supervisor_dashboard')
    
    return render(request, 'leaves/reject_request.html', {'leave_request': leave_request})

@login_required
def cancel_leave_request(request, request_id):
    """Cancel a leave request"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    leave_request = get_object_or_404(LeaveRequest, id=request_id)
    
    if leave_request.user != user_profile:
        messages.error(request, 'You can only cancel your own requests.')
        return redirect('leaves:dashboard')
    
    if leave_request.status != 'pending':
        messages.error(request, 'You can only cancel pending requests.')
        return redirect('leaves:dashboard')
    
    if request.method == 'POST':
        leave_request.status = 'cancelled'
        leave_request.save()
        
        # Create history entry
        LeaveHistory.objects.create(
            leave_request=leave_request,
            action='cancelled',
            performed_by=user_profile,
            comments='Request cancelled by employee'
        )
        
        messages.success(request, 'Leave request cancelled.')
        return redirect('leaves:employee_dashboard')
    
    return render(request, 'leaves/cancel_request.html', {'leave_request': leave_request})

@login_required
def profile(request):
    """User profile page"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    return render(request, 'leaves/profile.html', {'user_profile': user_profile})

@login_required
def leave_balance(request):
    """View leave balances"""
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        return redirect('leaves:auth_complete')
    
    current_year = timezone.now().year
    leave_balances = LeaveBalance.objects.filter(
        user=user_profile,
        year=current_year
    ).select_related('leave_type')
    
    return render(request, 'leaves/leave_balance.html', {'leave_balances': leave_balances})

def auth_complete(request):
    """Complete authentication setup for new users"""
    if not request.user.is_authenticated:
        return redirect('/accounts/google/login/')
    
    # Check if user email is from tempo.fit domain
    if not request.user.email.endswith('@tempo.fit'):
        messages.error(request, 'Only @tempo.fit email addresses are allowed.')
        return redirect('/accounts/logout/')
    
    # Check if user already has a profile
    try:
        user_profile = request.user.userprofile
        return redirect('leaves:dashboard')
    except UserProfile.DoesNotExist:
        pass
    
    # Create user profile based on email
    # This is where you would implement the logic to create UserProfile
    # based on the employee data you provided
    
    messages.info(request, 'Your account is being set up. Please contact HR if you cannot access the system.')
    return render(request, 'leaves/auth_complete.html')

def import_employees(request):
    """Import employees from CSV"""
    # This would be implemented as an admin-only view
    pass

def export_template(request):
    """Export CSV template for employee import"""
    # This would be implemented as an admin-only view
    pass

# Helper functions
def get_default_allocation(user_profile, leave_type):
    """Get default allocation for a user and leave type"""
    if leave_type.name == 'PTO':
        return Decimal('30' if user_profile.is_senior else '21')
    elif leave_type.name == 'PPTO':
        return Decimal('21')
    elif leave_type.name == 'Paternal':
        return Decimal('21')
    elif leave_type.name == 'Maternal':
        return Decimal('90')
    elif leave_type.name == 'Bereavement':
        return Decimal('3')
    elif leave_type.name == 'Sick':
        return Decimal('19')  # 12 + 7
    else:
        return Decimal('0')

def send_leave_request_notification(leave_request):
    """Send email notification to supervisor about new leave request"""
    if leave_request.user.supervisor and leave_request.user.supervisor.user.email:
        subject = f'New Leave Request from {leave_request.user.user.get_full_name()}'
        message = f"""
        A new leave request has been submitted:
        
        Employee: {leave_request.user.user.get_full_name()}
        Leave Type: {leave_request.leave_type.name}
        Duration: {leave_request.start_date} to {leave_request.end_date}
        Total Days: {leave_request.total_days}
        Reason: {leave_request.reason}
        
        Please review and approve/reject the request.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [leave_request.user.supervisor.user.email],
            fail_silently=True,
        )

def send_leave_status_notification(leave_request, status):
    """Send email notification to employee about leave request status change"""
    subject = f'Leave Request {status.title()}'
    message = f"""
    Your leave request has been {status}:
    
    Leave Type: {leave_request.leave_type.name}
    Duration: {leave_request.start_date} to {leave_request.end_date}
    Total Days: {leave_request.total_days}
    
    Supervisor Comments: {leave_request.supervisor_comments or 'None'}
    """
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [leave_request.user.user.email],
        fail_silently=True,
    )
