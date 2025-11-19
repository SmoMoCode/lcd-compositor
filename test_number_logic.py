#!/usr/bin/env python3
"""
Test to verify the Number widget SetNumberValue logic.
This simulates the JavaScript logic to ensure it works correctly.
"""

def format_number_for_digits(value, digits_info, add_leading_zeros, decimal_places):
    """
    Simulate the JavaScript SetNumberValue logic.
    
    Args:
        value: Float value to display
        digits_info: List of dicts with 'has_decimal' key
        add_leading_zeros: Boolean
        decimal_places: Integer or None
    
    Returns:
        List of tuples (digit_char, show_decimal) for each digit position
    """
    num_value = float(value)
    
    # Find decimal point position
    decimal_digit_index = -1
    for i, digit in enumerate(digits_info):
        if digit['has_decimal']:
            decimal_digit_index = i
            break
    
    # Format the number
    if decimal_places is not None and decimal_places >= 0 and decimal_digit_index >= 0:
        formatted_value = f"{num_value:.{decimal_places}f}"
    else:
        # Match JavaScript String() behavior which drops .0 for integers
        formatted_value = str(num_value)
        if formatted_value.endswith('.0'):
            formatted_value = formatted_value[:-2]
    
    # Split into parts
    parts = formatted_value.split('.')
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else ''
    
    # Apply leading zeros
    if add_leading_zeros:
        needed_length = decimal_digit_index + 1 if decimal_digit_index >= 0 else len(digits_info)
        integer_part = integer_part.rjust(needed_length, '0')
    
    # Build display string
    # Positions 0 through decimal_digit_index show integer part
    # Positions decimal_digit_index+1 onwards show fractional part
    if decimal_digit_index >= 0 and decimal_part:
        # We have a decimal point available AND we have fractional digits to show
        # Integer part: positions 0 to decimal_digit_index (inclusive)
        num_integer_positions = decimal_digit_index + 1
        integer_display = integer_part[-num_integer_positions:] if len(integer_part) >= num_integer_positions else integer_part
        integer_display = integer_display.rjust(num_integer_positions, ' ')
        
        # Fractional part: positions after decimal_digit_index
        num_fractional_positions = len(digits_info) - decimal_digit_index - 1
        fractional_display = decimal_part[:num_fractional_positions]
        fractional_display = fractional_display.ljust(num_fractional_positions, ' ')
        
        display_string = integer_display + fractional_display
    else:
        # No decimal point to show - treat all digits as integer
        display_string = integer_part[-len(digits_info):] if len(integer_part) >= len(digits_info) else integer_part
        display_string = display_string.rjust(len(digits_info), ' ')
    
    # Build result
    result = []
    for i, digit_info in enumerate(digits_info):
        char = display_string[i] if i < len(display_string) else ' '
        show_decimal = digit_info['has_decimal'] and len(decimal_part) > 0
        result.append((char, show_decimal))
    
    return result


def test_basic_cases():
    """Test basic number display cases."""
    print("Testing basic number display...")
    
    # Digits: [D:7], [D:7p], [D:7] (3 digits, decimal on middle)
    digits_info = [
        {'has_decimal': False},
        {'has_decimal': True},
        {'has_decimal': False}
    ]
    
    # Test 123 - should show "123" with no decimal (decimal point not shown for integer)
    result = format_number_for_digits(123, digits_info, False, None)
    expected = [('1', False), ('2', False), ('3', False)]
    if result != expected:
        print(f"✗ 123: expected {expected}, got {result}")
        return False
    print(f"✓ 123 → {result}")
    
    # Test 12.3 - should show "12.3" with decimal on middle digit
    result = format_number_for_digits(12.3, digits_info, False, None)
    expected = [('1', False), ('2', True), ('3', False)]
    if result != expected:
        print(f"✗ 12.3: expected {expected}, got {result}")
        return False
    print(f"✓ 12.3 → {result}")
    
    # Test 1.2 - should show " 1.2" with decimal on middle digit
    result = format_number_for_digits(1.2, digits_info, False, None)
    expected = [(' ', False), ('1', True), ('2', False)]
    if result != expected:
        print(f"✗ 1.2: expected {expected}, got {result}")
        return False
    print(f"✓ 1.2 → {result}")
    
    # Test 1.2 with leading zeros - should show "01.2"
    result = format_number_for_digits(1.2, digits_info, True, None)
    expected = [('0', False), ('1', True), ('2', False)]
    if result != expected:
        print(f"✗ 1.2 (leading zeros): expected {expected}, got {result}")
        return False
    print(f"✓ 1.2 (leading zeros) → {result}")
    
    # Test 12 with decimalPlaces=1 - should show "12.0"
    result = format_number_for_digits(12, digits_info, False, 1)
    expected = [('1', False), ('2', True), ('0', False)]
    if result != expected:
        print(f"✗ 12 (1 decimal): expected {expected}, got {result}")
        return False
    print(f"✓ 12 (1 decimal) → {result}")
    
    print("✓ Basic cases passed")
    return True


