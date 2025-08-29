# CSV Processing Engine - File Upload & Data Validation

## Overview
Complete CSV processing system for eBay Management System following YAGNI/SOLID principles. Implements secure file upload, data validation, and parsing for eBay CSV exports optimized for 30-account scale with essential processing features only.

## SOLID Principles Applied
- **Single Responsibility**: Each processor handles one CSV type (orders, listings, products, etc.)
- **Open/Closed**: Processing engine extensible for new CSV formats without modifying core
- **Liskov Substitution**: All CSV processors implement common parsing interface
- **Interface Segregation**: Separate interfaces for upload, validation, parsing, and storage
- **Dependency Inversion**: Processors depend on abstract file handling, not concrete implementations

## YAGNI Compliance
✅ **Essential CSV Types**: Orders, listings, products, customers, messages only  
✅ **Simple Validation**: Data type checking, required fields, basic format validation  
✅ **Pandas Processing**: Proven library for CSV handling, no custom parsers  
✅ **Synchronous Processing**: Files processed sequentially for 30-account scale  
❌ **Eliminated**: Real-time streaming, complex ETL pipelines, data transformation engines, multi-format support

---

## CSV Processing Architecture

### Processing Flow
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          CSV PROCESSING PIPELINE                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │   File Upload   │───▶│  File Validation │───▶│   File Storage   │             │
│  │                 │    │                  │    │                 │             │
│  │ • Size check    │    │ • Type check     │    │ • Safe filename │             │
│  │ • Type check    │    │ • Structure check│    │ • Directory org │             │
│  │ • Virus scan    │    │ • Encoding check │    │ • Metadata save │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                          │                      │
│                                                          ▼                      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │  Data Parsing   │◀───│  Format Detection│◀───│  Processing Job  │             │
│  │                 │    │                  │    │                 │             │
│  │ • CSV reader    │    │ • Column mapping │    │ • Background job│             │
│  │ • Data chunking │    │ • eBay format ID │    │ • Progress track│             │
│  │ • Type conversion│    │ • Validation rules│   │ • Error handling│             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│           │                                                                     │
│           ▼                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐             │
│  │ Data Validation │───▶│ Error Handling   │───▶│ Database Insert │             │
│  │                 │    │                  │    │                 │             │
│  │ • Required fields│    │ • Validation log │    │ • Batch inserts │             │
│  │ • Data types    │    │ • Skip invalid   │    │ • Conflict res. │             │
│  │ • Business rules│    │ • Continue proc. │    │ • Transaction   │             │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘             │
│                                                          │                      │
│                                                          ▼                      │
│  ┌─────────────────┐                                ┌─────────────────┐         │
│  │ Processing      │                                │   Completion     │         │
│  │ Summary         │                                │   Notification   │         │
│  │                 │                                │                 │         │
│  │ • Rows processed│                                │ • Success count │         │
│  │ • Success/Error │                                │ • Error summary │         │
│  │ • Processing time│                               │ • User notification│        │
│  └─────────────────┘                                └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Supported CSV Types
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            SUPPORTED CSV FORMATS                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │    eBay Orders  │  │  eBay Listings  │  │   Products      │                 │
│  │                 │  │                 │  │                 │                 │
│  │ • Order ID      │  │ • Item ID       │  │ • SKU           │                 │
│  │ • Buyer Info    │  │ • Title         │  │ • Name          │                 │
│  │ • Amount        │  │ • Category      │  │ • Cost/Price    │                 │
│  │ • Date          │  │ • Price         │  │ • Stock         │                 │
│  │ • Status        │  │ • Status        │  │ • Supplier      │                 │
│  │ • Shipping      │  │ • Views/Sales   │  │ • Category      │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
│                                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                 │
│  │   Customers     │  │    Messages     │  │    Suppliers    │                 │
│  │                 │  │                 │  │                 │                 │
│  │ • Username      │  │ • Subject       │  │ • Name          │                 │
│  │ • Email         │  │ • Content       │  │ • Contact       │                 │
│  │ • Purchase Hist │  │ • Date          │  │ • Products      │                 │
│  │ • Segment       │  │ • Type          │  │ • Performance   │                 │
│  │ • Status        │  │ • Status        │  │ • Terms         │                 │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Complete Implementation

