# lcd-compositor

=^..^=

A Python tool to extract layers from Adobe PSB/PSD files into individual images with position metadata.

## Features

- Extract all layers from PSB/PSD files
- Automatically crop each layer to its content bounds
- Generate a YAML file with layer positions for layout recreation
- Support for nested layer groups
- Easy setup with virtual environment and dependency checking

## Requirements

- Python 3.8 or higher
- pip (Python package manager)

## Installation

No manual installation needed! The `start.sh` script will automatically:
1. Create a Python virtual environment
2. Install all required dependencies
3. Run the extraction tool

## Usage

### Basic Usage

```bash
./start.sh input.psb
```

This will create a folder named `input_layers/` containing:
- Individual PNG images for each layer (cropped to content, named based on folder structure)
- `input.yml` file with layer positions and metadata
- Folders and layers starting with # are ignored

### Specify Output Directory

```bash
./start.sh input.psb -o custom_output_folder
```

### Command Line Options

```bash
./start.sh <input_file> [-o OUTPUT_DIR]

Arguments:
  input_file           Path to the PSB or PSD file to process

Options:
  -o, --output OUTPUT_DIR
                       Output directory for extracted layers
                       (default: <input_file>_layers)
```

## Output Format

### Directory Structure

```
input_layers/
├── Background.png
├── Smo--Mo--1.png
├── Smo--Mo--2.png
├── input.yml
├── lcd-screen.html
└── index.html
```

Filenames are generated based on the folder structure in the PSD file:
- Folder names are concatenated with layer names using `--` (double minus)
- Example: A layer "1" inside folders "Smo" > "Mo" becomes `Smo--Mo--1.png`
- Folders and layers starting with `#` are ignored
- Folders and layers starting with `[T]` are identified as toggles (widgets) that can be controlled

### YAML File Format

The generated YAML file contains:
- Source file information
- Document dimensions
- Layer details with filenames and positions
- Widgets section mapping toggle names to their associated layer files

Example:

```yaml
source_file: input.psb
document_width: 1920
document_height: 1080
layers:
  - filename: Background.png
    name: Background
    original_name: Background
    original_folder_path: []
    x: 0
    y: 0
    width: 1920
    height: 1080
  - filename: UI--Layer_1.png
    name: Layer 1
    original_name: Layer 1
    original_folder_path: [UI]
    x: 100
    y: 150
    width: 500
    height: 300
  - filename: LED_Indicator.png
    name: LED_Indicator
    original_name: '[T]LED_Indicator'
    original_folder_path: []
    x: 1700
    y: 50
    width: 100
    height: 100
widgets:
  LED_Indicator:
  - LED_Indicator.png
```

The `x` and `y` coordinates indicate where the top-left corner of each layer image should be placed to recreate the original layout.

### Widgets (Toggles)

Layers and folders can be marked as toggles by prefixing their names with `[T]`:

- **Layer Toggle**: A layer named `[T]LED` becomes a toggle widget named "LED" that controls just that layer
- **Folder Toggle**: A folder named `[T]Controls` becomes a toggle widget named "Controls" that controls all layers within that folder (recursively)

The widgets section in the YAML file maps each toggle name to the list of PNG files it controls.

### HTML Interface

Two HTML files are automatically generated:

#### `index.html` - Main Interface

The main interface features a split-panel layout:

- **Left Panel**: Widget controls with toggles for each `[T]`-prefixed layer or folder
- **Right Panel**: The LCD screen display showing all layers

Features:
- **Interactive Toggles**: Control visibility of widgets by toggling them on/off
- **Real-time Updates**: Changes are immediately reflected in the LCD screen
- **Responsive Layout**: The LCD screen automatically scales to fit the available space

#### `lcd-screen.html` - LCD Screen Display

The LCD screen display shows all layers positioned exactly as they appear in the original document:

- **Auto-scaling**: Automatically scales to fit the container while maintaining aspect ratio
- **Transparency Support**: Images are displayed with proper transparency handling
- **Widget Control API**: Exposes a `SetToggle(name, value)` function for programmatic control
- **Self-Contained**: Can be embedded in other pages or used standalone

To use:
1. Open `index.html` in any modern web browser
2. Use the toggle switches in the left panel to control widget visibility
3. All changes are immediately reflected in the LCD screen on the right

## Development

### Manual Setup (Optional)

If you prefer to set up manually:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python extract_layers.py input.psb
```

## Dependencies

- `psd-tools` - For reading PSB/PSD files
- `Pillow` - For image manipulation
- `PyYAML` - For YAML file generation

## License

This project is open source.