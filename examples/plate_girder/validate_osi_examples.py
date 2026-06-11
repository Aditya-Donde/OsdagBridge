#!/usr/bin/env python3
"""
OSI File Validator - Usage Examples

This script demonstrates how to use the OSI validator to check YAML configuration files
for correctness, completeness, and structural integrity.
"""

import sys
sys.path.insert(0, '/Users/nehasharma/osdagbridge/src')

from osdagbridge.desktop.ui.utils.test_Osi import OSIValidator


def example_1_validate_file():
    """Example 1: Validate a single OSI file"""
    validator = OSIValidator()
    
    # Validate the file
    result = validator.validate_osi_file('examples/plate_girder/example_osi_validation.yaml')
    
    # Check if valid
    if result['is_valid']:
        print("✅ OSI file is valid!")
        print(f"   Completeness: {result['completeness_score']:.1f}%")
    else:
        print("❌ OSI file has errors:")
        for error in result['errors']:
            print(f"   - {error}")
    
    # Check for warnings
    if result['warnings']:
        print("\n⚠️  Warnings:")
        for warning in result['warnings']:
            print(f"   - {warning}")


def example_2_check_completeness():
    """Example 2: Check data completeness"""
    validator = OSIValidator()
    result = validator.validate_osi_file('examples/plate_girder/example_osi_validation.yaml')
    
    print(f"\n📊 Completeness Score: {result['completeness_score']:.1f}%")
    
    if result['completeness_score'] < 100:
        print("\nMissing fields:")
        for error in result['errors']:
            if 'Missing' in error:
                print(f"  - {error}")


def example_3_check_value_ranges():
    """Example 3: Detect out-of-range values"""
    validator = OSIValidator()
    result = validator.validate_osi_file('examples/plate_girder/example_osi_invalid.yaml')
    
    print("\n📏 Value Range Errors:")
    for error in result['errors']:
        if 'Value at' in error:
            print(f"  - {error}")
    
    # Show suggested corrections
    if result['corrected_values']:
        print("\n💡 Suggested corrections:")
        for path, value in result['corrected_values'].items():
            print(f"  - {path} → {value}")


def example_4_check_structure():
    """Example 4: Check structural issues"""
    validator = OSIValidator()
    result = validator.validate_osi_file('examples/plate_girder/example_osi_validation.yaml')
    
    if result['structure_issues']:
        print("\n🏗️  Structure Issues:")
        for issue in result['structure_issues']:
            print(f"  - {issue}")
    else:
        print("\n✅ No structure issues found!")


if __name__ == "__main__":
    print("="*70)
    print("OSI FILE VALIDATOR - EXAMPLES")
    print("="*70)
    
    print("\n\n--- EXAMPLE 1: Basic Validation ---")
    example_1_validate_file()
    
    print("\n\n--- EXAMPLE 2: Completeness Check ---")
    example_2_check_completeness()
    
    print("\n\n--- EXAMPLE 3: Value Range Check ---")
    example_3_check_value_ranges()
    
    print("\n\n--- EXAMPLE 4: Structure Check ---")
    example_4_check_structure()
    
    print("\n" + "="*70)
    print("QUICK START:")
    print("="*70)
    print("\n1. From command line:")
    print("   python src/osdagbridge/desktop/ui/utils/test_Osi.py <your_osi_file.yaml>")
    print("\n2. In Python code:")
    print("   from osdagbridge.desktop.ui.utils.test_Osi import OSIValidator")
    print("   validator = OSIValidator()")
    print("   result = validator.validate_osi_file('path/to/file.yaml')")
    print("   print(result)")
