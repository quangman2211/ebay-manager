"""
Test CSV Import Transformer
Following SOLID principles - Single Responsibility for testing CSV transformation logic
YAGNI compliance: Essential test cases only
"""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock

from app.services.csv_import.listing_csv_transformer import (
    CSVListingTransformer, TransformationResult
)
from app.services.csv_import.listing_csv_detector import CSVListingFormat
from app.models.listing import ListingStatus


class TestCSVListingTransformer:
    """Test CSV listing transformation functionality"""
    
    @pytest.fixture
    def transformer(self):
        return CSVListingTransformer()
    
    def test_transform_active_listings_success(self, transformer):
        """Test successful transformation of active listings CSV"""
        csv_content = """Item ID,Title,Price,Quantity Available,Status,Start Date
123456789,Test Product 1,$19.99,5,Active,2024-01-01
987654321,Test Product 2,$29.99,3,Live,2024-01-02"""
        
        result = transformer.transform_csv_to_listings(
            csv_content, 
            CSVListingFormat.EBAY_ACTIVE_LISTINGS, 
            account_id=1
        )
        
        assert result.success is True
        assert result.processed_rows == 2
        assert result.skipped_rows == 0
        assert len(result.listings) == 2
        
        # Verify first listing
        listing1 = result.listings[0]
        assert listing1['ebay_item_id'] == '123456789'
        assert listing1['account_id'] == 1
        assert listing1['title'] == 'Test Product 1'
        assert listing1['price'] == Decimal('19.99')
        assert listing1['quantity_available'] == 5
        assert listing1['status'] == ListingStatus.ACTIVE.value
    
    def test_transform_sold_listings_success(self, transformer):
        """Test successful transformation of sold listings CSV"""
        csv_content = """Item ID,Title,Sale Price,Quantity Sold,Sale Date,Buyer Username
123456789,Test Sold Product,$25.99,1,2024-01-01,buyer123"""
        
        result = transformer.transform_csv_to_listings(
            csv_content,
            CSVListingFormat.EBAY_SOLD_LISTINGS,
            account_id=1
        )
        
        assert result.success is True
        assert result.processed_rows == 1
        assert len(result.listings) == 1
        
        listing = result.listings[0]
        assert listing['ebay_item_id'] == '123456789'
        assert listing['price'] == Decimal('25.99')
        assert listing['quantity_available'] == 0  # Sold listings have 0 available
        assert listing['status'] == ListingStatus.SOLD.value
        assert listing['buyer_username'] == 'buyer123'
    
    def test_transform_unsold_listings_success(self, transformer):
        """Test successful transformation of unsold listings CSV"""
        csv_content = """Item ID,Title,Listing Price,End Reason,Start Date
123456789,Test Unsold Product,$19.99,Ended,2024-01-01"""
        
        result = transformer.transform_csv_to_listings(
            csv_content,
            CSVListingFormat.EBAY_UNSOLD_LISTINGS,
            account_id=1
        )
        
        assert result.success is True
        assert result.processed_rows == 1
        assert len(result.listings) == 1
        
        listing = result.listings[0]
        assert listing['ebay_item_id'] == '123456789'
        assert listing['title'] == 'Test Unsold Product'
        assert listing['price'] == Decimal('19.99')
        assert listing['end_reason'] == 'Ended'
        assert listing['status'] == ListingStatus.ENDED.value
    
    def test_transform_missing_required_fields_skips_rows(self, transformer):
        """Test transformation skips rows with missing required fields"""
        csv_content = """Item ID,Title,Price,Quantity Available,Status
,Missing Item ID,$19.99,5,Active
123456789,,$29.99,3,Active
987654321,Valid Product,$39.99,2,Active"""
        
        result = transformer.transform_csv_to_listings(
            csv_content,
            CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            account_id=1
        )
        
        assert result.success is False  # Has errors
        assert result.processed_rows == 1  # Only valid product
        assert result.skipped_rows == 2  # Two invalid rows
        assert len(result.errors) == 2
        assert len(result.listings) == 1
        
        # Verify error messages
        assert any("Missing or invalid item ID" in error for error in result.errors)
        assert any("Missing title" in error for error in result.errors)
    
    def test_transform_invalid_price_format_generates_warnings(self, transformer):
        """Test transformation handles invalid price formats with warnings"""
        csv_content = """Item ID,Title,Price,Quantity Available,Status
123456789,Test Product,INVALID_PRICE,5,Active
987654321,Valid Product,$29.99,3,Active"""
        
        result = transformer.transform_csv_to_listings(
            csv_content,
            CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            account_id=1
        )
        
        assert result.success is True  # Still successful with warnings
        assert result.processed_rows == 2
        assert len(result.warnings) > 0
        assert len(result.listings) == 2
        
        # First listing should have price 0.00 due to invalid format
        assert result.listings[0]['price'] == Decimal('0.00')
        assert result.listings[1]['price'] == Decimal('29.99')
        
        # Verify warning message
        assert any("Invalid price format" in warning for warning in result.warnings)
    
    def test_transform_empty_csv_returns_failure(self, transformer):
        """Test transformation of empty CSV returns failure"""
        empty_csv = ""
        
        result = transformer.transform_csv_to_listings(
            empty_csv,
            CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            account_id=1
        )
        
        assert result.success is False
        assert result.processed_rows == 0
        assert len(result.errors) > 0
        assert "empty" in result.errors[0].lower()
    
    def test_transform_unsupported_format_returns_failure(self, transformer):
        """Test transformation with unsupported format returns failure"""
        csv_content = "Col1,Col2\nval1,val2"
        
        result = transformer.transform_csv_to_listings(
            csv_content,
            CSVListingFormat.UNKNOWN,
            account_id=1
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "Unsupported CSV format" in result.errors[0]
    
    def test_extract_item_id_handles_various_formats(self, transformer):
        """Test item ID extraction handles various column name formats"""
        import pandas as pd
        
        # Test different column name variations
        test_cases = [
            {"item id": "123456789"},
            {"itemid": "987654321"},
            {"item_id": "555666777"},
            {"ebay item id": "111222333"}
        ]
        
        for test_data in test_cases:
            row = pd.Series(test_data)
            item_id = transformer._extract_item_id(row)
            assert item_id is not None
            assert item_id.isdigit()
    
    def test_extract_price_cleans_currency_symbols(self, transformer):
        """Test price extraction removes currency symbols and formatting"""
        import pandas as pd
        
        test_cases = [
            {"price": "$19.99", "expected": Decimal("19.99")},
            {"price": "€25.50", "expected": Decimal("25.50")},
            {"price": "1,234.56", "expected": Decimal("1234.56")},
            {"price": " $15.00 ", "expected": Decimal("15.00")},
        ]
        
        for test_data in test_cases:
            row = pd.Series(test_data)
            price = transformer._extract_price(row, ["price"])
            assert price == test_data["expected"]
    
    def test_extract_datetime_handles_various_formats(self, transformer):
        """Test datetime extraction handles various date formats"""
        import pandas as pd
        
        test_cases = [
            {"date": "2024-01-01"},
            {"date": "01/01/2024"},
            {"date": "2024-01-01 12:30:00"},
            {"date": "Jan 1, 2024"}
        ]
        
        for test_data in test_cases:
            row = pd.Series(test_data)
            date_result = transformer._extract_datetime(row, ["date"])
            assert isinstance(date_result, datetime)
            assert date_result.year == 2024
            assert date_result.month == 1
            assert date_result.day == 1
    
    def test_map_end_reason_to_status_correctly(self, transformer):
        """Test end reason mapping to listing status"""
        test_cases = [
            ("Sold", ListingStatus.SOLD.value),
            ("Purchased by buyer", ListingStatus.SOLD.value),
            ("Cancelled by seller", ListingStatus.CANCELLED.value),
            ("Expired - no bids", ListingStatus.ENDED.value),
            ("Out of stock", ListingStatus.OUT_OF_STOCK.value),
            ("Unknown reason", ListingStatus.ENDED.value)  # Default
        ]
        
        for end_reason, expected_status in test_cases:
            result_status = transformer._map_end_reason_to_status(end_reason)
            assert result_status == expected_status
    
    def test_transform_handles_malformed_csv(self, transformer):
        """Test transformation handles malformed CSV gracefully"""
        malformed_csv = """Item ID,Title,Price,Quantity Available,Status
123456789,Test Product,$19.99,5,Active
987654321,"Product with "extra" quotes",$29.99,3,Active"""
        
        # Should not crash and should handle the malformed row gracefully
        result = transformer.transform_csv_to_listings(
            malformed_csv,
            CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            account_id=1
        )
        
        # Result might succeed or fail depending on pandas parsing, but should not crash
        assert isinstance(result, TransformationResult)
        assert isinstance(result.success, bool)
    
    def test_transform_large_title_truncation(self, transformer):
        """Test that long titles are truncated to model limits"""
        long_title = "A" * 600  # Longer than 500 character limit
        csv_content = f"""Item ID,Title,Price,Quantity Available,Status
123456789,{long_title},$19.99,5,Active"""
        
        result = transformer.transform_csv_to_listings(
            csv_content,
            CSVListingFormat.EBAY_ACTIVE_LISTINGS,
            account_id=1
        )
        
        assert result.success is True
        assert len(result.listings) == 1
        assert len(result.listings[0]['title']) == 500  # Truncated to limit