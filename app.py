import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import *
from streamlit_option_menu import option_menu
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, func
import hashlib
import json

# Page config
st.set_page_config(
    page_title="Tempo Leave Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_db():
    init_database()
    create_initial_data()
    return SessionLocal()

# Authentication functions
def verify_email_domain(email):
    """Check if email is from tempo.fit domain"""
    return email.endswith('@tempo.fit')

def authenticate_user(email):
    """Authenticate user by email"""
    if not verify_email_domain(email):
        return None
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return user
        return None
    finally:
        db.close()

def get_user_profile(user_id):
    """Get user profile by user ID"""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        return profile
    finally:
        db.close()

def simple_login():
    """Simple login form for demo purposes"""
    st.title("🏢 Tempo Leave Management System")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("Sign In")
        email = st.text_input("Email", placeholder="your.email@tempo.fit")
        
        submitted = st.form_submit_button("Sign In", type="primary")
        
        if submitted:
            if not email:
                st.error("Please enter your email address")
                return False
            
            if not verify_email_domain(email):
                st.error("Only @tempo.fit email addresses are allowed")
                return False
            
            user = authenticate_user(email)
            if user:
                st.session_state.user = user
                st.session_state.user_profile = get_user_profile(user.id)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("User not found. Please contact HR to set up your account.")
                return False
    
    # Demo accounts
    st.markdown("---")
    st.subheader("Demo Accounts")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Login as Hany (Employee)", type="secondary"):
            user = authenticate_user("hany@tempo.fit")
            if user:
                st.session_state.user = user
                st.session_state.user_profile = get_user_profile(user.id)
                st.rerun()
    
    with col2:
        if st.button("Login as Ossama (Supervisor)", type="secondary"):
            user = authenticate_user("ossama@tempo.fit")
            if user:
                st.session_state.user = user
                st.session_state.user_profile = get_user_profile(user.id)
                st.rerun()
    
    return False

def get_leave_balances(user_profile_id):
    """Get leave balances for a user"""
    db = SessionLocal()
    try:
        balances = db.query(LeaveBalance).join(LeaveType).filter(
            LeaveBalance.user_id == user_profile_id,
            LeaveBalance.year == datetime.now().year
        ).all()
        return balances
    finally:
        db.close()

def get_leave_requests(user_id=None, employee_id=None, status=None):
    """Get leave requests"""
    db = SessionLocal()
    try:
        query = db.query(LeaveRequest).join(User).join(UserProfile).join(LeaveType)
        
        if user_id:
            query = query.filter(LeaveRequest.user_id == user_id)
        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)
        if status:
            query = query.filter(LeaveRequest.status == status)
        
        requests = query.order_by(LeaveRequest.created_at.desc()).all()
        return requests
    finally:
        db.close()

def create_leave_request(user_id, employee_id, leave_type_id, start_date, end_date, duration_type, total_days, reason=None):
    """Create a new leave request"""
    db = SessionLocal()
    try:
        leave_request = LeaveRequest(
            user_id=user_id,
            employee_id=employee_id,
            leave_type_id=leave_type_id,
            start_date=start_date,
            end_date=end_date,
            duration_type=duration_type,
            total_days=total_days,
            reason=reason
        )
        db.add(leave_request)
        db.commit()
        return leave_request
    finally:
        db.close()

