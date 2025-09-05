import pandas as pd
from io import StringIO
from typing import List, Dict, Any, Tuple
from app.schemas import DataType


class CSVProcessor:
    @staticmethod
    def extract_ebay_seller_id(file_content: str) -> str | None:
        """
        Extract eBay seller ID from CSV footer
        eBay CSV exports typically have "Seller ID : username" at the end
        """
        try:
            lines = file_content.strip().split('\n')
            # Look through the last few lines for seller ID pattern
            for line in reversed(lines[-10:]):  # Check last 10 lines
                line = line.strip()
                if line.startswith('Seller ID') and ':' in line:
                    # Extract seller ID after the colon
                    seller_id = line.split(':', 1)[1].strip()
                    if seller_id:
                        return seller_id
            return None
        except Exception as e:
            print(f"Error extracting eBay seller ID: {e}")
            return None

    @staticmethod
    def extract_username_from_filename(filename: str) -> str | None:
        """
        Extract username from filename patterns
        Common patterns: username_orders.csv, username_listings.csv, orders_username.csv
        """
        try:
            import re
            # Remove file extension
            name_without_ext = filename.rsplit('.', 1)[0]
            
            # Pattern 1: username_orders or username_listings  
            match = re.match(r'^([a-zA-Z0-9_-]+)_(orders|listings)$', name_without_ext, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Pattern 2: orders_username or listings_username
            match = re.match(r'^(orders|listings)_([a-zA-Z0-9_-]+)$', name_without_ext, re.IGNORECASE)
            if match:
                return match.group(2)
                
            # Pattern 3: just username (if filename is simple username.csv)
            if re.match(r'^[a-zA-Z0-9_-]+$', name_without_ext):
                return name_without_ext
                
            return None
        except Exception as e:
            print(f"Error extracting username from filename: {e}")
            return None

    @staticmethod
    def detect_platform_username(file_content: str, filename: str = "", account_type: str = "ebay") -> str | None:
        """
        Detect platform-specific username from CSV content and filename
        Tries multiple detection methods in order of reliability
        """
        detected_username = None
        
        # Method 1: Extract from CSV footer (most reliable for eBay)
        if account_type.lower() == "ebay":
            detected_username = CSVProcessor.extract_ebay_seller_id(file_content)
        # Future: Add Etsy detection logic here
        # elif account_type.lower() == "etsy":
        #     detected_username = CSVProcessor.extract_etsy_shop_name(file_content)
        
        # Method 2: Extract from filename (fallback)
        if not detected_username and filename:
            detected_username = CSVProcessor.extract_username_from_filename(filename)
            
        return detected_username

    @staticmethod
    def _is_valid_order_number(order_number) -> bool:
        """
        Validate Order Number format - SOLID: Single Responsibility
        Order Numbers must:
        1. Not be empty or None
        2. Contain at least one digit
        3. Can be alphanumeric (e.g., "123456", "ORD-123456", "123456-789")
        """
        import re
        import pandas as pd
        
        # Handle pandas NaN values
        if pd.isna(order_number):
            return False
        
        order_number_str = str(order_number).strip()
        
        if not order_number_str or order_number_str.lower() in ['none', 'null', 'nan', '']:
            return False
        
        # Must contain at least one digit
        if not re.search(r'\d', order_number_str):
            return False
        
        # Check if it's not just whitespace or special characters
        if not re.search(r'[a-zA-Z0-9]', order_number_str):
            return False
            
        return True

    @staticmethod
    def validate_order_csv(df: pd.DataFrame) -> List[str]:
        """Validate order CSV format and return error messages if any"""
        # Real eBay column names (may have quotes)
        required_columns = [
            "Order Number", "Item Number", "Item Title", 
            "Buyer Username", "Buyer Name", "Sale Date",
            "Sold For", "Quantity"  # eBay uses "Sold For" instead of "Total Price"
        ]
        
        errors = []
        # Normalize column names by stripping quotes and whitespace
        actual_columns = [col.strip().strip('"').strip("'") for col in df.columns]
        
        missing_columns = []
        for required_col in required_columns:
            if required_col not in actual_columns:
                missing_columns.append(required_col)
        
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            # Debug info for troubleshooting
            errors.append(f"Available columns: {', '.join(actual_columns[:10])}...")  # Show first 10 columns
            return errors  # Return early if columns are missing
        
        # Validate Order Number format (SOLID: Single Responsibility - Order Number validation)
        if "Order Number" in actual_columns:
            invalid_order_numbers = []
            for index, row in df.iterrows():
                order_number = str(row.get("Order Number", "")).strip()
                if not CSVProcessor._is_valid_order_number(order_number):
                    invalid_order_numbers.append(f"Row {index + 2}: '{order_number}'")  # +2 for 1-indexed and header
            
            if invalid_order_numbers:
                errors.append(f"Invalid Order Numbers found (must contain digits): {'; '.join(invalid_order_numbers[:5])}")
                if len(invalid_order_numbers) > 5:
                    errors.append(f"... and {len(invalid_order_numbers) - 5} more invalid Order Numbers")
        
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
            
            # Normalize column names by stripping quotes and whitespace
            df.columns = [col.strip().strip('"').strip("'") for col in df.columns]
            
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
        """
        Extract the unique identifier from a CSV record with validation
        SOLID: Single Responsibility - Extract and validate item ID
        """
        import pandas as pd
        
        if data_type == DataType.ORDER:
            order_number_raw = record.get("Order Number", "")
            
            # Handle pandas NaN values
            if pd.isna(order_number_raw):
                raise ValueError(f"Invalid Order Number: 'NaN' (must contain digits)")
            
            order_number = str(order_number_raw).strip()
            # Validate Order Number before extracting (Dependency Inversion: rely on validation abstraction)
            if not CSVProcessor._is_valid_order_number(order_number_raw):
                raise ValueError(f"Invalid Order Number: '{order_number}' (must contain digits)")
            return order_number
        else:  # LISTING
            item_number_raw = record.get("Item number", "")
            
            # Handle pandas NaN values
            if pd.isna(item_number_raw):
                raise ValueError(f"Invalid Item Number: 'NaN' (cannot be empty)")
                
            item_number = str(item_number_raw).strip()
            if not item_number or item_number.lower() in ['none', 'null', 'nan', '']:
                raise ValueError(f"Invalid Item Number: '{item_number}' (cannot be empty)")
            return item_number

    @staticmethod
    def check_duplicates(records: List[Dict[str, Any]], data_type: DataType) -> List[str]:
        """
        Check for duplicate item IDs in the records
        SOLID: Single Responsibility - Only check duplicates, validation is done elsewhere
        """
        errors = []
        item_ids = []
        
        # Extract item IDs with error handling for validation
        for i, record in enumerate(records):
            try:
                item_id = CSVProcessor.extract_item_id(record, data_type)
                item_ids.append(item_id)
            except ValueError as e:
                errors.append(f"Record {i + 1}: {str(e)}")
        
        # Return early if there are validation errors
        if errors:
            return errors
        
        # Check for duplicates
        duplicates = []
        seen = set()
        
        for item_id in item_ids:
            if item_id in seen and item_id not in duplicates:
                duplicates.append(item_id)
            seen.add(item_id)
        
        if duplicates:
            errors.append(f"Duplicate item IDs found: {', '.join(duplicates)}")
        
        return errors