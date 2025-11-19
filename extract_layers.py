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


def extract_layer_image(layer, layer_index, output_dir, base_name, folder_path=None, toggle_name=None):
    """
    Extract a single layer and save it as an image.
    
    Args:
        layer: The layer to extract
        layer_index: Index of the layer for naming
        output_dir: Directory to save the image
        base_name: Base name for output files (not used in new naming scheme)
        folder_path: List of folder names from root to this layer
        toggle_name: Name of toggle controlling this layer (if any)
        
    Returns:
        dict: Layer information including filename, position, name, and toggle, or None if layer is empty
    """
    bounds = get_layer_bounds(layer)
    if not bounds:
        return None
    
    left, top, right, bottom = bounds
    
    # Get layer name or use index
    layer_name = layer.name if hasattr(layer, 'name') and layer.name else f"layer_{layer_index}"
    
    # Remove [T] prefix from layer name if present (for display purposes)
    display_name = layer_name
    if layer_name.startswith('[T]'):
        display_name = layer_name[3:]
    
    # Sanitize filename component
    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in display_name)
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
        
        layer_info = {
            'filename': filename,
            'name': display_name,
            'x': left,
            'y': top,
            'width': width,
            'height': height
        }
        
        # Add toggle information if this layer is part of a toggle
        if toggle_name:
            layer_info['toggle'] = toggle_name
        
        return layer_info
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


def process_layers_recursive(layer_group, layer_list, parent_offset=(0, 0), folder_path=None, toggle_path=None, widget_info=None):
    """
    Recursively process layers, including nested groups.
    
    Args:
        layer_group: The layer or group to process
        layer_list: List to append tuples of (layer, folder_path, toggle_name, widget_type, widget_name)
        parent_offset: Offset from parent groups (x, y)
        folder_path: List of folder names from root to current position
        toggle_path: Name of the toggle controlling this layer/group (if any)
        widget_info: Tuple of (widget_type, widget_name) if this layer is part of a widget
    """
    if folder_path is None:
        folder_path = []
    
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
                    
                    # Check if this group is a toggle [T]
                    current_toggle = toggle_path
                    current_widget_info = widget_info
                    
                    if layer_name.startswith('[T]'):
                        # Extract toggle name (remove [T] prefix)
                        toggle_name = layer_name[3:]
                        current_toggle = toggle_name
                        layer_name = toggle_name  # Use name without [T] for folder path
                    # Check if this group is a digit [D:7] or [D:7p]
                    elif layer_name.startswith('[D:'):
                        # Extract digit type and name
                        end_bracket = layer_name.find(']')
                        if end_bracket > 0:
                            digit_type = layer_name[1:end_bracket]  # e.g., "D:7" or "D:7p"
                            name_after_bracket = layer_name[end_bracket+1:].strip()
                            widget_name = name_after_bracket if name_after_bracket else digit_type.replace(':', '_')
                            current_widget_info = (digit_type, widget_name)
                            layer_name = widget_name
                    # Check if this group is a range [R]
                    elif layer_name.startswith('[R]'):
                        # Extract range name
                        name_after_bracket = layer_name[3:].strip()
                        widget_name = name_after_bracket if name_after_bracket else 'Range'
                        current_widget_info = ('R', widget_name)
                        layer_name = widget_name
                    
                    # Sanitize folder name
                    safe_folder_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in layer_name)
                    safe_folder_name = safe_folder_name.strip().replace(' ', '_')
                    # Add folder to path and recurse
                    new_path = folder_path + [safe_folder_name]
                    process_layers_recursive(layer, layer_list, parent_offset, new_path, current_toggle, current_widget_info)
                else:
                    # Group without name, recurse without changing path
                    process_layers_recursive(layer, layer_list, parent_offset, folder_path, toggle_path, widget_info)
            else:
                # It's a regular layer
                current_toggle = toggle_path
                current_widget_info = widget_info
                # Check if this layer is a toggle [T]
                if hasattr(layer, 'name') and layer.name.startswith('[T]'):
                    # Extract toggle name (remove [T] prefix)
                    toggle_name = layer.name[3:]
                    current_toggle = toggle_name
                
                # Add it with current folder path, toggle name, and widget info
                layer_list.append((layer, folder_path[:], current_toggle, current_widget_info))
    else:
        # This is a single layer (not a group)
        if hasattr(layer_group, 'name') and not layer_group.name.startswith('#'):
            current_toggle = toggle_path
            if layer_group.name.startswith('[T]'):
                toggle_name = layer_group.name[3:]
                current_toggle = toggle_name
            layer_list.append((layer_group, folder_path[:], current_toggle, widget_info))
        elif not hasattr(layer_group, 'name'):
            # Layer without name, add it anyway
            layer_list.append((layer_group, folder_path[:], toggle_path, widget_info))


