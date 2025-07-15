#!/usr/bin/env python3
"""
Deployment helper script for Leave Management System
"""

import os
import sys
import subprocess
import argparse

def test_supabase_connection():
    """Test Supabase PostgreSQL connection"""
    print("🔍 Testing Supabase connection...")
    
    # Set environment variable for production
    os.environ['PRODUCTION'] = 'true'
    
    try:
        from database import init_database, create_initial_data
        print("✅ Database imports successful")
        
        # Test connection
        init_database()
        print("✅ Database connection successful")
        
        # Create initial data
        create_initial_data()
        print("✅ Initial data created successfully")
        
        print("\n🎉 Supabase connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection test FAILED: {e}")
        print("\n💡 Suggestions:")
        print("1. Check your internet connection")
        print("2. Verify Supabase credentials")
        print("3. Try from a different network")
        print("4. Deploy to production where network might be different")
        return False

def test_local_connection():
    """Test local SQLite connection"""
    print("🔍 Testing local SQLite connection...")
    
    # Remove production flag
    os.environ.pop('PRODUCTION', None)
    
    try:
        from database import init_database, create_initial_data
        print("✅ Database imports successful")
        
        # Test connection
        init_database()
        print("✅ Local database connection successful")
        
        # Create initial data
        create_initial_data()
        print("✅ Initial data created successfully")
        
        print("\n🎉 Local connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Local connection test FAILED: {e}")
        return False

def setup_github():
    """Guide user through GitHub setup"""
    print("📋 GitHub Setup Guide:")
    print("=" * 50)
    
    print("1. Create a new repository on GitHub:")
    print("   - Go to https://github.com/new")
    print("   - Repository name: leave-management-system")
    print("   - Description: Leave Management System for Tempo.fit")
    print("   - Set to Public (required for free Streamlit Cloud)")
    print("   - Don't initialize with README (we already have files)")
    
    print("\n2. After creating the repository, run these commands:")
    print("   git remote add origin https://github.com/YOUR_USERNAME/leave-management-system.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    
    print("\n3. Your repository will be ready for deployment!")

def deploy_streamlit():
    """Guide user through Streamlit Cloud deployment"""
    print("🚀 Streamlit Cloud Deployment Guide:")
    print("=" * 50)
    
    print("1. Go to https://share.streamlit.io/")
    print("2. Sign in with your GitHub account")
    print("3. Click 'New app'")
    print("4. Select your repository: leave-management-system")
    print("5. Branch: main")
    print("6. Main file path: app.py")
    print("7. Advanced settings -> Add these secrets:")
    print("   DATABASE_URL = postgresql://postgres:Aa.01017234828!@db.wejbgeihnluhufvzdwee.supabase.co:5432/postgres")
    print("   PRODUCTION = true")
    print("8. Click 'Deploy'")
    print("9. Wait for deployment to complete")
    
    print("\n✅ Your app will be live at: https://your-app-name.streamlit.app")

def run_local():
    """Run the application locally"""
    print("🏃 Running application locally...")
    
    # Remove production flag
    os.environ.pop('PRODUCTION', None)
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run Streamlit: {e}")
        print("💡 Try: python -m streamlit run app.py")

def main():
    parser = argparse.ArgumentParser(description="Leave Management System Deployment Helper")
    parser.add_argument("action", choices=[
        "test-supabase", "test-local", "setup-github", "deploy-streamlit", "run-local"
    ], help="Action to perform")
    
    args = parser.parse_args()
    
    print("🏢 Leave Management System - Deployment Helper")
    print("=" * 50)
    
    if args.action == "test-supabase":
        test_supabase_connection()
    elif args.action == "test-local":
        test_local_connection()
    elif args.action == "setup-github":
        setup_github()
    elif args.action == "deploy-streamlit":
        deploy_streamlit()
    elif args.action == "run-local":
        run_local()

if __name__ == "__main__":
    main() 