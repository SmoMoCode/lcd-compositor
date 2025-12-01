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


def process_layers_recursive(layer_group, layer_list, parent_offset=(0, 0), folder_path=None, toggle_path=None, widget_info=None, number_widget_info=None):
    """
    Recursively process layers, including nested groups.
    
    Args:
        layer_group: The layer or group to process
        layer_list: List to append tuples of (layer, folder_path, toggle_name, widget_type, widget_name, number_widget_info)
        parent_offset: Offset from parent groups (x, y)
        folder_path: List of folder names from root to current position
        toggle_path: Name of the toggle controlling this layer/group (if any)
        widget_info: Tuple of (widget_type, widget_name) if this layer is part of a widget
        number_widget_info: Tuple of (parent_widget_type, parent_widget_name, digit_type, digit_name) if this is part of a Number/String widget
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
                    current_number_widget_info = number_widget_info
                    
                    if layer_name.startswith('[T]'):
                        # Extract toggle name (remove [T] prefix)
                        toggle_name = layer_name[3:]
                        current_toggle = toggle_name
                        layer_name = toggle_name  # Use name without [T] for folder path
                    # Check if this group is a Number [N]
                    elif layer_name.startswith('[N]'):
                        # Extract number widget name
                        name_after_bracket = layer_name[3:].strip()
                        widget_name = name_after_bracket if name_after_bracket else 'Number'
                        current_widget_info = ('N', widget_name)
                        layer_name = widget_name
                        
                        # Don't pass down number_widget_info yet - we'll handle digits specially below
                        # Number widget itself doesn't have layers, only its child digits do
                    # Check if this group is a String [S]
                    elif layer_name.startswith('[S]'):
                        # Extract string widget name
                        name_after_bracket = layer_name[3:].strip()
                        widget_name = name_after_bracket if name_after_bracket else 'String'
                        current_widget_info = ('S', widget_name)
                        layer_name = widget_name
                        
                        # String widget is similar to Number widget but for alphanumeric text
                        # It uses 16-segment digits for its child digits
                    # Check if this group is a digit [D:7] or [D:7p]
                    elif layer_name.startswith('[D:'):
                        # Extract digit type and name
                        end_bracket = layer_name.find(']')
                        if end_bracket > 0:
                            digit_type = layer_name[1:end_bracket]  # e.g., "D:7" or "D:7p"
                            name_after_bracket = layer_name[end_bracket+1:].strip()
                            widget_name = name_after_bracket if name_after_bracket else digit_type.replace(':', '_')
                            
                            # Check if we're inside a Number or String widget
                            if widget_info and widget_info[0] in ('N', 'S'):
                                # This digit is part of a Number or String widget
                                parent_widget_type = widget_info[0]
                                parent_widget_name = widget_info[1]
                                # We need to track which digit position this is
                                # We'll count digits as we encounter them
                                current_number_widget_info = (parent_widget_type, parent_widget_name, digit_type, widget_name)
                            else:
                                # Standalone digit widget
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
                    process_layers_recursive(layer, layer_list, parent_offset, new_path, current_toggle, current_widget_info, current_number_widget_info)
                else:
                    # Group without name, recurse without changing path
                    process_layers_recursive(layer, layer_list, parent_offset, folder_path, toggle_path, widget_info, number_widget_info)
            else:
                # It's a regular layer
                current_toggle = toggle_path
                current_widget_info = widget_info
                current_number_widget_info = number_widget_info
                # Check if this layer is a toggle [T]
                if hasattr(layer, 'name') and layer.name.startswith('[T]'):
                    # Extract toggle name (remove [T] prefix)
                    toggle_name = layer.name[3:]
                    current_toggle = toggle_name
                
                # Add it with current folder path, toggle name, widget info, and number widget info
                layer_list.append((layer, folder_path[:], current_toggle, current_widget_info, current_number_widget_info))
    else:
        # This is a single layer (not a group)
        if hasattr(layer_group, 'name') and not layer_group.name.startswith('#'):
            current_toggle = toggle_path
            if layer_group.name.startswith('[T]'):
                toggle_name = layer_group.name[3:]
                current_toggle = toggle_name
            layer_list.append((layer_group, folder_path[:], current_toggle, widget_info, number_widget_info))
        elif not hasattr(layer_group, 'name'):
            # Layer without name, add it anyway
            layer_list.append((layer_group, folder_path[:], toggle_path, widget_info, number_widget_info))


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
        let shadowElements = {};
        let toggleStates = {};
        
        // Shadow state with default values
        let shadowState = {
            isVisible: true,
            alphaValue: 0.25,
            offsetDistance: 4,
            angle: 315
        };
        
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
                        // Parse widget properties (type, segments, has_decimal, digits, etc.)
                        const match = line.match(/^\\s{4}(\\w+):\\s*(.*)$/);
                        const key = match[1];
                        let value = stripQuotes(match[2]);
                        
                        // Skip if this is the 'layers:' or 'digits:' line (will be followed by array items)
                        if ((key === 'layers' || key === 'digits') && value === '') {
                            // Ensure array exists
                            if (!data.widgets[currentWidget][key]) {
                                data.widgets[currentWidget][key] = [];
                            }
                        } else {
                            // Convert boolean strings
                            if (value === 'true') value = true;
                            else if (value === 'false') value = false;
                            else if (!isNaN(value) && value !== '') value = parseInt(value);
                            data.widgets[currentWidget][key] = value;
                        }
                    } else if (currentWidget && line.match(/^\\s{4}-\\s+(.+)$/)) {
                        // Digit array item (for Number widgets) - starts with '    - name:'
                        if (line.match(/^\\s{4}-\\s+name:/)) {
                            const nameMatch = line.match(/^\\s{4}-\\s+name:\\s*(.*)$/);
                            if (nameMatch) {
                                const digitName = stripQuotes(nameMatch[1]);
                                if (!data.widgets[currentWidget].digits) {
                                    data.widgets[currentWidget].digits = [];
                                }
                                data.widgets[currentWidget].digits.push({
                                    name: digitName,
                                    has_decimal: false,
                                    layers: []
                                });
                            }
                        } else {
                            // Regular layer file (for non-Number widgets like toggle/digit/range)
                            const layerFile = stripQuotes(line.match(/^\\s{4}-\\s+(.+)$/)[1]);
                            if (!data.widgets[currentWidget].layers) {
                                data.widgets[currentWidget].layers = [];
                            }
                            data.widgets[currentWidget].layers.push(layerFile);
                        }
                    } else if (currentWidget && line.match(/^\\s{6}(\\w+):\\s*(.*)$/)) {
                        // Digit properties (has_decimal, layers) - only for Number widgets
                        const match = line.match(/^\\s{6}(\\w+):\\s*(.*)$/);
                        const key = match[1];
                        let value = stripQuotes(match[2]);
                        
                        if (data.widgets[currentWidget].digits && data.widgets[currentWidget].digits.length > 0) {
                            const currentDigit = data.widgets[currentWidget].digits[data.widgets[currentWidget].digits.length - 1];
                            if (key === 'layers' && value === '') {
                                // layers array will follow
                                if (!currentDigit.layers) {
                                    currentDigit.layers = [];
                                }
                            } else {
                                if (value === 'true') value = true;
                                else if (value === 'false') value = false;
                                else if (!isNaN(value) && value !== '') value = parseInt(value);
                                currentDigit[key] = value;
                            }
                        }
                    } else if (currentWidget && line.match(/^\\s{6}-\\s+(.+)$/)) {
                        // Layer file in digit's layers array (for Number widgets)
                        const layerFile = stripQuotes(line.match(/^\\s{6}-\\s+(.+)$/)[1]);
                        if (data.widgets[currentWidget].digits && data.widgets[currentWidget].digits.length > 0) {
                            const currentDigit = data.widgets[currentWidget].digits[data.widgets[currentWidget].digits.length - 1];
                            if (!currentDigit.layers) {
                                currentDigit.layers = [];
                            }
                            currentDigit.layers.push(layerFile);
                        }
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
                // Create shadow element first (so it renders behind the main layer)
                const shadowImg = document.createElement('img');
                shadowImg.src = layer.filename;
                shadowImg.style.left = layer.x + 'px';
                shadowImg.style.top = layer.y + 'px';
                shadowImg.alt = layer.name + ' (shadow)';
                shadowImg.title = layer.name + ' (shadow)';
                shadowImg.dataset.layerIndex = index;
                shadowImg.dataset.filename = layer.filename;
                shadowImg.dataset.isShadow = 'true';
                
                container.appendChild(shadowImg);
                shadowElements[layer.filename] = shadowImg;
                
                // Create main layer element
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
            
            // Apply initial shadow settings
            updateShadows();
            
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
        
        // 16-segment character mapping: character -> segments to display
        // Segment order (layer order from top to bottom in PSD):
        // 0:a1, 1:a2, 2:f, 3:h, 4:i, 5:j, 6:b, 7:g1, 8:g2, 9:e, 10:k, 11:l, 12:m, 13:c, 14:d1, 15:d2
        const CHAR_16_SEGMENTS = {
            // Digits
            '0': [true, true, true, false, false, false, true, false, false, true, false, false, false, true, true, true],
            '1': [false, false, false, false, false, false, true, false, false, false, false, false, false, true, false, false],
            '2': [true, true, false, false, false, false, true, true, true, true, false, false, false, false, true, true],
            '3': [true, true, false, false, false, false, true, true, true, false, false, false, false, true, true, true],
            '4': [false, false, true, false, false, false, true, true, true, false, false, false, false, true, false, false],
            '5': [true, true, true, false, false, false, false, true, true, false, false, false, false, true, true, true],
            '6': [true, true, true, false, false, false, false, true, true, true, false, false, false, true, true, true],
            '7': [true, true, false, false, false, false, true, false, false, false, false, false, false, true, false, false],
            '8': [true, true, true, false, false, false, true, true, true, true, false, false, false, true, true, true],
            '9': [true, true, true, false, false, false, true, true, true, false, false, false, false, true, true, true],
            // Letters A-Z
            'A': [true, true, true, false, false, false, true, true, true, true, false, false, false, true, false, false],
            'B': [true, true, false, false, true, false, true, false, true, false, false, true, false, true, true, true],
            'C': [true, true, true, false, false, false, false, false, false, true, false, false, false, false, true, true],
            'D': [true, true, false, false, true, false, true, false, false, false, false, true, false, true, true, true],
            'E': [true, true, true, false, false, false, false, true, false, true, false, false, false, false, true, true],
            'F': [true, true, true, false, false, false, false, true, false, true, false, false, false, false, false, false],
            'G': [true, true, true, false, false, false, false, false, true, true, false, false, false, true, true, true],
            'H': [false, false, true, false, false, false, true, true, true, true, false, false, false, true, false, false],
            'I': [true, true, false, false, true, false, false, false, false, false, false, true, false, false, true, true],
            'J': [false, false, false, false, false, false, true, false, false, true, false, false, false, true, true, true],
            'K': [false, false, true, false, false, true, false, true, false, true, false, false, true, false, false, false],
            'L': [false, false, true, false, false, false, false, false, false, true, false, false, false, false, true, true],
            'M': [false, false, true, true, false, true, true, false, false, true, false, false, false, true, false, false],
            'N': [false, false, true, true, false, false, true, false, false, true, false, false, true, true, false, false],
            'O': [true, true, true, false, false, false, true, false, false, true, false, false, false, true, true, true],
            'P': [true, true, true, false, false, false, true, true, true, true, false, false, false, false, false, false],
            'Q': [true, true, true, false, false, false, true, false, false, true, false, false, true, true, true, true],
            'R': [true, true, true, false, false, false, true, true, true, true, false, false, true, false, false, false],
            'S': [true, true, true, false, false, false, false, true, true, false, false, false, false, true, true, true],
            'T': [true, true, false, false, true, false, false, false, false, false, false, true, false, false, false, false],
            'U': [false, false, true, false, false, false, true, false, false, true, false, false, false, true, true, true],
            'V': [false, false, true, false, false, false, false, false, false, true, true, false, true, false, false, false],
            'W': [false, false, true, false, false, false, true, false, false, true, true, false, true, true, false, false],
            'X': [false, false, false, true, false, true, false, false, false, false, true, false, true, false, false, false],
            'Y': [false, false, false, true, false, true, false, false, false, false, false, true, false, false, false, false],
            'Z': [true, true, false, false, false, true, false, false, false, false, true, false, false, false, true, true],
            // Special characters
            ' ': [false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false],
            '-': [false, false, false, false, false, false, false, true, true, false, false, false, false, false, false, false],
            '_': [false, false, false, false, false, false, false, false, false, false, false, false, false, false, true, true],
            '/': [false, false, false, false, false, true, false, false, false, false, true, false, false, false, false, false],
            '\\\\': [false, false, false, true, false, false, false, false, false, false, false, false, true, false, false, false],
            '.': [false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false], // Handled separately as decimal point
            '=': [false, false, false, false, false, false, false, true, true, false, false, false, false, false, true, true],
            '+': [false, false, false, false, true, false, false, true, true, false, false, true, false, false, false, false],
            '*': [false, false, false, true, true, true, false, true, true, false, true, true, true, false, false, false],
            '(': [false, false, false, true, false, false, false, false, false, false, false, false, true, false, false, false],
            ')': [false, false, false, false, false, true, false, false, false, false, true, false, false, false, false, false],
            '[': [true, true, true, false, false, false, false, false, false, true, false, false, false, false, true, true],
            ']': [true, true, false, false, false, false, true, false, false, false, false, false, false, true, true, true],
            "'": [false, false, false, false, false, true, false, false, false, false, false, false, false, false, false, false],
            '"': [false, false, false, false, false, true, true, false, false, false, false, false, false, false, false, false],
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
                
                // Update shadow visibility to match
                const shadowImg = shadowElements[filename];
                if (shadowImg && shadowState.isVisible) {
                    shadowImg.style.display = value ? 'block' : 'none';
                }
            });
        };
        
        // Update shadow positions and visibility
        function updateShadows() {
            const { isVisible, alphaValue, offsetDistance, angle } = shadowState;
            
            // Calculate offsets based on angle
            // angle 0 = light from top (shadow goes down): offsetX=0, offsetY=+distance
            // angle 90 = light from right (shadow goes left): offsetX=-distance, offsetY=0
            // angle 180 = light from bottom (shadow goes up): offsetX=0, offsetY=-distance
            // angle 270 = light from left (shadow goes right): offsetX=+distance, offsetY=0
            const radians = (angle * Math.PI) / 180;
            const offsetX = -Math.sin(radians) * offsetDistance;
            const offsetY = Math.cos(radians) * offsetDistance;
            
            // Update all shadow elements
            Object.keys(shadowElements).forEach(filename => {
                const shadowImg = shadowElements[filename];
                const mainImg = layerElements[filename];
                
                if (shadowImg && mainImg) {
                    // Get original position from main image
                    const originalX = parseFloat(mainImg.style.left);
                    const originalY = parseFloat(mainImg.style.top);
                    
                    // Apply shadow offset
                    shadowImg.style.left = (originalX + offsetX) + 'px';
                    shadowImg.style.top = (originalY + offsetY) + 'px';
                    
                    // Set shadow opacity and visibility
                    if (isVisible) {
                        shadowImg.style.display = mainImg.style.display; // Match main layer visibility
                        shadowImg.style.opacity = alphaValue;
                    } else {
                        shadowImg.style.display = 'none';
                    }
                }
            });
        }
        
        // SetShadow function - called from parent window
        window.SetShadow = function(isVisible, alphaValue, offsetDistance, angle) {
            shadowState.isVisible = isVisible;
            shadowState.alphaValue = alphaValue;
            shadowState.offsetDistance = offsetDistance;
            shadowState.angle = angle;
            
            updateShadows();
        };
        
        // SetDigit function - called from parent window
        // Supports both 7-segment and 16-segment displays
        window.SetDigit = function(name, character, showDecimal) {
            if (!yamlData || !yamlData.widgets || !yamlData.widgets[name]) {
                console.warn(`Digit widget "${name}" not found in YAML`);
                return;
            }
            
            const widget = yamlData.widgets[name];
            if (widget.type !== 'digit') {
                console.warn(`Widget "${name}" is not a digit widget`);
                return;
            }
            
            const segments = widget.segments || 7;
            const charStr = String(character).toUpperCase();
            
            // Get the segment states for the character
            let segmentStates;
            if (segments === 16) {
                // 16-segment display - supports alphanumeric
                segmentStates = CHAR_16_SEGMENTS[charStr];
                if (!segmentStates) {
                    // Default to blank if character not found
                    segmentStates = new Array(16).fill(false);
                }
            } else {
                // 7-segment display - only digits
                segmentStates = DIGIT_SEGMENTS[charStr] || [false, false, false, false, false, false, false];
            }
            
            // Update visibility of segment layers
            for (let i = 0; i < segments && i < widget.layers.length; i++) {
                const filename = widget.layers[i];
                const img = layerElements[filename];
                if (img) {
                    const isVisible = segmentStates[i];
                    img.style.display = isVisible ? 'block' : 'none';
                    
                    // Update shadow visibility
                    const shadowImg = shadowElements[filename];
                    if (shadowImg && shadowState.isVisible) {
                        shadowImg.style.display = isVisible ? 'block' : 'none';
                    }
                }
            }
            
            // Handle decimal point (layer after all segments)
            if (widget.has_decimal && widget.layers.length > segments) {
                const decimalFilename = widget.layers[segments];
                const decimalImg = layerElements[decimalFilename];
                if (decimalImg) {
                    decimalImg.style.display = showDecimal ? 'block' : 'none';
                    
                    // Update shadow visibility for decimal point
                    const shadowImg = shadowElements[decimalFilename];
                    if (shadowImg && shadowState.isVisible) {
                        shadowImg.style.display = showDecimal ? 'block' : 'none';
                    }
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
                    
                    // Update shadow visibility
                    const shadowImg = shadowElements[filename];
                    if (shadowImg && shadowState.isVisible) {
                        shadowImg.style.display = shouldShow ? 'block' : 'none';
                    }
                }
            });
        };
        
        // SetNumberValue function - called from parent window
        window.SetNumberValue = function(name, value, addLeadingZeros, decimalPlaces) {
            if (!yamlData || !yamlData.widgets || !yamlData.widgets[name]) {
                console.warn(`Number widget "${name}" not found in YAML`);
                return;
            }
            
            const widget = yamlData.widgets[name];
            if (widget.type !== 'number') {
                console.warn(`Widget "${name}" is not a number widget`);
                return;
            }
            
            if (!widget.digits || widget.digits.length === 0) {
                console.warn(`Number widget "${name}" has no digits`);
                return;
            }
            
            // Convert value to number
            const numValue = parseFloat(value);
            if (isNaN(numValue)) {
                console.warn(`Invalid number value: ${value}`);
                return;
            }
            
            // Find which digits have decimal points
            const digitsInfo = widget.digits.map(d => ({
                name: d.name,
                has_decimal: d.has_decimal,
                layers: d.layers
            }));
            
            // Determine decimal point position (which digit has the decimal point)
            let decimalDigitIndex = -1;
            for (let i = 0; i < digitsInfo.length; i++) {
                if (digitsInfo[i].has_decimal) {
                    decimalDigitIndex = i;
                    break;
                }
            }
            
            // Format the number based on settings
            // Convert to string to get actual decimal places
            let formattedValue = String(numValue);
            
            // Split into integer and decimal parts
            const parts = formattedValue.split('.');
            let integerPart = parts[0];
            let decimalPart = parts[1] || '';
            
            // Apply decimalPlaces as MINIMUM decimal places (pad with zeros if needed)
            if (decimalPlaces !== undefined && decimalPlaces >= 0 && decimalDigitIndex >= 0) {
                // Ensure we have at least decimalPlaces decimal digits
                if (decimalPart.length < decimalPlaces) {
                    decimalPart = decimalPart.padEnd(decimalPlaces, '0');
                }
            }
            
            // Apply leading zeros if needed
            if (addLeadingZeros) {
                const totalDigits = digitsInfo.length;
                const neededLength = decimalDigitIndex >= 0 ? decimalDigitIndex + 1 : totalDigits;
                integerPart = integerPart.padStart(neededLength, '0');
            }
            
            // Build the display string
            // Positions 0 through decimalDigitIndex show integer part
            // Positions decimalDigitIndex+1 onwards show fractional part
            let displayString = '';
            
            if (decimalDigitIndex >= 0 && decimalPart.length > 0) {
                // We have a decimal point available AND we have fractional digits to show
                // Integer part: positions 0 to decimalDigitIndex (inclusive)
                const numIntegerPositions = decimalDigitIndex + 1;
                let integerDisplay = integerPart.slice(-numIntegerPositions);
                integerDisplay = integerDisplay.padStart(numIntegerPositions, ' ');
                
                // Fractional part: positions after decimalDigitIndex
                const numFractionalPositions = digitsInfo.length - decimalDigitIndex - 1;
                let fractionalDisplay = decimalPart.slice(0, numFractionalPositions);
                fractionalDisplay = fractionalDisplay.padEnd(numFractionalPositions, ' ');
                
                displayString = integerDisplay + fractionalDisplay;
            } else {
                // No decimal point to show - treat all digits as integer
                displayString = integerPart.slice(-digitsInfo.length) || '0';
                displayString = displayString.padStart(digitsInfo.length, ' ');
            }
            
            // Set each digit
            for (let i = 0; i < digitsInfo.length; i++) {
                const char = displayString[i];
                const digitInfo = digitsInfo[i];
                
                // Show decimal point only if this digit has it and we're displaying a decimal value
                const showDecimal = digitInfo.has_decimal && decimalPart.length > 0;
                
                if (char === ' ' || char === undefined) {
                    // Hide this digit (blank)
                    for (let j = 0; j < 7 && j < digitInfo.layers.length; j++) {
                        const filename = digitInfo.layers[j];
                        const img = layerElements[filename];
                        if (img) {
                            img.style.display = 'none';
                        }
                        // Hide shadow too
                        const shadowImg = shadowElements[filename];
                        if (shadowImg) {
                            shadowImg.style.display = 'none';
                        }
                    }
                    // Hide decimal if present
                    if (digitInfo.has_decimal && digitInfo.layers.length > 7) {
                        const decimalFilename = digitInfo.layers[7];
                        const decimalImg = layerElements[decimalFilename];
                        if (decimalImg) {
                            decimalImg.style.display = 'none';
                        }
                        // Hide shadow too
                        const shadowImg = shadowElements[decimalFilename];
                        if (shadowImg) {
                            shadowImg.style.display = 'none';
                        }
                    }
                } else {
                    // Display the digit
                    const segments = DIGIT_SEGMENTS[char] || [false, false, false, false, false, false, false];
                    
                    // Update visibility of segment layers
                    for (let j = 0; j < 7 && j < digitInfo.layers.length; j++) {
                        const filename = digitInfo.layers[j];
                        const img = layerElements[filename];
                        if (img) {
                            const isVisible = segments[j];
                            img.style.display = isVisible ? 'block' : 'none';
                            
                            // Update shadow visibility
                            const shadowImg = shadowElements[filename];
                            if (shadowImg && shadowState.isVisible) {
                                shadowImg.style.display = isVisible ? 'block' : 'none';
                            }
                        }
                    }
                    
                    // Handle decimal point
                    if (digitInfo.has_decimal && digitInfo.layers.length > 7) {
                        const decimalFilename = digitInfo.layers[7];
                        const decimalImg = layerElements[decimalFilename];
                        if (decimalImg) {
                            decimalImg.style.display = showDecimal ? 'block' : 'none';
                            
                            // Update shadow visibility
                            const shadowImg = shadowElements[decimalFilename];
                            if (shadowImg && shadowState.isVisible) {
                                shadowImg.style.display = showDecimal ? 'block' : 'none';
                            }
                        }
                    }
                }
            }
        };
        
        // SetString function - called from parent window
        // Displays alphanumeric text using 16-segment digits
        window.SetString = function(name, text) {
            if (!yamlData || !yamlData.widgets || !yamlData.widgets[name]) {
                console.warn(`String widget "${name}" not found in YAML`);
                return;
            }
            
            const widget = yamlData.widgets[name];
            if (widget.type !== 'string') {
                console.warn(`Widget "${name}" is not a string widget`);
                return;
            }
            
            if (!widget.digits || widget.digits.length === 0) {
                console.warn(`String widget "${name}" has no digits`);
                return;
            }
            
            const digitsInfo = widget.digits.map(d => ({
                name: d.name,
                has_decimal: d.has_decimal,
                layers: d.layers,
                segments: 16  // String widgets use 16-segment digits
            }));
            
            // Process the text to handle periods that merge with previous digit's decimal point
            let processedChars = [];
            const textStr = String(text || '');
            
            for (let i = 0; i < textStr.length; i++) {
                const char = textStr[i];
                if (char === '.') {
                    // Check if previous char can have a decimal point
                    if (processedChars.length > 0 && processedChars[processedChars.length - 1].canHaveDecimal) {
                        // Merge with previous character
                        processedChars[processedChars.length - 1].showDecimal = true;
                    } else {
                        // Treat as separate character (though 16-segment may not display it well)
                        processedChars.push({ char: char, showDecimal: false, canHaveDecimal: false });
                    }
                } else {
                    processedChars.push({ char: char, showDecimal: false, canHaveDecimal: true });
                }
            }
            
            // Display characters across available digits (left-to-right)
            for (let i = 0; i < digitsInfo.length; i++) {
                const digitInfo = digitsInfo[i];
                
                if (i < processedChars.length) {
                    const charData = processedChars[i];
                    const char = charData.char.toUpperCase();
                    const showDecimal = charData.showDecimal && digitInfo.has_decimal;
                    
                    // Get segment states for this character
                    const segments = CHAR_16_SEGMENTS[char] || new Array(16).fill(false);
                    
                    // Update visibility of segment layers (16 segments)
                    for (let j = 0; j < 16 && j < digitInfo.layers.length; j++) {
                        const filename = digitInfo.layers[j];
                        const img = layerElements[filename];
                        if (img) {
                            const isVisible = segments[j];
                            img.style.display = isVisible ? 'block' : 'none';
                            
                            // Update shadow visibility
                            const shadowImg = shadowElements[filename];
                            if (shadowImg && shadowState.isVisible) {
                                shadowImg.style.display = isVisible ? 'block' : 'none';
                            }
                        }
                    }
                    
                    // Handle decimal point (17th layer if it exists)
                    if (digitInfo.has_decimal && digitInfo.layers.length > 16) {
                        const decimalFilename = digitInfo.layers[16];
                        const decimalImg = layerElements[decimalFilename];
                        if (decimalImg) {
                            decimalImg.style.display = showDecimal ? 'block' : 'none';
                            
                            // Update shadow visibility
                            const shadowImg = shadowElements[decimalFilename];
                            if (shadowImg && shadowState.isVisible) {
                                shadowImg.style.display = showDecimal ? 'block' : 'none';
                            }
                        }
                    }
                } else {
                    // Blank this digit
                    for (let j = 0; j < digitInfo.layers.length; j++) {
                        const filename = digitInfo.layers[j];
                        const img = layerElements[filename];
                        if (img) {
                            img.style.display = 'none';
                        }
                        // Hide shadow too
                        const shadowImg = shadowElements[filename];
                        if (shadowImg) {
                            shadowImg.style.display = 'none';
                        }
                    }
                }
            }
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
                        // Parse widget properties (type, segments, has_decimal, digits, etc.)
                        const match = line.match(/^\\s{4}(\\w+):\\s*(.*)$/);
                        const key = match[1];
                        let value = stripQuotes(match[2]);
                        
                        // Skip if this is the 'layers:' or 'digits:' line (will be followed by array items)
                        if ((key === 'layers' || key === 'digits') && value === '') {
                            // Ensure array exists
                            if (!data.widgets[currentWidget][key]) {
                                data.widgets[currentWidget][key] = [];
                            }
                        } else {
                            // Convert boolean strings
                            if (value === 'true') value = true;
                            else if (value === 'false') value = false;
                            else if (!isNaN(value) && value !== '') value = parseInt(value);
                            data.widgets[currentWidget][key] = value;
                        }
                    } else if (currentWidget && line.match(/^\\s{4}-\\s+(.+)$/)) {
                        // Could be digit array item or regular widget layer
                        if (line.match(/^\\s{4}-\\s+name:/)) {
                            // Digit array item for Number widgets
                            const nameMatch = line.match(/^\\s{4}-\\s+name:\\s*(.*)$/);
                            if (nameMatch) {
                                const digitName = stripQuotes(nameMatch[1]);
                                if (!data.widgets[currentWidget].digits) {
                                    data.widgets[currentWidget].digits = [];
                                }
                                data.widgets[currentWidget].digits.push({
                                    name: digitName,
                                    has_decimal: false,
                                    layers: []
                                });
                            }
                        } else {
                            // Regular layer file for non-Number widgets
                            const layerFile = stripQuotes(line.match(/^\\s{4}-\\s+(.+)$/)[1]);
                            if (!data.widgets[currentWidget].layers) {
                                data.widgets[currentWidget].layers = [];
                            }
                            data.widgets[currentWidget].layers.push(layerFile);
                        }
                    } else if (currentWidget && line.match(/^\\s{6}(\\w+):\\s*(.*)$/)) {
                        // Digit properties (has_decimal, layers) - only if we have digits
                        const match = line.match(/^\\s{6}(\\w+):\\s*(.*)$/);
                        const key = match[1];
                        let value = stripQuotes(match[2]);
                        
                        if (data.widgets[currentWidget].digits && data.widgets[currentWidget].digits.length > 0) {
                            const currentDigit = data.widgets[currentWidget].digits[data.widgets[currentWidget].digits.length - 1];
                            if (key === 'layers' && value === '') {
                                if (!currentDigit.layers) {
                                    currentDigit.layers = [];
                                }
                            } else {
                                if (value === 'true') value = true;
                                else if (value === 'false') value = false;
                                else if (!isNaN(value) && value !== '') value = parseInt(value);
                                currentDigit[key] = value;
                            }
                        }
                    } else if (currentWidget && line.match(/^\\s{6}-\\s+(.+)$/)) {
                        // Layer file in digit's layers array (for Number widgets)
                        const layerFile = stripQuotes(line.match(/^\\s{6}-\\s+(.+)$/)[1]);
                        if (data.widgets[currentWidget].digits && data.widgets[currentWidget].digits.length > 0) {
                            const currentDigit = data.widgets[currentWidget].digits[data.widgets[currentWidget].digits.length - 1];
                            if (!currentDigit.layers) {
                                currentDigit.layers = [];
                            }
                            currentDigit.layers.push(layerFile);
                        }
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
                
                // Create shadow controls first
                const shadowDiv = document.createElement('div');
                shadowDiv.className = 'widget';
                shadowDiv.style.borderBottom = '2px solid #4a4a4a';
                shadowDiv.style.marginBottom = '20px';
                shadowDiv.style.paddingBottom = '15px';
                
                const shadowHeader = document.createElement('div');
                shadowHeader.className = 'widget-header';
                shadowHeader.textContent = 'Shadow Effect';
                shadowDiv.appendChild(shadowHeader);
                
                // Shadow visibility checkbox
                const visibilityRow = document.createElement('div');
                visibilityRow.style.marginBottom = '10px';
                const visibilityLabel = document.createElement('label');
                const visibilityCheckbox = document.createElement('input');
                visibilityCheckbox.type = 'checkbox';
                visibilityCheckbox.id = 'shadow-visible';
                visibilityCheckbox.checked = true;
                visibilityCheckbox.addEventListener('change', updateShadow);
                visibilityLabel.appendChild(visibilityCheckbox);
                visibilityLabel.appendChild(document.createTextNode(' Enable Shadow'));
                visibilityRow.appendChild(visibilityLabel);
                shadowDiv.appendChild(visibilityRow);
                
                // Shadow alpha slider
                const alphaRow = document.createElement('div');
                alphaRow.style.marginBottom = '10px';
                const alphaLabel = document.createElement('span');
                alphaLabel.textContent = 'Opacity: ';
                alphaLabel.style.fontSize = '14px';
                alphaRow.appendChild(alphaLabel);
                const alphaValue = document.createElement('span');
                alphaValue.id = 'shadow-alpha-value';
                alphaValue.textContent = '0.25';
                alphaValue.style.fontSize = '14px';
                alphaValue.style.marginLeft = '5px';
                alphaRow.appendChild(alphaValue);
                const alphaSlider = document.createElement('input');
                alphaSlider.type = 'range';
                alphaSlider.id = 'shadow-alpha';
                alphaSlider.min = '0';
                alphaSlider.max = '100';
                alphaSlider.value = '25';
                alphaSlider.style.width = '100%';
                alphaSlider.style.marginTop = '5px';
                alphaSlider.addEventListener('input', (e) => {
                    alphaValue.textContent = (e.target.value / 100).toFixed(2);
                    updateShadow();
                });
                alphaRow.appendChild(document.createElement('br'));
                alphaRow.appendChild(alphaSlider);
                shadowDiv.appendChild(alphaRow);
                
                // Shadow distance input
                const distanceRow = document.createElement('div');
                distanceRow.style.marginBottom = '10px';
                const distanceLabel = document.createElement('span');
                distanceLabel.textContent = 'Distance: ';
                distanceLabel.style.fontSize = '14px';
                distanceRow.appendChild(distanceLabel);
                const distanceInput = document.createElement('input');
                distanceInput.type = 'number';
                distanceInput.id = 'shadow-distance';
                distanceInput.value = '4';
                distanceInput.min = '0';
                distanceInput.max = '50';
                distanceInput.style.width = '60px';
                distanceInput.addEventListener('input', updateShadow);
                distanceRow.appendChild(distanceInput);
                shadowDiv.appendChild(distanceRow);
                
                // Shadow angle slider
                const angleRow = document.createElement('div');
                angleRow.style.marginBottom = '10px';
                const angleLabel = document.createElement('span');
                angleLabel.textContent = 'Angle: ';
                angleLabel.style.fontSize = '14px';
                angleRow.appendChild(angleLabel);
                const angleValue = document.createElement('span');
                angleValue.id = 'shadow-angle-value';
                angleValue.textContent = '315°';
                angleValue.style.fontSize = '14px';
                angleValue.style.marginLeft = '5px';
                angleRow.appendChild(angleValue);
                const angleSlider = document.createElement('input');
                angleSlider.type = 'range';
                angleSlider.id = 'shadow-angle';
                angleSlider.min = '0';
                angleSlider.max = '360';
                angleSlider.value = '315';
                angleSlider.style.width = '100%';
                angleSlider.style.marginTop = '5px';
                angleSlider.addEventListener('input', (e) => {
                    angleValue.textContent = e.target.value + '°';
                    updateShadow();
                });
                angleRow.appendChild(document.createElement('br'));
                angleRow.appendChild(angleSlider);
                shadowDiv.appendChild(angleRow);
                
                container.appendChild(shadowDiv);
                
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
                        const segments = widget.segments || 7;
                        header.textContent = `${widgetName} (${segments}-seg)`;
                        widgetDiv.appendChild(header);
                        
                        const controls = document.createElement('div');
                        controls.className = 'widget-controls';
                        
                        const digitInput = document.createElement('input');
                        digitInput.type = 'text';
                        digitInput.id = `digit-${widgetName}`;
                        digitInput.value = segments === 16 ? 'A' : '0';
                        digitInput.maxLength = 1;
                        digitInput.placeholder = segments === 16 ? 'A-Z, 0-9' : '0-9';
                        digitInput.addEventListener('input', (e) => {
                            const value = e.target.value.toUpperCase();
                            // For 7-segment, only allow digits
                            // For 16-segment, allow alphanumeric and some special chars
                            const isValid = segments === 16 ? 
                                (value === '' || /^[A-Z0-9\\s\\-_\\/\\\\=+*()\\[\\]'"]$/.test(value)) :
                                (value === '' || (value >= '0' && value <= '9'));
                            
                            if (isValid) {
                                e.target.value = value;
                                const decimalCheckbox = document.getElementById(`digit-decimal-${widgetName}`);
                                const showDecimal = decimalCheckbox ? decimalCheckbox.checked : false;
                                setDigit(widgetName, value || (segments === 16 ? ' ' : '0'), showDecimal);
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
                                setDigit(widgetName, digitInput.value || (segments === 16 ? ' ' : '0'), e.target.checked);
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
                    } else if (widget.type === 'number') {
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = 'widget';
                        
                        const header = document.createElement('div');
                        header.className = 'widget-header';
                        const digitCount = widget.digits ? widget.digits.length : 0;
                        header.textContent = `${widgetName} (${digitCount} digits)`;
                        widgetDiv.appendChild(header);
                        
                        const controls = document.createElement('div');
                        controls.className = 'widget-controls';
                        controls.style.flexDirection = 'column';
                        controls.style.gap = '8px';
                        
                        // Value input row
                        const valueRow = document.createElement('div');
                        valueRow.style.display = 'flex';
                        valueRow.style.alignItems = 'center';
                        valueRow.style.gap = '5px';
                        
                        const valueLabel = document.createElement('span');
                        valueLabel.textContent = 'Value:';
                        valueRow.appendChild(valueLabel);
                        
                        const valueInput = document.createElement('input');
                        valueInput.type = 'number';
                        valueInput.id = `number-value-${widgetName}`;
                        valueInput.value = '0';
                        valueInput.step = '0.1';
                        valueInput.style.width = '100px';
                        valueInput.addEventListener('input', (e) => {
                            updateNumberWidget(widgetName);
                        });
                        valueRow.appendChild(valueInput);
                        controls.appendChild(valueRow);
                        
                        // Leading zeros row
                        const zerosRow = document.createElement('div');
                        zerosRow.style.display = 'flex';
                        zerosRow.style.alignItems = 'center';
                        
                        const zerosLabel = document.createElement('label');
                        const zerosCheckbox = document.createElement('input');
                        zerosCheckbox.type = 'checkbox';
                        zerosCheckbox.id = `number-zeros-${widgetName}`;
                        zerosCheckbox.addEventListener('change', (e) => {
                            updateNumberWidget(widgetName);
                        });
                        zerosLabel.appendChild(zerosCheckbox);
                        zerosLabel.appendChild(document.createTextNode(' Leading zeros'));
                        zerosRow.appendChild(zerosLabel);
                        controls.appendChild(zerosRow);
                        
                        // Decimal places row
                        const decimalRow = document.createElement('div');
                        decimalRow.style.display = 'flex';
                        decimalRow.style.alignItems = 'center';
                        decimalRow.style.gap = '5px';
                        
                        const decimalLabel = document.createElement('span');
                        decimalLabel.textContent = 'Decimal places:';
                        decimalRow.appendChild(decimalLabel);
                        
                        const decimalInput = document.createElement('input');
                        decimalInput.type = 'number';
                        decimalInput.id = `number-decimal-${widgetName}`;
                        decimalInput.value = '0';
                        decimalInput.min = '0';
                        decimalInput.max = '9';
                        decimalInput.style.width = '50px';
                        decimalInput.addEventListener('input', (e) => {
                            updateNumberWidget(widgetName);
                        });
                        decimalRow.appendChild(decimalInput);
                        controls.appendChild(decimalRow);
                        
                        widgetDiv.appendChild(controls);
                        container.appendChild(widgetDiv);
                    } else if (widget.type === 'string') {
                        const widgetDiv = document.createElement('div');
                        widgetDiv.className = 'widget';
                        
                        const header = document.createElement('div');
                        header.className = 'widget-header';
                        const digitCount = widget.digits ? widget.digits.length : 0;
                        header.textContent = `${widgetName} (${digitCount} chars)`;
                        widgetDiv.appendChild(header);
                        
                        const controls = document.createElement('div');
                        controls.className = 'widget-controls';
                        
                        const stringInput = document.createElement('input');
                        stringInput.type = 'text';
                        stringInput.id = `string-value-${widgetName}`;
                        stringInput.value = '';
                        stringInput.placeholder = 'Enter text...';
                        stringInput.maxLength = digitCount;
                        stringInput.style.width = '150px';
                        stringInput.addEventListener('input', (e) => {
                            setString(widgetName, e.target.value);
                        });
                        controls.appendChild(stringInput);
                        
                        widgetDiv.appendChild(controls);
                        container.appendChild(widgetDiv);
                    }
                });
                
                // Initialize LCD screen iframe reference
                const iframe = document.getElementById('lcd-screen');
                
                function initializeWidgets() {
                    lcdWindow = iframe.contentWindow;
                    
                    // Initialize shadow settings with default values
                    updateShadow();
                    
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
                        } else if (widget.type === 'number') {
                            updateNumberWidget(widgetName);
                        } else if (widget.type === 'string') {
                            const stringInput = document.getElementById(`string-value-${widgetName}`);
                            const text = stringInput ? stringInput.value : '';
                            setString(widgetName, text);
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
        
        // Set number value in LCD screen
        function setNumberValue(name, value, addLeadingZeros, decimalPlaces) {
            if (lcdWindow && lcdWindow.SetNumberValue) {
                lcdWindow.SetNumberValue(name, value, addLeadingZeros, decimalPlaces);
            }
        }
        
        // Set string value in LCD screen
        function setString(name, text) {
            if (lcdWindow && lcdWindow.SetString) {
                lcdWindow.SetString(name, text);
            }
        }
        
        // Update number widget with current control values
        function updateNumberWidget(name) {
            const valueInput = document.getElementById(`number-value-${name}`);
            const zerosCheckbox = document.getElementById(`number-zeros-${name}`);
            const decimalInput = document.getElementById(`number-decimal-${name}`);
            
            if (valueInput) {
                const value = parseFloat(valueInput.value) || 0;
                const addLeadingZeros = zerosCheckbox ? zerosCheckbox.checked : false;
                const decimalPlaces = decimalInput ? parseInt(decimalInput.value) || 0 : 0;
                setNumberValue(name, value, addLeadingZeros, decimalPlaces);
            }
        }
        
        // Update shadow settings in LCD screen
        function updateShadow() {
            const visibleCheckbox = document.getElementById('shadow-visible');
            const alphaSlider = document.getElementById('shadow-alpha');
            const distanceInput = document.getElementById('shadow-distance');
            const angleSlider = document.getElementById('shadow-angle');
            
            if (lcdWindow && lcdWindow.SetShadow) {
                const isVisible = visibleCheckbox ? visibleCheckbox.checked : true;
                const alphaValue = alphaSlider ? parseFloat(alphaSlider.value) / 100 : 0.25;
                const offsetDistance = distanceInput ? parseFloat(distanceInput.value) : 4;
                const angle = angleSlider ? parseFloat(angleSlider.value) : 315;
                
                lcdWindow.SetShadow(isVisible, alphaValue, offsetDistance, angle);
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
    widgets = {}  # Dictionary to store toggle, digit, range, and number information
    base_name = input_path.stem
    number_widgets_digits = {}  # Track digits for Number widgets: {number_widget_name: [digit_info_list]}
    
    for idx, (layer, folder_path, toggle_name, widget_info, number_widget_info) in enumerate(all_layers):
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
            
            # Handle Number/String widget digits
            if number_widget_info:
                parent_widget_type, number_widget_name, digit_type, digit_name = number_widget_info
                
                # Initialize Number or String widget if not exists
                if number_widget_name not in widgets:
                    widget_type = 'number' if parent_widget_type == 'N' else 'string'
                    widgets[number_widget_name] = {
                        'type': widget_type,
                        'digits': []
                    }
                    number_widgets_digits[number_widget_name] = []
                
                # Check if this digit is already tracked
                digit_found = False
                for digit_info in number_widgets_digits[number_widget_name]:
                    if digit_info['name'] == digit_name:
                        # Add layer to existing digit
                        digit_info['layers'].append(layer_info['filename'])
                        digit_found = True
                        break
                
                if not digit_found:
                    # New digit for this Number widget
                    has_decimal = digit_type.endswith('p')
                    digit_info = {
                        'name': digit_name,
                        'has_decimal': has_decimal,
                        'layers': [layer_info['filename']]
                    }
                    number_widgets_digits[number_widget_name].append(digit_info)
            # Collect digit and range widget information (standalone widgets, not part of Number)
            elif widget_info:
                widget_type, widget_name = widget_info
                if widget_name not in widgets:
                    if widget_type.startswith('D:'):
                        # Digit widget
                        has_decimal = widget_type.endswith('p')
                        # Extract segment count from digit type (e.g., "D:7" or "D:16")
                        digit_type_clean = widget_type.rstrip('p')  # Remove 'p' if present
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
                    elif widget_type == 'R':
                        # Range widget
                        widgets[widget_name] = {
                            'type': 'range',
                            'layers': []
                        }
                    elif widget_type == 'N':
                        # Number widget (initialized above when we see child digits)
                        # Create it here if no child digits exist yet
                        if widget_name not in widgets:
                            widgets[widget_name] = {
                                'type': 'number',
                                'digits': []
                            }
                            number_widgets_digits[widget_name] = []
                    elif widget_type == 'S':
                        # String widget (similar to Number but for alphanumeric text)
                        # Create it here if no child digits exist yet
                        if widget_name not in widgets:
                            widgets[widget_name] = {
                                'type': 'string',
                                'digits': []
                            }
                            number_widgets_digits[widget_name] = []
                
                # Only add layers for non-Number and non-String widgets (these meta-widgets use their child digits)
                if widget_type not in ('N', 'S'):
                    widgets[widget_name]['layers'].append(layer_info['filename'])
    
    # Finalize Number widgets: reverse digit layers and add to widgets
    for number_widget_name, digit_list in number_widgets_digits.items():
        # Reverse each digit's layers (PSD stores bottom-to-top)
        for digit_info in digit_list:
            digit_info['layers'].reverse()
        # Store the digits in the widget
        widgets[number_widget_name]['digits'] = digit_list
    
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
        # Reverse layer order for digit widgets
        # PSD files store layers bottom-to-top, but users arrange them top-to-bottom in UI
        for widget_name, widget_data in widgets.items():
            if widget_data['type'] == 'digit':
                widget_data['layers'].reverse()
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
