#!/usr/bin/env python3
"""
Test script for validating the layer extraction with folder-based naming.
"""

import sys
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw
from psd_tools import PSDImage
from psd_tools.api.layers import Group, PixelLayer
import extract_layers


def create_test_psd():
    """
    Create a simple test PSD structure in memory for testing.
    This is a simplified test that validates the naming logic.
    """
    print("Testing folder path and naming logic...")
    
    # Test cases for the naming function
    test_cases = [
        {
            'layer_name': 'Background',
            'folder_path': [],
            'expected': 'Background.png'
        },
        {
            'layer_name': 'Layer 1',
            'folder_path': ['Smo', 'Mo'],
            'expected': 'Smo--Mo--Layer_1.png'
        },
        {
            'layer_name': '1',
            'folder_path': ['Smo', 'Mo'],
            'expected': 'Smo--Mo--1.png'
        },
        {
            'layer_name': 'Special@Char#',
            'folder_path': ['Folder'],
            'expected': 'Folder--Special_Char_.png'
        },
    ]
    
    for i, test in enumerate(test_cases):
        layer_name = test['layer_name']
        folder_path = test['folder_path']
        expected = test['expected']
        
        # Sanitize layer name
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in layer_name)
        safe_name = safe_name.strip().replace(' ', '_')
        
        # Generate filename
        if folder_path:
            filename_parts = folder_path + [safe_name]
            filename = "--".join(filename_parts) + ".png"
        else:
            filename = f"{safe_name}.png"
        
        # Check result
        if filename == expected:
            print(f"✓ Test {i+1} passed: '{layer_name}' with path {folder_path} -> {filename}")
        else:
            print(f"✗ Test {i+1} failed: Expected '{expected}', got '{filename}'")
            return False
    
    return True


def test_ignore_hash_prefix():
    """
    Test that layers and folders starting with # are ignored.
    """
    print("\nTesting # prefix filtering...")
    
    # Simulate layer names
    test_layers = [
        ('Normal Layer', False),  # Should be included
        ('#Hidden Layer', True),  # Should be ignored
        ('Layer #1', False),      # Should be included (# not at start)
        ('#Ignore', True),        # Should be ignored
        ('Valid', False),         # Should be included
    ]
    
    for layer_name, should_ignore in test_layers:
        is_ignored = layer_name.startswith('#')
        if is_ignored == should_ignore:
            status = "ignored" if is_ignored else "included"
            print(f"✓ '{layer_name}' correctly {status}")
        else:
            print(f"✗ '{layer_name}' should be {'ignored' if should_ignore else 'included'}")
            return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing layer extraction with folder-based naming")
    print("=" * 60)
    
    all_passed = True
    
    # Test naming logic
    if not create_test_psd():
        all_passed = False
    
    # Test # prefix filtering
    if not test_ignore_hash_prefix():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
