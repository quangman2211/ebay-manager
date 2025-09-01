#!/usr/bin/env python3
"""
Comprehensive tests for CSV processing service
"""
import pytest
import pandas as pd
from app.csv_service import CSVProcessor
from app.schemas import DataType


class TestCSVProcessor:
    """Test CSV processing functionality"""

    def test_validate_order_csv_valid(self):
        """Test that valid order CSV passes validation"""
        data = {
            "Order Number": ["123456", "789012"],
            "Item Number": ["ITEM-001", "ITEM-002"],
            "Item Title": ["Test Item 1", "Test Item 2"],
            "Buyer Username": ["buyer1", "buyer2"],
            "Buyer Name": ["John Doe", "Jane Smith"],
            "Sale Date": ["2024-01-01", "2024-01-02"],
            "Sold For": ["$29.99", "$39.99"],
            "Quantity": [1, 2]
        }
        df = pd.DataFrame(data)
        errors = CSVProcessor.validate_order_csv(df)
        assert errors == []

    def test_validate_order_csv_missing_columns(self):
        """Test that order CSV with missing columns fails validation"""
        data = {
            "Order Number": ["123456"],
            "Item Number": ["ITEM-001"]
            # Missing other required columns
        }
        df = pd.DataFrame(data)
        errors = CSVProcessor.validate_order_csv(df)
        assert len(errors) == 1
        assert "Missing required columns" in errors[0]
        assert "Item Title" in errors[0]
        assert "Buyer Username" in errors[0]

    def test_validate_listing_csv_valid(self):
        """Test that valid listing CSV passes validation"""
        data = {
            "Item number": ["ITEM-001", "ITEM-002"],
            "Title": ["Test Listing 1", "Test Listing 2"],
            "Available quantity": [10, 5],
            "Current price": ["$29.99", "$39.99"],
            "Sold quantity": [3, 1],
            "Format": ["Buy It Now", "Auction"]
        }
        df = pd.DataFrame(data)
        errors = CSVProcessor.validate_listing_csv(df)
        assert errors == []

    def test_validate_listing_csv_missing_columns(self):
        """Test that listing CSV with missing columns fails validation"""
        data = {
            "Item number": ["ITEM-001"],
            "Title": ["Test Listing"]
            # Missing other required columns
        }
        df = pd.DataFrame(data)
        errors = CSVProcessor.validate_listing_csv(df)
        assert len(errors) == 1
        assert "Missing required columns" in errors[0]
        assert "Available quantity" in errors[0]

    def test_process_csv_file_order_success(self):
        """Test successful processing of order CSV"""
        csv_content = '''Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity
123456,ITEM-001,Test Item,buyer1,John Doe,2024-01-01,$29.99,1
789012,ITEM-002,Another Item,buyer2,Jane Smith,2024-01-02,$39.99,2'''
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert errors == []
        assert len(records) == 2
        assert records[0]["Order Number"] == 123456
        assert records[0]["Item Title"] == "Test Item"
        assert records[1]["Order Number"] == 789012

    def test_process_csv_file_listing_success(self):
        """Test successful processing of listing CSV"""
        csv_content = '''Item number,Title,Available quantity,Current price,Sold quantity,Format
ITEM-001,Test Listing 1,10,$29.99,3,Buy It Now
ITEM-002,Test Listing 2,5,$39.99,1,Auction'''
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.LISTING)
        
        assert errors == []
        assert len(records) == 2
        assert records[0]["Item number"] == "ITEM-001"
        assert records[0]["Title"] == "Test Listing 1"
        assert records[1]["Available quantity"] == 5

    def test_process_csv_file_with_bom(self):
        """Test processing CSV with BOM (Byte Order Mark)"""
        csv_content = '\ufeffOrder Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity\n123456,ITEM-001,Test Item,buyer1,John Doe,2024-01-01,$29.99,1'
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert errors == []
        assert len(records) == 1
        assert records[0]["Order Number"] == 123456

    def test_process_csv_file_with_empty_rows_at_top(self):
        """Test processing CSV with empty rows at the beginning"""
        csv_content = '''

"Order Number","Item Number","Item Title","Buyer Username","Buyer Name","Sale Date","Sold For","Quantity"
"123456","ITEM-001","Test Item","buyer1","John Doe","2024-01-01","$29.99","1"'''
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert errors == []
        assert len(records) == 1
        assert records[0]["Order Number"] == 123456

    def test_process_csv_file_invalid_format(self):
        """Test processing invalid CSV format"""
        csv_content = "Invalid,CSV,Format\nNo,Proper,Headers"
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert len(errors) == 1
        assert "Missing required columns" in errors[0]
        assert records == []

    def test_process_csv_file_empty_content(self):
        """Test processing empty CSV content"""
        csv_content = ""
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert len(errors) == 1
        assert "Error processing CSV" in errors[0]
        assert records == []

    def test_process_csv_file_malformed_content(self):
        """Test processing malformed CSV content"""
        csv_content = "Order Number,Item Number\n123456,ITEM-001,EXTRA,COLUMN"
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert len(errors) == 1
        assert "Missing required columns" in errors[0]
        assert records == []

    def test_process_csv_file_with_nan_values(self):
        """Test processing CSV with NaN/empty values"""
        csv_content = '''Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity
123456,ITEM-001,Test Item,buyer1,,2024-01-01,$29.99,1
789012,ITEM-002,Another Item,buyer2,Jane Smith,,,$39.99'''
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert errors == []
        assert len(records) == 2
        assert records[0]["Buyer Name"] is None
        assert records[1]["Sale Date"] is None

    def test_extract_item_id_order(self):
        """Test extracting item ID from order record"""
        record = {"Order Number": "123456", "Item Number": "ITEM-001"}
        item_id = CSVProcessor.extract_item_id(record, DataType.ORDER)
        assert item_id == "123456"

    def test_extract_item_id_listing(self):
        """Test extracting item ID from listing record"""
        record = {"Item number": "ITEM-001", "Title": "Test Listing"}
        item_id = CSVProcessor.extract_item_id(record, DataType.LISTING)
        assert item_id == "ITEM-001"

    def test_extract_item_id_missing_field(self):
        """Test extracting item ID when field is missing"""
        record = {"Title": "Test Listing"}
        item_id = CSVProcessor.extract_item_id(record, DataType.ORDER)
        assert item_id == ""

    def test_check_duplicates_none_found(self):
        """Test duplicate checking when no duplicates exist"""
        records = [
            {"Order Number": "123456"},
            {"Order Number": "789012"},
            {"Order Number": "345678"}
        ]
        errors = CSVProcessor.check_duplicates(records, DataType.ORDER)
        assert errors == []

    def test_check_duplicates_found(self):
        """Test duplicate checking when duplicates exist"""
        records = [
            {"Order Number": "123456"},
            {"Order Number": "789012"},
            {"Order Number": "123456"},  # Duplicate
            {"Order Number": "789012"}   # Another duplicate
        ]
        errors = CSVProcessor.check_duplicates(records, DataType.ORDER)
        assert len(errors) == 1
        assert "Duplicate item IDs found" in errors[0]
        assert "123456" in errors[0]
        assert "789012" in errors[0]

    def test_check_duplicates_single_duplicate(self):
        """Test duplicate checking with single duplicate"""
        records = [
            {"Item number": "ITEM-001"},
            {"Item number": "ITEM-002"},
            {"Item number": "ITEM-001"}  # Duplicate
        ]
        errors = CSVProcessor.check_duplicates(records, DataType.LISTING)
        assert len(errors) == 1
        assert "ITEM-001" in errors[0]

    def test_check_duplicates_empty_records(self):
        """Test duplicate checking with empty records"""
        records = []
        errors = CSVProcessor.check_duplicates(records, DataType.ORDER)
        assert errors == []

    def test_integration_full_workflow_order(self):
        """Test complete workflow for order CSV processing"""
        csv_content = '''Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity
123456,ITEM-001,Test Item 1,buyer1,John Doe,2024-01-01,$29.99,1
789012,ITEM-002,Test Item 2,buyer2,Jane Smith,2024-01-02,$39.99,2
345678,ITEM-003,Test Item 3,buyer3,Bob Johnson,2024-01-03,$19.99,1'''
        
        # Process CSV
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        assert errors == []
        assert len(records) == 3
        
        # Check for duplicates
        duplicate_errors = CSVProcessor.check_duplicates(records, DataType.ORDER)
        assert duplicate_errors == []
        
        # Extract item IDs
        item_ids = [CSVProcessor.extract_item_id(record, DataType.ORDER) for record in records]
        assert item_ids == ["123456", "789012", "345678"]

    def test_integration_full_workflow_listing(self):
        """Test complete workflow for listing CSV processing"""
        csv_content = '''Item number,Title,Available quantity,Current price,Sold quantity,Format
ITEM-001,Test Listing 1,10,$29.99,3,Buy It Now
ITEM-002,Test Listing 2,5,$39.99,1,Auction
ITEM-003,Test Listing 3,15,$19.99,5,Buy It Now'''
        
        # Process CSV
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.LISTING)
        assert errors == []
        assert len(records) == 3
        
        # Check for duplicates
        duplicate_errors = CSVProcessor.check_duplicates(records, DataType.LISTING)
        assert duplicate_errors == []
        
        # Extract item IDs
        item_ids = [CSVProcessor.extract_item_id(record, DataType.LISTING) for record in records]
        assert item_ids == ["ITEM-001", "ITEM-002", "ITEM-003"]

    def test_large_dataset_performance(self):
        """Test processing large CSV dataset efficiently"""
        # Create large dataset
        large_data = []
        header = "Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity"
        large_data.append(header)
        
        for i in range(1000):
            row = f"{100000+i},ITEM-{i:04d},Test Item {i},buyer{i},User {i},2024-01-{(i%28)+1:02d},$29.99,1"
            large_data.append(row)
        
        csv_content = '\n'.join(large_data)
        
        # Process should complete without timeout
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert errors == []
        assert len(records) == 1000
        assert records[0]["Order Number"] == 100000
        assert records[-1]["Order Number"] == 100999

    def test_special_characters_handling(self):
        """Test handling of special characters in CSV data"""
        csv_content = '''Order Number,Item Number,Item Title,Buyer Username,Buyer Name,Sale Date,Sold For,Quantity
123456,ITEM-001,"Item with ""quotes""",buyer1,"José García",2024-01-01,$29.99,1
789012,ITEM-002,"Item with, comma",buyer2,李明,2024-01-02,$39.99,2'''
        
        records, errors = CSVProcessor.process_csv_file(csv_content, DataType.ORDER)
        
        assert errors == []
        assert len(records) == 2
        assert 'quotes' in records[0]["Item Title"]
        assert records[0]["Buyer Name"] == "José García"
        assert records[1]["Buyer Name"] == "李明"
        assert "comma" in records[1]["Item Title"]