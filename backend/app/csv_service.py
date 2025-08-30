import pandas as pd
from io import StringIO
from typing import List, Dict, Any, Tuple
from app.schemas import DataType


class CSVProcessor:
    @staticmethod
    def validate_order_csv(df: pd.DataFrame) -> List[str]:
        """Validate order CSV format and return error messages if any"""
        required_columns = [
            "Order Number", "Item Number", "Item Title", 
            "Buyer Username", "Buyer Name", "Sale Date",
            "Sold For", "Quantity"  # eBay uses "Sold For" instead of "Total Price"
        ]
        
        errors = []
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        return errors

    @staticmethod
    def validate_listing_csv(df: pd.DataFrame) -> List[str]:
        """Validate listing CSV format and return error messages if any"""
        required_columns = [
            "Item number", "Title", "Available quantity",
            "Current price", "Sold quantity", "Format"
        ]
        
        errors = []
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        return errors

    @staticmethod
    def process_csv_file(file_content: str, data_type: DataType) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Process CSV file and return parsed data and any errors"""
        try:
            # Handle BOM (Byte Order Mark) if present
            if file_content.startswith('\ufeff'):
                file_content = file_content[1:]
            
            # Special handling for eBay CSV files that might have empty rows at the top
            lines = file_content.strip().split('\n')
            
            # Find the first line that contains actual column headers (has quoted strings)
            header_line_idx = 0
            for i, line in enumerate(lines):
                if '"' in line and 'Order Number' in line:  # Look for actual header content
                    header_line_idx = i
                    break
                elif '"' in line and 'Item number' in line:  # For listing CSV
                    header_line_idx = i
                    break
            
            # Reconstruct CSV content starting from header
            csv_lines = lines[header_line_idx:]
            # Filter out any lines that are just empty commas
            filtered_lines = []
            for line in csv_lines:
                if line.strip() and not line.strip().replace(',', '').replace('"', '') == '':
                    filtered_lines.append(line)
            
            cleaned_csv = '\n'.join(filtered_lines)
            df = pd.read_csv(StringIO(cleaned_csv))
            
            # Remove empty rows after header
            df = df.dropna(how='all')
            
            # Validate CSV format
            if data_type == DataType.ORDER:
                errors = CSVProcessor.validate_order_csv(df)
            else:
                errors = CSVProcessor.validate_listing_csv(df)
            
            if errors:
                return [], errors
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict('records')
            
            # Clean up the records - remove NaN values
            cleaned_records = []
            for record in records:
                cleaned_record = {k: (v if pd.notna(v) else None) for k, v in record.items()}
                cleaned_records.append(cleaned_record)
            
            return cleaned_records, []
            
        except Exception as e:
            return [], [f"Error processing CSV: {str(e)}"]

    @staticmethod
    def extract_item_id(record: Dict[str, Any], data_type: DataType) -> str:
        """Extract the unique identifier from a CSV record"""
        if data_type == DataType.ORDER:
            return str(record.get("Order Number", ""))
        else:  # LISTING
            return str(record.get("Item number", ""))

    @staticmethod
    def check_duplicates(records: List[Dict[str, Any]], data_type: DataType) -> List[str]:
        """Check for duplicate item IDs in the records"""
        item_ids = [CSVProcessor.extract_item_id(record, data_type) for record in records]
        duplicates = []
        seen = set()
        
        for item_id in item_ids:
            if item_id in seen and item_id not in duplicates:
                duplicates.append(item_id)
            seen.add(item_id)
        
        if duplicates:
            return [f"Duplicate item IDs found: {', '.join(duplicates)}"]
        
        return []