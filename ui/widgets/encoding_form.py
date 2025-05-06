#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Encoding Form Widget
Implements the form for configuring video encoding settings
"""

import os
import logging
from typing import Dict, List, Optional, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QFileDialog, QMessageBox, 
    QSpinBox, QDoubleSpinBox, QLineEdit, QGroupBox,
    QFormLayout, QCheckBox, QRadioButton, QButtonGroup,
    QTextEdit  # Added missing QTextEdit import
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal

from config.settings import Settings
from core.prefix_manager import PrefixManager

logger = logging.getLogger('video_encoder.ui.widgets.encoding_form')


class EncodingForm(QWidget):
    """Form for configuring video encoding settings"""
    
    def __init__(self, settings: Settings, prefix_manager: PrefixManager):
        super().__init__()
        self.settings = settings
        self.prefix_manager = prefix_manager
        
        # Initialize UI
        self.init_ui()
        
        # Load default values from settings
        self.load_defaults()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        main_layout = QHBoxLayout(self)  # Changed to horizontal layout to add help section
        
        # Left side - form content
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        
        # Quality settings group
        quality_group = QGroupBox("Quality Settings")
        quality_layout = QFormLayout(quality_group)
        
        # Quality preset
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "Very Low", "Low", "Medium", "High", "Very High",
            "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"
        ])
        quality_layout.addRow("Quality Preset:", self.quality_combo)
        
        # Output format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mkv", "webm", "mov"])
        quality_layout.addRow("Output Format:", self.format_combo)
        
        # Target size options
        self.target_size_check = QCheckBox("Specify Target Size")
        self.target_size_check.stateChanged.connect(self.toggle_target_size)
        quality_layout.addRow("", self.target_size_check)
        
        # Target size spinner
        self.target_size_spin = QSpinBox()
        self.target_size_spin.setRange(1, 10000)
        self.target_size_spin.setSuffix(" MB")
        self.target_size_spin.setValue(100)
        self.target_size_spin.setEnabled(False)
        quality_layout.addRow("Target Size:", self.target_size_spin)
        
        form_layout.addWidget(quality_group)
        
        # Input mode group
        input_group = QGroupBox("Input Mode")
        input_layout = QVBoxLayout(input_group)
        
        # Input mode selection
        self.input_mode_radio_group = QButtonGroup(self)
        self.files_radio = QRadioButton("Individual Files")
        self.directory_radio = QRadioButton("Directory")
        self.input_mode_radio_group.addButton(self.files_radio)
        self.input_mode_radio_group.addButton(self.directory_radio)
        self.files_radio.setChecked(True)
        
        # Connect signals
        self.files_radio.toggled.connect(self.toggle_input_mode)
        self.directory_radio.toggled.connect(self.toggle_input_mode)
        
        input_mode_layout = QHBoxLayout()
        input_mode_layout.addWidget(self.files_radio)
        input_mode_layout.addWidget(self.directory_radio)
        input_layout.addLayout(input_mode_layout)
        
        # Directory options
        self.directory_options = QWidget()
        directory_options_layout = QFormLayout(self.directory_options)
        
        # Directory path
        directory_path_layout = QHBoxLayout()
        self.directory_path_edit = QLineEdit()
        self.directory_path_edit.setReadOnly(True)
        directory_path_layout.addWidget(self.directory_path_edit)
        
        self.browse_directory_button = QPushButton("Browse...")
        self.browse_directory_button.clicked.connect(self.browse_input_directory)
        directory_path_layout.addWidget(self.browse_directory_button)
        
        directory_options_layout.addRow("Directory:", directory_path_layout)
        
        # Recursive option
        self.recursive_check = QCheckBox("Include Subdirectories")
        directory_options_layout.addRow("", self.recursive_check)
        
        # Add to layout
        input_layout.addWidget(self.directory_options)
        self.directory_options.setVisible(False)
        
        form_layout.addWidget(input_group)
        
        # Output settings group
        output_group = QGroupBox("Output Settings")
        output_layout = QFormLayout(output_group)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.browse_button)
        
        output_layout.addRow("Output Directory:", output_dir_layout)
        
        # Replace prefix combo with direct input field
        self.custom_prefix_edit = QLineEdit()
        self.custom_prefix_edit.setPlaceholderText("Enter filename template e.g. {filename}_{quality}")
        self.custom_prefix_edit.textChanged.connect(self.update_prefix_preview)
        output_layout.addRow("Filename Template:", self.custom_prefix_edit)
        
        # Preview of prefix template
        self.prefix_preview = QLabel("Preview: output.mp4")
        output_layout.addRow("", self.prefix_preview)
        
        # Connect signals for preview update
        self.format_combo.currentIndexChanged.connect(self.update_prefix_preview)
        
        form_layout.addWidget(output_group)
        
        # Add stretch to push everything to the top
        form_layout.addStretch()
        
        # Add form container to main layout
        main_layout.addWidget(form_container, 2)  # 2:1 ratio with help section
        
        # Right side - help section
        help_group = QGroupBox("Help")
        help_layout = QVBoxLayout(help_group)
        
        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setMinimumWidth(250)
        self.help_text.setStyleSheet("background-color: #f5f5f5;")
        help_layout.addWidget(self.help_text)
        
        # Add help group to main layout
        main_layout.addWidget(help_group, 1)  # 2:1 ratio with form
        
        # Connect signals for help text updates
        self.quality_combo.currentIndexChanged.connect(self.update_help_text)
        self.format_combo.currentIndexChanged.connect(self.update_help_text)
        self.target_size_check.stateChanged.connect(self.update_help_text)
        self.files_radio.toggled.connect(self.update_help_text)
        self.directory_radio.toggled.connect(self.update_help_text)
        self.custom_prefix_edit.textChanged.connect(self.update_help_text)
        
        # Initial help text
        self.update_help_text()
    
    def toggle_input_mode(self):
        """Toggle between file and directory input modes"""
        try:
            is_directory_mode = self.directory_radio.isChecked()
            self.directory_options.setVisible(is_directory_mode)
            
            # If switching to directory mode and we have a path, trigger scan
            if is_directory_mode and self.directory_path_edit.text():
                parent = self.window()
                if hasattr(parent, 'add_directory'):
                    parent.add_directory()
        except Exception as e:
            logger.error(f"Error toggling input mode: {e}")
    
    def browse_input_directory(self):
        """Open directory dialog to select input directory"""
        try:
            current_dir = self.directory_path_edit.text()
            if not current_dir or not os.path.isdir(current_dir):
                current_dir = os.path.expanduser('~')
            
            directory = QFileDialog.getExistingDirectory(
                self,
                "Select Input Directory",
                current_dir,
                QFileDialog.ShowDirsOnly
            )
            
            if directory:
                self.directory_path_edit.setText(directory)
                
                # Trigger directory scan if parent window exists
                parent = self.window()
                if hasattr(parent, 'add_directory'):
                    parent.add_directory()
        except Exception as e:
            logger.error(f"Error browsing directory: {e}")
    
    def load_defaults(self):
        """Load default values from settings"""
        # Set quality preset
        quality_map = {
            'very_low': 0,
            'low': 1,
            'medium': 2,
            'high': 3,
            'very_high': 4
        }
        default_quality = self.settings.get('default_quality', 'medium')
        self.quality_combo.setCurrentIndex(quality_map.get(default_quality, 2))
        
        # Set output format
        default_format = self.settings.get('default_format', 'mp4')
        index = self.format_combo.findText(default_format)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)
        
        # Set output directory
        output_dir = self.settings.get_output_directory()
        self.output_dir_edit.setText(output_dir)
        
        # Set prefix template
        default_template = self.settings.get('default_prefix_template', 'simple')
        templates = self.prefix_manager.get_all_templates()
        template_text = templates.get(default_template, '{filename}')
        self.custom_prefix_edit.setText(template_text)
        
        # Update preview
        self.update_prefix_preview()
    
    def update_prefix_templates(self):
        """Update the prefix template dropdown with available templates"""
        # This method is no longer needed since we removed the combo box
        # But we'll keep a minimal version for compatibility
        templates = self.prefix_manager.get_all_templates()
        default_template = self.settings.get('default_prefix_template', 'simple')
        template_text = templates.get(default_template, '{filename}')
        self.custom_prefix_edit.setText(template_text)
    
    def toggle_custom_prefix(self):
        """This method is no longer needed but kept for compatibility"""
        pass
    
    def show_placeholder_help(self):
        """Show help for placeholders in the help text area instead of a dialog"""
        self.update_help_text(show_placeholders=True)
    
    def update_help_text(self, show_placeholders=False):
        """Update the help text based on current selection"""
        help_html = "<html><body style='font-family: Arial, sans-serif;'>"
        
        # If showing placeholders specifically
        if show_placeholders:
            help_html += "<h3>Available Template Placeholders</h3>"
            help_html += "<p>You can use these placeholders in your filename template:</p>"
            help_html += "<ul>"
            
            placeholders = self.prefix_manager.get_available_placeholders()
            for placeholder, description in placeholders.items():
                help_html += f"<li><b>{placeholder}</b>: {description}</li>"
            
            help_html += "</ul>"
            help_html += "<p>Example: <code>{filename}_{quality}_{resolution}</code></p>"
        
        # Otherwise show context-sensitive help
        else:
            # Get current context
            current_section = ""
            
            # Check which section is being interacted with
            if self.sender() == self.quality_combo or self.sender() == self.format_combo or self.sender() == self.target_size_check:
                current_section = "quality"
            elif self.sender() == self.files_radio or self.sender() == self.directory_radio:
                current_section = "input"
            elif self.sender() == self.custom_prefix_edit:
                current_section = "template"
            else:
                # Default section on startup
                current_section = "general"
            
            # Generate help content based on context
            if current_section == "quality":
                help_html += "<h3>Quality Settings</h3>"
                help_html += "<p><b>Quality Preset:</b> Determines the compression level and visual quality.</p>"
                help_html += "<ul>"
                help_html += "<li><b>Very Low to Very High:</b> General quality presets with varying compression levels</li>"
                help_html += "<li><b>144p to 2160p:</b> Resolution-specific presets</li>"
                help_html += "</ul>"
                help_html += "<p><b>Output Format:</b> The container format for your video.</p>"
                help_html += "<ul>"
                help_html += "<li><b>MP4:</b> Best compatibility with most devices</li>"
                help_html += "<li><b>MKV:</b> Better for storing multiple audio tracks and subtitles</li>"
                help_html += "<li><b>WebM:</b> Optimized for web playback</li>"
                help_html += "<li><b>MOV:</b> Good compatibility with Apple devices</li>"
                help_html += "</ul>"
                help_html += "<p><b>Target Size:</b> Enable to specify a target file size in MB.</p>"
            
            elif current_section == "input":
                help_html += "<h3>Input Mode</h3>"
                help_html += "<p>Choose how you want to select files for conversion:</p>"
                help_html += "<ul>"
                help_html += "<li><b>Individual Files:</b> Select specific video files to convert</li>"
                help_html += "<li><b>Directory:</b> Convert all supported videos in a directory</li>"
                help_html += "</ul>"
                help_html += "<p>When using Directory mode, you can choose to include subdirectories in the scan.</p>"
            
            elif current_section == "template":
                help_html += "<h3>Filename Template</h3>"
                help_html += "<p>Customize how output files will be named using placeholders.</p>"
                help_html += "<p>Common placeholders:</p>"
                help_html += "<ul>"
                help_html += "<li><b>{filename}</b>: Original filename without extension</li>"
                help_html += "<li><b>{quality}</b>: Selected quality preset</li>"
                help_html += "<li><b>{resolution}</b>: Video resolution (WIDTHxHEIGHT)</li>"
                help_html += "<li><b>{date}</b>: Current date (YYYY-MM-DD)</li>"
                help_html += "</ul>"
                help_html += "<p>Click in this help section to see all available placeholders.</p>"
            
            else:  # general
                help_html += "<h3>Bulk Video Converter</h3>"
                help_html += "<p>This application helps you convert multiple video files with consistent settings.</p>"
                help_html += "<p><b>Basic workflow:</b></p>"
                help_html += "<ol>"
                help_html += "<li>Add video files using the 'Add Files' button</li>"
                help_html += "<li>Configure quality settings and output format</li>"
                help_html += "<li>Set your output directory</li>"
                help_html += "<li>Customize the filename template if needed</li>"
                help_html += "<li>Click 'Start Encoding' to begin conversion</li>"
                help_html += "</ol>"
                help_html += "<p>Click on different parts of the form to see specific help.</p>"
            
        help_html += "</body></html>"
        self.help_text.setHtml(help_html)
    
    def update_prefix_preview(self):
        """Update the preview of the prefix template"""
        try:
            # Get current template
            template = self.custom_prefix_edit.text()
            
            # Get current format
            output_format = self.format_combo.currentText()
            
            # Create a preview with example values
            preview = template
            
            # Replace placeholders with example values
            example_values = {
                '{filename}': 'video',
                '{ext}': 'mp4',
                '{date}': '2025-05-06',
                '{time}': '18-35-34',
                '{datetime}': '2025-05-06_18-35-34',
                '{create_date}': '2025-05-01',
                '{size}': '100',
                '{resolution}': '1920x1080',
                '{codec}': 'h264',
                '{duration}': '120.5',
                '{counter}': '1',
                '{quality}': self.quality_combo.currentText(),
                '{source}': 'videos',
                '{source_full}': 'C:\\videos'
            }
            
            for placeholder, value in example_values.items():
                preview = preview.replace(placeholder, value)
            
            # Add extension
            preview = f"{preview}.{output_format}"
            
            # Update preview label
            self.prefix_preview.setText(f"Preview: {preview}")
        except Exception as e:
            logger.error(f"Error updating prefix preview: {e}")
            self.prefix_preview.setText("Preview: output.mp4")
    
    def toggle_target_size(self, state):
        """Toggle target size spinner based on checkbox state"""
        self.target_size_spin.setEnabled(state == Qt.Checked)
    
    def browse_output_dir(self):
        """Open directory dialog to select output directory"""
        current_dir = self.output_dir_edit.text()
        if not current_dir or not os.path.isdir(current_dir):
            current_dir = os.path.expanduser('~')
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir,
            QFileDialog.ShowDirsOnly
        )
        
        if directory:
            self.output_dir_edit.setText(directory)
            # Save to settings
            self.settings.set('output_directory', directory)
            self.settings.save_settings()
    
    def get_settings(self) -> Tuple[str, str, Optional[int], str, str, Dict]:
        """Get the current encoding settings
        
        Returns:
            Tuple of (quality, output_format, target_size, output_dir, prefix_template, input_options)
        """
        # Quality
        quality = self.get_quality_value()
        
        # Output format
        output_format = self.format_combo.currentText()
        
        # Target size
        target_size = None
        if self.target_size_check.isChecked():
            target_size = self.target_size_spin.value()
        
        # Output directory
        output_dir = self.output_dir_edit.text()
        
        # Prefix template - now directly from the edit field
        prefix_template = self.custom_prefix_edit.text()
        
        # Input options
        input_options = {
            'mode': 'directory' if self.directory_radio.isChecked() else 'files',
            'directory': self.directory_path_edit.text() if self.directory_radio.isChecked() else '',
            'recursive': self.recursive_check.isChecked()
        }
        
        return quality, output_format, target_size, output_dir, prefix_template, input_options
    
    def get_quality_value(self) -> str:
        """Get the current quality value as a string"""
        quality_text = self.quality_combo.currentText().lower().replace(' ', '_')
        
        # Handle resolution presets
        if quality_text in ['144p', '240p', '360p', '480p', '720p', '1080p', '1440p', '2160p']:
            return quality_text
            
        # Handle named presets
        quality_map = {
            'very_low': 'very_low',
            'low': 'low',
            'medium': 'medium',
            'high': 'high',
            'very_high': 'very_high'
        }
        return quality_map.get(quality_text, 'medium')