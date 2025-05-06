#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings Dialog
Implements a dialog for configuring application settings
"""

import os
import logging
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QTabWidget, QWidget,
    QFormLayout, QCheckBox, QLineEdit, QSpinBox,
    QDialogButtonBox, QGroupBox, QFileDialog,
    QMessageBox, QKeySequenceEdit
)
from PyQt5.QtCore import Qt, QSettings, QSize
from PyQt5.QtGui import QKeySequence

from config.settings import Settings

logger = logging.getLogger('video_encoder.ui.widgets.settings_dialog')


class SettingsDialog(QDialog):
    """Dialog for configuring application settings"""
    
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.original_settings = {}
        self.shortcut_edits = {}
        
        # Save original settings for cancel
        self.backup_settings()
        
        # Initialize UI
        self.init_ui()
        
        # Load current settings
        self.load_settings()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Set dialog properties
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_general_tab()
        self.create_encoding_tab()
        self.create_interface_tab()
        self.create_shortcuts_tab()
        self.create_advanced_tab()
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.Reset)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self.apply_settings)
        button_box.button(QDialogButtonBox.Reset).clicked.connect(self.reset_settings)
        main_layout.addWidget(button_box)
    
    def create_general_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Language selection
        self.language_combo = QComboBox()
        for code, name in self.settings.AVAILABLE_LANGUAGES.items():
            self.language_combo.addItem(name, code)
        layout.addRow("Language:", self.language_combo)
        
        # Theme selection
        self.theme_combo = QComboBox()
        for theme in self.settings.AVAILABLE_THEMES:
            self.theme_combo.addItem(theme.capitalize(), theme)
        layout.addRow("Theme:", self.theme_combo)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setReadOnly(True)
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_output_dir)
        output_dir_layout.addWidget(self.browse_button)
        
        layout.addRow("Output Directory:", output_dir_layout)
        
        # Check for updates
        self.updates_check = QCheckBox("Check for updates on startup")
        layout.addRow("", self.updates_check)
        
        self.tab_widget.addTab(tab, "General")
    
    def create_encoding_tab(self):
        """Create the encoding settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Default quality preset
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["very_low", "low", "medium", "high", "very_high"])
        layout.addRow("Default Quality:", self.quality_combo)
        
        # Default output format
        self.format_combo = QComboBox()
        self.format_combo.addItems(["mp4", "mkv", "webm", "mov"])
        layout.addRow("Default Format:", self.format_combo)
        
        # Default prefix template
        self.prefix_combo = QComboBox()
        templates = self.settings.DEFAULT_SETTINGS.get('default_prefix_template', 'simple')
        self.prefix_combo.addItems(["simple", "with_quality", "with_date", "with_datetime", "with_resolution", "detailed", "full"])
        layout.addRow("Default Filename Template:", self.prefix_combo)
        
        self.tab_widget.addTab(tab, "Encoding")
    
    def create_interface_tab(self):
        """Create the interface settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Show tooltips
        self.tooltips_check = QCheckBox("Show tooltips")
        layout.addRow("", self.tooltips_check)
        
        # Confirm overwrite
        self.overwrite_check = QCheckBox("Confirm before overwriting files")
        layout.addRow("", self.overwrite_check)
        
        # Remember last directory
        self.remember_dir_check = QCheckBox("Remember last used directory")
        layout.addRow("", self.remember_dir_check)
        
        # Recent files limit
        self.recent_files_spin = QSpinBox()
        self.recent_files_spin.setRange(0, 50)
        layout.addRow("Maximum recent files:", self.recent_files_spin)
        
        self.tab_widget.addTab(tab, "Interface")
    
    def create_shortcuts_tab(self):
        """Create the keyboard shortcuts tab"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # Get default shortcuts
        shortcuts = self.settings.get('shortcuts', {})
        
        # Create shortcut editors
        for action, shortcut in shortcuts.items():
            # Create a more readable action name
            action_name = action.replace('_', ' ').title()
            
            # Create shortcut editor
            shortcut_edit = QKeySequenceEdit()
            shortcut_edit.setKeySequence(QKeySequence(shortcut))
            
            # Store reference to editor
            self.shortcut_edits[action] = shortcut_edit
            
            # Add to layout
            layout.addRow(f"{action_name}:", shortcut_edit)
        
        self.tab_widget.addTab(tab, "Shortcuts")
    
    def create_advanced_tab(self):
        """Create the advanced settings tab"""
        tab = QWidget()
        layout = QFormLayout(tab)
        
        # FFmpeg path
        ffmpeg_layout = QHBoxLayout()
        self.ffmpeg_path_edit = QLineEdit()
        ffmpeg_layout.addWidget(self.ffmpeg_path_edit)
        
        self.ffmpeg_browse_button = QPushButton("Browse...")
        self.ffmpeg_browse_button.clicked.connect(self.browse_ffmpeg_path)
        ffmpeg_layout.addWidget(self.ffmpeg_browse_button)
        
        layout.addRow("FFmpeg Path:", ffmpeg_layout)
        
        # Enable logging
        self.logging_check = QCheckBox("Enable logging")
        layout.addRow("", self.logging_check)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        layout.addRow("Log Level:", self.log_level_combo)
        
        self.tab_widget.addTab(tab, "Advanced")
    
    def backup_settings(self):
        """Backup original settings for cancel operation"""
        self.original_settings = self.settings.settings.copy()
    
    def load_settings(self):
        """Load current settings into the UI"""
        # General tab
        language = self.settings.get('language', 'en')
        index = self.language_combo.findData(language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        theme = self.settings.get('theme', 'system')
        index = self.theme_combo.findData(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self.output_dir_edit.setText(self.settings.get_output_directory())
        self.updates_check.setChecked(self.settings.get('check_updates', True))
        
        # Encoding tab
        quality = self.settings.get('default_quality', 'medium')
        index = self.quality_combo.findText(quality)
        if index >= 0:
            self.quality_combo.setCurrentIndex(index)
        
        format_str = self.settings.get('default_format', 'mp4')
        index = self.format_combo.findText(format_str)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)
        
        prefix = self.settings.get('default_prefix_template', 'simple')
        index = self.prefix_combo.findText(prefix)
        if index >= 0:
            self.prefix_combo.setCurrentIndex(index)
        
        # Interface tab
        self.tooltips_check.setChecked(self.settings.get('show_tooltips', True))
        self.overwrite_check.setChecked(self.settings.get('confirm_overwrite', True))
        self.remember_dir_check.setChecked(self.settings.get('remember_last_directory', True))
        self.recent_files_spin.setValue(self.settings.get('max_recent_files', 10))
        
        # Advanced tab
        self.ffmpeg_path_edit.setText(self.settings.get('ffmpeg_path', ''))
        self.logging_check.setChecked(self.settings.get('enable_logging', True))
        
        log_level = self.settings.get('log_level', 'INFO')
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
    
    def apply_settings(self):
        """Apply the current settings"""
        try:
            # General tab
            self.settings.set('language', self.language_combo.currentData())
            self.settings.set('theme', self.theme_combo.currentData())
            self.settings.set('output_directory', self.output_dir_edit.text())
            self.settings.set('check_updates', self.updates_check.isChecked())
            
            # Encoding tab
            self.settings.set('default_quality', self.quality_combo.currentText())
            self.settings.set('default_format', self.format_combo.currentText())
            self.settings.set('default_prefix_template', self.prefix_combo.currentText())
            
            # Interface tab
            self.settings.set('show_tooltips', self.tooltips_check.isChecked())
            self.settings.set('confirm_overwrite', self.overwrite_check.isChecked())
            self.settings.set('remember_last_directory', self.remember_dir_check.isChecked())
            self.settings.set('max_recent_files', self.recent_files_spin.value())
            
            # Shortcuts tab
            shortcuts = {}
            for action, edit in self.shortcut_edits.items():
                shortcuts[action] = edit.keySequence().toString()
            self.settings.set('shortcuts', shortcuts)
            
            # Advanced tab
            self.settings.set('ffmpeg_path', self.ffmpeg_path_edit.text())
            self.settings.set('enable_logging', self.logging_check.isChecked())
            self.settings.set('log_level', self.log_level_combo.currentText())
            
            # Save settings
            self.settings.save_settings()
            
            # Update backup
            self.backup_settings()
            
            return True
        except Exception as e:
            logger.error(f"Error applying settings: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply settings: {e}"
            )
            return False
    
    def reset_settings(self):
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.settings.reset()
            self.load_settings()
    
    def browse_output_dir(self):
        """Browse for output directory"""
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
    
    def browse_ffmpeg_path(self):
        """Browse for FFmpeg executable"""
        current_path = self.ffmpeg_path_edit.text()
        if not current_path or not os.path.isfile(current_path):
            current_path = os.path.expanduser('~')
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FFmpeg Executable",
            current_path,
            "Executables (*.exe);;All Files (*.*)"
        )
        
        if file_path:
            self.ffmpeg_path_edit.setText(file_path)
    
    def accept(self):
        """Handle dialog acceptance"""
        if self.apply_settings():
            super().accept()
    
    def reject(self):
        """Handle dialog rejection"""
        # Restore original settings
        self.settings.settings = self.original_settings.copy()
        super().reject()