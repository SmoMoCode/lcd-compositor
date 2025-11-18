# Quick Start Guide

=^..^=

## Installation

No installation needed! Just clone and run:

```bash
git clone https://github.com/SmoMoCode/lcd-compositor.git
cd lcd-compositor
./start.sh your_file.psb
```

## Basic Usage

### Extract layers from a PSB/PSD file:
```bash
./start.sh input.psb
```

This creates:
- `input_layers/` folder with all layer images
- `input_layers/input.yml` with position data

### Specify custom output folder:
```bash
./start.sh input.psb -o my_output_folder
```

## What You Get

### Layer Images
Each layer is saved as a PNG file, cropped to its content:
- `input_layer_000_Background.png`
- `input_layer_001_Layer_Name.png`
- `input_layer_002_Another_Layer.png`
- etc.

### YAML Metadata
The `.yml` file contains position data:
```yaml
layers:
  - filename: input_layer_000_Background.png
    name: Background
    x: 0      # X position (left)
    y: 0      # Y position (top)
    width: 1920
    height: 1080
```

Use the `x` and `y` coordinates to position each layer image to recreate the original layout.

## Requirements

- Python 3.8 or higher
- That's it! Dependencies are auto-installed.

## Troubleshooting

### "Python 3 is not installed"
Install Python from https://www.python.org/downloads/

### Permission denied on start.sh
Make it executable:
```bash
chmod +x start.sh
```

### Input file not found
Use absolute path or ensure file exists:
```bash
./start.sh /full/path/to/file.psb
```

## Features

- ✅ Supports PSB and PSD files
- ✅ Handles nested layer groups
- ✅ Auto-crops to content
- ✅ Preserves layer names
- ✅ Records exact positions
- ✅ No manual setup required

Happy extracting! 🎨
