#!/usr/bin/env python3
"""
Setup script to initialize the eBay Manager database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.init_db import create_tables, create_admin_user

if __name__ == "__main__":
    print("Setting up eBay Manager database...")
    create_tables()
    create_admin_user()
    print("Setup complete!")