def test_edge_cases():
    """Test edge cases."""
    print("\nTesting edge cases...")
    
    # 2 digits: [D:7p], [D:7] (decimal on first)
    # This allows displaying N.F where N=0-9 and F=0-9
    digits_info = [
        {'has_decimal': True},
        {'has_decimal': False}
    ]
    
    # Test 9.5 - with 2 digits [D:7p]_0, [D:7]_1
    # Integer "9" in pos 0 with decimal, fractional "5" in pos 1
    result = format_number_for_digits(9.5, digits_info, False, None)
    expected = [('9', True), ('5', False)]
    if result != expected:
        print(f"✗ 9.5 (2 digits): expected {expected}, got {result}")
        return False
    print(f"✓ 9.5 (2 digits) → {result}")
    
    # 4 digits: [D:7], [D:7], [D:7p], [D:7] (decimal on third)
    digits_info = [
        {'has_decimal': False},
        {'has_decimal': False},
        {'has_decimal': True},
        {'has_decimal': False}
    ]
    
    # Test 123.4
    result = format_number_for_digits(123.4, digits_info, False, None)
    expected = [('1', False), ('2', False), ('3', True), ('4', False)]
    if result != expected:
        print(f"✗ 123.4 (4 digits): expected {expected}, got {result}")
        return False
    print(f"✓ 123.4 (4 digits) → {result}")
    
    # Test 12.34
    result = format_number_for_digits(12.34, digits_info, False, None)
    expected = [(' ', False), ('1', False), ('2', True), ('3', False)]
    # Note: 12.34 should show " 12.3" because we can only show 1 digit after decimal
    if result != expected:
        print(f"✗ 12.34 (4 digits): expected {expected}, got {result}")
        return False
    print(f"✓ 12.34 (4 digits) → {result}")
    
    print("✓ Edge cases passed")
    return True


def test_no_decimal_point():
    """Test when no digit has a decimal point."""
    print("\nTesting no decimal point...")
    
    # 3 digits: [D:7], [D:7], [D:7] (no decimal)
    digits_info = [
        {'has_decimal': False},
        {'has_decimal': False},
        {'has_decimal': False}
    ]
    
    # Test 123
    result = format_number_for_digits(123, digits_info, False, None)
    expected = [('1', False), ('2', False), ('3', False)]
    if result != expected:
        print(f"✗ 123 (no decimal): expected {expected}, got {result}")
        return False
    print(f"✓ 123 (no decimal) → {result}")
    
    # Test 12.3 - decimal part should be ignored
    result = format_number_for_digits(12.3, digits_info, False, None)
    expected = [(' ', False), ('1', False), ('2', False)]
    # Should show " 12" because no decimal point available
    if result != expected:
        print(f"✗ 12.3 (no decimal): expected {expected}, got {result}")
        return False
    print(f"✓ 12.3 (no decimal) → {result}")
    
    print("✓ No decimal point cases passed")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Number widget logic")
    print("=" * 60)
    
    all_passed = True
    
    if not test_basic_cases():
        all_passed = False
    
    if not test_edge_cases():
        all_passed = False
    
    if not test_no_decimal_point():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All logic tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some logic tests failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
