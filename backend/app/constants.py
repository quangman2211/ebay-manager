"""
Application constants for eBay Manager system
"""

# GUEST Account Configuration
GUEST_ACCOUNT_CONFIG = {
    "USERNAME": "GUEST-ACCOUNT",
    "NAME": "System Guest Account",
    "PLATFORM_USERNAME": "system-guest",
    "ACCOUNT_TYPE": "system",
    "CONNECTION_STATUS": "system",
    "USER_ID": 1,  # System admin user
    "IS_DELETABLE": False,
    "IS_EDITABLE": False,
    "DESCRIPTION": "System account for preserving data from deleted accounts"
}

# Account Deletion Actions
class DeletionAction:
    TRANSFER_TO_GUEST = "transfer"
    PERMANENT_DELETE = "delete"

# System Account Types
class AccountType:
    EBAY = "ebay"
    ETSY = "etsy" 
    SYSTEM = "system"

# Connection Status Types
class ConnectionStatus:
    AUTHENTICATED = "authenticated"
    PENDING = "pending"
    EXPIRED = "expired"
    FAILED = "failed"
    SYSTEM = "system"