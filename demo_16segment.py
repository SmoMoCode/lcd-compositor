#!/usr/bin/env python3
"""
Demo script to show 16-segment digit and String widget configuration.
This generates example YAML output showing how the new widget types are structured.
"""

import yaml

# Example configuration showing all widget types
demo_config = {
    'source_file': 'example.psb',
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
        # 7-segment digit (existing)
        'Speed': {
            'type': 'digit',
            'segments': 7,
            'has_decimal': False,
            'layers': [
                'Speed--segment_A.png',
                'Speed--segment_F.png',
                'Speed--segment_B.png',
                'Speed--segment_G.png',
                'Speed--segment_E.png',
                'Speed--segment_C.png',
                'Speed--segment_D.png'
            ]
        },
        # 16-segment digit (NEW!)
        'Display': {
            'type': 'digit',
            'segments': 16,
            'has_decimal': True,
            'layers': [
                'Display--a1.png',
                'Display--a2.png',
                'Display--f.png',
                'Display--h.png',
                'Display--i.png',
                'Display--j.png',
                'Display--b.png',
                'Display--g1.png',
                'Display--g2.png',
                'Display--e.png',
                'Display--k.png',
                'Display--l.png',
                'Display--m.png',
                'Display--c.png',
                'Display--d1.png',
                'Display--d2.png',
                'Display--dp.png'
            ]
        },
        # String widget using 16-segment digits (NEW!)
        'Message': {
            'type': 'string',
            'digits': [
                {
                    'name': 'char0',
                    'has_decimal': False,
                    'layers': [
                        'Message--char0--a1.png',
                        'Message--char0--a2.png',
                        'Message--char0--f.png',
                        'Message--char0--h.png',
                        'Message--char0--i.png',
                        'Message--char0--j.png',
                        'Message--char0--b.png',
                        'Message--char0--g1.png',
                        'Message--char0--g2.png',
                        'Message--char0--e.png',
                        'Message--char0--k.png',
                        'Message--char0--l.png',
                        'Message--char0--m.png',
                        'Message--char0--c.png',
                        'Message--char0--d1.png',
                        'Message--char0--d2.png'
                    ]
                },
                {
                    'name': 'char1',
                    'has_decimal': True,
                    'layers': [
                        'Message--char1--a1.png',
                        'Message--char1--a2.png',
                        'Message--char1--f.png',
                        'Message--char1--h.png',
                        'Message--char1--i.png',
                        'Message--char1--j.png',
                        'Message--char1--b.png',
                        'Message--char1--g1.png',
                        'Message--char1--g2.png',
                        'Message--char1--e.png',
                        'Message--char1--k.png',
                        'Message--char1--l.png',
                        'Message--char1--m.png',
                        'Message--char1--c.png',
                        'Message--char1--d1.png',
                        'Message--char1--d2.png',
                        'Message--char1--dp.png'
                    ]
                }
            ]
        }
    }
}

def main():
    print("=" * 70)
    print("16-SEGMENT DIGIT AND STRING WIDGET DEMO")
    print("=" * 70)
    print()
    print("This demo shows the new widget types added to the LCD compositor:")
    print()
    print("1. [D:16] - 16-segment digit (alphanumeric)")
    print("2. [D:16p] - 16-segment digit with decimal point")
    print("3. [S] - String widget (multiple 16-segment digits for text display)")
    print()
    print("-" * 70)
    print("EXAMPLE YAML CONFIGURATION:")
    print("-" * 70)
    print()
    
    # Print the YAML
    yaml_output = yaml.dump(demo_config, default_flow_style=False, sort_keys=False)
    print(yaml_output)
    
    print()
    print("-" * 70)
    print("SUPPORTED CHARACTERS (16-segment):")
    print("-" * 70)
    print()
    print("• Digits: 0-9")
    print("• Letters: A-Z (uppercase)")
    print("• Special: space, -, _, /, \\, =, +, *, (, ), [, ], ', \"")
    print("• Period (.) merges with preceding digit's decimal point if available")
    print()
    print("-" * 70)
    print("PSD LAYER ORDER (top to bottom):")
    print("-" * 70)
    print()
    print("16-segment digit layers must be arranged in this order:")
    for i, segment in enumerate(['a1', 'a2', 'f', 'h', 'i', 'j', 'b', 'g1', 'g2', 'e', 'k', 'l', 'm', 'c', 'd1', 'd2'], 1):
        print(f"{i:2d}. {segment}")
    print("17. dp (optional decimal point for [D:16p])")
    print()
    print("-" * 70)
    print("USAGE EXAMPLES:")
    print("-" * 70)
    print()
    print("Folder Structure in PSD:")
    print("  • [D:16]Display - Single 16-segment digit")
    print("  • [D:16p]Temperature - 16-segment digit with decimal")
    print("  • [S]Message - String widget with multiple 16-segment digits")
    print("    ├── [D:16]char0")
    print("    ├── [D:16p]char1")
    print("    └── [D:16]char2")
    print()
    print("String Widget Examples:")
    print("  • 'HELLO' - Displays text across 5 digits")
    print("  • '12.34' - Period merges with digit 2's decimal point")
    print("  • 'AB-CD' - Uses hyphen character")
    print()
    print("=" * 70)

if __name__ == '__main__':
    main()
