"""
CSV Processing Utilities
Following SOLID principles - Interface Segregation and Single Responsibility
"""

import csv
import io
import uuid
import mimetypes
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator, Tuple
from pathlib import Path
from datetime import datetime
import pandas as pd
from fastapi import UploadFile, HTTPException

from app.schemas.csv import (
    CSVValidationError, CSVFileStatus, GenericCSVRow,
    CSVColumnMapping
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("csv_processor")

class CSVFileValidator:
    """
    CSV file validation utility
    Following SOLID: Single Responsibility for file validation
    """
    
    ALLOWED_MIME_TYPES = [
        'text/csv',
        'application/csv',
        'text/plain',
        'application/vnd.ms-excel'
    ]
    
    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[bool, str]:
        """
        Validate uploaded CSV file
        Returns: (is_valid, error_message)
        """
        # Check file extension
        if not file.filename:
            return False, "Filename is required"
            
        if not file.filename.lower().endswith(('.csv', '.txt')):
            return False, "File must be a CSV file (.csv or .txt extension)"
        
        # Check file size
        if file.size and file.size > settings.UPLOAD_MAX_SIZE:
            return False, f"File size exceeds maximum allowed size ({settings.UPLOAD_MAX_SIZE} bytes)"
            
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if mime_type and mime_type not in CSVFileValidator.ALLOWED_MIME_TYPES:
            return False, f"Invalid file type. Allowed types: {', '.join(CSVFileValidator.ALLOWED_MIME_TYPES)}"
        
        return True, ""
    
    @staticmethod
    def detect_csv_properties(content: bytes) -> Dict[str, Any]:
        """
        Detect CSV file properties (delimiter, encoding, etc.)
        Following SOLID: Single function responsibility
        """
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            decoded_content = None
            detected_encoding = 'utf-8'
            
            for encoding in encodings:
                try:
                    decoded_content = content.decode(encoding)
                    detected_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if not decoded_content:
                raise ValueError("Unable to decode file with supported encodings")
            
            # Detect dialect
            sample = decoded_content[:4096]  # Use first 4KB for detection
            sniffer = csv.Sniffer()
            
            try:
                dialect = sniffer.sniff(sample)
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ','  # Default fallback
            
            # Count rows and columns
            rows = decoded_content.split('\n')
            total_rows = len([row for row in rows if row.strip()])
            
            # Get headers from first row
            if rows:
                first_row = rows[0].strip()
                if first_row:
                    headers = [h.strip('"\'') for h in first_row.split(delimiter)]
                else:
                    headers = []
            else:
                headers = []
            
            return {
                'encoding': detected_encoding,
                'delimiter': delimiter,
                'total_rows': total_rows,
                'headers': headers,
                'sample_rows': rows[:5] if len(rows) > 1 else []
            }
            
        except Exception as e:
            logger.error(f"Error detecting CSV properties: {str(e)}")
            return {
                'encoding': 'utf-8',
                'delimiter': ',',
                'total_rows': 0,
                'headers': [],
                'sample_rows': []
            }

class CSVParser:
    """
    CSV parsing utility
    Following SOLID: Single Responsibility for CSV parsing operations
    """
    
    def __init__(self, encoding: str = 'utf-8', delimiter: str = ','):
        self.encoding = encoding
        self.delimiter = delimiter
    
    def parse_rows(self, content: bytes, skip_rows: int = 0, limit: Optional[int] = None) -> Iterator[Dict[str, str]]:
        """
        Parse CSV content and yield rows as dictionaries
        Following SOLID: Single method responsibility
        """
        try:
            decoded_content = content.decode(self.encoding)
            csv_file = io.StringIO(decoded_content)
            reader = csv.DictReader(csv_file, delimiter=self.delimiter)
            
            # Skip specified rows
            for _ in range(skip_rows):
                try:
                    next(reader)
                except StopIteration:
                    break
            
            count = 0
            for row in reader:
                if limit and count >= limit:
                    break
                
                # Clean up row data
                cleaned_row = {}
                for key, value in row.items():
                    if key is not None:  # Handle potential None keys
                        cleaned_key = str(key).strip()
                        cleaned_value = str(value).strip() if value is not None else ""
                        cleaned_row[cleaned_key] = cleaned_value
                
                yield cleaned_row
                count += 1
                
        except UnicodeDecodeError as e:
            logger.error(f"Unicode decode error: {str(e)}")
            raise ValueError(f"Unable to decode file with encoding {self.encoding}")
        except csv.Error as e:
            logger.error(f"CSV parsing error: {str(e)}")
            raise ValueError(f"Invalid CSV format: {str(e)}")
    
    def get_headers(self, content: bytes) -> List[str]:
        """
        Get CSV headers
        Following SOLID: Single method responsibility
        """
        try:
            decoded_content = content.decode(self.encoding)
            csv_file = io.StringIO(decoded_content)
            reader = csv.reader(csv_file, delimiter=self.delimiter)
            
            first_row = next(reader, [])
            return [str(header).strip() for header in first_row]
            
        except Exception as e:
            logger.error(f"Error getting headers: {str(e)}")
            return []

class CSVRowValidator(ABC):
    """
    Abstract CSV row validator
    Following SOLID: Interface Segregation - specific validators implement this
    """
    
    @abstractmethod
    def validate_row(self, row_data: Dict[str, str], row_number: int) -> GenericCSVRow:
        """Validate a single CSV row"""
        pass
    
    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """Get list of required columns for this CSV type"""
        pass
    
    @abstractmethod
    def get_column_mappings(self) -> List[CSVColumnMapping]:
        """Get column mappings for this CSV type"""
        pass

class GenericCSVValidator(CSVRowValidator):
    """
    Generic CSV validator for basic validation
    Following SOLID: Single Responsibility for generic validation
    """
    
    def __init__(self, required_columns: Optional[List[str]] = None):
        self.required_columns = required_columns or []
    
    def validate_row(self, row_data: Dict[str, str], row_number: int) -> GenericCSVRow:
        """
        Validate a generic CSV row
        Following SOLID: Single method responsibility
        """
        errors = []
        
        # Check for required columns
        for required_col in self.required_columns:
            if required_col not in row_data or not row_data[required_col].strip():
                errors.append(f"Required column '{required_col}' is missing or empty")
        
        # Check for completely empty rows
        if not any(value.strip() for value in row_data.values()):
            errors.append("Row is completely empty")
        
        return GenericCSVRow(
            row_number=row_number,
            data=row_data,
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def get_required_columns(self) -> List[str]:
        """Get required columns"""
        return self.required_columns
    
    def get_column_mappings(self) -> List[CSVColumnMapping]:
        """Get generic column mappings"""
        mappings = []
        for col in self.required_columns:
            mappings.append(CSVColumnMapping(
                csv_column=col,
                target_field=col.lower().replace(' ', '_'),
                is_required=True,
                data_type="string"
            ))
        return mappings

class CSVFileManager:
    """
    CSV file storage and management
    Following SOLID: Single Responsibility for file operations
    """
    
    def __init__(self):
        self.upload_path = Path(settings.UPLOAD_PATH)
        self.upload_path.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file: UploadFile, file_type: str) -> Tuple[str, Path]:
        """
        Save uploaded file and return file ID and path
        Following SOLID: Single method responsibility
        """
        # Generate unique file ID
        file_id = f"{file_type}_{uuid.uuid4().hex}_{int(datetime.utcnow().timestamp())}"
        
        # Create file path
        file_path = self.upload_path / f"{file_id}.csv"
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                content = file.file.read()
                buffer.write(content)
            
            logger.info(f"File saved: {file_id} ({file.filename}) - {len(content)} bytes")
            return file_id, file_path
            
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    def get_file_content(self, file_id: str) -> bytes:
        """
        Get file content by file ID
        Following SOLID: Single method responsibility  
        """
        file_path = self.upload_path / f"{file_id}.csv"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
        
        try:
            with open(file_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_id}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete file by file ID
        Following SOLID: Single method responsibility
        """
        file_path = self.upload_path / f"{file_id}.csv"
        
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            return False
    
    def get_file_size(self, file_id: str) -> int:
        """Get file size in bytes"""
        file_path = self.upload_path / f"{file_id}.csv"
        
        if not file_path.exists():
            return 0
        
        return file_path.stat().st_size

class CSVProcessor:
    """
    Main CSV processing coordinator
    Following SOLID: Single Responsibility for coordinating CSV operations
    """
    
    def __init__(self):
        self.file_manager = CSVFileManager()
        self.parser = CSVParser()
        
    def validate_and_process_file(
        self, 
        content: bytes, 
        validator: CSVRowValidator,
        skip_rows: int = 0
    ) -> Tuple[List[GenericCSVRow], List[CSVValidationError]]:
        """
        Validate and process CSV content
        Following SOLID: Single method responsibility
        """
        valid_rows = []
        errors = []
        
        try:
            # Detect CSV properties
            properties = CSVFileValidator.detect_csv_properties(content)
            self.parser = CSVParser(
                encoding=properties['encoding'],
                delimiter=properties['delimiter']
            )
            
            # Parse and validate rows
            row_number = skip_rows + 1
            for row_data in self.parser.parse_rows(content, skip_rows=skip_rows):
                validated_row = validator.validate_row(row_data, row_number)
                
                if validated_row.is_valid:
                    valid_rows.append(validated_row)
                else:
                    for error_msg in validated_row.errors:
                        errors.append(CSVValidationError(
                            row=row_number,
                            error_type="validation",
                            message=error_msg
                        ))
                
                row_number += 1
            
            logger.info(f"CSV processed: {len(valid_rows)} valid rows, {len(errors)} errors")
            return valid_rows, errors
            
        except Exception as e:
            logger.error(f"Error processing CSV: {str(e)}")
            errors.append(CSVValidationError(
                row=0,
                error_type="parsing",
                message=f"CSV parsing failed: {str(e)}"
            ))
            return [], errors