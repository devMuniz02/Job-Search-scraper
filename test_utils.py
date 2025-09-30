#!/usr/bin/env python3
"""
Test script for the utility modules

Simple tests to verify that the extracted utilities work correctly.
"""

import os
import tempfile
from datetime import datetime

def test_string_utilities():
    """Test string utility functions."""
    print("Testing string utilities...")
    
    from utils import norm, to_text, kw_boundary_search
    
    # Test norm function
    assert norm("  hello   world  ") == "hello world"
    assert norm(None) == ""
    assert norm("") == ""
    print("✓ norm() working correctly")
    
    # Test to_text function
    assert to_text("hello") == "hello"
    assert to_text(["item1", "item2"]) == "item1 | item2"
    assert to_text({"key": "value"}) == '{"key": "value"}'
    print("✓ to_text() working correctly")
    
    # Test keyword boundary search
    assert kw_boundary_search("python developer", "python") == True
    assert kw_boundary_search("python-dev", "python") == True
    assert kw_boundary_search("pythonic", "python") == False
    print("✓ kw_boundary_search() working correctly")


def test_date_utilities():
    """Test date utility functions."""
    print("\nTesting date utilities...")
    
    from utils import parse_date
    
    # Test various date formats
    date1 = parse_date("Jan 15, 2024")
    assert date1.year == 2024
    assert date1.month == 1
    assert date1.day == 15
    
    date2 = parse_date("2024-01-15")
    assert date2.year == 2024
    
    # Test invalid date
    invalid_date = parse_date("invalid")
    assert invalid_date == datetime.max
    
    print("✓ parse_date() working correctly")


def test_file_utilities():
    """Test file and database utility functions."""
    print("\nTesting file utilities...")
    
    from utils import load_db, save_db_atomic, upsert_rows
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, "test_db.json")
        
        # Test loading non-existent database
        db = load_db(test_db_path)
        assert db == {}
        print("✓ load_db() handles missing files correctly")
        
        # Test saving and loading database
        test_data = {"job1": {"title": "Software Engineer", "id": "123"}}
        save_db_atomic(test_db_path, test_data)
        
        loaded_data = load_db(test_db_path)
        assert loaded_data == test_data
        print("✓ save_db_atomic() and load_db() working correctly")
        
        # Test upsert_rows
        new_rows = [
            {"job_id": "job2", "title": "Data Scientist"},
            {"job_id": "job3", "title": "Product Manager"}
        ]
        added_count = upsert_rows(loaded_data, new_rows)
        assert added_count == 2
        assert len(loaded_data) == 3
        print("✓ upsert_rows() working correctly")


def test_html_utilities():
    """Test HTML processing utilities."""
    print("\nTesting HTML utilities...")
    
    from utils import extract_pay_ranges, block_text_from_html
    
    # Test pay range extraction
    text_with_pay = "The salary is USD $80,000 - $120,000 for this role"
    ranges = extract_pay_ranges(text_with_pay)
    assert len(ranges) == 1
    assert ranges[0]["range"] == "USD $80,000 - $120,000"
    print("✓ extract_pay_ranges() working correctly")
    
    # Test HTML to text conversion
    html = "<p>Hello</p><ul><li>Item 1</li><li>Item 2</li></ul><p>World</p>"
    text = block_text_from_html(html)
    assert "Hello" in text
    assert "• Item 1" in text
    assert "• Item 2" in text
    assert "World" in text
    print("✓ block_text_from_html() working correctly")


def test_url_utilities():
    """Test URL utility functions."""
    print("\nTesting URL utilities...")
    
    from utils import with_page
    
    # Test page URL modification
    base_url = "https://example.com/search?q=test&pg=1"
    page_2_url = with_page(base_url, 2)
    assert "pg=2" in page_2_url
    print("✓ with_page() working correctly")


def test_pattern_utilities():
    """Test text pattern utilities."""
    print("\nTesting pattern utilities...")
    
    from utils import find_span, slice_between, REQ_RE, PREF_RE
    
    # Test find_span
    text = "Required Qualifications: Python experience. Preferred Qualifications: AWS knowledge."
    start, end = find_span(text, REQ_RE)
    assert start is not None
    assert text[start:end] == "Required Qualifications"
    print("✓ find_span() working correctly")
    
    # Test slice_between
    req_text = slice_between(text, REQ_RE, (PREF_RE,))
    assert "Python experience" in req_text
    assert "AWS knowledge" not in req_text
    print("✓ slice_between() working correctly")


def test_configuration():
    """Test configuration module."""
    print("\nTesting configuration...")
    
    from utils import SEARCH_URL, DB_PATH, MAX_PAGES, AVOID_RULES
    
    # Verify key configurations exist
    assert isinstance(SEARCH_URL, str)
    assert "microsoft.com" in SEARCH_URL
    assert isinstance(DB_PATH, str)
    assert isinstance(MAX_PAGES, int)
    assert isinstance(AVOID_RULES, dict)
    
    print("✓ Configuration module loaded correctly")


def main():
    """Run all tests."""
    print("Running utility module tests...")
    print("=" * 50)
    
    try:
        test_string_utilities()
        test_date_utilities()  
        test_file_utilities()
        test_html_utilities()
        test_url_utilities()
        test_pattern_utilities()
        test_configuration()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Utility modules are working correctly.")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())