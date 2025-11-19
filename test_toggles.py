#!/usr/bin/env python3
"""
Test script for validating toggle/widget functionality.
"""

import sys
from test_integration import MockLayer
import extract_layers


def test_toggle_layer():
    """Test that layers with [T] prefix are correctly identified as toggles."""
    print("Testing [T] prefix toggle layer...")
    
    root_layers = []
    
    # Regular layer
    background = MockLayer("Background", 0, 0, 1920, 1080)
    root_layers.append(background)
    
    # Toggle layer with [T] prefix
    toggle_layer = MockLayer("[T]MyToggle", 100, 100, 200, 200)
    root_layers.append(toggle_layer)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 2 layers
    if len(all_layers) != 2:
        print(f"✗ Expected 2 layers, got {len(all_layers)}")
        return False
    
    # First layer should have no toggle
    layer1, folder_path1, toggle1, widget_info1 = all_layers[0]
    if layer1.name != "Background":
        print(f"✗ Expected first layer name 'Background', got '{layer1.name}'")
        return False
    if toggle1 is not None:
        print(f"✗ Expected first layer to have no toggle, got '{toggle1}'")
        return False
    
    # Second layer should have toggle name "MyToggle"
    layer2, folder_path2, toggle2, widget_info2 = all_layers[1]
    if layer2.name != "[T]MyToggle":
        print(f"✗ Expected second layer name '[T]MyToggle', got '{layer2.name}'")
        return False
    if toggle2 != "MyToggle":
        print(f"✗ Expected second layer toggle 'MyToggle', got '{toggle2}'")
        return False
    
    print("✓ Toggle layer correctly identified")
    return True


def test_toggle_folder():
    """Test that folders with [T] prefix apply toggle to all children."""
    print("\nTesting [T] prefix toggle folder...")
    
    root_layers = []
    
    # Regular layer
    background = MockLayer("Background", 0, 0, 1920, 1080)
    root_layers.append(background)
    
    # Toggle folder with children
    toggle_folder = MockLayer("[T]GroupToggle", is_group=True)
    child1 = MockLayer("Child1", 100, 100, 100, 100)
    child2 = MockLayer("Child2", 200, 200, 100, 100)
    toggle_folder.add_child(child1)
    toggle_folder.add_child(child2)
    root_layers.append(toggle_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 3 layers (Background + 2 children)
    if len(all_layers) != 3:
        print(f"✗ Expected 3 layers, got {len(all_layers)}")
        return False
    
    # First layer should have no toggle
    layer1, folder_path1, toggle1, widget_info1 = all_layers[0]
    if toggle1 is not None:
        print(f"✗ Expected first layer to have no toggle, got '{toggle1}'")
        return False
    
    # Both children should have the same toggle
    for i in [1, 2]:
        layer, folder_path, toggle_name, widget_info = all_layers[i]
        if toggle_name != "GroupToggle":
            print(f"✗ Expected layer {i} toggle 'GroupToggle', got '{toggle_name}'")
            return False
        # Folder path should include the sanitized folder name
        if folder_path != ["GroupToggle"]:
            print(f"✗ Expected folder path ['GroupToggle'], got {folder_path}")
            return False
    
    print("✓ Toggle folder correctly applies to all children")
    return True


def test_nested_toggle():
    """Test that nested toggles work correctly."""
    print("\nTesting nested toggle folders...")
    
    root_layers = []
    
    # Regular folder
    regular_folder = MockLayer("RegularFolder", is_group=True)
    
    # Toggle folder inside regular folder
    toggle_folder = MockLayer("[T]NestedToggle", is_group=True)
    child1 = MockLayer("Child1", 100, 100, 100, 100)
    toggle_folder.add_child(child1)
    regular_folder.add_child(toggle_folder)
    
    # Regular layer in regular folder
    regular_child = MockLayer("RegularChild", 200, 200, 100, 100)
    regular_folder.add_child(regular_child)
    
    root_layers.append(regular_folder)
    
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 2 layers
    if len(all_layers) != 2:
        print(f"✗ Expected 2 layers, got {len(all_layers)}")
        return False
    
    # First layer should have toggle
    layer1, folder_path1, toggle1, widget_info1 = all_layers[0]
    if toggle1 != "NestedToggle":
        print(f"✗ Expected first layer toggle 'NestedToggle', got '{toggle1}'")
        return False
    if folder_path1 != ["RegularFolder", "NestedToggle"]:
        print(f"✗ Expected folder path ['RegularFolder', 'NestedToggle'], got {folder_path1}")
        return False
    
    # Second layer should not have toggle
    layer2, folder_path2, toggle2, widget_info2 = all_layers[1]
    if toggle2 is not None:
        print(f"✗ Expected second layer to have no toggle, got '{toggle2}'")
        return False
    if folder_path2 != ["RegularFolder"]:
        print(f"✗ Expected folder path ['RegularFolder'], got {folder_path2}")
        return False
    
    print("✓ Nested toggles work correctly")
    return True


def main():
    """Run all toggle tests."""
    print("=" * 60)
    print("Testing toggle/widget functionality")
    print("=" * 60)
    
    all_passed = True
    
    if not test_toggle_layer():
        all_passed = False
    
    if not test_toggle_folder():
        all_passed = False
    
    if not test_nested_toggle():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All toggle tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
