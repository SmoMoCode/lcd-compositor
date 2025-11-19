#!/usr/bin/env python3
"""
Integration test for Number widget extraction and YAML generation.
"""

import sys
import tempfile
import shutil
from pathlib import Path
import yaml as pyyaml
from test_integration import MockLayer
import extract_layers


def test_number_widget_yaml_generation():
    """Test that Number widgets are correctly extracted and written to YAML."""
    print("Testing Number widget YAML generation...")
    
    root_layers = []
    
    # Regular background layer
    background = MockLayer("Background", 0, 0, 1920, 1080)
    root_layers.append(background)
    
    # Number widget with 3 digits
    number_folder = MockLayer("[N]Speed", is_group=True)
    
    # First digit (no decimal)
    digit1_folder = MockLayer("[D:7]hundreds", is_group=True)
    for i in range(7):
        segment = MockLayer(f"seg_A", 100 + i*10, 100, 50, 100)
        digit1_folder.add_child(segment)
    number_folder.add_child(digit1_folder)
    
    # Second digit (with decimal point)
    digit2_folder = MockLayer("[D:7p]tens", is_group=True)
    for i in range(8):  # 7 segments + decimal point
        segment = MockLayer(f"seg_B", 200 + i*10, 100, 50, 100)
        digit2_folder.add_child(segment)
    number_folder.add_child(digit2_folder)
    
    # Third digit (no decimal)
    digit3_folder = MockLayer("[D:7]ones", is_group=True)
    for i in range(7):
        segment = MockLayer(f"seg_C", 300 + i*10, 100, 50, 100)
        digit3_folder.add_child(segment)
    number_folder.add_child(digit3_folder)
    
    root_layers.append(number_folder)
    
    # Standalone digit for comparison
    standalone = MockLayer("[D:7]RPM", is_group=True)
    for i in range(7):
        segment = MockLayer(f"seg_D", 400 + i*10, 100, 50, 100)
        standalone.add_child(segment)
    root_layers.append(standalone)
    
    # Process layers
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Should have 1 background + 7+8+7 (number digits) + 7 (standalone) = 30 layers
    if len(all_layers) != 30:
        print(f"✗ Expected 30 layers, got {len(all_layers)}")
        return False
    
    # Build widgets dict as extract_psb_layers would
    widgets = {}
    number_widgets_digits = {}
    
    for idx, (layer, folder_path, toggle_name, widget_info, number_widget_info) in enumerate(all_layers):
        # Simulate what extract_layer_image would return
        layer_filename = f"layer_{idx}.png"
        
        if number_widget_info:
            number_widget_name, digit_type, digit_name = number_widget_info
            
            if number_widget_name not in widgets:
                widgets[number_widget_name] = {
                    'type': 'number',
                    'digits': []
                }
                number_widgets_digits[number_widget_name] = []
            
            # Find or create digit
            digit_found = False
            for digit_info in number_widgets_digits[number_widget_name]:
                if digit_info['name'] == digit_name:
                    digit_info['layers'].append(layer_filename)
                    digit_found = True
                    break
            
            if not digit_found:
                has_decimal = digit_type.endswith('p')
                digit_info = {
                    'name': digit_name,
                    'has_decimal': has_decimal,
                    'layers': [layer_filename]
                }
                number_widgets_digits[number_widget_name].append(digit_info)
        
        elif widget_info:
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
                elif widget_type == 'N':
                    if widget_name not in widgets:
                        widgets[widget_name] = {
                            'type': 'number',
                            'digits': []
                        }
                        number_widgets_digits[widget_name] = []
            
            if widget_type != 'N':
                widgets[widget_name]['layers'].append(layer_filename)
    
    # Finalize Number widgets
    for number_widget_name, digit_list in number_widgets_digits.items():
        for digit_info in digit_list:
            digit_info['layers'].reverse()
        widgets[number_widget_name]['digits'] = digit_list
    
    # Verify widget structure
    if 'Speed' not in widgets:
        print("✗ Speed Number widget not found in widgets")
        return False
    
    speed_widget = widgets['Speed']
    if speed_widget['type'] != 'number':
        print(f"✗ Expected Speed widget type 'number', got '{speed_widget['type']}'")
        return False
    
    if 'digits' not in speed_widget:
        print("✗ Speed widget missing 'digits' field")
        return False
    
    if len(speed_widget['digits']) != 3:
        print(f"✗ Expected Speed widget to have 3 digits, got {len(speed_widget['digits'])}")
        return False
    
    # Check digit names and decimal points
    digit_names = [d['name'] for d in speed_widget['digits']]
    if digit_names != ['hundreds', 'tens', 'ones']:
        print(f"✗ Expected digit names ['hundreds', 'tens', 'ones'], got {digit_names}")
        return False
    
    has_decimals = [d['has_decimal'] for d in speed_widget['digits']]
    if has_decimals != [False, True, False]:
        print(f"✗ Expected has_decimal [False, True, False], got {has_decimals}")
        return False
    
    # Check layer counts (should be 7, 8, 7 after reversal)
    layer_counts = [len(d['layers']) for d in speed_widget['digits']]
    if layer_counts != [7, 8, 7]:
        print(f"✗ Expected layer counts [7, 8, 7], got {layer_counts}")
        return False
    
    # Check standalone digit widget
    if 'RPM' not in widgets:
        print("✗ RPM standalone digit widget not found")
        return False
    
    rpm_widget = widgets['RPM']
    if rpm_widget['type'] != 'digit':
        print(f"✗ Expected RPM widget type 'digit', got '{rpm_widget['type']}'")
        return False
    
    if len(rpm_widget['layers']) != 7:
        print(f"✗ Expected RPM widget to have 7 layers, got {len(rpm_widget['layers'])}")
        return False
    
    print("✓ Number widget YAML structure correctly generated")
    return True


