#!/usr/bin/env python3
"""
Test script for validating Number widget functionality.
"""

import sys
from test_integration import MockLayer
import extract_layers


def test_number_widget_basic():
    """Test that folders with [N] prefix are correctly identified as Number widgets."""
    print("Testing [N] Number widget with child digits...")
    
    root_layers = []
    
    # Number folder with 3 child digit folders
    number_folder = MockLayer("[N]Speed", is_group=True)
    
    # First digit (no decimal)
    digit1_folder = MockLayer("[D:7]", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 100 + i*10, 100, 50, 100)
        digit1_folder.add_child(segment)
    number_folder.add_child(digit1_folder)
    
    # Second digit (with decimal point)
    digit2_folder = MockLayer("[D:7p]", is_group=True)
    for i in range(8):  # 7 segments + decimal point
        segment = MockLayer(f"segment_{i}", 200 + i*10, 100, 50, 100)
        digit2_folder.add_child(segment)
    number_folder.add_child(digit2_folder)
    
    # Third digit (no decimal)
    digit3_folder = MockLayer("[D:7]", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 300 + i*10, 100, 50, 100)
        digit3_folder.add_child(segment)
    number_folder.add_child(digit3_folder)
    
    root_layers.append(number_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 7 + 8 + 7 = 22 layers (segments)
    if len(all_layers) != 22:
        print(f"✗ Expected 22 layers, got {len(all_layers)}")
        return False
    
    # Check that all layers have the correct number_widget_info
    number_widget_layers = [l for l in all_layers if l[4] is not None]
    if len(number_widget_layers) != 22:
        print(f"✗ Expected all 22 layers to have number_widget_info, got {len(number_widget_layers)}")
        return False
    
    # Verify the number widget name
    for layer, folder_path, toggle_name, widget_info, number_widget_info in all_layers:
        if number_widget_info is None:
            print(f"✗ Expected layer to have number_widget_info, got None")
            return False
        number_widget_name, digit_type, digit_name = number_widget_info
        if number_widget_name != "Speed":
            print(f"✗ Expected number widget name 'Speed', got '{number_widget_name}'")
            return False
    
    print("✓ Number widget [N] correctly identified with child digits")
    return True


def test_number_widget_with_named_digits():
    """Test Number widget with named child digits."""
    print("\nTesting [N] Number widget with named child digits...")
    
    root_layers = []
    
    # Number folder with named digit folders
    number_folder = MockLayer("[N]Temperature", is_group=True)
    
    # First digit (hundreds)
    digit1_folder = MockLayer("[D:7]hundreds", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 100 + i*10, 100, 50, 100)
        digit1_folder.add_child(segment)
    number_folder.add_child(digit1_folder)
    
    # Second digit (tens with decimal)
    digit2_folder = MockLayer("[D:7p]tens", is_group=True)
    for i in range(8):
        segment = MockLayer(f"segment_{i}", 200 + i*10, 100, 50, 100)
        digit2_folder.add_child(segment)
    number_folder.add_child(digit2_folder)
    
    # Third digit (ones)
    digit3_folder = MockLayer("[D:7]ones", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 300 + i*10, 100, 50, 100)
        digit3_folder.add_child(segment)
    number_folder.add_child(digit3_folder)
    
    root_layers.append(number_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 7 + 8 + 7 = 22 layers
    if len(all_layers) != 22:
        print(f"✗ Expected 22 layers, got {len(all_layers)}")
        return False
    
    # Verify digit names are preserved
    digit_names_found = set()
    for layer, folder_path, toggle_name, widget_info, number_widget_info in all_layers:
        if number_widget_info:
            number_widget_name, digit_type, digit_name = number_widget_info
            digit_names_found.add(digit_name)
    
    expected_names = {'hundreds', 'tens', 'ones'}
    if digit_names_found != expected_names:
        print(f"✗ Expected digit names {expected_names}, got {digit_names_found}")
        return False
    
    print("✓ Number widget with named digits correctly identified")
    return True


def test_mixed_standalone_and_number_digits():
    """Test that standalone digit widgets and Number widget digits can coexist."""
    print("\nTesting mixed standalone digit and Number widget...")
    
    root_layers = []
    
    # Standalone digit widget
    standalone_digit = MockLayer("[D:7]StandaloneSpeed", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 50 + i*10, 100, 50, 100)
        standalone_digit.add_child(segment)
    root_layers.append(standalone_digit)
    
    # Number widget with 2 digits
    number_folder = MockLayer("[N]RPM", is_group=True)
    
    digit1_folder = MockLayer("[D:7]", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 200 + i*10, 100, 50, 100)
        digit1_folder.add_child(segment)
    number_folder.add_child(digit1_folder)
    
    digit2_folder = MockLayer("[D:7]", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 300 + i*10, 100, 50, 100)
        digit2_folder.add_child(segment)
    number_folder.add_child(digit2_folder)
    
    root_layers.append(number_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 7 (standalone) + 7 + 7 (number) = 21 layers
    if len(all_layers) != 21:
        print(f"✗ Expected 21 layers, got {len(all_layers)}")
        return False
    
    # Count layers with widget_info (standalone digit) and number_widget_info (number digits)
    standalone_count = 0
    number_count = 0
    
    for layer, folder_path, toggle_name, widget_info, number_widget_info in all_layers:
        if number_widget_info:
            number_count += 1
            number_widget_name, digit_type, digit_name = number_widget_info
            if number_widget_name != "RPM":
                print(f"✗ Expected number widget name 'RPM', got '{number_widget_name}'")
                return False
        elif widget_info:
            standalone_count += 1
            widget_type, widget_name = widget_info
            if widget_name != "StandaloneSpeed":
                print(f"✗ Expected standalone widget name 'StandaloneSpeed', got '{widget_name}'")
                return False
    
    if standalone_count != 7:
        print(f"✗ Expected 7 standalone digit layers, got {standalone_count}")
        return False
    
    if number_count != 14:
        print(f"✗ Expected 14 number widget digit layers, got {number_count}")
        return False
    
    print("✓ Mixed standalone and Number widget digits work correctly")
    return True


def main():
    """Run all Number widget tests."""
    print("=" * 60)
    print("Testing Number widget functionality")
    print("=" * 60)
    
    all_passed = True
    
    if not test_number_widget_basic():
        all_passed = False
    
    if not test_number_widget_with_named_digits():
        all_passed = False
    
    if not test_mixed_standalone_and_number_digits():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All Number widget tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