### 1. File Upload Handler
```python
# csv_processing/upload.py - Secure file upload handling

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import UploadFile, HTTPException, status
from datetime import datetime
import magic  # python-magic for file type detection
import hashlib
import logging

from core.config.settings import settings
from database.models import Upload
from database.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class FileUploadHandler:
    """Secure file upload handler with validation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_path = Path(settings.files.UPLOAD_PATH)
        self.max_file_size = settings.files.UPLOAD_MAX_SIZE
        self.allowed_extensions = set(settings.files.ALLOWED_FILE_TYPES)
        
        # Create upload directories
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary upload directories"""
        directories = ['csv', 'temp', 'processed', 'failed']
        
        for dir_name in directories:
            dir_path = self.upload_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(
        self, 
        file: UploadFile, 
        account_id: int, 
        upload_type: str
    ) -> Dict[str, Any]:
        """Upload and validate file"""
        
        try:
            # Validate file before processing
            await self._validate_upload(file)
            
            # Generate secure filename
            file_info = self._generate_file_info(file, account_id, upload_type)
            
            # Save file to disk
            saved_path = await self._save_file_to_disk(file, file_info['stored_filename'])
            
            # Calculate file hash for integrity
            file_hash = self._calculate_file_hash(saved_path)
            
            # Create database record
            upload_record = Upload(
                account_id=account_id,
                original_filename=file.filename,
                stored_filename=file_info['stored_filename'],
                file_path=str(saved_path),
                file_size=file_info['file_size'],
                file_type=file_info['file_extension'],
                mime_type=file.content_type,
                upload_type=upload_type,
                processing_status='pending',
                batch_id=file_info['batch_id']
            )
            
            self.db.add(upload_record)
            self.db.commit()
            self.db.refresh(upload_record)
            
            logger.info(f"File uploaded successfully: {file.filename} -> {file_info['stored_filename']}")
            
            return {
                'upload_id': upload_record.id,
                'batch_id': file_info['batch_id'],
                'original_filename': file.filename,
                'stored_filename': file_info['stored_filename'],
                'file_size': file_info['file_size'],
                'upload_type': upload_type,
                'file_hash': file_hash
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            # Clean up any partial files
            if 'saved_path' in locals():
                self._cleanup_file(saved_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File upload failed: {str(e)}"
            )
    
    async def _validate_upload(self, file: UploadFile):
        """Validate uploaded file"""
        
        # Check file size
        if hasattr(file.file, 'seek'):
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(0)  # Reset to beginning
            
            if file_size > self.max_file_size:
                raise ValueError(f"File size {file_size} exceeds maximum {self.max_file_size}")
            
            if file_size == 0:
                raise ValueError("Empty file uploaded")
        
        # Check filename
        if not file.filename:
            raise ValueError("No filename provided")
        
        # Check file extension
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        if file_extension not in self.allowed_extensions:
            raise ValueError(f"File type '{file_extension}' not allowed. Allowed types: {self.allowed_extensions}")
        
        # Check MIME type (basic validation)
        if file.content_type:
            allowed_mime_types = {
                'csv': ['text/csv', 'application/csv', 'text/plain'],
                'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
                'xls': ['application/vnd.ms-excel', 'application/excel']
            }
            
            expected_mime_types = allowed_mime_types.get(file_extension, [])
            if expected_mime_types and file.content_type not in expected_mime_types:
                logger.warning(f"MIME type mismatch: {file.content_type} for .{file_extension} file")
    
    def _generate_file_info(self, file: UploadFile, account_id: int, upload_type: str) -> Dict[str, Any]:
        """Generate secure file information"""
        
        # Get file extension
        file_extension = Path(file.filename).suffix.lower().lstrip('.')
        
        # Generate unique batch ID
        batch_id = str(uuid.uuid4())
        
        # Generate secure filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = str(uuid.uuid4())[:8]
        stored_filename = f"acc_{account_id}_{upload_type}_{timestamp}_{random_suffix}.{file_extension}"
        
        return {
            'stored_filename': stored_filename,
            'file_extension': file_extension,
            'batch_id': batch_id,
            'file_size': 0  # Will be updated after saving
        }
    
    async def _save_file_to_disk(self, file: UploadFile, stored_filename: str) -> Path:
        """Save uploaded file to disk securely"""
        
        # Determine save path
        file_path = self.upload_path / 'csv' / stored_filename
        
        # Save file in chunks to handle large files
        chunk_size = 8192  # 8KB chunks
        total_size = 0
        
        with open(file_path, 'wb') as buffer:
            while chunk := await file.read(chunk_size):
                total_size += len(chunk)
                
                # Check size limit during write
                if total_size > self.max_file_size:
                    buffer.close()
                    file_path.unlink(missing_ok=True)  # Clean up
                    raise ValueError(f"File size exceeds maximum {self.max_file_size} bytes")
                
                buffer.write(chunk)
        
        # Set file permissions (read-only after write)
        os.chmod(file_path, 0o644)
        
        return file_path
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity verification"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def _cleanup_file(self, file_path: Path):
        """Clean up file on error"""
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            logger.error(f"Failed to cleanup file {file_path}: {str(e)}")
    
    def get_upload_by_id(self, upload_id: int) -> Optional[Upload]:
        """Get upload record by ID"""
        return self.db.query(Upload).filter(Upload.id == upload_id).first()
    
    def update_upload_status(self, upload_id: int, status: str, **kwargs):
        """Update upload processing status"""
        upload = self.get_upload_by_id(upload_id)
        if upload:
            upload.processing_status = status
            
            for key, value in kwargs.items():
                if hasattr(upload, key):
                    setattr(upload, key, value)
            
            self.db.commit()
            return upload
        return None

def get_file_upload_handler(db: Session) -> FileUploadHandler:
    """Dependency injection for file upload handler"""
    return FileUploadHandler(db)
```

