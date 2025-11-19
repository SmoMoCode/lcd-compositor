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


def extract_layer_image(layer, layer_index, output_dir, base_name, folder_path=None, original_names=None):
    """
    Extract a single layer and save it as an image.
    
    Args:
        layer: The layer to extract
        layer_index: Index of the layer for naming
        output_dir: Directory to save the image
        base_name: Base name for output files (not used in new naming scheme)
        folder_path: List of folder names from root to this layer (sanitized)
        original_names: List of original folder names (with [T] prefix if present)
        
    Returns:
        dict: Layer information including filename, position, name, and original names, or None if layer is empty
    """
    bounds = get_layer_bounds(layer)
    if not bounds:
        return None
    
    left, top, right, bottom = bounds
    
    # Get layer name or use index
    layer_name = layer.name if hasattr(layer, 'name') and layer.name else f"layer_{layer_index}"
    original_layer_name = layer_name
    
    # Remove [T] prefix if present for filename
    clean_layer_name = layer_name[3:] if layer_name.startswith('[T]') else layer_name
    
    # Sanitize filename component
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in clean_layer_name)
    safe_name = safe_name.strip().replace(' ', '_')
    
    # Create filename based on folder structure
    # Format: FolderName--SubFolder--LayerName.png
    if folder_path:
        filename_parts = folder_path + [safe_name]
        filename = "--".join(filename_parts) + ".png"
    else:
        filename = f"{safe_name}.png"
    
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
            'name': clean_layer_name,
            'original_name': original_layer_name,
            'original_folder_path': original_names if original_names else [],
            'x': left,
            'y': top,
            'width': width,
            'height': height
        }
    except Exception as e:
        print(f"Warning: Could not extract layer {layer_index} ({layer_name}): {e}", file=sys.stderr)
        return None


def is_group(obj):
    """Check if an object is a group (iterable container)."""
    try:
        iter(obj)
        return True
    except TypeError:
        return False


def process_layers_recursive(layer_group, layer_list, parent_offset=(0, 0), folder_path=None, original_names=None):
    """
    Recursively process layers, including nested groups.
    
    Args:
        layer_group: The layer or group to process
        layer_list: List to append tuples of (layer, folder_path, original_folder_path)
        parent_offset: Offset from parent groups (x, y)
        folder_path: List of folder names from root to current position (sanitized)
        original_names: List of original folder names (with [T] prefix if present)
    """
    if folder_path is None:
        folder_path = []
    if original_names is None:
        original_names = []
    
    # Check if this is a group/container (iterable)
    if is_group(layer_group):
        # This is a group, process children
        for layer in layer_group:
            # Skip layers/folders starting with #
            if hasattr(layer, 'name') and layer.name.startswith('#'):
                continue
            
            # Check if this child is also a group
            if is_group(layer):
                # It's a nested group - add its name to the folder path
                if hasattr(layer, 'name'):
                    layer_name = layer.name
                    # Store original name for toggle detection
                    original_name = layer_name
                    # Remove [T] prefix if present
                    clean_name = layer_name[3:] if layer_name.startswith('[T]') else layer_name
                    # Sanitize folder name
                    safe_folder_name = "".join(c if c.isalnum() or c in (' ', '-', '_', '[', ']') else '_' for c in clean_name)
                    safe_folder_name = safe_folder_name.strip().replace(' ', '_')
                    # Add folder to path and recurse
                    new_path = folder_path + [safe_folder_name]
                    new_original_path = original_names + [original_name]
                    process_layers_recursive(layer, layer_list, parent_offset, new_path, new_original_path)
                else:
                    # Group without name, recurse without changing path
                    process_layers_recursive(layer, layer_list, parent_offset, folder_path, original_names)
            else:
                # It's a regular layer, add it with current folder path
                layer_list.append((layer, folder_path[:], original_names[:]))
    else:
        # This is a single layer (not a group)
        if hasattr(layer_group, 'name') and not layer_group.name.startswith('#'):
            layer_list.append((layer_group, folder_path[:], original_names[:]))
        elif not hasattr(layer_group, 'name'):
            # Layer without name, add it anyway
            layer_list.append((layer_group, folder_path[:], original_names[:]))


