# 🏢 Tempo Leave Management System

A comprehensive leave management system built with Streamlit and Supabase for internal company use.

## 🚀 Features

### For Employees:
- ✅ **Leave Balance Tracking**: View all leave types and remaining balances
- ✅ **Leave Request Submission**: Submit new leave requests with proper validation
- ✅ **Request History**: View all past and current leave requests
- ✅ **Real-time Status**: Track approval status of submitted requests
- ✅ **Employee Profile**: View personal information and employment details

### For Supervisors:
- ✅ **Team Dashboard**: Overview of all team members and their leave status
- ✅ **Approval Workflow**: Approve or reject leave requests with comments
- ✅ **Team Analytics**: View team leave usage and patterns
- ✅ **Dual Interface**: Access both employee and supervisor views
- ✅ **Real-time Notifications**: See pending requests requiring approval

### Leave Types Supported:
- **PTO**: 21 days (regular) / 30 days (senior) - includes casual leave
- **PPTO**: 21 days personal paid time off
- **Paternal Leave**: 21 days maximum
- **Maternal Leave**: 90 days maximum
- **Bereavement**: 3 days per incident
- **Sick Leave**: 19 days (12 @ 100%, 7 @ 50%)

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Email-based with @tempo.fit domain restriction
- **Deployment**: Streamlit Cloud
- **Data Visualization**: Plotly charts and metrics

## 📋 Prerequisites

- Python 3.11+
- Supabase account
- @tempo.fit email addresses for users

## 🔧 Installation & Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd tempo-leave-management
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup (Supabase)
1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Copy your database URL from Settings > Database
4. Update the DATABASE_URL in `.streamlit/secrets.toml`

### 4. Local Testing
```bash
streamlit run app.py
```

## 🚀 Deployment to Streamlit Cloud

### 1. Push to GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set main file as `app.py`
4. Add secrets in the Streamlit Cloud dashboard:
   ```toml
   DATABASE_URL = "your-supabase-database-url"
   ```

### 3. Environment Variables
In Streamlit Cloud secrets, add:
```toml
DATABASE_URL = "postgresql://postgres:password@host:5432/database"
```

## 📊 Database Schema

The application uses the following main tables:
- `users`: Basic user information
- `user_profiles`: Employee details and hierarchy
- `leave_types`: Available leave types
- `leave_balances`: Employee leave allocations
- `leave_requests`: Leave applications and approvals

## 👥 User Management

### Demo Accounts:
- **Employee**: `hany@tempo.fit`
- **Supervisor**: `ossama@tempo.fit`

### Adding New Users:
1. Add user data to the `create_initial_data()` function in `database.py`
2. Users must have @tempo.fit email addresses
3. Set supervisor relationships in the user profiles

## 🔐 Authentication

- **Domain Restriction**: Only @tempo.fit email addresses
- **Role-Based Access**: Employee and Supervisor roles
- **Session Management**: Streamlit session state
- **Simple Login**: Email-based authentication for demo

## 📱 User Interface

### Employee Dashboard:
- Leave balance cards with progress indicators
- Recent requests table with status colors
- Quick action buttons for common tasks
- Profile information and service years

### Supervisor Dashboard:
- Team metrics and statistics
- Pending requests requiring approval
- Team member overview table
- Approval/rejection workflow

## 🔄 Workflow

1. **Employee submits leave request**
2. **System validates request** (dates, balance, requirements)
3. **Request sent to supervisor** for approval
4. **Supervisor reviews and approves/rejects**
5. **Leave balance automatically updated** on approval
6. **Employee receives status update**

## 🛡️ Security Features

- Domain-restricted email authentication
- Role-based access control
- Database connection security
- Input validation and sanitization
- Session management

## 📈 Analytics & Reporting

- Real-time leave balance tracking
- Team leave usage patterns
- Department-wise analytics
- Historical request data
- Approval workflow metrics

## 🎨 UI/UX Features

- Modern, clean interface
- Responsive design
- Color-coded status indicators
- Interactive charts and metrics
- Mobile-friendly layout

## 🔧 Configuration

### Leave Types Configuration:
Edit `leave_types` in `database.py` to modify:
- Leave type names
- Documentation requirements
- Reason requirements
- Approval workflow

### Balance Allocation:
Modify `create_initial_data()` to adjust:
- Default leave allocations
- Senior employee benefits
- Annual carry-over rules

## 🚀 Live Demo

Once deployed, the application will be available at:
`https://your-app-name.streamlit.app`

## 📞 Support

For technical support or questions:
- Email: hr@tempo.fit
- Internal contact: System Administrator

## 📄 License

Internal use only - Tempo.fit Company

---

**Built with ❤️ for Tempo.fit Team** 