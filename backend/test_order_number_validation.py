"""
Test Order Number Validation - Enhanced CSV Processing
SOLID: Single Responsibility - Test only Order Number validation logic
"""
import pytest
import pandas as pd
from app.csv_service import CSVProcessor
from app.schemas import DataType


class TestOrderNumberValidation:
    """Test Order Number validation following SOLID principles"""
    
    def test_is_valid_order_number_valid_cases(self):
        """Test valid Order Number formats"""
        valid_numbers = [
            "123456",           # Pure numeric
            "123456789",        # Long numeric  
            "ORD-123456",       # Alphanumeric with prefix
            "123456-7890",      # Numeric with dash
            "ORDER123456",      # Text prefix
            "12345ABC",         # Numeric with suffix
            "AB123CD456",       # Mixed alphanumeric
        ]
        
        for order_number in valid_numbers:
            assert CSVProcessor._is_valid_order_number(order_number), f"'{order_number}' should be valid"
    
    def test_is_valid_order_number_invalid_cases(self):
        """Test invalid Order Number formats"""
        invalid_numbers = [
            "",                 # Empty string
            "   ",              # Whitespace only
            "None",             # String "None"  
            "null",             # String "null"
            "NaN",              # String "NaN"
            "ORDER",            # Text only, no digits
            "ABC-DEF",          # Text only with dash
            "---",              # Special chars only
            "ORDER-",           # Text with dash but no number
        ]
        
        for order_number in invalid_numbers:
            assert not CSVProcessor._is_valid_order_number(order_number), f"'{order_number}' should be invalid"
    
    def test_extract_item_id_valid_order_numbers(self):
        """Test extract_item_id with valid Order Numbers"""
        valid_records = [
            {"Order Number": "123456", "Item Number": "ITEM-001"},
            {"Order Number": "ORD-123456", "Item Number": "ITEM-002"}, 
            {"Order Number": "123456-789", "Item Number": "ITEM-003"},
        ]
        
        for record in valid_records:
            item_id = CSVProcessor.extract_item_id(record, DataType.ORDER)
            expected = str(record["Order Number"]).strip()
            assert item_id == expected, f"Expected '{expected}', got '{item_id}'"
    
    def test_extract_item_id_invalid_order_numbers(self):
        """Test extract_item_id with invalid Order Numbers raises ValueError"""
        invalid_records = [
            {"Order Number": "", "Item Number": "ITEM-001"},
            {"Order Number": "None", "Item Number": "ITEM-002"},
            {"Order Number": "ORDER", "Item Number": "ITEM-003"},
            {"Order Number": "   ", "Item Number": "ITEM-004"},
        ]
        
        for record in invalid_records:
            with pytest.raises(ValueError) as exc_info:
                CSVProcessor.extract_item_id(record, DataType.ORDER)
            
            assert "Invalid Order Number" in str(exc_info.value)
            assert record["Order Number"].strip() in str(exc_info.value)
    
    def test_validate_order_csv_with_invalid_order_numbers(self):
        """Test CSV validation catches invalid Order Numbers"""
        # Create DataFrame with mixed valid/invalid Order Numbers
        data = {
            "Order Number": ["123456", "", "ORDER", "789012", "None"],
            "Item Number": ["ITEM-001", "ITEM-002", "ITEM-003", "ITEM-004", "ITEM-005"],
            "Item Title": ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"],
            "Buyer Username": ["buyer1", "buyer2", "buyer3", "buyer4", "buyer5"],
            "Buyer Name": ["John", "Jane", "Bob", "Alice", "Charlie"],
            "Sale Date": ["2024-01-01"] * 5,
            "Sold For": ["$29.99"] * 5,
            "Quantity": ["1"] * 5
        }
        
        df = pd.DataFrame(data)
        errors = CSVProcessor.validate_order_csv(df)
        
        assert len(errors) > 0, "Should have validation errors"
        error_msg = " ".join(errors)
        assert "Invalid Order Numbers found" in error_msg
        # Note: Pandas converts empty string to NaN, so row numbers shift
        assert "Row 3:" in error_msg  # NaN at index 1 (Row 3 after header + 1-indexing)
        assert "Row 4:" in error_msg  # "ORDER" at index 2 (Row 4)  
        assert "Row 6:" in error_msg  # "None" at index 4 (Row 6)
    
    def test_validate_order_csv_all_valid_order_numbers(self):
        """Test CSV validation passes with all valid Order Numbers"""
        data = {
            "Order Number": ["123456", "ORD-789012", "123-456", "ORDER123"],
            "Item Number": ["ITEM-001", "ITEM-002", "ITEM-003", "ITEM-004"],
            "Item Title": ["Item 1", "Item 2", "Item 3", "Item 4"],
            "Buyer Username": ["buyer1", "buyer2", "buyer3", "buyer4"],
            "Buyer Name": ["John", "Jane", "Bob", "Alice"],
            "Sale Date": ["2024-01-01"] * 4,
            "Sold For": ["$29.99"] * 4,
            "Quantity": ["1"] * 4
        }
        
        df = pd.DataFrame(data)
        errors = CSVProcessor.validate_order_csv(df)
        
        # Should have no validation errors
        assert len(errors) == 0, f"Should have no errors, but got: {errors}"
    
    def test_check_duplicates_with_invalid_order_numbers(self):
        """Test duplicate checking handles validation errors properly"""
        records = [
            {"Order Number": "123456", "Item Number": "ITEM-001"},  # Valid
            {"Order Number": "", "Item Number": "ITEM-002"},        # Invalid - empty
            {"Order Number": "ORDER", "Item Number": "ITEM-003"},   # Invalid - no digits
            {"Order Number": "789012", "Item Number": "ITEM-004"},  # Valid
        ]
        
        errors = CSVProcessor.check_duplicates(records, DataType.ORDER)
        
        assert len(errors) > 0, "Should have validation errors"
        error_msg = " ".join(errors)
        assert "Record 2:" in error_msg  # Empty Order Number
        assert "Record 3:" in error_msg  # "ORDER" 
    
    def test_process_csv_file_with_invalid_order_numbers(self):
        """Test full CSV processing with invalid Order Numbers - should fail at CSV validation step"""
        csv_content = '''Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity
123456,ITEM-001,Valid Item,buyer1,John Doe,2024-01-01,$29.99,1
,ITEM-002,Invalid Empty,buyer2,Jane Smith,2024-01-02,$39.99,2
ORDER,ITEM-003,Invalid Text,buyer3,Bob Wilson,2024-01-03,$19.99,1
789012,ITEM-004,Valid Item 2,buyer4,Alice Brown,2024-01-04,$49.99,3'''
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        # Should fail at CSV validation step (which is called within process_csv_file)
        assert len(errors) > 0, f"CSV processing should fail due to Order Number validation errors"
        assert "Invalid Order Numbers found" in " ".join(errors)
        assert len(records) == 0, "Should have no records when validation fails"
    
    def test_integration_order_number_validation_flow(self):
        """Test complete validation flow as used in upload endpoints"""
        # This simulates the flow in main.py and upload_service.py
        csv_content = '''Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity
123456,ITEM-001,Valid Order,buyer1,John Doe,2024-01-01,$29.99,1
,ITEM-002,Empty Order Number,buyer2,Jane Smith,2024-01-02,$39.99,2
ORDER,ITEM-003,Text Only Order,buyer3,Bob Wilson,2024-01-03,$19.99,1'''
        
        # Step 1: Process CSV (should fail due to validation within process_csv_file)
        records, processing_errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        assert len(processing_errors) > 0, "CSV processing should fail due to Order Number validation"
        assert len(records) == 0, "Should have no records when validation fails"
        
        # Verify error messages contain proper details
        error_text = " ".join(processing_errors)
        assert "Invalid Order Number" in error_text
        assert "must contain digits" in error_text
    
    def test_integration_with_valid_data_only(self):
        """Test that valid data processes successfully"""
        csv_content = '''Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity
123456,ITEM-001,Valid Order 1,buyer1,John Doe,2024-01-01,$29.99,1
ORD-789012,ITEM-002,Valid Order 2,buyer2,Jane Smith,2024-01-02,$39.99,2
ORDER123,ITEM-003,Valid Order 3,buyer3,Bob Wilson,2024-01-03,$19.99,1'''
        
        # Process CSV (should succeed)
        records, processing_errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        assert len(processing_errors) == 0, f"CSV processing should succeed, but got: {processing_errors}"
        assert len(records) == 3, "Should have 3 records"
        
        # Check duplicates (should succeed)
        duplicate_errors = CSVProcessor.check_duplicates(records, DataType.ORDER)
        assert len(duplicate_errors) == 0, f"Should have no duplicate errors, but got: {duplicate_errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])