def extract_widgets(layers_info):
    """
    Extract widget (toggle) information from layers.
    
    Args:
        layers_info: List of layer dictionaries with original names and paths
        
    Returns:
        dict: Dictionary mapping widget names to their associated filenames
    """
    widgets = {}
    
    for layer in layers_info:
        original_name = layer.get('original_name', '')
        original_folder_path = layer.get('original_folder_path', [])
        filename = layer['filename']
        
        # Check if the layer itself has [T] prefix
        if original_name.startswith('[T]'):
            widget_name = original_name[3:]  # Remove [T] prefix
            if widget_name not in widgets:
                widgets[widget_name] = []
            widgets[widget_name].append(filename)
        
        # Check if any folder in the path has [T] prefix
        for folder_name in original_folder_path:
            if folder_name.startswith('[T]'):
                widget_name = folder_name[3:]  # Remove [T] prefix
                if widget_name not in widgets:
                    widgets[widget_name] = []
                widgets[widget_name].append(filename)
    
    return widgets


def create_lcd_screen_html(output_dir, yaml_filename, base_name):
    """
    Create the LCD screen HTML page for visualizing the layers.
    This is designed to be embedded in the index.html page.
    
    Args:
        output_dir: Directory containing the layers and YAML file
        yaml_filename: Name of the YAML file
        base_name: Base name for the HTML file
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LCD Screen</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #1a1a1a;
        }
        
        #canvas-container {
            position: relative;
            width: 100%;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        #canvas-wrapper {
            position: relative;
            transform-origin: center center;
        }
        
        #canvas-wrapper img {
            position: absolute;
            image-rendering: -webkit-optimize-contrast;
            image-rendering: crisp-edges;
        }
        
        .error {
            background-color: #5a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin: 20px;
            color: #ffffff;
        }
    </style>
</head>
<body>
    <div id="canvas-container">
        <div id="canvas-wrapper"></div>
    </div>
    
    <script>
        const YAML_FILE = '""" + yaml_filename + """';
        
        let yamlData = null;
        let layerElements = {};
        let toggleStates = {};
        
        // Simple YAML parser for our specific format
        function parseYAML(yamlText) {
            const lines = yamlText.split('\\n');
            const data = {
                layers: [],
                widgets: {}
            };
            let currentLayer = null;
            let currentWidget = null;
            let inWidgets = false;
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const trimmed = line.trim();
                
                if (trimmed === '' || trimmed.startsWith('#')) continue;
                
                // Check for widgets section
                if (trimmed === 'widgets:') {
                    inWidgets = true;
                    continue;
                }
                
                if (inWidgets) {
                    // Parse widget entries
                    const widgetMatch = line.match(/^\\s+(\\w+):/);
                    if (widgetMatch) {
                        currentWidget = widgetMatch[1];
                        data.widgets[currentWidget] = [];
                    } else if (currentWidget && line.match(/^\\s+-\\s+(.+)$/)) {
                        const filename = line.match(/^\\s+-\\s+(.+)$/)[1].trim();
                        data.widgets[currentWidget].push(filename);
                    }
                } else {
                    // Parse layers
                    if (line.match(/^\\s*-\\s+\\w+:/)) {
                        if (currentLayer) {
                            data.layers.push(currentLayer);
                        }
                        currentLayer = {};
                        const keyVal = line.match(/^\\s*-\\s+(\\w+):\\s*(.*)$/);
                        if (keyVal) {
                            const key = keyVal[1];
                            const value = keyVal[2].trim();
                            currentLayer[key] = isNaN(value) ? value : parseInt(value);
                        }
                    } else {
                        const match = line.match(/^(\\s*)(\\w+):\\s*(.*)$/);
                        if (match) {
                            const indent = match[1].length;
                            const key = match[2];
                            const value = match[3].trim();
                            
                            if (indent === 0) {
                                if (key !== 'layers' && key !== 'widgets') {
                                    data[key] = isNaN(value) ? value : parseInt(value);
                                }
                            } else if (currentLayer) {
                                currentLayer[key] = isNaN(value) ? value : parseInt(value);
                            }
                        }
                    }
                }
            }
            
            if (currentLayer) {
                data.layers.push(currentLayer);
            }
            
            return data;
        }
        
        // Load and parse YAML file
        async function loadYAML() {
            try {
                const response = await fetch(YAML_FILE);
                if (!response.ok) {
                    throw new Error(`Failed to load YAML file: ${response.statusText}`);
                }
                const yamlText = await response.text();
                const data = parseYAML(yamlText);
                return data;
            } catch (error) {
                console.error('Error loading YAML:', error);
                document.getElementById('canvas-container').innerHTML = 
                    '<div class="error"><h2>Error</h2><p>' + error.message + '</p></div>';
                throw error;
            }
        }
        
        // Create and position images
        function createLayers(data) {
            const wrapper = document.getElementById('canvas-wrapper');
            const docWidth = data.document_width;
            const docHeight = data.document_height;
            
            // Set wrapper size to document size
            wrapper.style.width = docWidth + 'px';
            wrapper.style.height = docHeight + 'px';
            
            // Create image elements for each layer
            data.layers.forEach((layer, index) => {
                const img = document.createElement('img');
                img.src = layer.filename;
                img.style.left = layer.x + 'px';
                img.style.top = layer.y + 'px';
                img.alt = layer.name;
                img.title = layer.name;
                img.dataset.filename = layer.filename;
                
                wrapper.appendChild(img);
                layerElements[layer.filename] = img;
            });
            
            // Initialize all toggles to true (visible)
            Object.keys(data.widgets || {}).forEach(widgetName => {
                toggleStates[widgetName] = true;
            });
            
            // Scale to fit container
            scaleToFit();
        }
        
        // Scale the canvas to fit the container
        function scaleToFit() {
            const container = document.getElementById('canvas-container');
            const wrapper = document.getElementById('canvas-wrapper');
            
            if (!wrapper.style.width) return;
            
            const docWidth = parseInt(wrapper.style.width);
            const docHeight = parseInt(wrapper.style.height);
            const containerWidth = container.clientWidth;
            const containerHeight = container.clientHeight;
            
            // Calculate scale to fit
            const scaleX = containerWidth / docWidth;
            const scaleY = containerHeight / docHeight;
            const scale = Math.min(scaleX, scaleY, 1); // Don't scale up
            
            wrapper.style.transform = `scale(${scale})`;
        }
        
        // Set toggle state for a widget
        function SetToggle(name, value) {
            toggleStates[name] = value;
            
            if (!yamlData || !yamlData.widgets || !yamlData.widgets[name]) {
                console.warn(`Toggle '${name}' not found in widgets`);
                return;
            }
            
            const filenames = yamlData.widgets[name];
            filenames.forEach(filename => {
                const img = layerElements[filename];
                if (img) {
                    img.style.display = value ? 'block' : 'none';
                }
            });
        }
        
        // Make SetToggle available globally
        window.SetToggle = SetToggle;
        
        // Initialize
        async function init() {
            try {
                yamlData = await loadYAML();
                createLayers(yamlData);
                
                // Handle resize
                window.addEventListener('resize', scaleToFit);
            } catch (error) {
                console.error('Initialization failed:', error);
            }
        }
        
        // Start when page loads
        window.addEventListener('load', init);
    </script>
</body>
</html>"""
    
    html_path = output_dir / "lcd-screen.html"
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    return html_path