def employee_dashboard():
    """Employee dashboard"""
    user = st.session_state.user
    profile = st.session_state.user_profile
    
    # Header
    st.title(f"Welcome, {user.first_name}! 👋")
    st.markdown(f"**{profile.position}** | **{profile.department}**")
    
    # Employee info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Employee ID", profile.employee_id)
    with col2:
        st.metric("Department", profile.department)
    with col3:
        years_service = (datetime.now().date() - profile.starting_date).days / 365.25
        st.metric("Years of Service", f"{years_service:.1f}")
    with col4:
        st.metric("Status", "Senior" if profile.is_senior else "Regular")
    
    st.markdown("---")
    
    # Leave balances
    st.subheader("📊 Leave Balances")
    balances = get_leave_balances(profile.id)
    
    if balances:
        balance_cols = st.columns(len(balances))
        for idx, balance in enumerate(balances):
            with balance_cols[idx]:
                available = float(balance.available_days)
                total = float(balance.allocated_days + balance.carry_over_days)
                used_pct = (float(balance.used_days) / total * 100) if total > 0 else 0
                
                color = "normal"
                if used_pct > 90:
                    color = "inverse"
                elif used_pct > 75:
                    color = "off"
                
                st.metric(
                    balance.leave_type.name,
                    f"{available:.1f} days",
                    f"{float(balance.used_days):.1f} used",
                    delta_color=color
                )
    
    # Recent requests
    st.subheader("📋 Recent Requests")
    requests = get_leave_requests(user_id=user.id)
    
    if requests:
        request_data = []
        for req in requests[:10]:  # Show last 10 requests
            request_data.append({
                "Date": req.created_at.strftime("%Y-%m-%d"),
                "Leave Type": req.leave_type.name,
                "Period": f"{req.start_date} to {req.end_date}",
                "Days": float(req.total_days),
                "Status": req.status.title(),
                "ID": req.id
            })
        
        df = pd.DataFrame(request_data)
        
        # Color code status
        def color_status(val):
            if val == "Pending":
                return "background-color: #FFF3CD"
            elif val == "Approved":
                return "background-color: #D4F8D4"
            elif val == "Rejected":
                return "background-color: #F8D7DA"
            return ""
        
        styled_df = df.style.applymap(color_status, subset=['Status'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.info("No leave requests yet. Create your first request below!")
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📝 New Leave Request", type="primary"):
            st.session_state.show_new_request = True
            st.rerun()
    
    with col2:
        if st.button("📊 View All Balances"):
            st.session_state.show_balances = True
            st.rerun()
    
    with col3:
        if st.button("📞 Contact HR"):
            st.info("Contact HR at: hr@tempo.fit")

def supervisor_dashboard():
    """Supervisor dashboard"""
    user = st.session_state.user
    profile = st.session_state.user_profile
    
    # Header
    st.title(f"Supervisor Dashboard - {user.first_name} 👨‍💼")
    st.markdown(f"**{profile.position}** | **{profile.department}**")
    
    # Get subordinates
    db = SessionLocal()
    try:
        subordinates = db.query(UserProfile).filter(
            UserProfile.supervisor_id == profile.id,
            UserProfile.is_active == True
        ).all()
    finally:
        db.close()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Team Size", len(subordinates))
    
    with col2:
        pending_requests = []
        for sub in subordinates:
            pending = get_leave_requests(employee_id=sub.id, status="pending")
            pending_requests.extend(pending)
        st.metric("Pending Requests", len(pending_requests))
    
    with col3:
        # Total team leave days this month
        current_month = datetime.now().month
        monthly_requests = []
        for sub in subordinates:
            requests = get_leave_requests(employee_id=sub.id, status="approved")
            monthly_requests.extend([r for r in requests if r.start_date.month == current_month])
        total_days = sum(float(r.total_days) for r in monthly_requests)
        st.metric("Team Leave Days (This Month)", f"{total_days:.1f}")
    
    with col4:
        st.metric("Departments", len(set(sub.department for sub in subordinates)))
    
    st.markdown("---")
    
    # Pending requests that need approval
    if pending_requests:
        st.subheader("⏳ Pending Approvals")
        
        for request in pending_requests:
            with st.expander(f"{request.user.first_name} {request.user.last_name} - {request.leave_type.name} ({request.start_date} to {request.end_date})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Employee:** {request.user.first_name} {request.user.last_name}")
                    st.write(f"**Position:** {request.employee.position}")
                    st.write(f"**Department:** {request.employee.department}")
                    st.write(f"**Leave Type:** {request.leave_type.name}")
                    st.write(f"**Duration:** {request.start_date} to {request.end_date} ({request.total_days} days)")
                    if request.reason:
                        st.write(f"**Reason:** {request.reason}")
                    st.write(f"**Requested:** {request.created_at.strftime('%Y-%m-%d %H:%M')}")
                
                with col2:
                    if st.button("✅ Approve", key=f"approve_{request.id}"):
                        approve_request(request.id, profile.id)
                        st.success("Request approved!")
                        st.rerun()
                    
                    if st.button("❌ Reject", key=f"reject_{request.id}"):
                        reject_request(request.id, profile.id)
                        st.error("Request rejected!")
                        st.rerun()
    
    # Team overview
    st.subheader("👥 Team Overview")
    
    if subordinates:
        team_data = []
        for sub in subordinates:
            balances = get_leave_balances(sub.id)
            requests = get_leave_requests(employee_id=sub.id)
            pending = [r for r in requests if r.status == "pending"]
            
            team_data.append({
                "Name": f"{sub.user.first_name} {sub.user.last_name}",
                "Employee ID": sub.employee_id,
                "Department": sub.department,
                "Position": sub.position,
                "Pending Requests": len(pending),
                "Total Requests": len(requests)
            })
        
        df = pd.DataFrame(team_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No team members found.")

def approve_request(request_id, supervisor_id):
    """Approve a leave request"""
    db = SessionLocal()
    try:
        request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if request:
            request.status = "approved"
            request.approved_by_id = supervisor_id
            request.approved_date = datetime.now()
            
            # Update leave balance
            balance = db.query(LeaveBalance).filter(
                LeaveBalance.user_id == request.employee_id,
                LeaveBalance.leave_type_id == request.leave_type_id,
                LeaveBalance.year == datetime.now().year
            ).first()
            
            if balance:
                balance.used_days += request.total_days
            
            db.commit()
    finally:
        db.close()

def reject_request(request_id, supervisor_id):
    """Reject a leave request"""
    db = SessionLocal()
    try:
        request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if request:
            request.status = "rejected"
            request.approved_by_id = supervisor_id
            request.approved_date = datetime.now()
            db.commit()
    finally:
        db.close()

def new_leave_request():
    """Create new leave request form"""
    st.subheader("📝 New Leave Request")
    
    user = st.session_state.user
    profile = st.session_state.user_profile
    
    with st.form("leave_request_form"):
        # Get leave types
        db = SessionLocal()
        try:
            leave_types = db.query(LeaveType).filter(LeaveType.is_active == True).all()
        finally:
            db.close()
        
        leave_type_options = {lt.name: lt.id for lt in leave_types}
        selected_leave_type = st.selectbox("Leave Type", options=leave_type_options.keys())
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", min_value=datetime.now().date())
        with col2:
            end_date = st.date_input("End Date", min_value=start_date)
        
        duration_type = st.selectbox("Duration Type", ["full_day", "half_day"])
        
        reason = st.text_area("Reason (required for casual leave)", height=100)
        
        submitted = st.form_submit_button("Submit Request", type="primary")
        
        if submitted:
            if start_date > end_date:
                st.error("End date must be after start date")
                return
            
            # Calculate total days
            if duration_type == "full_day":
                total_days = (end_date - start_date).days + 1
            else:  # half_day
                total_days = 0.5
            
            # Check if reason is required
            leave_type_obj = next(lt for lt in leave_types if lt.name == selected_leave_type)
            if leave_type_obj.requires_reason and not reason:
                st.error("Reason is required for this type of leave")
                return
            
            # Create request
            try:
                request = create_leave_request(
                    user_id=user.id,
                    employee_id=profile.id,
                    leave_type_id=leave_type_options[selected_leave_type],
                    start_date=start_date,
                    end_date=end_date,
                    duration_type=duration_type,
                    total_days=total_days,
                    reason=reason
                )
                
                st.success("Leave request submitted successfully!")
                st.session_state.show_new_request = False
                st.rerun()
            except Exception as e:
                st.error(f"Error creating request: {str(e)}")

def main():
    """Main application"""
    # Initialize database
    init_db()
    
    # Check if user is logged in
    if 'user' not in st.session_state:
        simple_login()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🏢 Tempo Leave")
        st.markdown(f"**{st.session_state.user.first_name} {st.session_state.user.last_name}**")
        st.markdown(f"*{st.session_state.user_profile.position}*")
        st.markdown("---")
        
        # Navigation menu
        if st.session_state.user_profile.is_supervisor:
            selected = option_menu(
                "Navigation",
                ["Employee View", "Supervisor View", "Profile", "Logout"],
                icons=['person', 'people', 'gear', 'box-arrow-right'],
                menu_icon="cast",
                default_index=0,
            )
        else:
            selected = option_menu(
                "Navigation",
                ["Dashboard", "Profile", "Logout"],
                icons=['house', 'gear', 'box-arrow-right'],
                menu_icon="cast",
                default_index=0,
            )
        
        if selected == "Logout":
            del st.session_state.user
            del st.session_state.user_profile
            st.rerun()
    
    # Main content area
    if selected == "Dashboard" or selected == "Employee View":
        employee_dashboard()
    elif selected == "Supervisor View":
        supervisor_dashboard()
    elif selected == "Profile":
        st.subheader("👤 Profile")
        profile = st.session_state.user_profile
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Employee ID:** {profile.employee_id}")
            st.write(f"**Position:** {profile.position}")
            st.write(f"**Department:** {profile.department}")
            st.write(f"**Email:** {st.session_state.user.email}")
        
        with col2:
            st.write(f"**Starting Date:** {profile.starting_date}")
            st.write(f"**Mobile:** {profile.mobile}")
            st.write(f"**Country:** {profile.country}")
            st.write(f"**Status:** {'Senior' if profile.is_senior else 'Regular'}")
    
    # Handle modal dialogs
    if 'show_new_request' in st.session_state and st.session_state.show_new_request:
        new_leave_request()
        
        if st.button("Cancel"):
            st.session_state.show_new_request = False
            st.rerun()

if __name__ == "__main__":
    main() 