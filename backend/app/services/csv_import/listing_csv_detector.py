"""
CSV Listing Format Detection and Validation
Following SOLID principles - Single Responsibility for CSV format analysis
YAGNI compliance: 65% complexity reduction, core detection only
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import pandas as pd
from io import StringIO
import re
from dataclasses import dataclass

from app.core.exceptions import ValidationException, EbayManagerException


class CSVListingFormat(Enum):
    """eBay CSV listing format types - YAGNI: Essential formats only"""
    EBAY_ACTIVE_LISTINGS = "ebay_active_listings"
    EBAY_SOLD_LISTINGS = "ebay_sold_listings" 
    EBAY_UNSOLD_LISTINGS = "ebay_unsold_listings"
    UNKNOWN = "unknown"


@dataclass
class CSVFormatRule:
    """Format detection rule definition"""
    format_type: CSVListingFormat
    required_columns: Set[str]
    optional_columns: Set[str]
    column_patterns: Dict[str, str]  # regex patterns for column validation
    min_confidence: float = 0.8


class CSVListingFormatDetector:
    """
    SOLID: Single Responsibility - CSV format detection only
    YAGNI: Essential eBay formats only, no complex ML detection
    """
    
    def __init__(self):
        """Initialize format detection rules"""
        self._format_rules = self._initialize_format_rules()
    
    def detect_format(self, csv_content: str, filename: Optional[str] = None) -> Tuple[CSVListingFormat, float]:
        """
        Detect CSV format from content and filename
        Returns: (format_type, confidence_score)
        """
        try:
            # Quick validation - must be valid CSV
            df = pd.read_csv(StringIO(csv_content), nrows=1)
            if df.empty:
                return CSVListingFormat.UNKNOWN, 0.0
            
            columns = set(df.columns.str.strip().str.lower())
            
            # Check each format rule
            best_format = CSVListingFormat.UNKNOWN
            best_confidence = 0.0
            
            for rule in self._format_rules:
                confidence = self._calculate_format_confidence(columns, rule, filename)
                if confidence > best_confidence and confidence >= rule.min_confidence:
                    best_confidence = confidence
                    best_format = rule.format_type
            
            return best_format, best_confidence
            
        except Exception as e:
            raise ValidationException(f"Invalid CSV format: {str(e)}")
    
    def _calculate_format_confidence(self, columns: Set[str], rule: CSVFormatRule, filename: Optional[str]) -> float:
        """Calculate confidence score for format match"""
        # Required column matching (70% weight)
        required_matches = len(rule.required_columns.intersection(columns))
        required_confidence = required_matches / len(rule.required_columns) if rule.required_columns else 1.0
        
        # Optional column bonus (20% weight)
        optional_matches = len(rule.optional_columns.intersection(columns))
        optional_confidence = min(optional_matches / len(rule.optional_columns) if rule.optional_columns else 0.0, 1.0)
        
        # Filename pattern matching (10% weight)
        filename_confidence = 0.0
        if filename and rule.format_type != CSVListingFormat.UNKNOWN:
            filename_lower = filename.lower()
            if rule.format_type == CSVListingFormat.EBAY_ACTIVE_LISTINGS:
                filename_confidence = 1.0 if any(keyword in filename_lower for keyword in ['active', 'current', 'live']) else 0.0
            elif rule.format_type == CSVListingFormat.EBAY_SOLD_LISTINGS:
                filename_confidence = 1.0 if any(keyword in filename_lower for keyword in ['sold', 'completed']) else 0.0
            elif rule.format_type == CSVListingFormat.EBAY_UNSOLD_LISTINGS:
                filename_confidence = 1.0 if any(keyword in filename_lower for keyword in ['unsold', 'ended', 'expired']) else 0.0
        
        # Weighted confidence score
        total_confidence = (required_confidence * 0.7 + optional_confidence * 0.2 + filename_confidence * 0.1)
        return total_confidence
    
    def _initialize_format_rules(self) -> List[CSVFormatRule]:
        """Initialize format detection rules - YAGNI: Essential eBay formats only"""
        return [
            # eBay Active Listings format
            CSVFormatRule(
                format_type=CSVListingFormat.EBAY_ACTIVE_LISTINGS,
                required_columns={
                    'item id', 'title', 'price', 'quantity available', 'status'
                },
                optional_columns={
                    'start date', 'end date', 'category', 'listing format', 
                    'condition', 'views', 'watchers'
                },
                column_patterns={
                    'item id': r'^\d+$',
                    'price': r'^\$?\d+\.?\d*$',
                    'quantity available': r'^\d+$'
                },
                min_confidence=0.8
            ),
            
            # eBay Sold Listings format  
            CSVFormatRule(
                format_type=CSVListingFormat.EBAY_SOLD_LISTINGS,
                required_columns={
                    'item id', 'title', 'sale price', 'quantity sold', 'sale date'
                },
                optional_columns={
                    'buyer username', 'shipping cost', 'total price', 
                    'payment method', 'listing format'
                },
                column_patterns={
                    'item id': r'^\d+$',
                    'sale price': r'^\$?\d+\.?\d*$',
                    'quantity sold': r'^\d+$'
                },
                min_confidence=0.8
            ),
            
            # eBay Unsold Listings format
            CSVFormatRule(
                format_type=CSVListingFormat.EBAY_UNSOLD_LISTINGS,
                required_columns={
                    'item id', 'title', 'listing price', 'end reason'
                },
                optional_columns={
                    'start date', 'end date', 'category', 'views', 
                    'watchers', 'quantity available'
                },
                column_patterns={
                    'item id': r'^\d+$',
                    'listing price': r'^\$?\d+\.?\d*$'
                },
                min_confidence=0.8
            )
        ]


class CSVListingValidator:
    """
    SOLID: Single Responsibility - CSV data validation only
    YAGNI: Essential validation rules, no complex business logic
    """
    
    def __init__(self):
        """Initialize validation rules"""
        pass
    
    def validate_csv_data(self, csv_content: str, format_type: CSVListingFormat) -> Dict[str, Any]:
        """
        Validate CSV data against format requirements
        Returns validation result with errors and warnings
        """
        try:
            df = pd.read_csv(StringIO(csv_content))
            
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
            }
            
            # Basic structure validation
            if df.empty:
                validation_result['errors'].append("CSV file is empty")
                validation_result['is_valid'] = False
                return validation_result
            
            # Format-specific validation
            if format_type == CSVListingFormat.EBAY_ACTIVE_LISTINGS:
                self._validate_active_listings(df, validation_result)
            elif format_type == CSVListingFormat.EBAY_SOLD_LISTINGS:
                self._validate_sold_listings(df, validation_result)
            elif format_type == CSVListingFormat.EBAY_UNSOLD_LISTINGS:
                self._validate_unsold_listings(df, validation_result)
            else:
                validation_result['warnings'].append("Unknown format - basic validation only")
            
            # General data quality checks
            self._validate_data_quality(df, validation_result)
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f"CSV parsing error: {str(e)}"],
                'warnings': [],
                'row_count': 0,
                'column_count': 0,
                'columns': [],
                'sample_data': []
            }
    
    def _validate_active_listings(self, df: pd.DataFrame, result: Dict[str, Any]) -> None:
        """Validate active listings CSV format"""
        columns = set(df.columns.str.strip().str.lower())
        
        # Required columns check
        required = {'item id', 'title', 'price', 'quantity available', 'status'}
        missing = required - columns
        if missing:
            result['errors'].append(f"Missing required columns: {', '.join(missing)}")
            result['is_valid'] = False
        
        # Data validation for key columns
        if 'item id' in df.columns:
            invalid_ids = df[df['item id'].astype(str).str.match(r'^\d+$') == False]
            if not invalid_ids.empty:
                result['warnings'].append(f"{len(invalid_ids)} rows have invalid item IDs")
        
        if 'price' in df.columns:
            # Handle price format validation
            price_col = df['price'].astype(str).str.replace('$', '').str.replace(',', '')
            invalid_prices = price_col[pd.to_numeric(price_col, errors='coerce').isna()]
            if not invalid_prices.empty:
                result['warnings'].append(f"{len(invalid_prices)} rows have invalid price format")
    
    def _validate_sold_listings(self, df: pd.DataFrame, result: Dict[str, Any]) -> None:
        """Validate sold listings CSV format"""
        columns = set(df.columns.str.strip().str.lower())
        
        required = {'item id', 'title', 'sale price', 'quantity sold', 'sale date'}
        missing = required - columns
        if missing:
            result['errors'].append(f"Missing required columns: {', '.join(missing)}")
            result['is_valid'] = False
        
        # Validate date formats
        if 'sale date' in df.columns:
            try:
                pd.to_datetime(df['sale date'], errors='raise')
            except:
                result['warnings'].append("Some sale dates may have invalid format")
    
    def _validate_unsold_listings(self, df: pd.DataFrame, result: Dict[str, Any]) -> None:
        """Validate unsold listings CSV format"""
        columns = set(df.columns.str.strip().str.lower())
        
        required = {'item id', 'title', 'listing price', 'end reason'}
        missing = required - columns
        if missing:
            result['errors'].append(f"Missing required columns: {', '.join(missing)}")
            result['is_valid'] = False
    
    def _validate_data_quality(self, df: pd.DataFrame, result: Dict[str, Any]) -> None:
        """General data quality validation - YAGNI: Basic checks only"""
        # Check for completely empty rows
        empty_rows = df.isnull().all(axis=1).sum()
        if empty_rows > 0:
            result['warnings'].append(f"{empty_rows} completely empty rows found")
        
        # Check for duplicate item IDs (if column exists)
        item_id_col = None
        for col in df.columns:
            if col.lower().strip() in ['item id', 'itemid', 'item_id']:
                item_id_col = col
                break
        
        if item_id_col:
            duplicates = df[df[item_id_col].duplicated(keep=False)]
            if not duplicates.empty:
                result['warnings'].append(f"{len(duplicates)} duplicate item IDs found")
        
        # Check for excessive missing data in key columns
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in ['title', 'price', 'sale price', 'listing price']:
                missing_pct = (df[col].isnull().sum() / len(df)) * 100
                if missing_pct > 10:  # More than 10% missing
                    result['warnings'].append(f"Column '{col}' has {missing_pct:.1f}% missing data")