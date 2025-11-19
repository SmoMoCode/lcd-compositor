#!/usr/bin/env python3
"""
Test script for validating digit and range widget functionality.
"""

import sys
from test_integration import MockLayer
import extract_layers


def test_digit_widget():
    """Test that folders with [D:7] prefix are correctly identified as digit widgets."""
    print("Testing [D:7] digit widget...")
    
    root_layers = []
    
    # Digit folder with 7 segments
    digit_folder = MockLayer("[D:7]speed", is_group=True)
    # Add 7 segment layers (A, F, B, G, E, C, D)
    for i in range(7):
        segment = MockLayer(f"segment_{i}", 100 + i*10, 100, 50, 100)
        digit_folder.add_child(segment)
    root_layers.append(digit_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 7 layers (segments)
    if len(all_layers) != 7:
        print(f"✗ Expected 7 layers, got {len(all_layers)}")
        return False
    
    # All layers should have widget_info with type 'D:7'
    for i, (layer, folder_path, toggle_name, widget_info) in enumerate(all_layers):
        if widget_info is None:
            print(f"✗ Expected layer {i} to have widget_info, got None")
            return False
        widget_type, widget_name = widget_info
        if widget_type != "D:7":
            print(f"✗ Expected widget type 'D:7', got '{widget_type}'")
            return False
        if widget_name != "speed":
            print(f"✗ Expected widget name 'speed', got '{widget_name}'")
            return False
        if folder_path != ["speed"]:
            print(f"✗ Expected folder path ['speed'], got {folder_path}")
            return False
    
    print("✓ Digit widget [D:7] correctly identified")
    return True


def test_digit_widget_with_decimal():
    """Test that folders with [D:7p] prefix are correctly identified as digit widgets with decimal."""
    print("\nTesting [D:7p] digit widget with decimal...")
    
    root_layers = []
    
    # Digit folder with 7 segments + decimal
    digit_folder = MockLayer("[D:7p]temperature", is_group=True)
    # Add 7 segment layers + 1 decimal point
    for i in range(8):
        segment = MockLayer(f"segment_{i}", 100 + i*10, 100, 50, 100)
        digit_folder.add_child(segment)
    root_layers.append(digit_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 8 layers (7 segments + decimal)
    if len(all_layers) != 8:
        print(f"✗ Expected 8 layers, got {len(all_layers)}")
        return False
    
    # All layers should have widget_info with type 'D:7p'
    for i, (layer, folder_path, toggle_name, widget_info) in enumerate(all_layers):
        if widget_info is None:
            print(f"✗ Expected layer {i} to have widget_info, got None")
            return False
        widget_type, widget_name = widget_info
        if widget_type != "D:7p":
            print(f"✗ Expected widget type 'D:7p', got '{widget_type}'")
            return False
        if widget_name != "temperature":
            print(f"✗ Expected widget name 'temperature', got '{widget_name}'")
            return False
    
    print("✓ Digit widget [D:7p] correctly identified")
    return True


def test_range_widget():
    """Test that folders with [R] prefix are correctly identified as range widgets."""
    print("\nTesting [R] range widget...")
    
    root_layers = []
    
    # Range folder with child layers
    range_folder = MockLayer("[R]powerLevel", is_group=True)
    # Add 10 child layers
    for i in range(10):
        child = MockLayer(f"level_{i+1}", 100 + i*20, 100, 50, 100)
        range_folder.add_child(child)
    root_layers.append(range_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 10 layers
    if len(all_layers) != 10:
        print(f"✗ Expected 10 layers, got {len(all_layers)}")
        return False
    
    # All layers should have widget_info with type 'R'
    for i, (layer, folder_path, toggle_name, widget_info) in enumerate(all_layers):
        if widget_info is None:
            print(f"✗ Expected layer {i} to have widget_info, got None")
            return False
        widget_type, widget_name = widget_info
        if widget_type != "R":
            print(f"✗ Expected widget type 'R', got '{widget_type}'")
            return False
        if widget_name != "powerLevel":
            print(f"✗ Expected widget name 'powerLevel', got '{widget_name}'")
            return False
        if folder_path != ["powerLevel"]:
            print(f"✗ Expected folder path ['powerLevel'], got {folder_path}")
            return False
    
    print("✓ Range widget [R] correctly identified")
    return True


def test_mixed_widgets():
    """Test that different widget types can coexist."""
    print("\nTesting mixed widget types...")
    
    root_layers = []
    
    # Regular layer
    background = MockLayer("Background", 0, 0, 1920, 1080)
    root_layers.append(background)
    
    # Toggle widget
    toggle_folder = MockLayer("[T]MyToggle", is_group=True)
    toggle_child = MockLayer("Child", 100, 100, 100, 100)
    toggle_folder.add_child(toggle_child)
    root_layers.append(toggle_folder)
    
    # Digit widget
    digit_folder = MockLayer("[D:7]rpm", is_group=True)
    for i in range(7):
        segment = MockLayer(f"seg_{i}", 200 + i*10, 100, 50, 100)
        digit_folder.add_child(segment)
    root_layers.append(digit_folder)
    
    # Range widget
    range_folder = MockLayer("[R]battery", is_group=True)
    for i in range(5):
        bar = MockLayer(f"bar_{i+1}", 300 + i*20, 100, 50, 100)
        range_folder.add_child(bar)
    root_layers.append(range_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 1 + 1 + 7 + 5 = 14 layers
    if len(all_layers) != 14:
        print(f"✗ Expected 14 layers, got {len(all_layers)}")
        return False
    
    # Check first layer (background) - no widget
    layer0, folder_path0, toggle0, widget_info0 = all_layers[0]
    if layer0.name != "Background":
        print(f"✗ Expected first layer 'Background', got '{layer0.name}'")
        return False
    if widget_info0 is not None:
        print(f"✗ Expected first layer to have no widget_info, got {widget_info0}")
        return False
    
    # Check second layer (toggle child) - has toggle
    layer1, folder_path1, toggle1, widget_info1 = all_layers[1]
    if toggle1 != "MyToggle":
        print(f"✗ Expected toggle 'MyToggle', got '{toggle1}'")
        return False
    
    # Check digit layers (indices 2-8)
    for i in range(2, 9):
        layer, folder_path, toggle_name, widget_info = all_layers[i]
        if widget_info is None:
            print(f"✗ Expected layer {i} to have widget_info for digit")
            return False
        widget_type, widget_name = widget_info
        if widget_type != "D:7":
            print(f"✗ Expected digit widget type 'D:7' at layer {i}, got '{widget_type}'")
            return False
        if widget_name != "rpm":
            print(f"✗ Expected digit widget name 'rpm' at layer {i}, got '{widget_name}'")
            return False
    
    # Check range layers (indices 9-13)
    for i in range(9, 14):
        layer, folder_path, toggle_name, widget_info = all_layers[i]
        if widget_info is None:
            print(f"✗ Expected layer {i} to have widget_info for range")
            return False
        widget_type, widget_name = widget_info
        if widget_type != "R":
            print(f"✗ Expected range widget type 'R' at layer {i}, got '{widget_type}'")
            return False
        if widget_name != "battery":
            print(f"✗ Expected range widget name 'battery' at layer {i}, got '{widget_name}'")
            return False
    
    print("✓ Mixed widget types work correctly")
    return True


def main():
    """Run all widget tests."""
    print("=" * 60)
    print("Testing digit and range widget functionality")
    print("=" * 60)
    
    all_passed = True
    
    if not test_digit_widget():
        all_passed = False
    
    if not test_digit_widget_with_decimal():
        all_passed = False
    
    if not test_range_widget():
        all_passed = False
    
    if not test_mixed_widgets():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All widget tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
