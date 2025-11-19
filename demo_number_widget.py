#!/usr/bin/env python3
"""
Demo script to show Number widget YAML output.
This demonstrates what a real extraction would produce.
"""

import yaml

def create_demo_yaml():
    """Create a demo YAML file showing Number widget structure."""
    
    yaml_data = {
        'source_file': 'demo.psb',
        'document_width': 1920,
        'document_height': 1080,
        'layers': [
            {
                'filename': 'Background.png',
                'name': 'Background',
                'x': 0,
                'y': 0,
                'width': 1920,
                'height': 1080
            }
        ],
        'widgets': {
            'Speed': {
                'type': 'number',
                'digits': [
                    {
                        'name': 'hundreds',
                        'has_decimal': False,
                        'layers': [
                            'Speed--hundreds--segment_A.png',
                            'Speed--hundreds--segment_F.png',
                            'Speed--hundreds--segment_B.png',
                            'Speed--hundreds--segment_G.png',
                            'Speed--hundreds--segment_E.png',
                            'Speed--hundreds--segment_C.png',
                            'Speed--hundreds--segment_D.png'
                        ]
                    },
                    {
                        'name': 'tens',
                        'has_decimal': True,
                        'layers': [
                            'Speed--tens--segment_A.png',
                            'Speed--tens--segment_F.png',
                            'Speed--tens--segment_B.png',
                            'Speed--tens--segment_G.png',
                            'Speed--tens--segment_E.png',
                            'Speed--tens--segment_C.png',
                            'Speed--tens--segment_D.png',
                            'Speed--tens--decimal.png'
                        ]
                    },
                    {
                        'name': 'ones',
                        'has_decimal': False,
                        'layers': [
                            'Speed--ones--segment_A.png',
                            'Speed--ones--segment_F.png',
                            'Speed--ones--segment_B.png',
                            'Speed--ones--segment_G.png',
                            'Speed--ones--segment_E.png',
                            'Speed--ones--segment_C.png',
                            'Speed--ones--segment_D.png'
                        ]
                    }
                ]
            },
            'StatusLight': {
                'type': 'toggle',
                'layers': ['StatusLight--light.png']
            }
        }
    }
    
    return yaml_data


def main():
    """Generate and display demo YAML."""
    print("=" * 70)
    print("Number Widget Demo - YAML Output")
    print("=" * 70)
    print()
    print("This demonstrates the YAML structure generated when extracting")
    print("a PSB file with a Number widget.")
    print()
    print("PSB Structure:")
    print("  [N]Speed")
    print("    └─ [D:7]hundreds")
    print("    └─ [D:7p]tens")
    print("    └─ [D:7]ones")
    print()
    print("Generated YAML:")
    print("-" * 70)
    
    demo_data = create_demo_yaml()
    yaml_str = yaml.dump(demo_data, default_flow_style=False, sort_keys=False)
    print(yaml_str)
    
    print("-" * 70)
    print()
    print("Key Features:")
    print("  ✓ Number widget type: 'number'")
    print("  ✓ Contains 3 digits with metadata")
    print("  ✓ Middle digit (tens) has decimal point capability")
    print("  ✓ Each digit has 7 segments (or 8 with decimal)")
    print()
    print("HTML Interface Controls:")
    print("  • Value input: Enter any number (e.g., 12.3, 123, 1.2)")
    print("  • Leading zeros: Pad integer part with zeros")
    print("  • Decimal places: Force number of decimal digits")
    print()
    print("Example Displays:")
    print("  123     → '123' (no decimal shown)")
    print("  12.3    → '12.3' (decimal on tens digit)")
    print("  1.2     → ' 1.2' (leading space)")
    print("  1.2 +LZ → '01.2' (with leading zero)")
    print("  12 +DP1 → '12.0' (with 1 decimal place)")
    print()
    print("=" * 70)
    print("✓ Number Widget Implementation Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
