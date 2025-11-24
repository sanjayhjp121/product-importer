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
        normalized_row = {k.lower().strip(): v.strip() if v else None for k, v in row.items()}
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
    if not row.get('sku'):
        return False, f"Row {row_number}: SKU is required"
    
    if not row.get('name'):
        return False, f"Row {row_number}: Name is required"
    
    # SKU should not be empty after stripping
    sku = row['sku'].strip()
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
    return {
        'sku': row['sku'].strip(),
        'name': row['name'].strip(),
        'description': row.get('description', '').strip() or None,
        'active': True  # Default to active
    }