def test_yaml_output_format():
    """Test that the YAML output can be written and read back correctly."""
    print("\nTesting YAML output format...")
    
    # Create sample widget data
    widgets = {
        'Temperature': {
            'type': 'number',
            'digits': [
                {
                    'name': 'digit1',
                    'has_decimal': False,
                    'layers': ['layer1.png', 'layer2.png']
                },
                {
                    'name': 'digit2',
                    'has_decimal': True,
                    'layers': ['layer3.png', 'layer4.png', 'layer5.png']
                }
            ]
        },
        'Status': {
            'type': 'toggle',
            'layers': ['status.png']
        }
    }
    
    yaml_data = {
        'source_file': 'test.psb',
        'document_width': 1920,
        'document_height': 1080,
        'widgets': widgets
    }
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        temp_path = f.name
        pyyaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
    
    try:
        # Read back and verify
        with open(temp_path, 'r') as f:
            loaded_data = pyyaml.safe_load(f)
        
        if 'widgets' not in loaded_data:
            print("✗ YAML missing 'widgets' section")
            return False
        
        if 'Temperature' not in loaded_data['widgets']:
            print("✗ Temperature widget not found in loaded YAML")
            return False
        
        temp_widget = loaded_data['widgets']['Temperature']
        if temp_widget['type'] != 'number':
            print(f"✗ Expected type 'number', got '{temp_widget['type']}'")
            return False
        
        if 'digits' not in temp_widget:
            print("✗ Temperature widget missing 'digits'")
            return False
        
        if len(temp_widget['digits']) != 2:
            print(f"✗ Expected 2 digits, got {len(temp_widget['digits'])}")
            return False
        
        # Check first digit
        digit1 = temp_widget['digits'][0]
        if digit1['name'] != 'digit1':
            print(f"✗ Expected digit name 'digit1', got '{digit1['name']}'")
            return False
        
        if digit1['has_decimal'] != False:
            print(f"✗ Expected has_decimal False, got {digit1['has_decimal']}")
            return False
        
        # Check second digit
        digit2 = temp_widget['digits'][1]
        if digit2['has_decimal'] != True:
            print(f"✗ Expected has_decimal True, got {digit2['has_decimal']}")
            return False
        
        print("✓ YAML output format is correct")
        return True
    finally:
        # Clean up
        Path(temp_path).unlink()


def main():
    """Run all integration tests for Number widget."""
    print("=" * 60)
    print("Number widget integration tests")
    print("=" * 60)
    
    all_passed = True
    
    if not test_number_widget_yaml_generation():
        all_passed = False
    
    if not test_yaml_output_format():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All integration tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
