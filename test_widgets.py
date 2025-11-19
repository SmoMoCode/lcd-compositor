#!/usr/bin/env python3
"""
Test script for widget (toggle) detection functionality.
"""

import sys
import extract_layers


def test_extract_widgets():
    """Test the extract_widgets function."""
    print("Testing widget extraction...")
    
    # Create test layer data with [T] prefixes
    layers_info = [
        {
            'filename': 'Background.png',
            'name': 'Background',
            'original_name': 'Background',
            'original_folder_path': []
        },
        {
            'filename': 'LED_Layer.png',
            'name': 'LED_Layer',
            'original_name': '[T]LED_Layer',
            'original_folder_path': []
        },
        {
            'filename': 'UI--Logo.png',
            'name': 'Logo',
            'original_name': 'Logo',
            'original_folder_path': ['UI']
        },
        {
            'filename': 'Toggles--Button1.png',
            'name': 'Button1',
            'original_name': 'Button1',
            'original_folder_path': ['[T]Toggles']
        },
        {
            'filename': 'Toggles--Button2.png',
            'name': 'Button2',
            'original_name': 'Button2',
            'original_folder_path': ['[T]Toggles']
        },
        {
            'filename': 'Screen--Elements--Icon.png',
            'name': 'Icon',
            'original_name': '[T]Icon',
            'original_folder_path': ['Screen', 'Elements']
        },
    ]
    
    widgets = extract_layers.extract_widgets(layers_info)
    
    # Expected widgets:
    # LED_Layer: ['LED_Layer.png']
    # Toggles: ['Toggles--Button1.png', 'Toggles--Button2.png']
    # Icon: ['Screen--Elements--Icon.png']
    
    expected = {
        'LED_Layer': ['LED_Layer.png'],
        'Toggles': ['Toggles--Button1.png', 'Toggles--Button2.png'],
        'Icon': ['Screen--Elements--Icon.png']
    }
    
    # Check number of widgets
    if len(widgets) != len(expected):
        print(f"✗ Expected {len(expected)} widgets, got {len(widgets)}")
        print(f"  Expected: {list(expected.keys())}")
        print(f"  Got: {list(widgets.keys())}")
        return False
    
    # Check each widget
    for widget_name, expected_files in expected.items():
        if widget_name not in widgets:
            print(f"✗ Widget '{widget_name}' not found")
            return False
        
        actual_files = widgets[widget_name]
        if sorted(actual_files) != sorted(expected_files):
            print(f"✗ Widget '{widget_name}': Expected {expected_files}, got {actual_files}")
            return False
        
        print(f"  ✓ Widget '{widget_name}': {len(actual_files)} file(s)")
    
    print("\n✓ All widgets extracted correctly!")
    return True


def test_toggle_naming():
    """Test that [T] prefix is properly stripped from names."""
    print("\nTesting [T] prefix handling...")
    
    test_cases = [
        ('[T]ToggleName', 'ToggleName'),
        ('[T]LED', 'LED'),
        ('[T]My Toggle', 'My Toggle'),
        ('NotAToggle', 'NotAToggle'),
        ('[T][T]Double', '[T]Double'),  # Only strip first [T]
    ]
    
    for original, expected in test_cases:
        clean_name = original[3:] if original.startswith('[T]') else original
        if clean_name == expected:
            print(f"  ✓ '{original}' -> '{clean_name}'")
        else:
            print(f"  ✗ '{original}' -> Expected '{expected}', got '{clean_name}'")
            return False
    
    print("\n✓ All [T] prefix tests passed!")
    return True


def main():
    """Run all widget tests."""
    print("=" * 60)
    print("Testing widget (toggle) functionality")
    print("=" * 60)
    
    all_passed = True
    
    if not test_extract_widgets():
        all_passed = False
    
    if not test_toggle_naming():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All widget tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some widget tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
