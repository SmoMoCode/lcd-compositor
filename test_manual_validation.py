#!/usr/bin/env python3
"""
Manual validation test that creates a mock PSD structure and generates output.
This helps verify the complete pipeline including YAML generation and HTML files.
"""

import sys
import tempfile
import shutil
from pathlib import Path
from test_integration import MockLayer
import extract_layers
import yaml


def create_mock_psd_with_widgets():
    """Create a comprehensive mock PSD structure with all widget types."""
    print("Creating mock PSD structure with digit and range widgets...")
    
    root_layers = []
    
    # Background layer
    background = MockLayer("Background", 0, 0, 800, 600)
    root_layers.append(background)
    
    # Toggle widget
    toggle_folder = MockLayer("[T]StatusLight", is_group=True)
    light = MockLayer("light", 100, 100, 50, 50)
    toggle_folder.add_child(light)
    root_layers.append(toggle_folder)
    
    # Digit widget without decimal
    digit_folder1 = MockLayer("[D:7]Speed", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{chr(65+i)}", 200 + i*5, 100, 20, 80)
        digit_folder1.add_child(segment)
    root_layers.append(digit_folder1)
    
    # Digit widget with decimal
    digit_folder2 = MockLayer("[D:7p]Temp", is_group=True)
    for i in range(7):
        segment = MockLayer(f"segment_{chr(65+i)}", 400 + i*5, 100, 20, 80)
        digit_folder2.add_child(segment)
    # Add decimal point
    decimal = MockLayer("decimal", 435, 180, 5, 5)
    digit_folder2.add_child(decimal)
    root_layers.append(digit_folder2)
    
    # Range widget
    range_folder = MockLayer("[R]PowerLevel", is_group=True)
    for i in range(10):
        bar = MockLayer(f"bar_{i+1}", 50 + i*15, 300, 10, 100)
        range_folder.add_child(bar)
    root_layers.append(range_folder)
    
    # Mock root that returns our structure
    class MockPSD:
        width = 800
        height = 600
        
        def __iter__(self):
            return iter(root_layers)
        
        def descendants(self):
            # Flatten all layers for counting
            all = []
            def collect(layers):
                for layer in layers:
                    all.append(layer)
                    if layer.is_group:
                        collect(layer.children)
            collect(root_layers)
            return all
    
    return MockPSD()


def test_yaml_generation():
    """Test that YAML is generated correctly with widget metadata."""
    print("\n" + "=" * 60)
    print("Testing YAML generation with widget metadata")
    print("=" * 60)
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "test_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock PSD
        mock_psd = create_mock_psd_with_widgets()
        
        # Process layers
        all_layers = []
        extract_layers.process_layers_recursive(mock_psd, all_layers)
        
        print(f"\nProcessed {len(all_layers)} layers")
        
        # Collect widgets like extract_psb_layers does
        widgets = {}
        layers_info = []
        
        for idx, (layer, folder_path, toggle_name, widget_info) in enumerate(all_layers):
            # Create minimal layer info
            layer_info = {
                'filename': f"layer_{idx}.png",
                'name': layer.name,
                'x': layer.bbox[0],
                'y': layer.bbox[1],
                'width': layer.bbox[2] - layer.bbox[0],
                'height': layer.bbox[3] - layer.bbox[1]
            }
            layers_info.append(layer_info)
            
            # Collect toggle information
            if toggle_name:
                if toggle_name not in widgets:
                    widgets[toggle_name] = {
                        'type': 'toggle',
                        'layers': []
                    }
                widgets[toggle_name]['layers'].append(layer_info['filename'])
            
            # Collect digit and range widget information
            if widget_info:
                widget_type, widget_name = widget_info
                if widget_name not in widgets:
                    if widget_type.startswith('D:'):
                        # Digit widget
                        has_decimal = widget_type.endswith('p')
                        widgets[widget_name] = {
                            'type': 'digit',
                            'segments': 7,
                            'has_decimal': has_decimal,
                            'layers': []
                        }
                    elif widget_type == 'R':
                        # Range widget
                        widgets[widget_name] = {
                            'type': 'range',
                            'layers': []
                        }
                widgets[widget_name]['layers'].append(layer_info['filename'])
        
        # Create YAML data
        yaml_data = {
            'source_file': 'test.psb',
            'document_width': mock_psd.width,
            'document_height': mock_psd.height,
            'layers': layers_info,
            'widgets': widgets
        }
        
        # Write YAML file
        yaml_path = output_dir / "test.yml"
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"\nGenerated YAML file: {yaml_path}")
        
        # Read and display YAML
        with open(yaml_path, 'r') as f:
            yaml_content = f.read()
        
        print("\nYAML Content:")
        print("-" * 60)
        print(yaml_content)
        print("-" * 60)
        
        # Verify widgets
        print("\nWidget Summary:")
        for widget_name, widget_data in widgets.items():
            widget_type = widget_data['type']
            layer_count = len(widget_data['layers'])
            
            if widget_type == 'toggle':
                print(f"  ✓ Toggle: {widget_name} ({layer_count} layer(s))")
            elif widget_type == 'digit':
                has_decimal = widget_data.get('has_decimal', False)
                decimal_str = " with decimal" if has_decimal else ""
                expected_count = 8 if has_decimal else 7
                status = "✓" if layer_count == expected_count else "✗"
                print(f"  {status} Digit: {widget_name}{decimal_str} ({layer_count}/{expected_count} layer(s))")
            elif widget_type == 'range':
                print(f"  ✓ Range: {widget_name} ({layer_count} layer(s))")
        
        # Verify expected widgets
        expected_widgets = {
            'StatusLight': ('toggle', 1),
            'Speed': ('digit', 7),
            'Temp': ('digit', 8),
            'PowerLevel': ('range', 10)
        }
        
        all_correct = True
        for widget_name, (expected_type, expected_count) in expected_widgets.items():
            if widget_name not in widgets:
                print(f"  ✗ Missing widget: {widget_name}")
                all_correct = False
            else:
                widget = widgets[widget_name]
                if widget['type'] != expected_type:
                    print(f"  ✗ Wrong type for {widget_name}: expected {expected_type}, got {widget['type']}")
                    all_correct = False
                if len(widget['layers']) != expected_count:
                    print(f"  ✗ Wrong layer count for {widget_name}: expected {expected_count}, got {len(widget['layers'])}")
                    all_correct = False
        
        if all_correct:
            print("\n✓ All widgets generated correctly!")
            return True
        else:
            print("\n✗ Some widgets have errors")
            return False


def main():
    """Run manual validation tests."""
    print("=" * 60)
    print("Manual Validation Test")
    print("=" * 60)
    
    if not test_yaml_generation():
        print("\n✗ Validation failed")
        return 1
    
    print("\n" + "=" * 60)
    print("✓ Manual validation passed!")
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
