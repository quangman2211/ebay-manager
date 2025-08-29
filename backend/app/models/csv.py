"""
CSV Upload Database Model
Following SOLID principles - Single Responsibility for CSV upload data management
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel

class CSVUpload(BaseModel):
    """
    CSV Upload model for tracking uploaded CSV files
    Following SOLID: Single Responsibility for CSV upload data structure
    """
    
    __tablename__ = 'csv_uploads'
    
    # Basic upload information
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # orders, listings, products, etc.
    
    # Processing information
    batch_id = Column(String(100), nullable=False, index=True)
    status = Column(String(50), default='uploaded', nullable=False)  # uploaded, processing, completed, failed
    
    # Processing results
    total_rows = Column(Integer, nullable=True)
    processed_rows = Column(Integer, nullable=True)
    success_rows = Column(Integer, nullable=True)
    error_rows = Column(Integer, nullable=True)
    
    # Validation and processing details
    validation_errors = Column(JSON, nullable=True)  # List of validation errors
    processing_summary = Column(JSON, nullable=True)  # Processing statistics
    error_message = Column(Text, nullable=True)  # Error message if processing failed
    
    # Metadata
    description = Column(String(500), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    account = relationship("Account", back_populates="csv_uploads", lazy="select")
    user = relationship("User", back_populates="csv_uploads", lazy="select")
    
    def __repr__(self):
        return f"<CSVUpload(id={self.id}, filename={self.original_filename}, status={self.status})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if upload processing is completed"""
        return self.status in ['completed', 'failed']
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if not self.total_rows or self.total_rows == 0:
            return 0.0
        return (self.success_rows or 0) / self.total_rows * 100