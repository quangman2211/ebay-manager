"""
CSV Processing Schemas
Following SOLID principles - Single Responsibility for CSV data validation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class CSVFileStatus(str, Enum):
    """CSV file processing status"""
    UPLOADED = "uploaded"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    PROCESSING = "processing" 
    PROCESSED = "processed"
    FAILED = "failed"

class CSVValidationError(BaseModel):
    """
    CSV validation error schema
    Following SOLID: Single Responsibility for error reporting
    """
    row: int = Field(..., description="Row number where error occurred")
    column: Optional[str] = Field(None, description="Column name with error")
    error_type: str = Field(..., description="Type of validation error")
    message: str = Field(..., description="Human-readable error message")
    value: Optional[str] = Field(None, description="Invalid value that caused error")

class CSVUploadRequest(BaseModel):
    """
    CSV upload request schema
    Following SOLID: Single Responsibility for upload validation
    """
    file_type: str = Field(..., pattern="^(order|listing|product|customer)$")
    account_id: Optional[int] = Field(None, description="Associated eBay account ID")
    description: Optional[str] = Field(None, max_length=200)
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate supported file types"""
        allowed_types = ['order', 'listing', 'product', 'customer']
        if v not in allowed_types:
            raise ValueError(f'File type must be one of: {", ".join(allowed_types)}')
        return v

class CSVUploadResponse(BaseModel):
    """
    CSV upload response schema
    Following SOLID: Single Responsibility for upload response
    """
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    status: CSVFileStatus = Field(..., description="Current file status")
    upload_date: datetime = Field(..., description="Upload timestamp")
    preview_rows: int = Field(0, description="Number of rows available for preview")
    total_rows: Optional[int] = Field(None, description="Total rows in CSV")

class CSVValidationRequest(BaseModel):
    """
    CSV validation request schema
    Following SOLID: Single Responsibility for validation requests
    """
    file_id: str = Field(..., description="File ID to validate")
    skip_rows: int = Field(0, ge=0, le=10, description="Number of header rows to skip")
    column_mapping: Optional[Dict[str, str]] = Field(None, description="Custom column mapping")

class CSVValidationResponse(BaseModel):
    """
    CSV validation response schema  
    Following SOLID: Single Responsibility for validation results
    """
    file_id: str = Field(..., description="File identifier")
    status: CSVFileStatus = Field(..., description="Validation status")
    is_valid: bool = Field(..., description="Whether CSV is valid")
    total_rows: int = Field(..., description="Total number of rows")
    valid_rows: int = Field(..., description="Number of valid rows")
    errors: List[CSVValidationError] = Field(default=[], description="Validation errors")
    warnings: List[str] = Field(default=[], description="Non-critical warnings")
    detected_columns: List[str] = Field(default=[], description="Detected column headers")
    sample_data: List[Dict[str, Any]] = Field(default=[], description="Sample valid rows")

class CSVPreviewRequest(BaseModel):
    """
    CSV preview request schema
    Following SOLID: Single Responsibility for preview requests
    """
    file_id: str = Field(..., description="File ID to preview")
    start_row: int = Field(0, ge=0, description="Starting row for preview")
    limit: int = Field(10, ge=1, le=100, description="Number of rows to preview")

class CSVPreviewResponse(BaseModel):
    """
    CSV preview response schema
    Following SOLID: Single Responsibility for preview data
    """
    file_id: str = Field(..., description="File identifier")
    headers: List[str] = Field(..., description="CSV column headers")
    rows: List[List[str]] = Field(..., description="Preview data rows")
    total_rows: int = Field(..., description="Total rows in file")
    has_more: bool = Field(..., description="Whether more rows are available")

class CSVProcessRequest(BaseModel):
    """
    CSV processing request schema
    Following SOLID: Single Responsibility for processing requests
    """
    file_id: str = Field(..., description="File ID to process")
    import_mode: str = Field("insert", pattern="^(insert|update|upsert)$")
    batch_size: int = Field(1000, ge=10, le=5000, description="Processing batch size")
    dry_run: bool = Field(False, description="Validate only, don't import data")
    
    @validator('import_mode')
    def validate_import_mode(cls, v):
        """Validate import mode"""
        allowed_modes = ['insert', 'update', 'upsert']
        if v not in allowed_modes:
            raise ValueError(f'Import mode must be one of: {", ".join(allowed_modes)}')
        return v

class CSVProcessResponse(BaseModel):
    """
    CSV processing response schema
    Following SOLID: Single Responsibility for processing results
    """
    file_id: str = Field(..., description="File identifier")
    status: CSVFileStatus = Field(..., description="Processing status")
    records_processed: int = Field(0, description="Number of records processed")
    records_inserted: int = Field(0, description="Number of records inserted")
    records_updated: int = Field(0, description="Number of records updated")
    records_skipped: int = Field(0, description="Number of records skipped")
    errors: List[CSVValidationError] = Field(default=[], description="Processing errors")
    processing_time_seconds: float = Field(0.0, description="Total processing time")
    started_at: datetime = Field(..., description="Processing start time")
    completed_at: Optional[datetime] = Field(None, description="Processing completion time")

class CSVFileInfo(BaseModel):
    """
    CSV file information schema
    Following SOLID: Single Responsibility for file metadata
    """
    file_id: str = Field(..., description="File identifier")
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="Type of CSV file")
    file_size: int = Field(..., description="File size in bytes")
    status: CSVFileStatus = Field(..., description="Current file status")
    account_id: Optional[int] = Field(None, description="Associated account ID")
    upload_date: datetime = Field(..., description="Upload timestamp")
    last_modified: datetime = Field(..., description="Last modification time")
    total_rows: Optional[int] = Field(None, description="Total rows in CSV")
    description: Optional[str] = Field(None, description="File description")

class CSVColumnMapping(BaseModel):
    """
    CSV column mapping schema
    Following SOLID: Single Responsibility for column mapping
    """
    csv_column: str = Field(..., description="CSV column name")
    target_field: str = Field(..., description="Target database field")
    is_required: bool = Field(False, description="Whether field is required")
    data_type: str = Field("string", description="Expected data type")
    validation_rules: List[str] = Field(default=[], description="Validation rules")

class GenericCSVRow(BaseModel):
    """
    Generic CSV row for validation
    Following SOLID: Single Responsibility for row validation
    """
    row_number: int = Field(..., description="Row number in CSV")
    data: Dict[str, Any] = Field(..., description="Row data")
    is_valid: bool = Field(True, description="Whether row is valid")
    errors: List[str] = Field(default=[], description="Row validation errors")
    
    class Config:
        arbitrary_types_allowed = True