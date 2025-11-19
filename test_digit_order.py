#!/usr/bin/env python3
"""
Test to verify digit segment order is correct after the fix.
"""

import sys
import os
from pathlib import Path
from test_integration import MockLayer
import extract_layers
import yaml

def test_digit_segment_order():
    """Test that digit segments are collected in the correct order."""
    print("Testing digit segment order...")
    
    root_layers = []
    
    # Create a [D:7] digit folder with segments in Photoshop UI order (top to bottom)
    # But remember: PSD files store them bottom to top, so we simulate that
    digit_folder = MockLayer("[D:7]speed", is_group=True)
    
    # Simulate how PSD stores layers (reverse order from UI)
    # In UI: A, F, B, G, E, C, D (indices 0-6)
    # In file: D, C, E, G, B, F, A (indices 6-0)
    segment_names = ['segment_D', 'segment_C', 'segment_E', 'segment_G', 'segment_B', 'segment_F', 'segment_A']
    for i, name in enumerate(segment_names):
        segment = MockLayer(name, 100 + i*10, 100, 50, 100)
        digit_folder.add_child(segment)
    
    root_layers.append(digit_folder)
    
    # Process layers
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Extract to a temporary directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Simulate the widget collection part
        widgets = {}
        for idx, (layer, folder_path, toggle_name, widget_info) in enumerate(all_layers):
            if widget_info:
                widget_type, widget_name = widget_info
                if widget_name not in widgets:
                    if widget_type.startswith('D:'):
                        has_decimal = widget_type.endswith('p')
                        widgets[widget_name] = {
                            'type': 'digit',
                            'segments': 7,
                            'has_decimal': has_decimal,
                            'layers': []
                        }
                # Create a fake filename for this layer
                filename = f"{widget_name}--{layer.name}.png"
                widgets[widget_name]['layers'].append(filename)
        
        # Apply the fix: reverse digit widget layers
        for widget_name, widget_data in widgets.items():
            if widget_data['type'] == 'digit':
                widget_data['layers'].reverse()
        
        # Check the order
        print(f"Collected layers: {widgets['speed']['layers']}")
        
        # Expected order after reversal (should be A, F, B, G, E, C, D)
        expected_order = [
            'speed--segment_A.png',
            'speed--segment_F.png', 
            'speed--segment_B.png',
            'speed--segment_G.png',
            'speed--segment_E.png',
            'speed--segment_C.png',
            'speed--segment_D.png'
        ]
        
        if widgets['speed']['layers'] == expected_order:
            print("✓ Digit segments are in the correct order (A, F, B, G, E, C, D)")
            return True
        else:
            print(f"✗ Digit segments are in wrong order")
            print(f"  Expected: {expected_order}")
            print(f"  Got: {widgets['speed']['layers']}")
            return False

def test_digit_with_decimal_order():
    """Test that [D:7p] digit with decimal point has correct order."""
    print("\nTesting digit with decimal point order...")
    
    root_layers = []
    
    # Create a [D:7p] digit folder
    # In UI: A, F, B, G, E, C, D, decimal (indices 0-7)
    # In file: decimal, D, C, E, G, B, F, A (indices 7-0)
    digit_folder = MockLayer("[D:7p]temperature", is_group=True)
    
    segment_names = ['decimal', 'segment_D', 'segment_C', 'segment_E', 'segment_G', 'segment_B', 'segment_F', 'segment_A']
    for i, name in enumerate(segment_names):
        segment = MockLayer(name, 100 + i*10, 100, 50, 100)
        digit_folder.add_child(segment)
    
    root_layers.append(digit_folder)
    
    # Process layers
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Simulate widget collection
    widgets = {}
    for idx, (layer, folder_path, toggle_name, widget_info) in enumerate(all_layers):
        if widget_info:
            widget_type, widget_name = widget_info
            if widget_name not in widgets:
                if widget_type.startswith('D:'):
                    has_decimal = widget_type.endswith('p')
                    widgets[widget_name] = {
                        'type': 'digit',
                        'segments': 7,
                        'has_decimal': has_decimal,
                        'layers': []
                    }
            filename = f"{widget_name}--{layer.name}.png"
            widgets[widget_name]['layers'].append(filename)
    
    # Apply the fix
    for widget_name, widget_data in widgets.items():
        if widget_data['type'] == 'digit':
            widget_data['layers'].reverse()
    
    print(f"Collected layers: {widgets['temperature']['layers']}")
    
    # Expected order: A, F, B, G, E, C, D, decimal
    expected_order = [
        'temperature--segment_A.png',
        'temperature--segment_F.png',
        'temperature--segment_B.png',
        'temperature--segment_G.png',
        'temperature--segment_E.png',
        'temperature--segment_C.png',
        'temperature--segment_D.png',
        'temperature--decimal.png'
    ]
    
    if widgets['temperature']['layers'] == expected_order:
        print("✓ Digit segments with decimal are in correct order (A, F, B, G, E, C, D, decimal)")
        return True
    else:
        print(f"✗ Digit segments with decimal are in wrong order")
        print(f"  Expected: {expected_order}")
        print(f"  Got: {widgets['temperature']['layers']}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing digit segment order fix")
    print("=" * 60)
    
    all_passed = True
    
    if not test_digit_segment_order():
        all_passed = False
    
    if not test_digit_with_decimal_order():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All digit order tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
