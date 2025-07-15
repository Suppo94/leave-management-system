from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from datetime import datetime
from leaves.models import UserProfile, LeaveType, LeaveBalance

class Command(BaseCommand):
    help = 'Set up initial data for leave management system'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up initial data...'))
        
        # Create leave types
        self.create_leave_types()
        
        # Create initial employee data
        self.create_employees()
        
        self.stdout.write(self.style.SUCCESS('Initial data setup complete!'))

    def create_leave_types(self):
        """Create the different leave types"""
        self.stdout.write('Creating leave types...')
        
        leave_types = [
            {
                'name': 'PTO',
                'requires_approval': True,
                'requires_documentation': False,
                'requires_reason': True,  # For casual leave within PTO
                'pay_percentage': Decimal('100.00'),
            },
            {
                'name': 'PPTO',
                'requires_approval': True,
                'requires_documentation': False,
                'requires_reason': False,
                'pay_percentage': Decimal('100.00'),
            },
            {
                'name': 'Paternal',
                'requires_approval': True,
                'requires_documentation': True,
                'requires_reason': False,
                'pay_percentage': Decimal('100.00'),
            },
            {
                'name': 'Maternal',
                'requires_approval': True,
                'requires_documentation': True,
                'requires_reason': False,
                'pay_percentage': Decimal('100.00'),
            },
            {
                'name': 'Bereavement',
                'requires_approval': True,
                'requires_documentation': True,
                'requires_reason': True,
                'pay_percentage': Decimal('100.00'),
            },
            {
                'name': 'Sick',
                'requires_approval': True,
                'requires_documentation': True,
                'requires_reason': False,
                'pay_percentage': Decimal('100.00'),  # Variable based on duration
            },
        ]
        
        for leave_type_data in leave_types:
            leave_type, created = LeaveType.objects.get_or_create(
                name=leave_type_data['name'],
                defaults=leave_type_data
            )
            if created:
                self.stdout.write(f'  Created leave type: {leave_type.name}')
            else:
                self.stdout.write(f'  Leave type already exists: {leave_type.name}')

    def create_employees(self):
        """Create employees and their profiles based on provided data"""
        self.stdout.write('Creating employees...')
        
        # Employee data from the CSV provided
        employees_data = [
            {
                'id': 104,
                'name': 'Hany Darwish',
                'email': 'hany@tempo.fit',
                'position': 'Front-End Engineer II',
                'department': 'Front-End',
                'starting_date': '2019-02-01',
                'mobile': '0100 9383977',
                'birth_date': '1976-12-22',
                'manager_id': 101,
                'gender': 'Male',
                'is_senior': True,  # Based on years of service
            },
            {
                'id': 123,
                'name': 'Khadija Hosni Lotfy',
                'email': 'khadijah@tempo.fit',
                'position': 'QA Engineer II',
                'department': 'QA',
                'starting_date': '2020-11-15',
                'mobile': '010 63488226',
                'birth_date': '1989-01-06',
                'manager_id': 101,
                'gender': 'Female',
                'is_senior': False,
            },
            {
                'id': 101,
                'name': 'Ossama Eldeeb',
                'email': 'ossama@tempo.fit',
                'position': 'Country Manager',
                'department': 'People & Admin',
                'starting_date': '2019-05-22',
                'mobile': '010 08881808',
                'birth_date': '1976-09-19',
                'manager_id': None,  # Top level manager
                'gender': 'Male',
                'is_senior': True,
                'is_supervisor': True,
            },
            {
                'id': 152,
                'name': 'Salma Ramadan',
                'email': 'salmaramadan@tempo.fit',
                'position': 'HR Manager',
                'department': 'HR',
                'starting_date': '2021-07-05',
                'mobile': '010 93491999',
                'birth_date': '1995-09-28',
                'manager_id': 101,
                'gender': 'Female',
                'is_senior': False,
            },
            {
                'id': 131,
                'name': 'Mohamed Alaa Abdelaziz',
                'email': 'mohamed.alaa@tempo.fit',
                'position': 'Program Manager II',
                'department': 'Data Collection',
                'starting_date': '2021-08-15',
                'mobile': '010 20370035',
                'birth_date': '1988-03-31',
                'manager_id': 101,
                'gender': 'Male',
                'is_senior': False,
                'is_supervisor': True,
            },
            {
                'id': 303,
                'name': 'Paul Abrudan',
                'email': 'pabrudan@tempo.fit',
                'position': 'Engineering Manager',
                'department': 'Mobile',
                'starting_date': '2020-01-01',
                'mobile': '',
                'birth_date': None,
                'manager_id': 302,
                'gender': 'Male',
                'is_senior': True,
                'is_supervisor': True,
            },
        ]
        
        # Create managers mapping
        manager_mapping = {}
        
        # First pass - create all users and profiles
        for emp_data in employees_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                email=emp_data['email'],
                defaults={
                    'username': emp_data['email'],
                    'first_name': emp_data['name'].split()[0],
                    'last_name': ' '.join(emp_data['name'].split()[1:]),
                }
            )
            
            if created:
                self.stdout.write(f'  Created user: {user.email}')
            
            # Parse dates
            starting_date = datetime.strptime(emp_data['starting_date'], '%Y-%m-%d').date()
            birth_date = None
            if emp_data['birth_date']:
                birth_date = datetime.strptime(emp_data['birth_date'], '%Y-%m-%d').date()
            
            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'employee_id': str(emp_data['id']),
                    'position': emp_data['position'],
                    'department': emp_data['department'],
                    'starting_date': starting_date,
                    'mobile': emp_data['mobile'],
                    'birth_date': birth_date,
                    'gender': emp_data['gender'],
                    'is_senior': emp_data.get('is_senior', False),
                    'is_supervisor': emp_data.get('is_supervisor', False),
                }
            )
            
            manager_mapping[emp_data['id']] = {
                'profile': profile,
                'manager_id': emp_data['manager_id']
            }
            
            if created:
                self.stdout.write(f'  Created profile: {profile.employee_id} - {profile.user.get_full_name()}')
        
        # Second pass - set up supervisor relationships
        for emp_id, data in manager_mapping.items():
            if data['manager_id']:
                manager_data = manager_mapping.get(data['manager_id'])
                if manager_data:
                    data['profile'].supervisor = manager_data['profile']
                    data['profile'].save()
                    self.stdout.write(f'  Set supervisor for {data["profile"].employee_id}: {manager_data["profile"].employee_id}')
        
        # Create leave balances for all employees
        self.create_leave_balances()

    def create_leave_balances(self):
        """Create initial leave balances for all employees"""
        self.stdout.write('Creating leave balances...')
        
        current_year = timezone.now().year
        leave_types = LeaveType.objects.all()
        profiles = UserProfile.objects.all()
        
        for profile in profiles:
            for leave_type in leave_types:
                # Calculate default allocation based on leave type and seniority
                if leave_type.name == 'PTO':
                    allocated_days = Decimal('30') if profile.is_senior else Decimal('21')
                elif leave_type.name == 'PPTO':
                    allocated_days = Decimal('21')
                elif leave_type.name == 'Paternal':
                    allocated_days = Decimal('21')
                elif leave_type.name == 'Maternal':
                    allocated_days = Decimal('90')
                elif leave_type.name == 'Bereavement':
                    allocated_days = Decimal('3')
                elif leave_type.name == 'Sick':
                    allocated_days = Decimal('19')  # 12 + 7 days
                else:
                    allocated_days = Decimal('0')
                
                balance, created = LeaveBalance.objects.get_or_create(
                    user=profile,
                    leave_type=leave_type,
                    year=current_year,
                    defaults={
                        'allocated_days': allocated_days,
                        'used_days': Decimal('0'),
                        'carry_over_days': Decimal('0'),
                    }
                )
                
                if created:
                    self.stdout.write(f'  Created balance: {profile.employee_id} - {leave_type.name}: {allocated_days} days')
        
        self.stdout.write(self.style.SUCCESS('Leave balances created successfully!')) 