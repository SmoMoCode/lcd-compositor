#!/usr/bin/env python3
"""
PSB/PSD Layer Extractor

This script extracts layers from Adobe PSB/PSD files and saves them as individual
images with their position information in a YAML file.
"""

import argparse
import os
import sys
from pathlib import Path
from psd_tools import PSDImage
from PIL import Image
import yaml


def get_layer_bounds(layer):
    """
    Get the actual content bounds of a layer.
    
    Args:
        layer: A PSD layer object
        
    Returns:
        tuple: (left, top, right, bottom) bounds or None if layer is empty
    """
    try:
        # Get the layer's bounding box
        bbox = layer.bbox
        if bbox and bbox[2] > bbox[0] and bbox[3] > bbox[1]:
            return bbox
    except Exception:
        pass
    return None


def extract_layer_image(layer, layer_index, output_dir, base_name):
    """
    Extract a single layer and save it as an image.
    
    Args:
        layer: The layer to extract
        layer_index: Index of the layer for naming
        output_dir: Directory to save the image
        base_name: Base name for output files
        
    Returns:
        dict: Layer information including filename, position, and name, or None if layer is empty
    """
    bounds = get_layer_bounds(layer)
    if not bounds:
        return None
    
    left, top, right, bottom = bounds
    
    # Get layer name or use index
    layer_name = layer.name if hasattr(layer, 'name') and layer.name else f"layer_{layer_index}"
    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in layer_name)
    safe_name = safe_name.strip().replace(' ', '_')
    
    # Create filename
    filename = f"{base_name}_layer_{layer_index:03d}_{safe_name}.png"
    filepath = output_dir / filename
    
    try:
        # Convert layer to PIL Image
        layer_image = layer.topil()
        
        # Crop to content bounds
        # Note: topil() already returns the layer in its correct position, 
        # but we need to crop to the actual bounds
        width = right - left
        height = top - bottom
        
        # Save the image
        layer_image.save(filepath, 'PNG')
        
        return {
            'filename': filename,
            'name': layer_name,
            'x': left,
            'y': top,
            'width': width,
            'height': height
        }
    except Exception as e:
        print(f"Warning: Could not extract layer {layer_index} ({layer_name}): {e}", file=sys.stderr)
        return None


def process_layers_recursive(layer_group, layer_list, parent_offset=(0, 0)):
    """
    Recursively process layers, including nested groups.
    
    Args:
        layer_group: The layer or group to process
        layer_list: List to append layers to
        parent_offset: Offset from parent groups (x, y)
    """
    if hasattr(layer_group, '__iter__'):
        # This is a group, process children
        for layer in layer_group:
            process_layers_recursive(layer, layer_list, parent_offset)
    else:
        # This is a single layer
        layer_list.append(layer_group)


def extract_psb_layers(input_file, output_dir=None):
    """
    Extract all layers from a PSB/PSD file.
    
    Args:
        input_file: Path to the PSB/PSD file
        output_dir: Directory to save extracted layers (defaults to input_file_layers)
        
    Returns:
        tuple: (output_directory, yaml_file_path)
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Determine output directory
    if output_dir is None:
        output_dir = input_path.parent / f"{input_path.stem}_layers"
    else:
        output_dir = Path(output_dir)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading PSB/PSD file: {input_file}")
    
    # Load the PSD file
    psd = PSDImage.open(input_file)
    
    print(f"Document size: {psd.width}x{psd.height}")
    print(f"Number of layers: {len(list(psd.descendants()))}")
    
    # Collect all layers (including nested ones)
    all_layers = []
    process_layers_recursive(psd, all_layers)
    
    # Extract each layer
    layers_info = []
    base_name = input_path.stem
    
    for idx, layer in enumerate(all_layers):
        layer_info = extract_layer_image(layer, idx, output_dir, base_name)
        if layer_info:
            layers_info.append(layer_info)
            print(f"Extracted: {layer_info['filename']} at ({layer_info['x']}, {layer_info['y']})")
    
    # Create YAML file
    yaml_filename = f"{base_name}.yml"
    yaml_path = output_dir / yaml_filename
    
    yaml_data = {
        'source_file': input_path.name,
        'document_width': psd.width,
        'document_height': psd.height,
        'layers': layers_info
    }
    
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"\nExtracted {len(layers_info)} layers to: {output_dir}")
    print(f"Layer information saved to: {yaml_path}")
    
    return output_dir, yaml_path


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract layers from Adobe PSB/PSD files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.psb
  %(prog)s input.psd -o custom_output_folder
  %(prog)s /path/to/file.psb
        """
    )
    
    parser.add_argument(
        'input_file',
        help='Path to the PSB or PSD file to process'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        help='Output directory for extracted layers (default: <input_file>_layers)',
        default=None
    )
    
    args = parser.parse_args()
    
    try:
        extract_psb_layers(args.input_file, args.output_dir)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
