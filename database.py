from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Date, Time, Text
from sqlalchemy.types import Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, date
from decimal import Decimal
import streamlit as st
import os

# Database configuration with smart fallback
def get_database_url():
    """Get database URL with fallback logic"""
    # Check if we're in a production environment
    is_production = any([
        "STREAMLIT_CLOUD" in os.environ,
        "HEROKU" in os.environ,
        "RAILWAY" in os.environ,
        "RENDER" in os.environ,
        "VERCEL" in os.environ,
        os.environ.get("PRODUCTION", "").lower() == "true"
    ])
    
    # Try to get from Streamlit secrets first
    try:
        DATABASE_URL = st.secrets.get("DATABASE_URL", None)
        if DATABASE_URL:
            return DATABASE_URL
    except:
        pass
    
    # Get from environment variable
    env_url = os.environ.get('DATABASE_URL', None)
    if env_url:
        return env_url
    
    # Production vs Local fallback
    if is_production:
        # Production: Use Supabase PostgreSQL
        return 'postgresql://postgres:Aa.01017234828!@db.wejbgeihnluhufvzdwee.supabase.co:5432/postgres'
    else:
        # Local development: Use SQLite
        return 'sqlite:///leave_management.db'

DATABASE_URL = get_database_url()

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    profile = relationship("UserProfile", back_populates="user", uselist=False)

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    employee_id = Column(String, unique=True, index=True)
    position = Column(String)
    department = Column(String)
    starting_date = Column(Date)
    mobile = Column(String)
    birth_date = Column(Date)
    is_supervisor = Column(Boolean, default=False)
    supervisor_id = Column(Integer, ForeignKey("user_profiles.id"))
    country = Column(String, default="Egypt")
    gender = Column(String)
    is_senior = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    supervisor = relationship("UserProfile", remote_side=[id])
    leave_balances = relationship("LeaveBalance", back_populates="user")
    leave_requests = relationship("LeaveRequest", back_populates="employee", foreign_keys="LeaveRequest.employee_id")

class LeaveType(Base):
    __tablename__ = "leave_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    requires_approval = Column(Boolean, default=True)
    requires_documentation = Column(Boolean, default=False)
    requires_reason = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    pay_percentage = Column(Numeric(5, 2), default=100.00)
    
    # Relationships
    leave_balances = relationship("LeaveBalance", back_populates="leave_type")
    leave_requests = relationship("LeaveRequest", back_populates="leave_type")

class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"))
    allocated_days = Column(Numeric(6, 2), default=0)
    used_days = Column(Numeric(6, 2), default=0)
    carry_over_days = Column(Numeric(6, 2), default=0)
    year = Column(Integer, default=datetime.now().year)
    
    # Relationships
    user = relationship("UserProfile", back_populates="leave_balances")
    leave_type = relationship("LeaveType", back_populates="leave_balances")
    
    @property
    def available_days(self):
        return self.allocated_days + self.carry_over_days - self.used_days

class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("user_profiles.id"))
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    duration_type = Column(String, default="full_day")  # full_day, half_day, hours
    total_days = Column(Numeric(6, 2))
    reason = Column(Text)
    status = Column(String, default="pending")  # pending, approved, rejected, cancelled
    
    # Approval fields
    approved_by_id = Column(Integer, ForeignKey("user_profiles.id"))
    approved_date = Column(DateTime)
    supervisor_comments = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Document
    supporting_document = Column(String)  # File path
    
    # Relationships
    employee = relationship("UserProfile", back_populates="leave_requests", foreign_keys=[employee_id])
    leave_type = relationship("LeaveType", back_populates="leave_requests")
    approved_by = relationship("UserProfile", foreign_keys=[approved_by_id])

# Database functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)

@st.cache_resource
def get_database_connection():
    """Get cached database connection"""
    return engine

def create_initial_data():
    """Create initial leave types and sample data"""
    db = SessionLocal()
    
    # Check if data already exists
    if db.query(LeaveType).first():
        db.close()
        return
    
    # Create leave types
    leave_types = [
        {"name": "PTO", "requires_reason": True, "requires_documentation": False},
        {"name": "PPTO", "requires_reason": False, "requires_documentation": False},
        {"name": "Paternal", "requires_reason": False, "requires_documentation": True},
        {"name": "Maternal", "requires_reason": False, "requires_documentation": True},
        {"name": "Bereavement", "requires_reason": True, "requires_documentation": True},
        {"name": "Sick", "requires_reason": False, "requires_documentation": True},
    ]
    
    for lt_data in leave_types:
        leave_type = LeaveType(**lt_data)
        db.add(leave_type)
    
    # Create sample users
    sample_users = [
        {
            "email": "hany@tempo.fit",
            "first_name": "Hany",
            "last_name": "Darwish",
            "employee_id": "104",
            "position": "Front-End Engineer II",
            "department": "Front-End",
            "starting_date": date(2019, 2, 1),
            "mobile": "0100 9383977",
            "birth_date": date(1976, 12, 22),
            "gender": "Male",
            "is_senior": True,
        },
        {
            "email": "ossama@tempo.fit",
            "first_name": "Ossama",
            "last_name": "Eldeeb",
            "employee_id": "101",
            "position": "Country Manager",
            "department": "People & Admin",
            "starting_date": date(2019, 5, 22),
            "mobile": "010 08881808",
            "birth_date": date(1976, 9, 19),
            "gender": "Male",
            "is_senior": True,
            "is_supervisor": True,
        },
    ]
    
    for user_data in sample_users:
        # Extract profile data
        profile_data = {k: v for k, v in user_data.items() if k not in ["email", "first_name", "last_name"]}
        
        # Create user
        user = User(
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"]
        )
        db.add(user)
        db.flush()  # Get user ID
        
        # Create profile
        profile = UserProfile(user_id=user.id, **profile_data)
        db.add(profile)
        db.flush()
        
        # Create leave balances
        leave_types_db = db.query(LeaveType).all()
        for lt in leave_types_db:
            if lt.name == "PTO":
                allocated = 30 if profile_data.get("is_senior", False) else 21
            elif lt.name == "PPTO":
                allocated = 21
            elif lt.name == "Paternal":
                allocated = 21
            elif lt.name == "Maternal":
                allocated = 90
            elif lt.name == "Bereavement":
                allocated = 3
            elif lt.name == "Sick":
                allocated = 19
            else:
                allocated = 0
            
            balance = LeaveBalance(
                user_id=profile.id,
                leave_type_id=lt.id,
                allocated_days=allocated,
                used_days=0,
                carry_over_days=0,
                year=datetime.now().year
            )
            db.add(balance)
    
    db.commit()
    db.close() 