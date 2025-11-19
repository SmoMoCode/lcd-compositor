#!/usr/bin/env python3
"""
Integration test for layer extraction with folder-based naming.
This tests the complete flow with mock PSD data.
"""

import sys
import tempfile
import shutil
from pathlib import Path


class MockLayer:
    """Mock layer object for testing."""
    def __init__(self, name, x=0, y=0, width=100, height=100, is_group=False):
        self.name = name
        self.bbox = (x, y, x + width, y + height)
        self.is_group = is_group
        self.children = []
        
    def __iter__(self):
        """Make this iterable if it's a group."""
        if self.is_group:
            return iter(self.children)
        raise TypeError("Layer is not iterable")
    
    def add_child(self, child):
        """Add a child to this group."""
        if self.is_group:
            self.children.append(child)


def test_process_layers_recursive():
    """Test the process_layers_recursive function with mock data."""
    import extract_layers
    
    print("Testing process_layers_recursive with mock PSD structure...")
    
    # Create a mock PSD structure:
    # - Background (root layer)
    # - UI (group)
    #   - Logo (layer)
    #   - #Hidden (layer - should be ignored)
    # - #IgnoredGroup (group - should be ignored)
    #   - SomeLayer (layer)
    # - Smo (group)
    #   - Mo (group)
    #     - 1 (layer)
    #     - 2 (layer)
    #     - #3 (layer - should be ignored)
    
    root_layers = []
    
    # Background at root
    background = MockLayer("Background", 0, 0, 1920, 1080)
    root_layers.append(background)
    
    # UI group
    ui_group = MockLayer("UI", is_group=True)
    logo = MockLayer("Logo", 100, 150, 500, 300)
    hidden = MockLayer("#Hidden", 200, 200, 100, 100)
    ui_group.add_child(logo)
    ui_group.add_child(hidden)
    root_layers.append(ui_group)
    
    # #IgnoredGroup - should be ignored completely
    ignored_group = MockLayer("#IgnoredGroup", is_group=True)
    some_layer = MockLayer("SomeLayer", 50, 50, 100, 100)
    ignored_group.add_child(some_layer)
    root_layers.append(ignored_group)
    
    # Smo > Mo > layers
    smo_group = MockLayer("Smo", is_group=True)
    mo_group = MockLayer("Mo", is_group=True)
    layer1 = MockLayer("1", 300, 400, 200, 200)
    layer2 = MockLayer("2", 500, 600, 150, 150)
    layer3 = MockLayer("#3", 700, 800, 100, 100)
    mo_group.add_child(layer1)
    mo_group.add_child(layer2)
    mo_group.add_child(layer3)
    smo_group.add_child(mo_group)
    root_layers.append(smo_group)
    
    # Process the layers - create a mock root container
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Verify results
    print(f"\nFound {len(all_layers)} layers (after filtering):")
    
    expected_results = [
        ("Background", []),
        ("Logo", ["UI"]),
        ("1", ["Smo", "Mo"]),
        ("2", ["Smo", "Mo"]),
    ]
    
    if len(all_layers) != len(expected_results):
        print(f"✗ Expected {len(expected_results)} layers, got {len(all_layers)}")
        print("Actual layers found:")
        for layer, folder_path in all_layers:
            print(f"  - '{layer.name}' with path {folder_path}")
        return False
    
    for i, (layer, folder_path, toggle_name) in enumerate(all_layers):
        expected_name, expected_path = expected_results[i]
        
        if layer.name != expected_name:
            print(f"✗ Layer {i}: Expected name '{expected_name}', got '{layer.name}'")
            return False
        
        if folder_path != expected_path:
            print(f"✗ Layer {i}: Expected path {expected_path}, got {folder_path}")
            return False
        
        # Generate expected filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in layer.name)
        safe_name = safe_name.strip().replace(' ', '_')
        if folder_path:
            expected_filename = "--".join(folder_path + [safe_name]) + ".png"
        else:
            expected_filename = f"{safe_name}.png"
        
        toggle_str = f" (toggle: {toggle_name})" if toggle_name else ""
        print(f"  ✓ Layer '{layer.name}' -> {expected_filename}{toggle_str}")
    
    print("\n✓ All layers processed correctly with proper folder paths!")
    return True


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Integration test for layer extraction")
    print("=" * 60)
    
    if not test_process_layers_recursive():
        print("\n✗ Tests failed")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ All integration tests passed!")
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
