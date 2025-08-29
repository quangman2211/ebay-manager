"""
User Model for Authentication
Following SOLID principles - Single Responsibility for user data management
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func, CheckConstraint, text
from sqlalchemy.orm import relationship
from .base import BaseModel

class User(BaseModel):
    """
    User model for authentication and authorization
    Following SOLID: Single Responsibility for user data
    """
    __tablename__ = "users"
    
    # Authentication Fields
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User Information
    first_name = Column(String(50))
    last_name = Column(String(50))
    role = Column(String(20), default='user', nullable=False, index=True)
    
    # Account Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True))
    
    # Relationships (imported lazily to avoid circular imports)
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan", lazy="select")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(username) >= 3', name='users_username_length'),
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", 
            name='users_email_format'
        ),
        CheckConstraint("role IN ('admin', 'user')", name='users_role_check'),
    )
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"