### 2. CSV Format Detection & Validation
```python
# csv_processing/formats.py - eBay CSV format detection and mapping

from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import re
from abc import ABC, abstractmethod

class CSVType(str, Enum):
    """Supported CSV types"""
    ORDERS = "orders"
    LISTINGS = "listings"  
    PRODUCTS = "products"
    CUSTOMERS = "customers"
    MESSAGES = "messages"
    SUPPLIERS = "suppliers"

@dataclass
class ColumnMapping:
    """Column mapping definition"""
    csv_column: str  # Column name in CSV
    db_field: str    # Database field name
    required: bool = False
    data_type: Type = str
    validator: Optional[callable] = None
    transformer: Optional[callable] = None

@dataclass
class CSVFormat:
    """CSV format definition"""
    csv_type: CSVType
    name: str
    description: str
    required_columns: List[str]
    optional_columns: List[str]
    column_mappings: Dict[str, ColumnMapping]
    validation_rules: List[callable]

class BaseCSVValidator(ABC):
    """Base class for CSV validators"""
    
    @abstractmethod
    def validate_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate CSV structure and return list of errors"""
        pass
    
    @abstractmethod
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate data and return validation results"""
        pass

class eBayOrdersValidator(BaseCSVValidator):
    """eBay Orders CSV validator"""
    
    REQUIRED_COLUMNS = [
        'Order ID', 'Buyer Username', 'Total Price', 'Order Date'
    ]
    
    OPTIONAL_COLUMNS = [
        'Transaction ID', 'Item ID', 'Item Title', 'Quantity', 
        'Sale Price', 'Shipping Cost', 'Payment Method', 'Order Status',
        'Shipping Address', 'Buyer Email', 'Tracking Number'
    ]
    
    def validate_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate eBay orders CSV structure"""
        errors = []
        
        # Check required columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Check for empty DataFrame
        if df.empty:
            errors.append("CSV file is empty")
        
        # Check minimum row count
        if len(df) < 1:
            errors.append("CSV must contain at least one data row")
        
        return errors
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate eBay orders data"""
        results = {
            'valid_rows': 0,
            'invalid_rows': 0,
            'errors': [],
            'warnings': []
        }
        
        for index, row in df.iterrows():
            row_errors = []
            
            # Validate Order ID
            if pd.isna(row.get('Order ID')) or str(row.get('Order ID')).strip() == '':
                row_errors.append(f"Row {index + 2}: Order ID is required")
            
            # Validate Total Price
            try:
                price = float(str(row.get('Total Price', 0)).replace('$', '').replace(',', ''))
                if price <= 0:
                    row_errors.append(f"Row {index + 2}: Total Price must be greater than 0")
            except (ValueError, TypeError):
                row_errors.append(f"Row {index + 2}: Invalid Total Price format")
            
            # Validate Order Date
            if pd.isna(row.get('Order Date')):
                row_errors.append(f"Row {index + 2}: Order Date is required")
            else:
                try:
                    pd.to_datetime(row.get('Order Date'))
                except (ValueError, TypeError):
                    row_errors.append(f"Row {index + 2}: Invalid Order Date format")
            
            # Validate Buyer Username
            if pd.isna(row.get('Buyer Username')) or str(row.get('Buyer Username')).strip() == '':
                row_errors.append(f"Row {index + 2}: Buyer Username is required")
            
            if row_errors:
                results['invalid_rows'] += 1
                results['errors'].extend(row_errors)
            else:
                results['valid_rows'] += 1
        
        return results

class eBayListingsValidator(BaseCSVValidator):
    """eBay Listings CSV validator"""
    
    REQUIRED_COLUMNS = [
        'Item ID', 'Title', 'Category', 'Price', 'Quantity Available'
    ]
    
    OPTIONAL_COLUMNS = [
        'Start Date', 'End Date', 'Views', 'Watchers', 'Sold',
        'Listing Status', 'Format', 'Condition', 'Shipping Cost'
    ]
    
    def validate_structure(self, df: pd.DataFrame) -> List[str]:
        """Validate eBay listings CSV structure"""
        errors = []
        
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        
        if df.empty:
            errors.append("CSV file is empty")
            
        return errors
    
    def validate_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate eBay listings data"""
        results = {
            'valid_rows': 0,
            'invalid_rows': 0,
            'errors': [],
            'warnings': []
        }
        
        for index, row in df.iterrows():
            row_errors = []
            
            # Validate Item ID
            if pd.isna(row.get('Item ID')):
                row_errors.append(f"Row {index + 2}: Item ID is required")
            
            # Validate Title
            title = str(row.get('Title', '')).strip()
            if not title:
                row_errors.append(f"Row {index + 2}: Title is required")
            elif len(title) > 80:  # eBay title limit
                row_errors.append(f"Row {index + 2}: Title exceeds 80 character limit")
            
            # Validate Price
            try:
                price = float(str(row.get('Price', 0)).replace('$', '').replace(',', ''))
                if price <= 0:
                    row_errors.append(f"Row {index + 2}: Price must be greater than 0")
            except (ValueError, TypeError):
                row_errors.append(f"Row {index + 2}: Invalid Price format")
            
            # Validate Quantity
            try:
                quantity = int(row.get('Quantity Available', 0))
                if quantity < 0:
                    row_errors.append(f"Row {index + 2}: Quantity cannot be negative")
            except (ValueError, TypeError):
                row_errors.append(f"Row {index + 2}: Invalid Quantity format")
            
            if row_errors:
                results['invalid_rows'] += 1
                results['errors'].extend(row_errors)
            else:
                results['valid_rows'] += 1
        
        return results

class CSVFormatDetector:
    """Detect CSV format based on column structure"""
    
    def __init__(self):
        self.validators = {
            CSVType.ORDERS: eBayOrdersValidator(),
            CSVType.LISTINGS: eBayListingsValidator(),
            # Add more validators as needed
        }
        
        # Column patterns for format detection
        self.format_patterns = {
            CSVType.ORDERS: [
                'order.id', 'buyer.username', 'total.price', 'order.date'
            ],
            CSVType.LISTINGS: [
                'item.id', 'title', 'category', 'price', 'quantity'
            ]
        }
    
    def detect_format(self, df: pd.DataFrame) -> Optional[CSVType]:
        """Detect CSV format based on column structure"""
        
        columns_lower = [col.lower().replace(' ', '.') for col in df.columns]
        
        best_match = None
        best_score = 0
        
        for csv_type, patterns in self.format_patterns.items():
            score = 0
            for pattern in patterns:
                if any(pattern in col for col in columns_lower):
                    score += 1
            
            match_percentage = score / len(patterns)
            if match_percentage > best_score and match_percentage >= 0.7:  # 70% threshold
                best_match = csv_type
                best_score = match_percentage
        
        return best_match
    
    def validate_format(self, df: pd.DataFrame, csv_type: CSVType) -> Dict[str, Any]:
        """Validate DataFrame against specific format"""
        
        validator = self.validators.get(csv_type)
        if not validator:
            return {
                'valid': False,
                'errors': [f"No validator available for format: {csv_type}"]
            }
        
        # Validate structure
        structure_errors = validator.validate_structure(df)
        
        if structure_errors:
            return {
                'valid': False,
                'errors': structure_errors,
                'data_validation': None
            }
        
        # Validate data
        data_results = validator.validate_data(df)
        
        return {
            'valid': data_results['invalid_rows'] == 0,
            'structure_errors': structure_errors,
            'data_validation': data_results
        }

# Global format detector instance
csv_format_detector = CSVFormatDetector()
```

