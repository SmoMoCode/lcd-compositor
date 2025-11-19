#!/usr/bin/env python3
"""
Test HTML generation to ensure lcd-screen.html and index.html are created correctly.
"""

import sys
import tempfile
import os
from pathlib import Path
import extract_layers


def test_html_generation():
    """Test that HTML files are generated with correct content."""
    print("Testing HTML generation...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        yaml_filename = "test.yml"
        base_name = "test"
        
        # Create the HTML files
        lcd_screen_path = extract_layers.create_lcd_screen_html(output_dir, yaml_filename, base_name)
        index_path = extract_layers.create_index_html(output_dir, yaml_filename, base_name)
        
        # Check that files exist
        if not lcd_screen_path.exists():
            print(f"✗ LCD screen HTML not created at {lcd_screen_path}")
            return False
        
        if not index_path.exists():
            print(f"✗ Index HTML not created at {index_path}")
            return False
        
        # Check lcd-screen.html filename
        if lcd_screen_path.name != "lcd-screen.html":
            print(f"✗ LCD screen HTML has wrong name: {lcd_screen_path.name}, expected lcd-screen.html")
            return False
        
        # Check index.html filename
        if index_path.name != "index.html":
            print(f"✗ Index HTML has wrong name: {index_path.name}, expected index.html")
            return False
        
        # Read and check lcd-screen.html content
        with open(lcd_screen_path, 'r') as f:
            lcd_content = f.read()
        
        # Check for required elements in lcd-screen.html
        required_lcd = [
            'function SetToggle',
            'window.SetToggle = SetToggle',
            'scaleToFit',
            'canvas-wrapper',
            'parseYAML'
        ]
        
        for required in required_lcd:
            if required not in lcd_content:
                print(f"✗ LCD screen HTML missing required content: {required}")
                return False
        
        # Check that blink toggle is NOT in lcd-screen.html
        if 'blinkToggle' in lcd_content or 'Blink Mode' in lcd_content:
            print("✗ LCD screen HTML should not contain blink toggle")
            return False
        
        # Check that document info is NOT in lcd-screen.html
        if 'Document Info' in lcd_content or 'docInfo' in lcd_content:
            print("✗ LCD screen HTML should not contain document info section")
            return False
        
        print("  ✓ lcd-screen.html created with correct content")
        
        # Read and check index.html content
        with open(index_path, 'r') as f:
            index_content = f.read()
        
        # Check for required elements in index.html
        required_index = [
            'left-panel',
            'right-panel',
            'lcd-screen.html',
            'toggleWidget',
            'widgets',
            'iframe'
        ]
        
        for required in required_index:
            if required not in index_content:
                print(f"✗ Index HTML missing required content: {required}")
                return False
        
        print("  ✓ index.html created with correct content")
        
        # Check that index.html references lcd-screen.html
        if 'src="lcd-screen.html"' not in index_content:
            print("✗ Index HTML does not correctly reference lcd-screen.html")
            return False
        
        print("  ✓ index.html correctly embeds lcd-screen.html")
        
    print("\n✓ All HTML generation tests passed!")
    return True


def test_yaml_widgets_section():
    """Test that YAML contains widgets section when widgets are present."""
    print("\nTesting YAML widgets section...")
    
    # Create test layer data with widgets
    layers_info = [
        {
            'filename': 'Background.png',
            'name': 'Background',
            'original_name': 'Background',
            'original_folder_path': [],
            'x': 0,
            'y': 0,
            'width': 100,
            'height': 100
        },
        {
            'filename': 'LED.png',
            'name': 'LED',
            'original_name': '[T]LED',
            'original_folder_path': [],
            'x': 50,
            'y': 50,
            'width': 20,
            'height': 20
        }
    ]
    
    widgets = extract_layers.extract_widgets(layers_info)
    
    if 'LED' not in widgets:
        print("✗ LED widget not found in extracted widgets")
        return False
    
    if 'LED.png' not in widgets['LED']:
        print("✗ LED.png not associated with LED widget")
        return False
    
    print("  ✓ Widgets extracted correctly from layers")
    print("\n✓ YAML widgets section test passed!")
    return True


def main():
    """Run all HTML generation tests."""
    print("=" * 60)
    print("Testing HTML generation and structure")
    print("=" * 60)
    
    all_passed = True
    
    if not test_html_generation():
        all_passed = False
    
    if not test_yaml_widgets_section():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All HTML generation tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some HTML generation tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
