"""CSV processing service."""
import csv
import io
from typing import Iterator, Dict, List, Optional
from app.models import Product


def parse_csv_file(file_content: bytes) -> Iterator[Dict[str, str]]:
    """
    Parse CSV file content and yield rows as dictionaries.
    
    Args:
        file_content: Raw bytes of CSV file
        
    Yields:
        Dictionary with row data (keys are lowercase column names)
    """
    text_content = file_content.decode('utf-8-sig')  # Handle BOM
    reader = csv.DictReader(io.StringIO(text_content))
    
    for row in reader:
        # Normalize keys to lowercase and strip whitespace
        # Skip None or empty keys (empty column headers)
        normalized_row = {}
        for k, v in row.items():
            if k is not None:
                key = k.lower().strip()
                if key:  # Only add non-empty keys
                    normalized_row[key] = v.strip() if v else None
        yield normalized_row


def validate_csv_row(row: Dict[str, str], row_number: int) -> tuple[bool, Optional[str]]:
    """
    Validate a CSV row.
    
    Args:
        row: Dictionary with row data
        row_number: Row number for error reporting
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check required fields
    sku_value = row.get('sku')
    if not sku_value:
        return False, f"Row {row_number}: SKU is required"
    
    name_value = row.get('name')
    if not name_value:
        return False, f"Row {row_number}: Name is required"
    
    # SKU should not be empty after stripping
    sku = sku_value.strip() if sku_value else ''
    if not sku:
        return False, f"Row {row_number}: SKU cannot be empty"
    
    return True, None


def row_to_product_dict(row: Dict[str, str]) -> Dict:
    """
    Convert CSV row to product dictionary for database insertion.
    
    Args:
        row: Dictionary with row data
        
    Returns:
        Dictionary with product fields
    """
    sku_value = row.get('sku', '')
    name_value = row.get('name', '')
    desc_value = row.get('description', '')
    
    return {
        'sku': sku_value.strip() if sku_value else '',
        'name': name_value.strip() if name_value else '',
        'description': desc_value.strip() if desc_value else None,
        'active': True  # Default to active
    }

