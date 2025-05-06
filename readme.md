


          
# Bulk Video Converter

A powerful desktop application for batch converting, compressing, and optimizing video files with a user-friendly interface.

![Bulk Video Converter](https://raw.githubusercontent.com/oxcakmak/Python-Bulk-Video-Converter/refs/heads/main/screenshot.jpg)

## Features

- **Batch Processing**: Convert multiple video files simultaneously
- **Quality Presets**: Choose from various quality settings (Very Low to Very High)
- **Resolution Presets**: Easily convert to standard resolutions (144p to 2160p)
- **Target Size**: Specify a target file size for your output videos
- **Multiple Output Formats**: Support for MP4, MKV, WebM, and MOV formats
- **Directory Mode**: Process entire folders of videos at once
- **Custom Filename Templates**: Create custom naming patterns for output files
- **Drag and Drop**: Easily add files via drag and drop interface
- **Progress Tracking**: Monitor conversion progress in real-time

## Support Me

This software is developed during my free time and I will be glad if somebody will support me.

Everyone's time should be valuable, so please consider donating.

[https://buymeacoffee.com/oxcakmak](https://buymeacoffee.com/oxcakmak)

## Installation

### Prerequisites

- Python 3.6 or higher
- FFmpeg installed and available in your system PATH

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/bulk_converter.git
   cd bulk_converter
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

## Dependencies

The application requires the following Python packages:
- PyQt5 >= 5.15.0 - GUI Framework
- ffmpeg-python >= 0.2.0 - Video Processing
- Pillow >= 8.0.0 - Image Processing
- pathlib >= 1.0.1 - Path manipulation
- python-i18n >= 0.3.9 - Internationalization

## Usage

### Basic Workflow

1. **Add Files**: Click "Add Files" or drag and drop video files into the application
2. **Configure Settings**: 
   - Select quality preset
   - Choose output format
   - Set target size (optional)
   - Configure output directory
   - Select filename template
3. **Start Encoding**: Click "Start Encoding" to begin the conversion process

### Advanced Options

#### Quality Settings

Choose from predefined quality presets:
- Very Low, Low, Medium, High, Very High
- Resolution-based: 144p, 240p, 360p, 480p, 720p, 1080p, 1440p, 2160p

#### Input Modes

- **Individual Files**: Process selected video files
- **Directory Mode**: Process all supported videos in a directory
  - Option to include subdirectories

#### Output Settings

- **Output Directory**: Choose where converted files will be saved
- **Filename Templates**: Customize output filenames using placeholders:
  - `{filename}` - Original filename without extension
  - `{quality}` - Selected quality preset
  - `{date}` - Current date (YYYY-MM-DD)
  - `{datetime}` - Current date and time
  - `{resolution}` - Video resolution (WIDTHxHEIGHT)
  - `{codec}` - Original video codec
  - And many more...

## Supported Formats

### Input Formats
MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V, MPG, MPEG, 3GP, 3G2, MXF, TS

### Output Formats
MP4, MKV, WebM, MOV

## Customization

### Themes
The application supports multiple themes that can be changed in the Settings menu.

### Languages
Multiple language support is available through the Settings menu.

## Building Standalone Executables

You can create standalone executables using PyInstaller:

```bash
pyinstaller --onefile --windowed app.py
```

## Project Structure

```
bulk_converter/
├── app.py                  # Main application entry point
├── config/                 # Configuration files
│   ├── languages/          # Translation files
│   └── settings.py         # Settings management
├── core/                   # Core functionality
│   ├── encoder.py          # Video encoding logic
│   ├── file_manager.py     # File operations
│   └── prefix_manager.py   # Filename template handling
├── ui/                     # User interface
│   ├── main_window.py      # Main application window
│   └── widgets/            # UI components
│       ├── encoding_form.py    # Encoding settings form
│       ├── file_list.py        # File list widget
│       └── settings_dialog.py  # Settings dialog
└── utils/                  # Utility functions
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FFmpeg for providing the powerful video processing capabilities
- PyQt5 for the GUI framework
- All contributors who have helped improve this project

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Ensure FFmpeg is installed and available in your system PATH
2. **Import errors**: Make sure all dependencies are installed with `pip install -r requirements.txt`
3. **Unsupported format**: Check if your input file format is in the supported formats list

For more help, please open an issue on the GitHub repository.