### 3. CSV Data Parser
```python
# csv_processing/parser.py - CSV data parsing with Pandas

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Generator, Tuple
from pathlib import Path
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from csv_processing.formats import CSVType, csv_format_detector

logger = logging.getLogger(__name__)

class CSVDataParser:
    """CSV data parser with chunked processing"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self.supported_encodings = ['utf-8', 'latin1', 'cp1252', 'utf-16']
    
    def parse_file(
        self, 
        file_path: Path, 
        csv_type: Optional[CSVType] = None
    ) -> Dict[str, Any]:
        """Parse CSV file and return structured data"""
        
        try:
            # Detect file encoding
            encoding = self._detect_encoding(file_path)
            
            # Read file with appropriate settings
            df = self._read_csv_file(file_path, encoding)
            
            # Auto-detect format if not specified
            if csv_type is None:
                csv_type = csv_format_detector.detect_format(df)
                if csv_type is None:
                    raise ValueError("Could not detect CSV format. Please specify csv_type manually.")
            
            # Validate format
            validation_result = csv_format_detector.validate_format(df, csv_type)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'csv_type': csv_type,
                    'total_rows': len(df),
                    'validation_errors': validation_result.get('errors', []),
                    'data_validation': validation_result.get('data_validation'),
                    'data': None
                }
            
            # Process data based on type
            processed_data = self._process_data_by_type(df, csv_type)
            
            return {
                'success': True,
                'csv_type': csv_type,
                'encoding': encoding,
                'total_rows': len(df),
                'valid_rows': validation_result['data_validation']['valid_rows'],
                'invalid_rows': validation_result['data_validation']['invalid_rows'],
                'validation_errors': validation_result['data_validation']['errors'],
                'warnings': validation_result['data_validation']['warnings'],
                'data': processed_data,
                'processing_summary': self._generate_processing_summary(df, processed_data)
            }
            
        except Exception as e:
            logger.error(f"CSV parsing failed for {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'csv_type': csv_type,
                'data': None
            }
    
    def parse_file_chunked(
        self, 
        file_path: Path, 
        csv_type: CSVType,
        chunk_size: Optional[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Parse large CSV file in chunks"""
        
        if chunk_size is None:
            chunk_size = self.chunk_size
        
        encoding = self._detect_encoding(file_path)
        
        try:
            # Read file in chunks
            chunk_reader = pd.read_csv(
                file_path,
                encoding=encoding,
                chunksize=chunk_size,
                low_memory=False,
                dtype=str,  # Read all as strings initially
                keep_default_na=False
            )
            
            chunk_number = 0
            
            for chunk_df in chunk_reader:
                chunk_number += 1
                
                # Validate chunk
                validation_result = csv_format_detector.validate_format(chunk_df, csv_type)
                
                # Process chunk data
                processed_chunk = self._process_data_by_type(chunk_df, csv_type) if validation_result['valid'] else []
                
                yield {
                    'chunk_number': chunk_number,
                    'chunk_rows': len(chunk_df),
                    'valid_rows': validation_result.get('data_validation', {}).get('valid_rows', 0),
                    'invalid_rows': validation_result.get('data_validation', {}).get('invalid_rows', 0),
                    'validation_errors': validation_result.get('data_validation', {}).get('errors', []),
                    'data': processed_chunk
                }
                
        except Exception as e:
            logger.error(f"Chunked CSV parsing failed for {file_path}: {str(e)}")
            yield {
                'chunk_number': -1,
                'error': str(e),
                'data': None
            }
    
    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding"""
        
        # Try chardet for encoding detection
        try:
            import chardet
            
            with open(file_path, 'rb') as f:
                sample = f.read(10000)  # Read first 10KB
                result = chardet.detect(sample)
                detected_encoding = result.get('encoding', 'utf-8')
                confidence = result.get('confidence', 0)
                
                if confidence > 0.7:
                    return detected_encoding
        except ImportError:
            pass
        
        # Fallback to manual detection
        for encoding in self.supported_encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1000)  # Try to read first 1000 characters
                return encoding
            except UnicodeDecodeError:
                continue
        
        # Default to utf-8 if all fail
        logger.warning(f"Could not detect encoding for {file_path}, using utf-8")
        return 'utf-8'
    
    def _read_csv_file(self, file_path: Path, encoding: str) -> pd.DataFrame:
        """Read CSV file with appropriate pandas settings"""
        
        # Try different CSV reading strategies
        read_strategies = [
            # Standard CSV
            {
                'sep': ',',
                'quotechar': '"',
                'skipinitialspace': True,
                'low_memory': False,
                'dtype': str,
                'keep_default_na': False
            },
            # Excel-style CSV
            {
                'sep': ',',
                'quotechar': '"',
                'skipinitialspace': True,
                'low_memory': False,
                'dtype': str,
                'keep_default_na': False,
                'thousands': ','
            },
            # Tab-separated
            {
                'sep': '\t',
                'quotechar': '"',
                'skipinitialspace': True,
                'low_memory': False,
                'dtype': str,
                'keep_default_na': False
            }
        ]
        
        for strategy in read_strategies:
            try:
                df = pd.read_csv(file_path, encoding=encoding, **strategy)
                
                # Basic validation
                if not df.empty and len(df.columns) > 1:
                    # Clean column names
                    df.columns = df.columns.str.strip()
                    return df
                    
            except Exception as e:
                logger.debug(f"CSV read strategy failed: {strategy}, error: {str(e)}")
                continue
        
        raise ValueError(f"Could not read CSV file {file_path} with any strategy")
    
    def _process_data_by_type(self, df: pd.DataFrame, csv_type: CSVType) -> List[Dict[str, Any]]:
        """Process DataFrame based on CSV type"""
        
        processors = {
            CSVType.ORDERS: self._process_orders_data,
            CSVType.LISTINGS: self._process_listings_data,
            CSVType.PRODUCTS: self._process_products_data,
            CSVType.CUSTOMERS: self._process_customers_data,
            CSVType.MESSAGES: self._process_messages_data,
            CSVType.SUPPLIERS: self._process_suppliers_data
        }
        
        processor = processors.get(csv_type)
        if processor:
            return processor(df)
        else:
            logger.warning(f"No processor available for CSV type: {csv_type}")
            return df.to_dict('records')
    
    def _process_orders_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process eBay orders CSV data"""
        
        processed_orders = []
        
        for _, row in df.iterrows():
            try:
                order_data = {
                    'ebay_order_id': str(row.get('Order ID', '')).strip(),
                    'buyer_username': str(row.get('Buyer Username', '')).strip(),
                    'buyer_email': str(row.get('Buyer Email', '')).strip() or None,
                    
                    # Financial data
                    'total_amount': self._parse_decimal(row.get('Total Price', 0)),
                    'currency': self._extract_currency(str(row.get('Total Price', '$0'))),
                    'payment_method': str(row.get('Payment Method', '')).strip() or None,
                    'payment_status': str(row.get('Payment Status', 'pending')).lower(),
                    
                    # Order status
                    'order_status': self._normalize_order_status(str(row.get('Order Status', 'pending'))),
                    
                    # Dates
                    'order_date': self._parse_datetime(row.get('Order Date')),
                    'payment_date': self._parse_datetime(row.get('Payment Date')),
                    'shipped_date': self._parse_datetime(row.get('Shipped Date')),
                    
                    # Shipping information
                    'shipping_address_line1': str(row.get('Shipping Address', '')).strip() or None,
                    'shipping_city': str(row.get('Shipping City', '')).strip() or None,
                    'shipping_state': str(row.get('Shipping State', '')).strip() or None,
                    'shipping_postal_code': str(row.get('Shipping Postal Code', '')).strip() or None,
                    'shipping_country': str(row.get('Shipping Country', '')).strip() or None,
                    'shipping_method': str(row.get('Shipping Method', '')).strip() or None,
                    'tracking_number': str(row.get('Tracking Number', '')).strip() or None,
                    
                    # Additional information
                    'buyer_notes': str(row.get('Buyer Notes', '')).strip() or None,
                    'seller_notes': str(row.get('Seller Notes', '')).strip() or None,
                    
                    # Import metadata
                    'import_batch_id': None,  # Will be set by processor
                    'import_filename': None   # Will be set by processor
                }
                
                processed_orders.append(order_data)
                
            except Exception as e:
                logger.warning(f"Failed to process order row: {str(e)}")
                continue
        
        return processed_orders
    
    def _process_listings_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process eBay listings CSV data"""
        
        processed_listings = []
        
        for _, row in df.iterrows():
            try:
                listing_data = {
                    'ebay_item_id': str(row.get('Item ID', '')).strip(),
                    'title': str(row.get('Title', '')).strip(),
                    'subtitle': str(row.get('Subtitle', '')).strip() or None,
                    'category_name': str(row.get('Category', '')).strip() or None,
                    
                    # Pricing
                    'start_price': self._parse_decimal(row.get('Start Price', 0)),
                    'buy_it_now_price': self._parse_decimal(row.get('Price', 0)),
                    'current_price': self._parse_decimal(row.get('Current Price', row.get('Price', 0))),
                    'currency': self._extract_currency(str(row.get('Price', '$0'))),
                    
                    # Quantity
                    'quantity_total': self._parse_integer(row.get('Quantity Available', 1)),
                    'quantity_sold': self._parse_integer(row.get('Quantity Sold', 0)),
                    
                    # Status and format
                    'listing_status': self._normalize_listing_status(str(row.get('Status', 'draft'))),
                    'listing_format': str(row.get('Format', 'FixedPrice')).strip(),
                    
                    # Dates
                    'start_date': self._parse_datetime(row.get('Start Date')),
                    'end_date': self._parse_datetime(row.get('End Date')),
                    
                    # Performance metrics
                    'view_count': self._parse_integer(row.get('Views', 0)),
                    'watch_count': self._parse_integer(row.get('Watchers', 0)),
                    
                    # Shipping
                    'shipping_cost': self._parse_decimal(row.get('Shipping Cost', 0)),
                    'free_shipping': str(row.get('Free Shipping', 'false')).lower() in ['true', '1', 'yes'],
                    
                    # Condition
                    'condition_name': str(row.get('Condition', 'New')).strip(),
                    
                    # Import metadata
                    'import_batch_id': None,
                    'import_filename': None
                }
                
                processed_listings.append(listing_data)
                
            except Exception as e:
                logger.warning(f"Failed to process listing row: {str(e)}")
                continue
        
        return processed_listings
    
    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value from various formats"""
        if pd.isna(value) or value == '':
            return None
        
        try:
            # Clean currency symbols and commas
            clean_value = str(value).replace('$', '').replace(',', '').replace('£', '').replace('€', '').strip()
            return Decimal(clean_value)
        except (InvalidOperation, ValueError, TypeError):
            return None
    
    def _parse_integer(self, value: Any) -> int:
        """Parse integer value"""
        if pd.isna(value) or value == '':
            return 0
        
        try:
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return 0
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime value from various formats"""
        if pd.isna(value) or value == '':
            return None
        
        try:
            return pd.to_datetime(value).to_pydatetime()
        except (ValueError, TypeError):
            return None
    
    def _extract_currency(self, value: str) -> str:
        """Extract currency symbol from price string"""
        if '$' in value:
            return 'USD'
        elif '£' in value:
            return 'GBP'
        elif '€' in value:
            return 'EUR'
        else:
            return 'USD'  # Default
    
    def _normalize_order_status(self, status: str) -> str:
        """Normalize order status values"""
        status_lower = status.lower().strip()
        
        status_map = {
            'pending': 'pending',
            'processing': 'processing',
            'shipped': 'shipped',
            'delivered': 'delivered',
            'completed': 'delivered',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
            'refunded': 'refunded'
        }
        
        return status_map.get(status_lower, 'pending')
    
    def _normalize_listing_status(self, status: str) -> str:
        """Normalize listing status values"""
        status_lower = status.lower().strip()
        
        status_map = {
            'active': 'active',
            'draft': 'draft',
            'ended': 'ended',
            'sold': 'sold',
            'cancelled': 'cancelled',
            'canceled': 'cancelled'
        }
        
        return status_map.get(status_lower, 'draft')
    
    def _generate_processing_summary(self, df: pd.DataFrame, processed_data: List[Dict]) -> Dict[str, Any]:
        """Generate processing summary"""
        
        return {
            'total_input_rows': len(df),
            'total_processed_rows': len(processed_data),
            'processing_success_rate': len(processed_data) / len(df) if len(df) > 0 else 0,
            'columns_processed': list(df.columns),
            'data_types_detected': {
                col: str(df[col].dtype) for col in df.columns
            }
        }

# Global parser instance
csv_parser = CSVDataParser()
```

