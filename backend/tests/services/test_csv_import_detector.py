"""
Test CSV Import Format Detector and Validator
Following SOLID principles - Single Responsibility for testing CSV detection logic
YAGNI compliance: Essential test cases only
"""

import pytest
from unittest.mock import Mock, AsyncMock
from io import StringIO

from app.services.csv_import.listing_csv_detector import (
    CSVListingFormatDetector, CSVListingValidator, CSVListingFormat
)
from app.core.exceptions import ValidationException


class TestCSVListingFormatDetector:
    """Test CSV format detection functionality"""
    
    @pytest.fixture
    def detector(self):
        return CSVListingFormatDetector()
    
    def test_detect_active_listings_format(self, detector):
        """Test detection of eBay active listings format"""
        csv_content = "Item ID,Title,Price,Quantity Available,Status,Start Date\n123456,Test Product,$19.99,5,Active,2024-01-01"
        
        format_type, confidence = detector.detect_format(csv_content, "active_listings.csv")
        
        assert format_type == CSVListingFormat.EBAY_ACTIVE_LISTINGS
        assert confidence >= 0.8
    
    def test_detect_sold_listings_format(self, detector):
        """Test detection of eBay sold listings format"""
        csv_content = "Item ID,Title,Sale Price,Quantity Sold,Sale Date,Buyer Username\n123456,Test Product,$19.99,1,2024-01-01,buyer123"
        
        format_type, confidence = detector.detect_format(csv_content, "sold_listings.csv")
        
        assert format_type == CSVListingFormat.EBAY_SOLD_LISTINGS
        assert confidence >= 0.8
    
    def test_detect_unsold_listings_format(self, detector):
        """Test detection of eBay unsold listings format"""
        csv_content = "Item ID,Title,Listing Price,End Reason,Start Date\n123456,Test Product,$19.99,Ended,2024-01-01"
        
        format_type, confidence = detector.detect_format(csv_content, "unsold_listings.csv")
        
        assert format_type == CSVListingFormat.EBAY_UNSOLD_LISTINGS
        assert confidence >= 0.8
    
    def test_detect_unknown_format_low_confidence(self, detector):
        """Test detection with unknown format returns low confidence"""
        csv_content = "Random Column,Another Column\nvalue1,value2"
        
        format_type, confidence = detector.detect_format(csv_content, "random.csv")
        
        assert format_type == CSVListingFormat.UNKNOWN
        assert confidence < 0.8
    
    def test_filename_bonus_affects_confidence(self, detector):
        """Test that filename patterns affect confidence scoring"""
        # CSV with minimal required columns
        csv_content = "Item ID,Title,Price,Quantity Available,Status\n123456,Test Product,$19.99,5,Active"
        
        # Test with matching filename
        format_type1, confidence1 = detector.detect_format(csv_content, "active_listings.csv")
        
        # Test with non-matching filename
        format_type2, confidence2 = detector.detect_format(csv_content, "random_file.csv")
        
        assert format_type1 == format_type2 == CSVListingFormat.EBAY_ACTIVE_LISTINGS
        assert confidence1 > confidence2  # Filename match should increase confidence
    
    def test_invalid_csv_raises_exception(self, detector):
        """Test that invalid CSV content raises ValidationException"""
        invalid_csv = "This is not a CSV file\nInvalid format"
        
        with pytest.raises(ValidationException) as exc_info:
            detector.detect_format(invalid_csv, "test.csv")
        
        assert "Invalid CSV format" in str(exc_info.value)
    
    def test_empty_csv_returns_unknown(self, detector):
        """Test that empty CSV returns unknown format"""
        empty_csv = "\n\n"
        
        format_type, confidence = detector.detect_format(empty_csv, "empty.csv")
        
        assert format_type == CSVListingFormat.UNKNOWN
        assert confidence == 0.0


