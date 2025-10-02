#!/usr/bin/env python3
"""
Test script to verify content comparison logic in organize_jobs_by_date
"""

import json
import tempfile
import os

def test_content_comparison():
    """Test the content comparison logic."""
    
    # Sample data
    test_data = [
        {
            "job_id": "123",
            "title": "Software Engineer",
            "locations": ["Seattle, WA"],
            "date_posted": "2025-10-01"
        },
        {
            "job_id": "456", 
            "title": "Python Developer",
            "locations": ["Remote"],
            "date_posted": "2025-10-01"
        }
    ]
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        # Save with json.dump (what we used to do)
        json.dump(test_data, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    try:
        # Read the file content
        with open(temp_file, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Generate new content with json.dumps (what we do now)
        current_content = json.dumps(test_data, ensure_ascii=False, indent=2)
        
        print("=== CONTENT COMPARISON TEST ===")
        print(f"Existing content length: {len(existing_content)}")
        print(f"Current content length: {len(current_content)}")
        print(f"Contents are equal: {current_content == existing_content}")
        
        if current_content != existing_content:
            print("\n=== DIFFERENCES ===")
            print("Existing content:")
            print(repr(existing_content))
            print("\nCurrent content:")
            print(repr(current_content))
            
            # Try comparing the parsed JSON instead
            try:
                existing_data = json.loads(existing_content)
                current_data = json.loads(current_content)
                print(f"\nParsed data are equal: {existing_data == current_data}")
            except Exception as e:
                print(f"Error parsing JSON: {e}")
        
    finally:
        os.unlink(temp_file)

def test_content_comparison_robust():
    """Test a more robust content comparison approach."""
    
    test_data = [{"job_id": "123", "title": "Test Job"}]
    
    # Test with different formatting
    content1 = json.dumps(test_data, ensure_ascii=False, indent=2)
    content2 = json.dumps(test_data, ensure_ascii=False, indent=4)  # Different indentation
    content3 = json.dumps(test_data, ensure_ascii=False)  # No indentation
    
    print("\n=== ROBUST COMPARISON TEST ===")
    print(f"Content1 == Content2: {content1 == content2}")
    print(f"Content1 == Content3: {content1 == content3}")
    
    # Try parsing and comparing
    try:
        data1 = json.loads(content1)
        data2 = json.loads(content2)
        data3 = json.loads(content3)
        
        print(f"Parsed data1 == data2: {data1 == data2}")
        print(f"Parsed data1 == data3: {data1 == data3}")
    except Exception as e:
        print(f"Error in robust test: {e}")

if __name__ == "__main__":
    test_content_comparison()
    test_content_comparison_robust()