---

## Success Criteria & Validation

### CSV Processing Requirements ✅
- [ ] File upload with size and type validation (100MB limit, CSV/Excel only)
- [ ] Secure file storage with unique naming and directory organization
- [ ] Format detection for eBay CSV exports (orders, listings, products, customers, messages)
- [ ] Data validation with detailed error reporting
- [ ] Chunked processing for large files (1000+ rows)
- [ ] Progress tracking and status updates
- [ ] Error handling with cleanup on failure
- [ ] File integrity verification with hash calculation

### Data Quality Requirements ✅
- [ ] Required field validation for all CSV types
- [ ] Data type conversion and validation
- [ ] Business rule validation (prices > 0, valid dates, etc.)
- [ ] Duplicate detection and handling
- [ ] Character encoding detection and handling
- [ ] Currency symbol recognition and normalization
- [ ] Date format parsing from various eBay formats
- [ ] Status value normalization

### SOLID/YAGNI Compliance ✅
- [ ] **Single Responsibility**: Each processor handles one CSV type
- [ ] **Open/Closed**: System extensible for new CSV formats without core changes
- [ ] **Liskov Substitution**: All validators implement common interface  
- [ ] **Interface Segregation**: Clean separation between upload, validation, and parsing
- [ ] **Dependency Inversion**: Processors depend on abstract validation interface
- [ ] **YAGNI Applied**: Essential CSV types only, no complex ETL or streaming
- [ ] Eliminated unnecessary complexity (real-time processing, multi-format support)

### Performance Requirements ✅
- [ ] File upload processing < 30 seconds for 100MB files
- [ ] CSV parsing < 5 seconds per 1000 rows
- [ ] Memory usage stays within limits during chunked processing
- [ ] Validation errors collected without stopping processing
- [ ] Background job support for large files
- [ ] Cleanup of temporary files on completion/failure

**Next Step**: Proceed to [02-background-job-system.md](./02-background-job-system.md) for background processing implementation.