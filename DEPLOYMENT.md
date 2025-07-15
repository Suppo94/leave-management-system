# Leave Management System - Deployment Guide

## 🚀 Deployment Options

### Option 1: Streamlit Cloud (Recommended)

**Prerequisites:**
- GitHub account
- Streamlit Cloud account (free at https://share.streamlit.io/)

**Steps:**

1. **Push code to GitHub repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/leave-management.git
   git push -u origin main
   ```

2. **Deploy to Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Click "New app"
   - Connect your GitHub repository
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Configure Database (Production)**
   - In Streamlit Cloud, go to your app settings
   - Add secret variables:
     ```
     DATABASE_URL = "postgresql://postgres:Aa.01017234828!@db.wejbgeihnluhufvzdwee.supabase.co:5432/postgres"
     ```

### Option 2: Heroku

**Prerequisites:**
- Heroku account
- Heroku CLI installed

**Steps:**

1. **Create Heroku app**
   ```bash
   heroku create your-app-name
   ```

2. **Set environment variables**
   ```bash
   heroku config:set DATABASE_URL="postgresql://postgres:Aa.01017234828!@db.wejbgeihnluhufvzdwee.supabase.co:5432/postgres"
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

### Option 3: Railway

**Prerequisites:**
- Railway account (https://railway.app/)
- GitHub repository

**Steps:**

1. **Connect GitHub repository**
   - Login to Railway
   - Create new project
   - Connect GitHub repository

2. **Set environment variables**
   ```
   DATABASE_URL = postgresql://postgres:Aa.01017234828!@db.wejbgeihnluhufvzdwee.supabase.co:5432/postgres
   ```

3. **Deploy automatically**
   - Railway will automatically build and deploy

## 🛠️ Local Development

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/leave-management.git
cd leave-management

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

### Local Database
- Uses SQLite by default for local development
- Database file: `leave_management.db`
- Automatically creates tables and sample data

## 🔧 Configuration

### Database Configuration
- **Local**: Uses SQLite (`sqlite:///leave_management.db`)
- **Production**: Uses PostgreSQL (Supabase)
- **Configuration**: Set `DATABASE_URL` environment variable

### Application Settings
- **Company**: Tempo.fit
- **Domain**: tempo.fit
- **Authentication**: Email-based (Google OAuth ready)

## 📋 Features

### Employee Dashboard
- View leave balances
- Submit leave requests
- View request history
- Profile management

### Supervisor Dashboard
- View team member balances
- Approve/reject leave requests
- Team analytics
- Department overview

### Admin Features
- Employee management
- Leave type configuration
- Balance adjustments
- System settings

## 🚨 Troubleshooting

### Common Issues

1. **Database connection error**
   - Check DATABASE_URL environment variable
   - Verify database credentials
   - Ensure database is accessible

2. **Missing dependencies**
   - Run `pip install -r requirements.txt`
   - Check Python version compatibility

3. **Deployment fails**
   - Check logs in deployment platform
   - Verify all required files are committed
   - Check environment variables

### Support
For issues and questions, please create an issue in the GitHub repository.

## 📝 Next Steps

1. **Configure Google OAuth** (Optional)
   - Set up Google Cloud Console
   - Configure OAuth consent screen
   - Add client credentials

2. **Set up Email Notifications** (Optional)
   - Configure SMTP settings
   - Set up email templates

3. **Customize Branding**
   - Update company logo
   - Customize color scheme
   - Add company-specific policies 