#!/usr/bin/env python3
"""
Script to create a superuser for the admin panel.
Usage: python create_superuser.py
"""

import sys
from getpass import getpass
from app.database import get_db
from app.models import User
from app.auth.hashing import hash_password


def create_superuser():
    """Interactive script to create a superuser"""
    print("=" * 50)
    print("Create Superuser for Admin Panel")
    print("=" * 50)
    
    # Get user details
    name = input("\nEnter name: ").strip()
    if not name:
        print("❌ Name cannot be empty")
        return
    
    email = input("Enter email: ").strip()
    if not email:
        print("❌ Email cannot be empty")
        return
    
    country = input("Enter country (e.g., US, UK, IN): ").strip() or "US"
    
    password = getpass("Enter password: ")
    if not password:
        print("❌ Password cannot be empty")
        return
    
    password_confirm = getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match")
        return
    
    # Create the superuser
    db = next(get_db())
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"\n⚠️  User with email '{email}' already exists!")
            update = input("Update to superuser? (y/n): ").strip().lower()
            if update == 'y':
                existing_user.is_superuser = True
                existing_user.isactive = True
                if password:
                    existing_user.password = hash_password(password)
                db.commit()
                print(f"✅ User '{email}' updated to superuser successfully!")
            else:
                print("❌ Operation cancelled")
            return
        
        # Create new superuser
        superuser = User(
            name=name,
            email=email,
            password=hash_password(password),
            country=country,
            isactive=True,
            is_superuser=True
        )
        
        db.add(superuser)
        db.commit()
        
        print("\n" + "=" * 50)
        print("✅ Superuser created successfully!")
        print("=" * 50)
        print(f"Name: {name}")
        print(f"Email: {email}")
        print(f"Country: {country}")
        print(f"Is Superuser: True")
        print(f"Is Active: True")
        print("\nYou can now login to /admin with these credentials.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error creating superuser: {str(e)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_superuser()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(0)
