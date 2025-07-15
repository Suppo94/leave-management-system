from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Submit, Row, Column, HTML
from crispy_forms.bootstrap import FormActions
from decimal import Decimal
from datetime import datetime, timedelta
import csv
import io

from .models import LeaveRequest, LeaveType, LeaveBalance, UserProfile

class LeaveRequestForm(forms.ModelForm):
    """Form for creating and editing leave requests"""
    
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_type', 'start_date', 'end_date', 'start_time', 'end_time',
            'duration_type', 'reason', 'supporting_document'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter active leave types
        self.fields['leave_type'].queryset = LeaveType.objects.filter(is_active=True)
        
        # Set up crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-10'
        
        self.helper.layout = Layout(
            Fieldset(
                'Leave Request Details',
                'leave_type',
                Row(
                    Column('start_date', css_class='form-group col-md-6 mb-0'),
                    Column('end_date', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'duration_type',
                Row(
                    Column('start_time', css_class='form-group col-md-6 mb-0'),
                    Column('end_time', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'reason',
                'supporting_document',
                HTML('<div id="leave-calculation"></div>'),
            ),
            FormActions(
                Submit('submit', 'Submit Request', css_class='btn-primary'),
                HTML('<a href="{% url "leaves:employee_dashboard" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        duration_type = cleaned_data.get('duration_type')
        leave_type = cleaned_data.get('leave_type')
        reason = cleaned_data.get('reason')
        
        # Validate dates
        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError('End date cannot be before start date.')
            
            # Check if leave is in the past
            if start_date < timezone.now().date():
                raise ValidationError('Leave cannot be scheduled for past dates.')
        
        # Validate times for hourly leave
        if duration_type == 'hours' and start_time and end_time:
            if start_time >= end_time:
                raise ValidationError('End time must be after start time.')
            
            # Calculate duration in hours
            duration_hours = (datetime.combine(start_date, end_time) - 
                            datetime.combine(start_date, start_time)).seconds / 3600
            
            if duration_hours < 0.5:
                raise ValidationError('Minimum leave duration is 30 minutes.')
            
            if duration_hours > 8:
                raise ValidationError('Maximum leave duration is 8 hours per day.')
        
        # Check if reason is required for casual leave
        if leave_type and leave_type.requires_reason and not reason:
            raise ValidationError('Reason is required for this type of leave.')
        
        # Calculate total days
        if start_date and end_date:
            if duration_type == 'full_day':
                total_days = (end_date - start_date).days + 1
            elif duration_type == 'half_day':
                total_days = Decimal('0.5')
            else:  # hours
                if start_time and end_time:
                    duration_hours = (datetime.combine(start_date, end_time) - 
                                    datetime.combine(start_date, start_time)).seconds / 3600
                    total_days = Decimal(str(duration_hours / 8))
                else:
                    total_days = Decimal('0')
            
            cleaned_data['total_days'] = total_days
            
            # Check leave balance
            if self.user and leave_type:
                try:
                    leave_balance = LeaveBalance.objects.get(
                        user=self.user,
                        leave_type=leave_type,
                        year=timezone.now().year
                    )
                    if leave_balance.available_days < total_days:
                        raise ValidationError(
                            f'Insufficient leave balance. Available: {leave_balance.available_days} days, Requested: {total_days} days'
                        )
                except LeaveBalance.DoesNotExist:
                    # Create default balance if it doesn't exist
                    pass
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.total_days = self.cleaned_data['total_days']
        
        if commit:
            instance.save()
        
        return instance

class EmployeeImportForm(forms.Form):
    """Form for importing employees from CSV"""
    
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with employee data',
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            Fieldset(
                'Import Employees',
                'csv_file',
                HTML('<p class="help-text">Download the template below to see the required format.</p>'),
                HTML('<a href="{% url "leaves:export_template" %}" class="btn btn-info btn-sm">Download Template</a>'),
            ),
            FormActions(
                Submit('submit', 'Import', css_class='btn-primary'),
                HTML('<a href="{% url "admin:leaves_userprofile_changelist" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        
        if not csv_file.name.endswith('.csv'):
            raise ValidationError('File must be a CSV file.')
        
        # Read and validate CSV content
        try:
            file_content = csv_file.read().decode('utf-8')
            csv_file.seek(0)  # Reset file pointer
            
            # Parse CSV
            csv_reader = csv.DictReader(io.StringIO(file_content))
            
            # Check for required columns
            required_columns = ['ID', 'Name', 'Email', 'Position', 'Department', 'Starting Date', 'Reported To (Direct Manager)', 'Manager Email']
            
            if not all(col in csv_reader.fieldnames for col in required_columns):
                raise ValidationError(f'CSV must contain columns: {", ".join(required_columns)}')
            
            # Validate data
            row_count = 0
            for row in csv_reader:
                row_count += 1
                if row_count > 1000:  # Limit to prevent memory issues
                    raise ValidationError('CSV file is too large. Maximum 1000 rows allowed.')
                
                # Validate email format
                email = row.get('Email', '').strip()
                if email and not email.endswith('@tempo.fit'):
                    raise ValidationError(f'Row {row_count}: Email must be from @tempo.fit domain: {email}')
        
        except UnicodeDecodeError:
            raise ValidationError('File must be encoded in UTF-8.')
        except csv.Error as e:
            raise ValidationError(f'Invalid CSV format: {str(e)}')
        
        return csv_file

class ApprovalForm(forms.Form):
    """Form for approving/rejecting leave requests"""
    
    action = forms.ChoiceField(
        choices=[('approve', 'Approve'), ('reject', 'Reject')],
        widget=forms.RadioSelect,
        required=True
    )
    
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Optional comments for the employee'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Fieldset(
                'Approval Decision',
                'action',
                'comments',
            ),
            FormActions(
                Submit('submit', 'Submit Decision', css_class='btn-primary'),
                HTML('<a href="{% url "leaves:supervisor_dashboard" %}" class="btn btn-secondary">Cancel</a>')
            )
        )

class LeaveBalanceForm(forms.ModelForm):
    """Form for editing leave balances"""
    
    class Meta:
        model = LeaveBalance
        fields = ['allocated_days', 'carry_over_days']
        widgets = {
            'allocated_days': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
            'carry_over_days': forms.NumberInput(attrs={'step': '0.5', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Fieldset(
                'Leave Balance',
                'allocated_days',
                'carry_over_days',
                HTML('<p class="help-text">Current used days: {{ form.instance.used_days }}</p>'),
                HTML('<p class="help-text">Available days: {{ form.instance.available_days }}</p>'),
            ),
            FormActions(
                Submit('submit', 'Update Balance', css_class='btn-primary'),
                HTML('<a href="{{ request.META.HTTP_REFERER }}" class="btn btn-secondary">Cancel</a>')
            )
        ) 