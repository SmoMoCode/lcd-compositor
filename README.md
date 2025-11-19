# lcd-compositor

=^..^=

A Python tool to extract layers from Adobe PSB/PSD files into individual images with position metadata.

## Features

- Extract all layers from PSB/PSD files
- Automatically crop each layer to its content bounds
- Generate a YAML file with layer positions for layout recreation
- Support for nested layer groups
- Interactive HTML interface with widget controls
- Support for Toggle, Digit (7-segment), and Range widgets
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
└── input_preview.html
```

Filenames are generated based on the folder structure in the PSD file:
- Folder names are concatenated with layer names using `--` (double minus)
- Example: A layer "1" inside folders "Smo" > "Mo" becomes `Smo--Mo--1.png`
- Folders and layers starting with `#` are ignored

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
  - filename: Background.png
    name: Background
    x: 0
    y: 0
    width: 1920
    height: 1080
  - filename: UI--Layer_1.png
    name: Layer 1
    x: 100
    y: 150
    width: 500
    height: 300
```

The `x` and `y` coordinates indicate where the top-left corner of each layer image should be placed to recreate the original layout.

### HTML Interface

Two HTML files are automatically generated for interactive visualization:

1. **`index.html`** - Main interface with:
   - **Controls Panel**: Interactive widgets to control layer visibility and state
   - **LCD Screen**: Real-time preview of the composed layers
   - **Widget Support**: Toggle, Digit (7-segment), Number, and Range widgets

2. **`lcd-screen.html`** - Embedded LCD screen display (loaded by index.html)

To use the interface:
1. Open `index.html` in any modern web browser
2. Use the controls panel on the left to interact with widgets
3. View real-time updates in the LCD screen on the right

## Widget Types

The tool supports special folder naming conventions to create interactive widgets:

### Toggle Widgets `[T]`

Folders or layers prefixed with `[T]` create a toggle widget:
- Example: `[T]StatusLight` creates a checkbox control
- All child layers are shown/hidden together when toggled

### Digit Widgets `[D:7]`, `[D:7p]`, `[D:16]`, or `[D:16p]`

Folders prefixed with `[D:7]` create a 7-segment digit display:
- `[D:7]Speed` - Standard 7-segment digit (0-9)
- `[D:7p]Temp` - 7-segment digit with decimal point
- Layers must be in this order:
  1. Top segment (A)
  2. Top-left segment (F)
  3. Top-right segment (B)
  4. Middle segment (G)
  5. Bottom-left segment (E)
  6. Bottom-right segment (C)
  7. Bottom segment (D)
  8. Decimal point (optional, for `[D:7p]`)
- Creates a text input (0-9) and optional decimal checkbox in the controls

Folders prefixed with `[D:16]` create a 16-segment alphanumeric display:
- `[D:16]Display` - 16-segment digit (A-Z, 0-9, and special characters)
- `[D:16p]Display` - 16-segment digit with decimal point
- Layers must be in this order (from top to bottom in PSD):
  1. a1 (top-left of top bar)
  2. a2 (top-right of top bar)
  3. f (left upper vertical)
  4. h (top-left diagonal)
  5. i (top center vertical)
  6. j (top-right diagonal)
  7. b (right upper vertical)
  8. g1 (middle-left horizontal)
  9. g2 (middle-right horizontal)
  10. e (left lower vertical)
  11. k (bottom-left diagonal)
  12. l (bottom center vertical)
  13. m (bottom-right diagonal)
  14. c (right lower vertical)
  15. d1 (bottom-left of bottom bar)
  16. d2 (bottom-right of bottom bar)
  17. Decimal point (optional, for `[D:16p]`)
- Supports alphanumeric characters (A-Z, 0-9) and common punctuation
- Creates a text input and optional decimal checkbox in the controls

### Number Widgets `[N]`

Folders prefixed with `[N]` create a multi-digit number display (a meta-widget using digit widgets):
- Example: `[N]Speed` with child folders `[D:7]`, `[D:7p]`, `[D:7]`
- Child digit folders can have optional names: `[D:7]hundreds`, `[D:7p]tens`, `[D:7]ones`
- Displays floating-point numbers across multiple digits
- Automatically handles decimal point placement based on which digit has `[D:7p]`
- Controls in index.html:
  - **Value**: Number input for the value to display
  - **Leading zeros**: Checkbox to pad with zeros (e.g., 12.3 → 012.3)
  - **Decimal places**: Number of digits to show after decimal point (e.g., 12 → 12.0 with 1 decimal place)
- Example configurations:
  - Digits `[D:7]`, `[D:7p]`, `[D:7]` can display: 123, 12.3, 1.23, 0.1
  - With leading zeros: 123, 012.3, 001.2
  - With decimal places=1: 120.0, 012.3, 001.2

### String Widgets `[S]`

Folders prefixed with `[S]` create a multi-character text display using 16-segment digits:
- Example: `[S]Message` with child folders `[D:16p]`, `[D:16p]`, `[D:16]`
- Similar to Number widgets but for alphanumeric text instead of numeric values
- Uses 16-segment digits for displaying letters, numbers, and symbols
- Child digit folders should use `[D:16]` or `[D:16p]`
- Period (`.`) characters in the input text will merge with the preceding digit's decimal point (if available)
- Controls in index.html:
  - **Text input**: String field for entering alphanumeric text
- Example: A String widget with 5 digits can display "HELLO", "12.34", "AB-CD", etc.

### Range Widgets `[R]`

Folders prefixed with `[R]` create a range widget:
- Example: `[R]powerLevel` with 10 child layers
- Creates START and END number inputs
- Shows layers within the specified range
- If START=0 and END=0, all layers are hidden
- If START=1 and END=10, all layers are shown
- If START=9 and END=10, only the last two layers are shown
- Widget label shows total count: "powerLevel (10)"

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