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