class TestCSVListingValidator:
    """Test CSV listing validation functionality"""
    
    @pytest.fixture
    def validator(self):
        return CSVListingValidator()
    
    def test_validate_active_listings_success(self, validator):
        """Test successful validation of active listings CSV"""
        csv_content = "Item ID,Title,Price,Quantity Available,Status\n123456789,Test Product,$19.99,5,Active"
        
        result = validator.validate_csv_data(csv_content, CSVListingFormat.EBAY_ACTIVE_LISTINGS)
        
        assert result['is_valid'] is True
        assert result['row_count'] == 1
        assert len(result['errors']) == 0
        assert len(result['sample_data']) == 1
    
    def test_validate_missing_required_columns(self, validator):
        """Test validation fails with missing required columns"""
        csv_content = "Title,Price\nTest Product,$19.99"  # Missing required columns
        
        result = validator.validate_csv_data(csv_content, CSVListingFormat.EBAY_ACTIVE_LISTINGS)
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert any("Missing required columns" in error for error in result['errors'])
    
    def test_validate_sold_listings_success(self, validator):
        """Test successful validation of sold listings CSV"""
        csv_content = "Item ID,Title,Sale Price,Quantity Sold,Sale Date\n123456789,Test Product,$19.99,1,2024-01-01"
        
        result = validator.validate_csv_data(csv_content, CSVListingFormat.EBAY_SOLD_LISTINGS)
        
        assert result['is_valid'] is True
        assert result['row_count'] == 1
        assert len(result['errors']) == 0
    
    def test_validate_unsold_listings_success(self, validator):
        """Test successful validation of unsold listings CSV"""
        csv_content = "Item ID,Title,Listing Price,End Reason\n123456789,Test Product,$19.99,Ended"
        
        result = validator.validate_csv_data(csv_content, CSVListingFormat.EBAY_UNSOLD_LISTINGS)
        
        assert result['is_valid'] is True
        assert result['row_count'] == 1
        assert len(result['errors']) == 0
    
    def test_validate_empty_csv_fails(self, validator):
        """Test validation fails for empty CSV"""
        empty_csv = ""
        
        result = validator.validate_csv_data(empty_csv, CSVListingFormat.EBAY_ACTIVE_LISTINGS)
        
        assert result['is_valid'] is False
        assert any("empty" in error.lower() for error in result['errors'])
    
    def test_validate_data_quality_warnings(self, validator):
        """Test data quality validation generates warnings"""
        # CSV with some data quality issues
        csv_content = """Item ID,Title,Price,Quantity Available,Status
123456789,Test Product 1,$19.99,5,Active
123456789,Test Product 2,$29.99,3,Active
987654321,,,$15.99,2,Inactive"""  # Duplicate ID and missing title
        
        result = validator.validate_csv_data(csv_content, CSVListingFormat.EBAY_ACTIVE_LISTINGS)
        
        # Should be valid but with warnings
        assert result['is_valid'] is True
        assert len(result['warnings']) > 0
        assert any("duplicate" in warning.lower() for warning in result['warnings'])
    
    def test_validate_invalid_price_format_warnings(self, validator):
        """Test validation generates warnings for invalid price formats"""
        csv_content = """Item ID,Title,Price,Quantity Available,Status
123456789,Test Product,NOT_A_PRICE,5,Active"""
        
        result = validator.validate_csv_data(csv_content, CSVListingFormat.EBAY_ACTIVE_LISTINGS)
        
        # Should be valid but with warnings about price format
        assert result['is_valid'] is True
        assert len(result['warnings']) > 0
        assert any("invalid price format" in warning.lower() for warning in result['warnings'])
    
    def test_validate_unknown_format_basic_validation(self, validator):
        """Test validation with unknown format performs basic validation only"""
        csv_content = "Col1,Col2,Col3\nval1,val2,val3"
        
        result = validator.validate_csv_data(csv_content, CSVListingFormat.UNKNOWN)
        
        assert result['is_valid'] is True
        assert len(result['warnings']) > 0
        assert any("unknown format" in warning.lower() for warning in result['warnings'])
    
    def test_validate_csv_parsing_error(self, validator):
        """Test handling of CSV parsing errors"""
        invalid_csv = "This is not\na valid CSV\nwith proper formatting"
        
        result = validator.validate_csv_data(invalid_csv, CSVListingFormat.EBAY_ACTIVE_LISTINGS)
        
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert any("parsing error" in error.lower() for error in result['errors'])