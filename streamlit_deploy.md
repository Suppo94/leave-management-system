# 🚀 Streamlit Cloud Deployment Guide

## Prerequisites
- GitHub account
- Streamlit Cloud account (free at https://share.streamlit.io/)
- Your leave management system files

## Step 1: Push to GitHub

```bash
# Initialize git repository (if not already done)
git init

# Add all files
git add .

# Commit changes
git commit -m "Initial commit - Leave Management System"

# Create repository on GitHub and add remote
git remote add origin https://github.com/YOUR_USERNAME/leave-management.git

# Push to GitHub
git push -u origin main
```

## Step 2: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit https://share.streamlit.io/
   - Click "Sign in with GitHub"
   - Authorize Streamlit Cloud

2. **Create New App**
   - Click "New app"
   - Select your GitHub repository
   - Choose branch: `main`
   - Main file path: `app.py`
   - App URL: Choose a unique name (e.g., `tempo-leave-management`)

3. **Configure Secrets**
   - Click "Advanced settings"
   - Add the following secrets:
   ```toml
   # For production with Supabase
   DATABASE_URL = "postgresql://postgres:Aa.01017234828!@db.wejbgeihnluhufvzdwee.supabase.co:5432/postgres"
   
   # App settings
   APP_NAME = "Leave Management System"
   COMPANY_NAME = "Tempo.fit"
   COMPANY_DOMAIN = "tempo.fit"
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete
   - Your app will be available at: `https://YOUR_APP_NAME.streamlit.app`

## Step 3: Test Production Deployment

1. **Access the App**
   - Open the deployed URL
   - Test login with any @tempo.fit email

2. **Verify Database**
   - Check if employee data is loaded
   - Test leave request submission
   - Test supervisor approval workflow

## Troubleshooting

### Database Connection Issues
If you get database connection errors:
1. Verify the DATABASE_URL in Streamlit Cloud secrets
2. Check if Supabase service is accessible
3. Ensure the database credentials are correct

### App Not Loading
If the app doesn't load:
1. Check the deployment logs in Streamlit Cloud
2. Verify all dependencies are in requirements.txt
3. Check for import errors in the logs

## Environment Variables (Alternative)

Instead of secrets, you can use environment variables:

```toml
# In Streamlit Cloud secrets
DATABASE_URL = "postgresql://postgres:Aa.01017234828!@db.wejbgeihnluhufvzdwee.supabase.co:5432/postgres"
PRODUCTION = "true"
```

## Success Checklist

- [ ] Repository pushed to GitHub
- [ ] App deployed to Streamlit Cloud
- [ ] Database URL configured in secrets
- [ ] App loads without errors
- [ ] Authentication works with @tempo.fit emails
- [ ] Employee data is populated
- [ ] Leave requests can be submitted
- [ ] Supervisor approvals work
- [ ] All features functional

## Support

If you encounter issues:
1. Check Streamlit Cloud logs
2. Verify database connectivity
3. Test locally first to isolate issues
4. Contact support if needed

Your app will be live at: `https://YOUR_CHOSEN_NAME.streamlit.app` 