def create_lcd_screen_html(output_dir, yaml_filename):
    """
    Create the LCD screen HTML file for embedding in the container.
    
    Args:
        output_dir: Directory containing the layers and YAML file
        yaml_filename: Name of the YAML file
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
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100vw;
            height: 100vh;
        }
        
        #canvas-container {
            position: relative;
            background-color: #1a1a1a;
            transform-origin: center center;
        }
        
        #canvas-container img {
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
    <div id="canvas-container"></div>
    
    <script>
        const YAML_FILE = '""" + yaml_filename + """';
        
        let yamlData = null;
        let layerElements = {};
        let toggleStates = {};
        
        // Helper function to strip quotes from YAML values
        function stripQuotes(value) {
            value = value.trim();
            if ((value.startsWith("'") && value.endsWith("'")) || 
                (value.startsWith('"') && value.endsWith('"'))) {
                return value.slice(1, -1);
            }
            return value;
        }
        
        // Simple YAML parser for our specific format
        function parseYAML(yamlText) {
            const lines = yamlText.split('\\n');
            const data = {
                layers: [],
                widgets: {}
            };
            let currentLayer = null;
            let currentWidget = null;
            let inWidgetsSection = false;
            let inLayersSection = false;
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const trimmed = line.trim();
                
                if (trimmed === '' || trimmed.startsWith('#')) continue;
                
                // Check for main sections
                if (line.match(/^widgets:/)) {
                    inWidgetsSection = true;
                    inLayersSection = false;
                    continue;
                }
                if (line.match(/^layers:/)) {
                    inLayersSection = true;
                    inWidgetsSection = false;
                    continue;
                }
                
                // Parse layers section
                if (inLayersSection && line.match(/^\\s*-\\s+\\w+:/)) {
                    if (currentLayer) {
                        data.layers.push(currentLayer);
                    }
                    currentLayer = {};
                    const keyVal = line.match(/^\\s*-\\s+(\\w+):\\s*(.*)$/);
                    if (keyVal) {
                        const key = keyVal[1];
                        const value = stripQuotes(keyVal[2]);
                        currentLayer[key] = isNaN(value) ? value : parseInt(value);
                    }
                } else if (inLayersSection && currentLayer) {
                    const match = line.match(/^\\s+(\\w+):\\s*(.*)$/);
                    if (match) {
                        const key = match[1];
                        const value = stripQuotes(match[2]);
                        currentLayer[key] = isNaN(value) ? value : parseInt(value);
                    }
                }
                
                // Parse widgets section
                if (inWidgetsSection) {
                    const widgetMatch = line.match(/^\\s+(\\w+):/);
                    if (widgetMatch && line.match(/^\\s{2}\\w+:/)) {
                        const widgetName = widgetMatch[1];
                        currentWidget = widgetName;
                        data.widgets[widgetName] = { type: 'toggle', layers: [] };
                    } else if (currentWidget && line.match(/^\\s{4}(\\w+):\\s*(.*)$/)) {
                        // Parse widget properties (type, segments, has_decimal, etc.)
                        const match = line.match(/^\\s{4}(\\w+):\\s*(.*)$/);
                        const key = match[1];
                        let value = stripQuotes(match[2]);
                        
                        // Skip if this is the 'layers:' line (it will be followed by array items)
                        if (key === 'layers' && value === '') {
                            // Ensure layers array exists
                            if (!data.widgets[currentWidget].layers) {
                                data.widgets[currentWidget].layers = [];
                            }
                        } else {
                            // Convert boolean strings
                            if (value === 'true') value = true;
                            else if (value === 'false') value = false;
                            else if (!isNaN(value) && value !== '') value = parseInt(value);
                            data.widgets[currentWidget][key] = value;
                        }
                    } else if (currentWidget && line.match(/^\\s+-\\s+(.+)$/)) {
                        const layerFile = stripQuotes(line.match(/^\\s+-\\s+(.+)$/)[1]);
                        // Ensure layers array exists before pushing
                        if (!data.widgets[currentWidget].layers) {
                            data.widgets[currentWidget].layers = [];
                        }
                        data.widgets[currentWidget].layers.push(layerFile);
                    }
                }
                
                // Top-level properties
                const topMatch = line.match(/^(\\w+):\\s*(.*)$/);
                if (topMatch && !inLayersSection && !inWidgetsSection) {
                    const key = topMatch[1];
                    const value = stripQuotes(topMatch[2]);
                    if (key !== 'layers' && key !== 'widgets') {
                        data[key] = isNaN(value) ? value : parseInt(value);
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
                document.body.innerHTML = 
                    '<div class="error"><h2>Error</h2><p>' + error.message + '</p></div>';
                throw error;
            }
        }
        
        // Create and position images
        function createLayers(data) {
            const container = document.getElementById('canvas-container');
            const docWidth = data.document_width;
            const docHeight = data.document_height;
            
            // Set container size to document dimensions
            container.style.width = docWidth + 'px';
            container.style.height = docHeight + 'px';
            
            // Scale container to fit viewport while maintaining aspect ratio
            scaleContainer();
            
            // Create image elements for each layer
            data.layers.forEach((layer, index) => {
                const img = document.createElement('img');
                img.src = layer.filename;
                img.style.left = layer.x + 'px';
                img.style.top = layer.y + 'px';
                img.alt = layer.name;
                img.title = layer.name;
                img.dataset.layerIndex = index;
                img.dataset.filename = layer.filename;
                
                container.appendChild(img);
                layerElements[layer.filename] = img;
            });
            
            // Initialize toggle states
            if (data.widgets) {
                Object.keys(data.widgets).forEach(toggleName => {
                    toggleStates[toggleName] = true; // Default to on
                });
            }
        }
        
        // Scale container to fit viewport
        function scaleContainer() {
            const container = document.getElementById('canvas-container');
            if (!container || !yamlData) return;
            
            const docWidth = yamlData.document_width;
            const docHeight = yamlData.document_height;
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;
            
            // Calculate scale to fit viewport
            const scaleX = viewportWidth / docWidth;
            const scaleY = viewportHeight / docHeight;
            const scale = Math.min(scaleX, scaleY, 1); // Don't scale up
            
            container.style.transform = `scale(${scale})`;
        }
        
        // 7-segment digit mapping: digit -> segments to display
        // Segments: A(top), F(top-left), B(top-right), G(middle), E(bottom-left), C(bottom-right), D(bottom)
        const DIGIT_SEGMENTS = {
            '0': [true, true, true, false, true, true, true],   // A,F,B,E,C,D
            '1': [false, false, true, false, false, true, false], // B,C
            '2': [true, false, true, true, true, false, true],  // A,B,G,E,D
            '3': [true, false, true, true, false, true, true],  // A,B,G,C,D
            '4': [false, true, true, true, false, true, false], // F,B,G,C
            '5': [true, true, false, true, false, true, true],  // A,F,G,C,D
            '6': [true, true, false, true, true, true, true],   // A,F,G,E,C,D
            '7': [true, false, true, false, false, true, false], // A,B,C
            '8': [true, true, true, true, true, true, true],    // All
            '9': [true, true, true, true, false, true, true]    // A,F,B,G,C,D
        };
        
        // SetToggle function - called from parent window
        window.SetToggle = function(name, value) {
            if (!yamlData || !yamlData.widgets || !yamlData.widgets[name]) {
                console.warn(`Toggle "${name}" not found in YAML`);
                return;
            }
            
            toggleStates[name] = value;
            const widget = yamlData.widgets[name];
            
            // Update visibility of all layers controlled by this toggle
            widget.layers.forEach(filename => {
                const img = layerElements[filename];
                if (img) {
                    img.style.display = value ? 'block' : 'none';
                }
            });
        };
        
        // SetDigit function - called from parent window
        window.SetDigit = function(name, digit, showDecimal) {
            if (!yamlData || !yamlData.widgets || !yamlData.widgets[name]) {
                console.warn(`Digit widget "${name}" not found in YAML`);
                return;
            }
            
            const widget = yamlData.widgets[name];
            if (widget.type !== 'digit') {
                console.warn(`Widget "${name}" is not a digit widget`);
                return;
            }
            
            // Get the segment states for the digit
            const digitStr = String(digit);
            const segments = DIGIT_SEGMENTS[digitStr] || [false, false, false, false, false, false, false];
            
            // Update visibility of segment layers (first 7 layers are segments)
            for (let i = 0; i < 7 && i < widget.layers.length; i++) {
                const filename = widget.layers[i];
                const img = layerElements[filename];
                if (img) {
                    img.style.display = segments[i] ? 'block' : 'none';
                }
            }
            
            // Handle decimal point (8th layer if it exists)
            if (widget.has_decimal && widget.layers.length > 7) {
                const decimalFilename = widget.layers[7];
                const decimalImg = layerElements[decimalFilename];
                if (decimalImg) {
                    decimalImg.style.display = showDecimal ? 'block' : 'none';
                }
            }
        };
        
        // SetRange function - called from parent window
        window.SetRange = function(name, start, end) {
            if (!yamlData || !yamlData.widgets || !yamlData.widgets[name]) {
                console.warn(`Range widget "${name}" not found in YAML`);
                return;
            }
            
            const widget = yamlData.widgets[name];
            if (widget.type !== 'range') {
                console.warn(`Widget "${name}" is not a range widget`);
                return;
            }
            
            // Update visibility based on range
            // If both start and end are 0, hide all
            // Otherwise show layers from start-1 to end-1 (0-indexed)
            widget.layers.forEach((filename, index) => {
                const img = layerElements[filename];
                if (img) {
                    const layerNum = index + 1; // Layer numbers are 1-indexed
                    const shouldShow = (start > 0 || end > 0) && layerNum >= start && layerNum <= end;
                    img.style.display = shouldShow ? 'block' : 'none';
                }
            });
        };
        
        // Initialize
        async function init() {
            try {
                yamlData = await loadYAML();
                createLayers(yamlData);
                
                // Listen for window resize
                window.addEventListener('resize', scaleContainer);
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


def create_index_html(output_dir, yaml_filename):
    """
    Create the index.html container page with widgets on left and LCD screen on right.
    
    Args:
        output_dir: Directory containing the layers and YAML file
        yaml_filename: Name of the YAML file
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
            height: 100vh;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            height: 100vh;
        }
        
        .widgets-panel {
            width: 300px;
            background-color: #3a3a3a;
            padding: 20px;
            overflow-y: auto;
            border-right: 2px solid #4a4a4a;
        }
        
        .widgets-panel h1 {
            font-size: 24px;
            margin-bottom: 20px;
            color: #ffffff;
        }
        
        .widget {
            margin-bottom: 15px;
            padding: 10px;
            background-color: #2b2b2b;
            border-radius: 5px;
        }
        
        .widget label {
            display: flex;
            align-items: center;
            cursor: pointer;
            font-size: 16px;
        }
        
        .widget input[type="checkbox"] {
            width: 20px;
            height: 20px;
            margin-right: 10px;
            cursor: pointer;
        }
        
        .widget input[type="text"],
        .widget input[type="number"] {
            padding: 5px;
            margin: 5px;
            background-color: #4a4a4a;
            color: #ffffff;
            border: 1px solid #5a5a5a;
            border-radius: 3px;
            width: 60px;
            font-size: 14px;
        }
        
        .widget-header {
            font-weight: bold;
            margin-bottom: 8px;
            color: #aaaaaa;
        }
        
        .widget-controls {
            display: flex;
            align-items: center;
            gap: 5px;
            flex-wrap: wrap;
        }
        
        .widget-controls label {
            margin: 0;
            font-size: 14px;
        }
        
        .lcd-panel {
            flex: 1;
            position: relative;
            background-color: #1a1a1a;
        }
        
        .lcd-panel iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        .no-widgets {
            color: #888;
            font-style: italic;
            padding: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="widgets-panel">
            <h1>Controls</h1>
            <div id="widgets-container">
                <div class="no-widgets">Loading widgets...</div>
            </div>
        </div>
        <div class="lcd-panel">
            <iframe id="lcd-screen" src="lcd-screen.html"></iframe>
        </div>
    </div>
    
    <script>
        const YAML_FILE = '""" + yaml_filename + """';
        let lcdWindow = null;
        
        // Helper function to strip quotes from YAML values
        function stripQuotes(value) {
            value = value.trim();
            if ((value.startsWith("'") && value.endsWith("'")) || 
                (value.startsWith('"') && value.endsWith('"'))) {
                return value.slice(1, -1);
            }
            return value;
        }
        
        // Simple YAML parser for our specific format
        function parseYAML(yamlText) {
            const lines = yamlText.split('\\n');
            const data = {
                widgets: {}
            };
            let currentWidget = null;
            let inWidgetsSection = false;
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const trimmed = line.trim();
                
                if (trimmed === '' || trimmed.startsWith('#')) continue;
                
                // Check for widgets section
                if (line.match(/^widgets:/)) {
                    inWidgetsSection = true;
                    continue;
                }
                
                // Exit widgets section if we hit another top-level key
                if (inWidgetsSection && line.match(/^\\w+:/) && !line.match(/^\\s/)) {
                    inWidgetsSection = false;
                }
                
                // Parse widgets
                if (inWidgetsSection) {
                    const widgetMatch = line.match(/^\\s+(\\w+):/);
                    if (widgetMatch && line.match(/^\\s{2}\\w+:/)) {
                        const widgetName = widgetMatch[1];
                        currentWidget = widgetName;
                        data.widgets[widgetName] = { type: 'toggle', layers: [] };
                    } else if (currentWidget && line.match(/^\\s{4}(\\w+):\\s*(.*)$/)) {
                        // Parse widget properties (type, segments, has_decimal, etc.)
                        const match = line.match(/^\\s{4}(\\w+):\\s*(.*)$/);
                        const key = match[1];
                        let value = stripQuotes(match[2]);
                        
                        // Skip if this is the 'layers:' line (it will be followed by array items)
                        if (key === 'layers' && value === '') {
                            // Ensure layers array exists
                            if (!data.widgets[currentWidget].layers) {
                                data.widgets[currentWidget].layers = [];
                            }
                        } else {
                            // Convert boolean strings
                            if (value === 'true') value = true;
                            else if (value === 'false') value = false;
                            else if (!isNaN(value) && value !== '') value = parseInt(value);
                            data.widgets[currentWidget][key] = value;
                        }
                    } else if (currentWidget && line.match(/^\\s+-\\s+(.+)$/)) {
                        const layerFile = stripQuotes(line.match(/^\\s+-\\s+(.+)$/)[1]);
                        // Ensure layers array exists before pushing
                        if (!data.widgets[currentWidget].layers) {
                            data.widgets[currentWidget].layers = [];
                        }
                        data.widgets[currentWidget].layers.push(layerFile);
                    }
                }
            }
            
            return data;
        }
        
        // Load widgets from YAML
        async function loadWidgets() {
            try {
                const response = await fetch(YAML_FILE);
                if (!response.ok) {
                    throw new Error(`Failed to load YAML file: ${response.statusText}`);
                }
                const yamlText = await response.text();
                const data = parseYAML(yamlText);
                
                const container = document.getElementById('widgets-container');
                
                if (!data.widgets || Object.keys(data.widgets).length === 0) {
                    container.innerHTML = '<div class="no-widgets">No widgets found</div>';
                    return;
                }
                
                container.innerHTML = '';
                
                // Create controls for each widget
                Object.keys(data.widgets).forEach(widgetName => {
                    const widget = data.widgets[widgetName];
                    
                    if (widget.type === 'toggle') {
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = 'widget';
                        
                        const label = document.createElement('label');
                        
                        const checkbox = document.createElement('input');
                        checkbox.type = 'checkbox';
                        checkbox.checked = true; // Default to on
                        checkbox.id = `toggle-${widgetName}`;
                        checkbox.addEventListener('change', (e) => {
                            setToggle(widgetName, e.target.checked);
                        });
                        
                        const text = document.createTextNode(widgetName);
                        
                        label.appendChild(checkbox);
                        label.appendChild(text);
                        widgetDiv.appendChild(label);
                        container.appendChild(widgetDiv);
                    } else if (widget.type === 'digit') {
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = 'widget';
                        
                        const header = document.createElement('div');
                        header.className = 'widget-header';
                        header.textContent = widgetName;
                        widgetDiv.appendChild(header);
                        
                        const controls = document.createElement('div');
                        controls.className = 'widget-controls';
                        
                        const digitInput = document.createElement('input');
                        digitInput.type = 'text';
                        digitInput.id = `digit-${widgetName}`;
                        digitInput.value = '0';
                        digitInput.maxLength = 1;
                        digitInput.placeholder = '0-9';
                        digitInput.addEventListener('input', (e) => {
                            const value = e.target.value;
                            if (value === '' || (value >= '0' && value <= '9')) {
                                const decimalCheckbox = document.getElementById(`digit-decimal-${widgetName}`);
                                const showDecimal = decimalCheckbox ? decimalCheckbox.checked : false;
                                setDigit(widgetName, value || '0', showDecimal);
                            } else {
                                e.target.value = e.target.value.slice(0, -1);
                            }
                        });
                        controls.appendChild(digitInput);
                        
                        if (widget.has_decimal) {
                            const decimalLabel = document.createElement('label');
                            const decimalCheckbox = document.createElement('input');
                            decimalCheckbox.type = 'checkbox';
                            decimalCheckbox.id = `digit-decimal-${widgetName}`;
                            decimalCheckbox.addEventListener('change', (e) => {
                                const digitInput = document.getElementById(`digit-${widgetName}`);
                                setDigit(widgetName, digitInput.value || '0', e.target.checked);
                            });
                            decimalLabel.appendChild(decimalCheckbox);
                            decimalLabel.appendChild(document.createTextNode(' .'));
                            controls.appendChild(decimalLabel);
                        }
                        
                        widgetDiv.appendChild(controls);
                        container.appendChild(widgetDiv);
                    } else if (widget.type === 'range') {
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = 'widget';
                        
                        const header = document.createElement('div');
                        header.className = 'widget-header';
                        const count = widget.layers ? widget.layers.length : 0;
                        header.textContent = `${widgetName} (${count})`;
                        widgetDiv.appendChild(header);
                        
                        const controls = document.createElement('div');
                        controls.className = 'widget-controls';
                        
                        const startLabel = document.createElement('span');
                        startLabel.textContent = 'START:';
                        controls.appendChild(startLabel);
                        
                        const startInput = document.createElement('input');
                        startInput.type = 'number';
                        startInput.id = `range-start-${widgetName}`;
                        startInput.value = '0';
                        startInput.min = '0';
                        startInput.max = count.toString();
                        startInput.addEventListener('input', (e) => {
                            const endInput = document.getElementById(`range-end-${widgetName}`);
                            setRange(widgetName, parseInt(e.target.value) || 0, parseInt(endInput.value) || 0);
                        });
                        controls.appendChild(startInput);
                        
                        const endLabel = document.createElement('span');
                        endLabel.textContent = 'END:';
                        controls.appendChild(endLabel);
                        
                        const endInput = document.createElement('input');
                        endInput.type = 'number';
                        endInput.id = `range-end-${widgetName}`;
                        endInput.value = '0';
                        endInput.min = '0';
                        endInput.max = count.toString();
                        endInput.addEventListener('input', (e) => {
                            const startInput = document.getElementById(`range-start-${widgetName}`);
                            setRange(widgetName, parseInt(startInput.value) || 0, parseInt(e.target.value) || 0);
                        });
                        controls.appendChild(endInput);
                        
                        widgetDiv.appendChild(controls);
                        container.appendChild(widgetDiv);
                    }
                });
                
                // Initialize LCD screen iframe reference
                const iframe = document.getElementById('lcd-screen');
                
                function initializeWidgets() {
                    lcdWindow = iframe.contentWindow;
                    
                    // Initialize all widgets to their current state
                    Object.keys(data.widgets).forEach(widgetName => {
                        const widget = data.widgets[widgetName];
                        
                        if (widget.type === 'toggle') {
                            const checkbox = document.getElementById(`toggle-${widgetName}`);
                            if (checkbox) {
                                setToggle(widgetName, checkbox.checked);
                            }
                        } else if (widget.type === 'digit') {
                            const digitInput = document.getElementById(`digit-${widgetName}`);
                            const decimalCheckbox = document.getElementById(`digit-decimal-${widgetName}`);
                            const digit = digitInput ? digitInput.value : '0';
                            const showDecimal = decimalCheckbox ? decimalCheckbox.checked : false;
                            setDigit(widgetName, digit, showDecimal);
                        } else if (widget.type === 'range') {
                            const startInput = document.getElementById(`range-start-${widgetName}`);
                            const endInput = document.getElementById(`range-end-${widgetName}`);
                            const start = startInput ? parseInt(startInput.value) : 0;
                            const end = endInput ? parseInt(endInput.value) : 0;
                            setRange(widgetName, start, end);
                        }
                    });
                }
                
                // Check if iframe is already loaded
                if (iframe.contentWindow && iframe.contentWindow.document.readyState === 'complete') {
                    initializeWidgets();
                } else {
                    iframe.addEventListener('load', initializeWidgets);
                }
                
            } catch (error) {
                console.error('Error loading widgets:', error);
                const container = document.getElementById('widgets-container');
                container.innerHTML = '<div class="no-widgets">Error loading widgets</div>';
            }
        }
        
        // Set toggle state in LCD screen
        function setToggle(name, value) {
            if (lcdWindow && lcdWindow.SetToggle) {
                lcdWindow.SetToggle(name, value);
            }
        }
        
        // Set digit state in LCD screen
        function setDigit(name, digit, showDecimal) {
            if (lcdWindow && lcdWindow.SetDigit) {
                lcdWindow.SetDigit(name, digit, showDecimal);
            }
        }
        
        // Set range state in LCD screen
        function setRange(name, start, end) {
            if (lcdWindow && lcdWindow.SetRange) {
                lcdWindow.SetRange(name, start, end);
            }
        }
        
        // Initialize
        window.addEventListener('load', loadWidgets);
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
    
    # Extract each layer and collect widget information
    layers_info = []
    widgets = {}  # Dictionary to store toggle, digit, and range information
    base_name = input_path.stem
    
    for idx, (layer, folder_path, toggle_name, widget_info) in enumerate(all_layers):
        layer_info = extract_layer_image(layer, idx, output_dir, base_name, folder_path, toggle_name)
        if layer_info:
            layers_info.append(layer_info)
            print(f"Extracted: {layer_info['filename']} at ({layer_info['x']}, {layer_info['y']})")
            
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
    
    # Create YAML file
    yaml_filename = f"{base_name}.yml"
    yaml_path = output_dir / yaml_filename
    
    yaml_data = {
        'source_file': input_path.name,
        'document_width': psd.width,
        'document_height': psd.height,
        'layers': layers_info
    }
    
    # Add widgets section if any toggles were found
    if widgets:
        yaml_data['widgets'] = widgets
    
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"\nExtracted {len(layers_info)} layers to: {output_dir}")
    print(f"Layer information saved to: {yaml_path}")
    if widgets:
        print(f"Found {len(widgets)} widget(s): {', '.join(widgets.keys())}")
    
    # Create LCD screen HTML
    lcd_screen_path = create_lcd_screen_html(output_dir, yaml_filename)
    print(f"LCD screen page created: {lcd_screen_path}")
    
    # Create index HTML container
    index_path = create_index_html(output_dir, yaml_filename)
    print(f"Index page created: {index_path}")
    
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
