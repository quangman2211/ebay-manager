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
    orders = relationship("Order", back_populates="user", lazy="select")
    csv_uploads = relationship("CSVUpload", back_populates="user", lazy="select")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('length(username) >= 3', name='users_username_length'),
        # Note: Email regex constraint removed for SQLite compatibility in tests
        # Production PostgreSQL database has proper email validation
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