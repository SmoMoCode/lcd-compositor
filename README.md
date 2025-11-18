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
- Individual PNG images for each layer (cropped to content)
- `input.yml` file with layer positions and metadata

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
├── input_layer_000_Background.png
├── input_layer_001_Layer_1.png
├── input_layer_002_Text_Layer.png
└── input.yml
```

### YAML File Format

The generated YAML file contains:
- Source file information
- Document dimensions
- Layer details with filenames and positions

Example:

```yaml
source_file: input.psb
document_width: 1920
document_height: 1080
layers:
  - filename: input_layer_000_Background.png
    name: Background
    x: 0
    y: 0
    width: 1920
    height: 1080
  - filename: input_layer_001_Layer_1.png
    name: Layer 1
    x: 100
    y: 150
    width: 500
    height: 300
```

The `x` and `y` coordinates indicate where the top-left corner of each layer image should be placed to recreate the original layout.

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