def create_index_html(output_dir, yaml_filename, base_name):
    """
    Create the index.html page with left panel for toggles and right panel for LCD screen.
    
    Args:
        output_dir: Directory containing the layers and YAML file
        yaml_filename: Name of the YAML file
        base_name: Base name for the HTML file
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LCD Compositor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: Arial, sans-serif;
            background-color: #2b2b2b;
            color: #ffffff;
            overflow: hidden;
        }
        
        #container {
            display: flex;
            width: 100vw;
            height: 100vh;
        }
        
        #left-panel {
            width: 300px;
            background-color: #3a3a3a;
            padding: 20px;
            overflow-y: auto;
            border-right: 2px solid #4a4a4a;
        }
        
        #left-panel h1 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #ffffff;
        }
        
        #widgets {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        
        .widget-item {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px;
            background-color: #2b2b2b;
            border-radius: 5px;
        }
        
        .widget-item label {
            flex: 1;
            cursor: pointer;
            font-size: 16px;
        }
        
        .widget-item input[type="checkbox"] {
            width: 24px;
            height: 24px;
            cursor: pointer;
        }
        
        #right-panel {
            flex: 1;
            background-color: #1a1a1a;
            overflow: hidden;
        }
        
        #right-panel iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        .no-widgets {
            color: #888;
            font-style: italic;
        }
    </style>
</head>
<body>
    <div id="container">
        <div id="left-panel">
            <h1>Widgets</h1>
            <div id="widgets">
                <p class="no-widgets">Loading...</p>
            </div>
        </div>
        <div id="right-panel">
            <iframe id="lcd-screen" src="lcd-screen.html"></iframe>
        </div>
    </div>
    
    <script>
        const YAML_FILE = '""" + yaml_filename + """';
        
        // Simple YAML parser for widgets section
        function parseYAML(yamlText) {
            const lines = yamlText.split('\\n');
            const widgets = {};
            let inWidgets = false;
            let currentWidget = null;
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const trimmed = line.trim();
                
                if (trimmed === '' || trimmed.startsWith('#')) continue;
                
                if (trimmed === 'widgets:') {
                    inWidgets = true;
                    continue;
                }
                
                if (inWidgets) {
                    const widgetMatch = line.match(/^\\s+(\\w+):/);
                    if (widgetMatch) {
                        currentWidget = widgetMatch[1];
                        widgets[currentWidget] = [];
                    } else if (currentWidget && line.match(/^\\s+-\\s+(.+)$/)) {
                        const filename = line.match(/^\\s+-\\s+(.+)$/)[1].trim();
                        widgets[currentWidget].push(filename);
                    }
                }
            }
            
            return widgets;
        }
        
        // Load widgets from YAML
        async function loadWidgets() {
            try {
                const response = await fetch(YAML_FILE);
                if (!response.ok) {
                    throw new Error(`Failed to load YAML file: ${response.statusText}`);
                }
                const yamlText = await response.text();
                const widgets = parseYAML(yamlText);
                return widgets;
            } catch (error) {
                console.error('Error loading widgets:', error);
                return {};
            }
        }
        
        // Create widget controls
        function createWidgetControls(widgets) {
            const widgetsContainer = document.getElementById('widgets');
            widgetsContainer.innerHTML = '';
            
            const widgetNames = Object.keys(widgets);
            
            if (widgetNames.length === 0) {
                widgetsContainer.innerHTML = '<p class="no-widgets">No widgets found</p>';
                return;
            }
            
            widgetNames.forEach(widgetName => {
                const widgetItem = document.createElement('div');
                widgetItem.className = 'widget-item';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `widget-${widgetName}`;
                checkbox.checked = true; // Default to on
                checkbox.addEventListener('change', (e) => {
                    toggleWidget(widgetName, e.target.checked);
                });
                
                const label = document.createElement('label');
                label.htmlFor = `widget-${widgetName}`;
                label.textContent = widgetName;
                
                widgetItem.appendChild(checkbox);
                widgetItem.appendChild(label);
                widgetsContainer.appendChild(widgetItem);
            });
        }
        
        // Toggle widget on/off
        function toggleWidget(name, value) {
            const iframe = document.getElementById('lcd-screen');
            if (iframe && iframe.contentWindow && iframe.contentWindow.SetToggle) {
                iframe.contentWindow.SetToggle(name, value);
            }
        }
        
        // Initialize
        async function init() {
            const widgets = await loadWidgets();
            createWidgetControls(widgets);
        }
        
        // Wait for iframe to load before initializing
        window.addEventListener('load', () => {
            const iframe = document.getElementById('lcd-screen');
            iframe.addEventListener('load', init);
        });
    </script>
</body>
</html>"""
    
    html_path = output_dir / "index.html"
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    return html_path


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
    
    for idx, (layer, folder_path, original_names) in enumerate(all_layers):
        layer_info = extract_layer_image(layer, idx, output_dir, base_name, folder_path, original_names)
        if layer_info:
            layers_info.append(layer_info)
            print(f"Extracted: {layer_info['filename']} at ({layer_info['x']}, {layer_info['y']})")
    
    # Extract widget information
    widgets = extract_widgets(layers_info)
    
    # Create YAML file
    yaml_filename = f"{base_name}.yml"
    yaml_path = output_dir / yaml_filename
    
    yaml_data = {
        'source_file': input_path.name,
        'document_width': psd.width,
        'document_height': psd.height,
        'layers': layers_info,
        'widgets': widgets
    }
    
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"\nExtracted {len(layers_info)} layers to: {output_dir}")
    print(f"Layer information saved to: {yaml_path}")
    if widgets:
        print(f"Found {len(widgets)} widget(s): {', '.join(widgets.keys())}")
    
    # Create HTML files
    lcd_screen_path = create_lcd_screen_html(output_dir, yaml_filename, base_name)
    print(f"LCD screen HTML created: {lcd_screen_path}")
    
    index_path = create_index_html(output_dir, yaml_filename, base_name)
    print(f"Index HTML created: {index_path}")
    
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
