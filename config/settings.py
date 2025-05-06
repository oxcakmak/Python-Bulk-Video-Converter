#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings Module
Handles application configuration including themes, languages, and user preferences
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger('video_encoder.config.settings')


class Settings:
    """Manages application settings and preferences"""
    
    # Default settings
    DEFAULT_SETTINGS = {
        # General settings
        'language': 'en',  # Default language
        'theme': 'system',  # Default theme (system, light, dark)
        'output_directory': '',  # Default output directory (empty = user's videos folder)
        'check_updates': True,  # Check for updates on startup
        
        # Encoding settings
        'default_quality': 'medium',  # Default quality preset
        'default_format': 'mp4',  # Default output format
        'default_prefix_template': 'simple',  # Default prefix template
        'default_input_mode': 'files',  # Default input mode (files or directory)
        'recursive_scan': False,  # Scan subdirectories by default
        
        # UI settings
        'show_tooltips': True,  # Show tooltips
        'confirm_overwrite': True,  # Confirm before overwriting files
        'remember_last_directory': True,  # Remember last used directory
        
        # Advanced settings
        'ffmpeg_path': '',  # Custom FFmpeg path (empty = auto-detect)
        'max_recent_files': 10,  # Maximum number of recent files to remember
        'enable_logging': True,  # Enable logging
        'log_level': 'INFO',  # Logging level
        
        # Shortcuts
        'shortcuts': {
            'open_file': 'Ctrl+O',
            'save_file': 'Ctrl+S',
            'start_conversion': 'Ctrl+R',
            'stop_conversion': 'Ctrl+X',
            'settings': 'Ctrl+P',
            'exit': 'Alt+F4'
        },
        
        # Recent files
        'recent_files': []
    }
    
    # Available themes
    AVAILABLE_THEMES = ['system', 'light', 'dark', 'blue', 'green']
    
    # Available languages
    AVAILABLE_LANGUAGES = {
        'en': 'English',
        'es': 'Español',
        'fr': 'Français',
        'de': 'Deutsch',
        'it': 'Italiano',
        'pt': 'Português',
        'ru': 'Русский',
        'zh': '中文',
        'ja': '日本語',
        'ko': '한국어'
    }
    
    def __init__(self):
        """Initialize settings"""
        self.settings_dir = self._get_settings_dir()
        self.settings_file = os.path.join(self.settings_dir, 'settings.json')
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def _get_settings_dir(self) -> str:
        """Get the settings directory, create if it doesn't exist"""
        try:
            # Use platform-specific app data directory
            if os.name == 'nt':  # Windows
                app_data = os.environ.get('APPDATA', '')
                if not app_data:
                    app_data = os.path.expanduser('~')
                settings_dir = os.path.join(app_data, 'VideoEncoder')
            else:  # macOS, Linux
                settings_dir = os.path.expanduser('~/.config/video-encoder')
            
            # Create directory if it doesn't exist
            os.makedirs(settings_dir, exist_ok=True)
            return settings_dir
        except Exception as e:
            logger.error(f"Error creating settings directory: {e}")
            # Fallback to current directory
            return os.path.abspath('.')
    
    def load_settings(self) -> bool:
        """Load settings from file
        
        Returns:
            True if settings were loaded successfully, False otherwise
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Update settings with loaded values
                for key, value in loaded_settings.items():
                    if key in self.settings:
                        self.settings[key] = value
                
                # Removed the logging message here
                return True
            else:
                # Removed the logging message here too
                return False
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return False
    
    def save_settings(self) -> bool:
        """Save settings to file
        
        Returns:
            True if settings were saved successfully, False otherwise
        """
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set a setting value
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            True if setting was set successfully, False otherwise
        """
        try:
            self.settings[key] = value
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False
    
    def reset(self) -> bool:
        """Reset settings to defaults
        
        Returns:
            True if settings were reset successfully, False otherwise
        """
        try:
            self.settings = self.DEFAULT_SETTINGS.copy()
            return self.save_settings()
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False
    
    def add_recent_file(self, file_path: str) -> bool:
        """Add a file to recent files list
        
        Args:
            file_path: File path to add
            
        Returns:
            True if file was added successfully, False otherwise
        """
        try:
            recent_files = self.settings.get('recent_files', [])
            
            # Remove if already exists
            if file_path in recent_files:
                recent_files.remove(file_path)
            
            # Add to beginning of list
            recent_files.insert(0, file_path)
            
            # Limit list size
            max_recent = self.settings.get('max_recent_files', 10)
            self.settings['recent_files'] = recent_files[:max_recent]
            
            return True
        except Exception as e:
            logger.error(f"Error adding recent file: {e}")
            return False
    
    def get_recent_files(self) -> List[str]:
        """Get list of recent files
        
        Returns:
            List of recent file paths
        """
        return self.settings.get('recent_files', [])
    
    def clear_recent_files(self) -> bool:
        """Clear recent files list
        
        Returns:
            True if list was cleared successfully, False otherwise
        """
        try:
            self.settings['recent_files'] = []
            return True
        except Exception as e:
            logger.error(f"Error clearing recent files: {e}")
            return False
    
    def get_shortcut(self, action: str) -> str:
        """Get keyboard shortcut for an action
        
        Args:
            action: Action name
            
        Returns:
            Shortcut string or empty string if not found
        """
        shortcuts = self.settings.get('shortcuts', {})
        return shortcuts.get(action, '')
    
    def set_shortcut(self, action: str, shortcut: str) -> bool:
        """Set keyboard shortcut for an action
        
        Args:
            action: Action name
            shortcut: Shortcut string
            
        Returns:
            True if shortcut was set successfully, False otherwise
        """
        try:
            shortcuts = self.settings.get('shortcuts', {})
            shortcuts[action] = shortcut
            self.settings['shortcuts'] = shortcuts
            return True
        except Exception as e:
            logger.error(f"Error setting shortcut: {e}")
            return False
    
    def get_output_directory(self) -> str:
        """Get output directory, with fallback to user's videos folder
        
        Returns:
            Output directory path
        """
        output_dir = self.settings.get('output_directory', '')
        
        if not output_dir or not os.path.isdir(output_dir):
            # Fallback to user's videos folder
            if os.name == 'nt':  # Windows
                output_dir = os.path.join(os.path.expanduser('~'), 'Videos')
            else:  # macOS, Linux
                output_dir = os.path.join(os.path.expanduser('~'), 'Videos')
            
            # Create if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
        
        return output_dir
    
    def get_theme_stylesheet(self) -> str:
        """Get CSS stylesheet for current theme
        
        Returns:
            CSS stylesheet string
        """
        theme = self.settings.get('theme', 'system')
        
        # If system theme, detect from system
        if theme == 'system':
            # This is a simplified detection, would be more complex in real app
            # For Windows, could use registry or win32api
            # For macOS/Linux, could use system commands
            # For now, default to light
            theme = 'light'
        
        # Return appropriate stylesheet
        if theme == 'dark':
            return self._get_dark_theme()
        elif theme == 'blue':
            return self._get_blue_theme()
        elif theme == 'green':
            return self._get_green_theme()
        else:  # light theme
            return self._get_light_theme()
    
    def _get_light_theme(self) -> str:
        """Get light theme stylesheet"""
        return """
        QWidget {
            background-color: #f5f5f5;
            color: #212121;
        }
        
        QMainWindow, QDialog {
            background-color: #f5f5f5;
        }
        
        QPushButton {
            background-color: #e0e0e0;
            border: 1px solid #bdbdbd;
            border-radius: 4px;
            padding: 5px 10px;
        }
        
        QPushButton:hover {
            background-color: #d5d5d5;
        }
        
        QPushButton:pressed {
            background-color: #bdbdbd;
        }
        
        QLineEdit, QComboBox, QSpinBox {
            background-color: #ffffff;
            border: 1px solid #bdbdbd;
            border-radius: 4px;
            padding: 3px;
        }
        
        QProgressBar {
            border: 1px solid #bdbdbd;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #2196f3;
        }
        
        QMenuBar {
            background-color: #f5f5f5;
        }
        
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #bdbdbd;
        }
        
        QMenu::item:selected {
            background-color: #e0e0e0;
        }
        """
    
    def _get_dark_theme(self) -> str:
        """Get dark theme stylesheet"""
        return """
        QWidget {
            background-color: #212121;
            color: #f5f5f5;
        }
        
        QMainWindow, QDialog {
            background-color: #212121;
        }
        
        QPushButton {
            background-color: #424242;
            border: 1px solid #616161;
            border-radius: 4px;
            padding: 5px 10px;
            color: #f5f5f5;
        }
        
        QPushButton:hover {
            background-color: #616161;
        }
        
        QPushButton:pressed {
            background-color: #757575;
        }
        
        QLineEdit, QComboBox, QSpinBox {
            background-color: #424242;
            border: 1px solid #616161;
            border-radius: 4px;
            padding: 3px;
            color: #f5f5f5;
        }
        
        QProgressBar {
            border: 1px solid #616161;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #2196f3;
        }
        
        QMenuBar {
            background-color: #212121;
        }
        
        QMenuBar::item:selected {
            background-color: #424242;
        }
        
        QMenu {
            background-color: #424242;
            border: 1px solid #616161;
        }
        
        QMenu::item:selected {
            background-color: #616161;
        }
        """
    
    def _get_blue_theme(self) -> str:
        """Get blue theme stylesheet"""
        return """
        QWidget {
            background-color: #e3f2fd;
            color: #0d47a1;
        }
        
        QMainWindow, QDialog {
            background-color: #e3f2fd;
        }
        
        QPushButton {
            background-color: #bbdefb;
            border: 1px solid #64b5f6;
            border-radius: 4px;
            padding: 5px 10px;
            color: #0d47a1;
        }
        
        QPushButton:hover {
            background-color: #90caf9;
        }
        
        QPushButton:pressed {
            background-color: #64b5f6;
        }
        
        QLineEdit, QComboBox, QSpinBox {
            background-color: #ffffff;
            border: 1px solid #64b5f6;
            border-radius: 4px;
            padding: 3px;
            color: #0d47a1;
        }
        
        QProgressBar {
            border: 1px solid #64b5f6;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #2196f3;
        }
        
        QMenuBar {
            background-color: #e3f2fd;
        }
        
        QMenuBar::item:selected {
            background-color: #bbdefb;
        }
        
        QMenu {
            background-color: #e3f2fd;
            border: 1px solid #64b5f6;
        }
        
        QMenu::item:selected {
            background-color: #bbdefb;
        }
        """
    
    def _get_green_theme(self) -> str:
        """Get green theme stylesheet"""
        return """
        QWidget {
            background-color: #e8f5e9;
            color: #1b5e20;
        }
        
        QMainWindow, QDialog {
            background-color: #e8f5e9;
        }
        
        QPushButton {
            background-color: #c8e6c9;
            border: 1px solid #81c784;
            border-radius: 4px;
            padding: 5px 10px;
            color: #1b5e20;
        }
        
        QPushButton:hover {
            background-color: #a5d6a7;
        }
        
        QPushButton:pressed {
            background-color: #81c784;
        }
        
        QLineEdit, QComboBox, QSpinBox {
            background-color: #ffffff;
            border: 1px solid #81c784;
            border-radius: 4px;
            padding: 3px;
            color: #1b5e20;
        }
        
        QProgressBar {
            border: 1px solid #81c784;
            border-radius: 4px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #4caf50;
        }
        
        QMenuBar {
            background-color: #e8f5e9;
        }
        
        QMenuBar::item:selected {
            background-color: #c8e6c9;
        }
        
        QMenu {
            background-color: #e8f5e9;
            border: 1px solid #81c784;
        }
        
        QMenu::item:selected {
            background-color: #c8e6c9;
        }
        """