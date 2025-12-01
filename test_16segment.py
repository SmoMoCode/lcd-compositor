#!/usr/bin/env python3
"""
Test for 16-segment digit and String widget functionality.
"""

import sys
import os
from pathlib import Path
from test_integration import MockLayer
import extract_layers
import yaml
import tempfile


def test_16_segment_digit():
    """Test that [D:16] digit widget is correctly identified and has 16 segments."""
    print("Testing [D:16] 16-segment digit widget...")
    
    root_layers = []
    
    # Create a [D:16] digit folder with 16 segments
    digit_folder = MockLayer("[D:16]display", is_group=True)
    
    # Add 16 segments in reverse order (as PSD stores them)
    segment_names = ['d2', 'd1', 'c', 'm', 'l', 'k', 'e', 'g2', 'g1', 'b', 'j', 'i', 'h', 'f', 'a2', 'a1']
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
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Simulate the widget collection part
        widgets = {}
        for idx, (layer, folder_path, toggle_name, widget_info, number_widget_info) in enumerate(all_layers):
            if widget_info:
                widget_type, widget_name = widget_info
                if widget_name not in widgets:
                    if widget_type.startswith('D:'):
                        has_decimal = widget_type.endswith('p')
                        # Extract segment count from digit type
                        digit_type_clean = widget_type.rstrip('p')
                        segments = 7  # default
                        if ':' in digit_type_clean:
                            try:
                                segments = int(digit_type_clean.split(':')[1])
                            except (IndexError, ValueError):
                                segments = 7
                        widgets[widget_name] = {
                            'type': 'digit',
                            'segments': segments,
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
        
        # Check the widget configuration
        assert 'display' in widgets, "Widget 'display' not found"
        assert widgets['display']['type'] == 'digit', "Widget type should be 'digit'"
        assert widgets['display']['segments'] == 16, f"Expected 16 segments, got {widgets['display']['segments']}"
        assert widgets['display']['has_decimal'] == False, "Should not have decimal"
        assert len(widgets['display']['layers']) == 16, f"Expected 16 layers, got {len(widgets['display']['layers'])}"
        
        print("✓ 16-segment digit widget correctly identified with 16 segments")
        return True


def test_16_segment_digit_with_decimal():
    """Test that [D:16p] digit widget with decimal is correctly identified."""
    print("\nTesting [D:16p] 16-segment digit with decimal...")
    
    root_layers = []
    
    # Create a [D:16p] digit folder with 16 segments + decimal
    digit_folder = MockLayer("[D:16p]temp", is_group=True)
    
    # Add 16 segments + decimal in reverse order
    segment_names = ['dp', 'd2', 'd1', 'c', 'm', 'l', 'k', 'e', 'g2', 'g1', 'b', 'j', 'i', 'h', 'f', 'a2', 'a1']
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
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Simulate the widget collection part
        widgets = {}
        for idx, (layer, folder_path, toggle_name, widget_info, number_widget_info) in enumerate(all_layers):
            if widget_info:
                widget_type, widget_name = widget_info
                if widget_name not in widgets:
                    if widget_type.startswith('D:'):
                        has_decimal = widget_type.endswith('p')
                        digit_type_clean = widget_type.rstrip('p')
                        segments = 7
                        if ':' in digit_type_clean:
                            try:
                                segments = int(digit_type_clean.split(':')[1])
                            except (IndexError, ValueError):
                                segments = 7
                        widgets[widget_name] = {
                            'type': 'digit',
                            'segments': segments,
                            'has_decimal': has_decimal,
                            'layers': []
                        }
                filename = f"{widget_name}--{layer.name}.png"
                widgets[widget_name]['layers'].append(filename)
        
        # Apply the fix: reverse digit widget layers
        for widget_name, widget_data in widgets.items():
            if widget_data['type'] == 'digit':
                widget_data['layers'].reverse()
        
        # Check the widget configuration
        assert 'temp' in widgets, "Widget 'temp' not found"
        assert widgets['temp']['type'] == 'digit', "Widget type should be 'digit'"
        assert widgets['temp']['segments'] == 16, f"Expected 16 segments, got {widgets['temp']['segments']}"
        assert widgets['temp']['has_decimal'] == True, "Should have decimal"
        assert len(widgets['temp']['layers']) == 17, f"Expected 17 layers (16 + decimal), got {len(widgets['temp']['layers'])}"
        
        print("✓ 16-segment digit with decimal correctly identified")
        return True


def test_string_widget():
    """Test that [S] String widget is correctly identified."""
    print("\nTesting [S] String widget...")
    
    root_layers = []
    
    # Create a [S] string widget with 3 [D:16p] digits
    string_folder = MockLayer("[S]message", is_group=True)
    
    for digit_idx in range(3):
        digit_folder = MockLayer(f"[D:16p]char{digit_idx}", is_group=True)
        # Add 16 segments + decimal in reverse order
        segment_names = ['dp', 'd2', 'd1', 'c', 'm', 'l', 'k', 'e', 'g2', 'g1', 'b', 'j', 'i', 'h', 'f', 'a2', 'a1']
        for i, name in enumerate(segment_names):
            segment = MockLayer(name, 100 + i*10, 100 + digit_idx*200, 50, 100)
            digit_folder.add_child(segment)
        string_folder.add_child(digit_folder)
    
    root_layers.append(string_folder)
    
    # Process layers
    class MockRoot:
        def __iter__(self):
            return iter(root_layers)
    
    all_layers = []
    extract_layers.process_layers_recursive(MockRoot(), all_layers)
    
    # Extract to a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Simulate the widget collection part
        widgets = {}
        number_widgets_digits = {}
        
        for idx, (layer, folder_path, toggle_name, widget_info, number_widget_info) in enumerate(all_layers):
            # Handle String widget digits
            if number_widget_info:
                parent_widget_type, parent_widget_name, digit_type, digit_name = number_widget_info
                
                # Initialize String widget if not exists
                if parent_widget_name not in widgets:
                    widget_type = 'number' if parent_widget_type == 'N' else 'string'
                    widgets[parent_widget_name] = {
                        'type': widget_type,
                        'digits': []
                    }
                    number_widgets_digits[parent_widget_name] = []
                
                # Check if this digit is already tracked
                digit_found = False
                for digit_info in number_widgets_digits[parent_widget_name]:
                    if digit_info['name'] == digit_name:
                        # Add layer to existing digit
                        digit_info['layers'].append(f"{parent_widget_name}--{digit_name}--{layer.name}.png")
                        digit_found = True
                        break
                
                if not digit_found:
                    # New digit for this String widget
                    has_decimal = digit_type.endswith('p')
                    digit_info = {
                        'name': digit_name,
                        'has_decimal': has_decimal,
                        'layers': [f"{parent_widget_name}--{digit_name}--{layer.name}.png"]
                    }
                    number_widgets_digits[parent_widget_name].append(digit_info)
        
        # Finalize String widgets: reverse digit layers and add to widgets
        for widget_name, digit_list in number_widgets_digits.items():
            for digit_info in digit_list:
                digit_info['layers'].reverse()
            widgets[widget_name]['digits'] = digit_list
        
        # Check the widget configuration
        assert 'message' in widgets, "Widget 'message' not found"
        assert widgets['message']['type'] == 'string', f"Widget type should be 'string', got {widgets['message']['type']}"
        assert len(widgets['message']['digits']) == 3, f"Expected 3 digits, got {len(widgets['message']['digits'])}"
        
        for i, digit in enumerate(widgets['message']['digits']):
            assert digit['has_decimal'] == True, f"Digit {i} should have decimal"
            assert len(digit['layers']) == 17, f"Digit {i} should have 17 layers, got {len(digit['layers'])}"
        
        print("✓ String widget correctly identified with 3 16-segment digits")
        return True


def test_16_segment_character_patterns():
    """Test that key 16-segment character patterns are correct."""
    print("\nTesting 16-segment character pattern correctness...")
    
    # Segment order:
    # 0:a1, 1:a2, 2:f, 3:h, 4:i, 5:j, 6:b, 7:g1, 8:g2, 9:e, 10:k, 11:l, 12:m, 13:c, 14:d1, 15:d2
    
    # Segment name to index mapping for readability
    SEG = {
        'a1': 0, 'a2': 1, 'f': 2, 'h': 3, 'i': 4, 'j': 5, 'b': 6,
        'g1': 7, 'g2': 8, 'e': 9, 'k': 10, 'l': 11, 'm': 12, 'c': 13,
        'd1': 14, 'd2': 15
    }
    
    def segs_to_array(segment_names):
        """Convert list of segment names to boolean array."""
        result = [False] * 16
        for name in segment_names:
            if name in SEG:
                result[SEG[name]] = True
        return result
    
    # Expected patterns for key characters that were previously incorrect
    expected_patterns = {
        # '0' should be outer rectangle only (no diagonals)
        '0': segs_to_array(['a1', 'a2', 'f', 'b', 'e', 'c', 'd1', 'd2']),
        # '1' should be right side only (b and c)
        '1': segs_to_array(['b', 'c']),
        # '2' should have top, right-upper, middle, left-lower, bottom
        '2': segs_to_array(['a1', 'a2', 'b', 'g1', 'g2', 'e', 'd1', 'd2']),
        # '3' should have top, right, middle, bottom (no center vertical)
        '3': segs_to_array(['a1', 'a2', 'b', 'g1', 'g2', 'c', 'd1', 'd2']),
        # '4' should have upper-left, middle, right (no center vertical)
        '4': segs_to_array(['f', 'g1', 'g2', 'b', 'c']),
        # 'K' should have left side, upper-right diagonal, middle-left, lower-right diagonal
        'K': segs_to_array(['f', 'j', 'g1', 'e', 'm']),
        # 'V' should have left side with both lower diagonals
        'V': segs_to_array(['f', 'e', 'k', 'm']),
        # 'W' should have sides with lower diagonals
        'W': segs_to_array(['f', 'b', 'e', 'k', 'm', 'c']),
        # 'Z' should have top, upper-right diagonal, lower-left diagonal, bottom
        'Z': segs_to_array(['a1', 'a2', 'j', 'k', 'd1', 'd2']),
    }
    
    # Read the actual patterns from the generated HTML
    # We need to parse the JavaScript to extract the patterns
    import re
    
    # Read the extract_layers.py file to get the CHAR_16_SEGMENTS
    with open('extract_layers.py', 'r') as f:
        content = f.read()
    
    # Find the CHAR_16_SEGMENTS definition in the JavaScript
    start_marker = "const CHAR_16_SEGMENTS = {"
    end_marker = "};"
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("✗ Could not find CHAR_16_SEGMENTS in extract_layers.py")
        return False
    
    # Extract the patterns
    segment_section = content[start_idx:content.find(end_marker, start_idx) + 2]
    
    all_passed = True
    for char, expected in expected_patterns.items():
        # Find the pattern for this character
        if char == '\\':
            pattern_match = re.search(r"'\\\\\\\\': \[(.*?)\]", segment_section)
        else:
            escaped_char = re.escape(char)
            pattern_match = re.search(rf"'{escaped_char}': \[(.*?)\]", segment_section)
        
        if not pattern_match:
            print(f"✗ Could not find pattern for character '{char}'")
            all_passed = False
            continue
        
        # Parse the pattern
        pattern_str = pattern_match.group(1)
        actual = [v.strip() == 'true' for v in pattern_str.split(',')]
        
        if actual != expected:
            print(f"✗ Character '{char}' has incorrect pattern")
            print(f"  Expected: {expected}")
            print(f"  Actual:   {actual}")
            
            # Show which segments differ
            diffs = []
            seg_names = ['a1', 'a2', 'f', 'h', 'i', 'j', 'b', 'g1', 'g2', 'e', 'k', 'l', 'm', 'c', 'd1', 'd2']
            for i, (e, a) in enumerate(zip(expected, actual)):
                if e != a:
                    diffs.append(f"{seg_names[i]}:{a}->{e}")
            print(f"  Changes needed: {', '.join(diffs)}")
            all_passed = False
        else:
            print(f"  ✓ Character '{char}' pattern is correct")
    
    if all_passed:
        print("✓ All 16-segment character patterns are correct")
    
    return all_passed


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing 16-segment digit and String widget functionality")
    print("=" * 60)
    
    all_passed = True
    
    try:
        if not test_16_segment_digit():
            all_passed = False
    except Exception as e:
        print(f"✗ test_16_segment_digit failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_16_segment_digit_with_decimal():
            all_passed = False
    except Exception as e:
        print(f"✗ test_16_segment_digit_with_decimal failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_string_widget():
            all_passed = False
    except Exception as e:
        print(f"✗ test_string_widget failed: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    try:
        if not test_16_segment_character_patterns():
            all_passed = False
    except Exception as e:
        print(f"✗ test_16_segment_character_patterns failed: {e}")
        import traceback
        traceback.print_exc()
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
