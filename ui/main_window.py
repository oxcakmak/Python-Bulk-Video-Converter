#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Window Module
Implements the main application window for the video encoder
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QFileDialog, QMessageBox, 
    QProgressBar, QAction, QMenu, QToolBar, QStatusBar,
    QTabWidget, QSplitter, QFrame, QListWidget, QListWidgetItem,
    QCheckBox, QSpinBox, QDoubleSpinBox, QLineEdit, QGroupBox,
    QFormLayout, QSizePolicy, QApplication, QActionGroup
)
from PyQt5.QtCore import Qt, QSize, QUrl, QThread, pyqtSignal, QMimeData, QSettings
from PyQt5.QtGui import QIcon, QPixmap, QDrag, QKeySequence, QDragEnterEvent, QDropEvent

from config.settings import Settings
from core.encoder import VideoEncoder
from core.file_manager import FileManager
from core.prefix_manager import PrefixManager
from ui.widgets.encoding_form import EncodingForm
from ui.widgets.file_list import FileListWidget
from ui.widgets.settings_dialog import SettingsDialog

logger = logging.getLogger('video_encoder.ui.main_window')


class EncoderThread(QThread):
    """Thread for running encoding operations without blocking the UI"""
    progress_update = pyqtSignal(int, str)
    encoding_finished = pyqtSignal(bool, str)
    
    def __init__(self, encoder: VideoEncoder, input_path: str, output_path: str, 
                 quality: str, target_size: Optional[int] = None,
                 output_format: Optional[str] = None):
        super().__init__()
        self.encoder = encoder
        self.input_path = input_path
        self.output_path = output_path
        self.quality = quality
        self.target_size = target_size
        self.output_format = output_format
        self.cancelled = False
    
    def run(self):
        """Run the encoding process"""
        try:
            # This is a simplified version - in a real app, you would
            # hook into ffmpeg progress updates
            self.progress_update.emit(0, "Starting encoding...")
            
            # Simulate progress updates
            for i in range(1, 101):
                if self.cancelled:
                    self.encoding_finished.emit(False, "Encoding cancelled")
                    return
                
                # In a real app, this would be actual progress from ffmpeg
                self.progress_update.emit(i, f"Encoding: {i}%")
                self.msleep(50)  # Simulate work
            
            # Perform the actual encoding
            success, message = self.encoder.convert_video(
                self.input_path, 
                self.output_path,
                self.quality,
                self.target_size,
                self.output_format
            )
            
            self.encoding_finished.emit(success, message)
        except Exception as e:
            logger.error(f"Error in encoder thread: {e}")
            self.encoding_finished.emit(False, str(e))
    
    def cancel(self):
        """Cancel the encoding process"""
        self.cancelled = True


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.encoder = VideoEncoder()
        self.file_manager = FileManager()
        self.prefix_manager = PrefixManager()
        self.encoder_thread = None
        
        # Initialize UI
        self.init_ui()
        
        # Apply theme
        self.apply_theme()
        
        # Load recent files
        self.load_recent_files()
        
        # Setup drag and drop
        self.setAcceptDrops(True)
    
    def init_ui(self):
        """Initialize the user interface"""
        try:
            # Set window properties
            self.setWindowTitle("Video Encoder")
            self.setMinimumSize(800, 600)
            
            # Create central widget and main layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            main_layout = QVBoxLayout(central_widget)
            
            # Create splitter for file list and encoding form
            splitter = QSplitter(Qt.Horizontal)
            main_layout.addWidget(splitter)
            
            # File list section
            file_list_container = QWidget()
            file_list_layout = QVBoxLayout(file_list_container)
            file_list_layout.setContentsMargins(0, 0, 0, 0)
            
            # File list label
            file_list_label = QLabel("Input Files")
            file_list_label.setAlignment(Qt.AlignCenter)
            file_list_layout.addWidget(file_list_label)
            
            # File list widget
            try:
                self.file_list = FileListWidget(self)
                file_list_layout.addWidget(self.file_list)
            except Exception as e:
                logger.error(f"Error creating file list widget: {e}")
                self.file_list = QListWidget()  # Fallback to basic list widget
                file_list_layout.addWidget(self.file_list)
            
            # File buttons
            file_buttons_layout = QHBoxLayout()
            self.add_file_button = QPushButton("Add Files")
            self.add_file_button.clicked.connect(self.add_files)
            self.remove_file_button = QPushButton("Remove")
            self.remove_file_button.clicked.connect(self.remove_selected_files)
            self.clear_files_button = QPushButton("Clear All")
            self.clear_files_button.clicked.connect(self.clear_files)
            
            file_buttons_layout.addWidget(self.add_file_button)
            file_buttons_layout.addWidget(self.remove_file_button)
            file_buttons_layout.addWidget(self.clear_files_button)
            file_list_layout.addLayout(file_buttons_layout)
            
            # Add file list to splitter
            splitter.addWidget(file_list_container)
            
            # Encoding form section
            try:
                self.encoding_form = EncodingForm(self.settings, self.prefix_manager)
                splitter.addWidget(self.encoding_form)
            except Exception as e:
                logger.error(f"Error creating encoding form: {e}")
                # Create a simple placeholder widget as fallback
                placeholder = QWidget()
                placeholder_layout = QVBoxLayout(placeholder)
                placeholder_layout.addWidget(QLabel("Error loading encoding form. Please restart the application."))
                splitter.addWidget(placeholder)
            
            # Set initial splitter sizes
            splitter.setSizes([300, 500])
            
            # Progress section
            progress_group = QGroupBox("Encoding Progress")
            progress_layout = QVBoxLayout(progress_group)
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            progress_layout.addWidget(self.progress_bar)
            
            self.status_label = QLabel("Ready")
            progress_layout.addWidget(self.status_label)
            
            # Action buttons
            action_layout = QHBoxLayout()
            self.start_button = QPushButton("Start Encoding")
            self.start_button.clicked.connect(self.start_encoding)
            self.stop_button = QPushButton("Stop")
            self.stop_button.clicked.connect(self.stop_encoding)
            self.stop_button.setEnabled(False)
            
            action_layout.addWidget(self.start_button)
            action_layout.addWidget(self.stop_button)
            progress_layout.addLayout(action_layout)
            
            main_layout.addWidget(progress_group)
            
            # Create menu bar
            self.create_menu_bar()
            
            # Create status bar
            self.statusBar = QStatusBar()
            self.setStatusBar(self.statusBar)
            self.statusBar.showMessage("Ready")
        except Exception as e:
            logger.critical(f"Failed to initialize UI: {e}", exc_info=True)
            # Create minimal UI to prevent complete failure
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            error_layout = QVBoxLayout(central_widget)
            error_label = QLabel(f"Error initializing UI: {e}\nPlease restart the application.")
            error_layout.addWidget(error_label)
    
    def create_menu_bar(self):
        """Create the application menu bar"""
        try:
            # File menu
            file_menu = self.menuBar().addMenu("&File")
            
            open_action = QAction("&Open Files...", self)
            open_action.setShortcut(QKeySequence(self.settings.get_shortcut('open_file')))
            open_action.triggered.connect(self.add_files)
            file_menu.addAction(open_action)
            
            # Recent files submenu
            self.recent_menu = QMenu("Recent Files", self)
            file_menu.addMenu(self.recent_menu)
            
            clear_recent_action = QAction("Clear Recent Files", self)
            clear_recent_action.triggered.connect(self.clear_recent_files)
            self.recent_menu.addAction(clear_recent_action)
            self.recent_menu.addSeparator()
            
            # Exit action
            exit_action = QAction("E&xit", self)
            exit_action.setShortcut(QKeySequence(self.settings.get_shortcut('exit')))
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # Encoding menu
            encoding_menu = self.menuBar().addMenu("&Encoding")
            
            start_action = QAction("&Start Encoding", self)
            start_action.setShortcut(QKeySequence(self.settings.get_shortcut('start_conversion')))
            start_action.triggered.connect(self.start_encoding)
            encoding_menu.addAction(start_action)
            
            stop_action = QAction("S&top Encoding", self)
            stop_action.setShortcut(QKeySequence(self.settings.get_shortcut('stop_conversion')))
            stop_action.triggered.connect(self.stop_encoding)
            encoding_menu.addAction(stop_action)
            
            # Settings menu
            settings_menu = self.menuBar().addMenu("&Settings")
            
            preferences_action = QAction("&Preferences...", self)
            preferences_action.setShortcut(QKeySequence(self.settings.get_shortcut('settings')))
            preferences_action.triggered.connect(self.show_settings)
            settings_menu.addAction(preferences_action)
            
            # Theme submenu
            theme_menu = QMenu("Theme", self)
            settings_menu.addMenu(theme_menu)
            
            theme_group = QActionGroup(self)
            for theme in self.settings.AVAILABLE_THEMES:
                theme_action = QAction(theme.capitalize(), self, checkable=True)
                if theme == self.settings.get('theme', 'system'):
                    theme_action.setChecked(True)
                theme_action.triggered.connect(lambda checked, t=theme: self.change_theme(t))
                theme_group.addAction(theme_action)
                theme_menu.addAction(theme_action)
            
            # Language submenu
            language_menu = QMenu("Language", self)
            settings_menu.addMenu(language_menu)
            
            language_group = QActionGroup(self)
            for code, name in self.settings.AVAILABLE_LANGUAGES.items():
                language_action = QAction(name, self, checkable=True)
                if code == self.settings.get('language', 'en'):
                    language_action.setChecked(True)
                language_action.triggered.connect(lambda checked, c=code: self.change_language(c))
                language_group.addAction(language_action)
                language_menu.addAction(language_action)
            
            # Help menu
            help_menu = self.menuBar().addMenu("&Help")
            
            about_action = QAction("&About", self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
        except Exception as e:
            logger.error(f"Error creating menu bar: {e}")
            # Create a minimal menu bar to allow the application to continue
            file_menu = self.menuBar().addMenu("&File")
            exit_action = QAction("E&xit", self)
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
    
    def apply_theme(self):
        """Apply the current theme stylesheet"""
        stylesheet = self.settings.get_theme_stylesheet()
        self.setStyleSheet(stylesheet)
    
    def change_theme(self, theme: str):
        """Change the application theme"""
        self.settings.set('theme', theme)
        self.settings.save_settings()
        self.apply_theme()
    
    def change_language(self, language_code: str):
        """Change the application language"""
        self.settings.set('language', language_code)
        self.settings.save_settings()
        QMessageBox.information(
            self, 
            "Language Changed", 
            "Please restart the application for the language change to take effect."
        )
    
    def show_settings(self):
        """Show the settings dialog"""
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec_():
            # Apply changes if dialog was accepted
            self.apply_theme()
    
    def show_about(self):
        """Show the about dialog"""
        QMessageBox.about(
            self,
            "About Video Encoder",
            "<h3>Video Encoder</h3>"
            "<p>Version 1.0</p>"
            "<p>A simple application for encoding and compressing video files.</p>"
            "<p>Uses FFmpeg for video processing.</p>"
        )
    
    def add_files(self):
        """Open file dialog to add files"""
        # Get last directory if enabled
        start_dir = ""
        if self.settings.get('remember_last_directory', True):
            recent_files = self.settings.get_recent_files()
            if recent_files:
                start_dir = os.path.dirname(recent_files[0])
        
        # Open file dialog
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Video Files",
            start_dir,
            "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm);;All Files (*.*)"
        )
        
        if files:
            # Remember directory
            if self.settings.get('remember_last_directory', True):
                self.settings.set('last_directory', os.path.dirname(files[0]))
            
            # Add files to list
            self.add_files_to_list(files)
    
    def add_files_to_list(self, file_paths: List[str]):
        """Add files to the list widget"""
        try:
            # Check if any files were provided
            if not file_paths:
                return
            
            # Filter for supported files
            supported_files = []
            for file_path in file_paths:
                if self.encoder.is_supported_format(file_path):
                    supported_files.append(file_path)
            
            # Add files to list
            count = self.file_list.add_files(supported_files)
            
            # Update status
            if count > 0:
                self.statusBar.showMessage(f"Added {count} files")
                
                # Save last directory to settings
                if self.settings.get('remember_last_directory', True) and count > 0:
                    last_dir = os.path.dirname(file_paths[0])
                    self.settings.set('last_directory', last_dir)
                    self.settings.save_settings()
                    
                # Add to recent files
                for file_path in supported_files:
                    self.settings.add_recent_file(file_path)
            else:
                self.statusBar.showMessage("No supported files found")
        except Exception as e:
            logger.error(f"Error adding files to list: {e}", exc_info=True)
            self.statusBar.showMessage(f"Error adding files: {str(e)}")
        
        # Update recent files menu
        self.update_recent_files_menu()
    
    def remove_selected_files(self):
        """Remove selected files from the list"""
        self.file_list.remove_selected_files()
    
    def clear_files(self):
        """Clear all files from the list"""
        self.file_list.clear()
    
    def load_recent_files(self):
        """Load recent files from settings"""
        self.update_recent_files_menu()
    
    def update_recent_files_menu(self):
        """Update the recent files menu"""
        # Clear existing items (except the clear action and separator)
        for action in self.recent_menu.actions()[2:]:
            self.recent_menu.removeAction(action)
        
        # Add recent files
        recent_files = self.settings.get_recent_files()
        if recent_files:
            for file_path in recent_files:
                action = QAction(os.path.basename(file_path), self)
                action.setStatusTip(file_path)
                action.triggered.connect(lambda checked, path=file_path: self.open_recent_file(path))
                self.recent_menu.addAction(action)
    
    def open_recent_file(self, file_path: str):
        """Open a file from the recent files list"""
        if os.path.exists(file_path):
            self.add_files_to_list([file_path])
        else:
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file {file_path} no longer exists."
            )
            # Remove from recent files
            recent_files = self.settings.get_recent_files()
            if file_path in recent_files:
                recent_files.remove(file_path)
                self.settings.set('recent_files', recent_files)
                self.settings.save_settings()
                self.update_recent_files_menu()
    
    def clear_recent_files(self):
        """Clear the recent files list"""
        self.settings.clear_recent_files()
        self.settings.save_settings()
        self.update_recent_files_menu()
    
    def start_encoding(self):
        """Start the encoding process"""
        try:
            # Check if files are selected
            if self.file_list.count() == 0:
                QMessageBox.warning(self, "No Files", "Please add files to encode")
                return
            
            # Get encoding settings
            quality, output_format, target_size, output_dir, prefix_template, input_options = self.encoding_form.get_settings()
            
            # Validate output directory
            if not output_dir:
                QMessageBox.warning(self, "No Output Directory", "Please select an output directory")
                return
            
            if not os.path.isdir(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not create output directory: {e}")
                    return
            
            # Disable start button and enable stop button
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            # Reset progress
            self.progress_bar.setValue(0)
            self.status_label.setText("Starting encoding...")
            
            # Get current file
            if self.file_list.count() > 0:
                current_item = self.file_list.item(self.file_list.current_index)
                if current_item:
                    input_path = current_item.data(Qt.UserRole)
                    
                    # Generate output filename
                    try:
                        # Get video info for template
                        video_info = self.encoder.get_video_info(input_path)
                        
                        # Generate output path
                        output_path = self.file_manager.generate_output_path(
                            input_path, output_dir, prefix_template, output_format, video_info, quality
                        )
                    except Exception as e:
                        logger.error(f"Error generating output path: {e}")
                        # Fallback to basic output path
                        filename = os.path.basename(input_path)
                        name, _ = os.path.splitext(filename)
                        output_path = os.path.join(output_dir, f"{name}.{output_format}")
                    
                    # Start encoding thread
                    self.encoder_thread = EncoderThread(
                        self.encoder, input_path, output_path, quality, target_size, output_format
                    )
                    self.encoder_thread.progress_update.connect(self.update_progress)
                    self.encoder_thread.encoding_finished.connect(self.file_encoding_finished)
                    self.encoder_thread.start()
        except Exception as e:
            logger.error(f"Error starting encoding: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Error starting encoding: {str(e)}")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
    def process_next_file(self, quality: str, output_format: str, target_size: Optional[int],
                         output_dir: str, prefix_template: str):
        """Process the next file in the queue"""
        # Check if there are files left to process
        if self.file_list.current_index >= self.file_list.count():
            # All files processed
            self.encoding_finished(True, "All files processed successfully")
            return
        
        # Get the next file
        input_path = self.file_list.item(self.file_list.current_index).data(Qt.UserRole)
        
        # Get video info for prefix template
        video_info = self.encoder.get_video_info(input_path)
        
        # Generate output path
        output_path = self.file_manager.generate_output_path(
            input_path,
            output_dir,
            prefix_template,
            output_format,
            video_info,
            quality
        )
        
        # Check if output file already exists
        if os.path.exists(output_path) and self.settings.get('confirm_overwrite', True):
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"The output file {os.path.basename(output_path)} already exists. Overwrite?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.YesToAll,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                # Skip this file
                self.file_list.current_index += 1
                self.process_next_file(quality, output_format, target_size, output_dir, prefix_template)
                return
            elif reply == QMessageBox.YesToAll:
                # Don't ask again for this session
                self.settings.set('confirm_overwrite', False)
        
        # Update status
        self.status_label.setText(f"Encoding: {os.path.basename(input_path)}")
        self.statusBar.showMessage(f"Encoding file {self.file_list.current_index + 1} of {self.file_list.count()}")
        
        # Start encoding thread
        self.encoder_thread = EncoderThread(
            self.encoder,
            input_path,
            output_path,
            quality,
            target_size,
            output_format
        )
        
        # Connect signals
        self.encoder_thread.progress_update.connect(self.update_progress)
        self.encoder_thread.encoding_finished.connect(self.file_encoding_finished)
        
        # Start thread
        self.encoder_thread.start()
    
    def update_progress(self, value: int, message: str):
        """Update the progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def file_encoding_finished(self, success: bool, message: str):
        """Handle completion of file encoding"""
        try:
            # Update progress bar and status
            self.progress_bar.setValue(100 if success else 0)
            self.status_label.setText(message)
            
            # Get encoding settings - handle potential errors
            try:
                quality, output_format, target_size, output_dir, prefix_template, input_options = self.encoding_form.get_settings()
            except Exception as settings_error:
                logger.error(f"Error getting encoding settings: {settings_error}")
                quality, output_format, target_size, output_dir, prefix_template = "medium", "mp4", None, "", "{filename}"
                input_options = {'mode': 'files', 'directory': '', 'recursive': False}
            
            # Update status
            if success:
                self.statusBar.showMessage(f"Encoding completed successfully")
            else:
                self.statusBar.showMessage(f"Encoding failed: {message}")
            
            # Enable/disable buttons
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            # Reset encoder thread
            self.encoder_thread = None
        except Exception as e:
            logger.error(f"Error in file_encoding_finished: {e}", exc_info=True)
            self.statusBar.showMessage(f"Error: {str(e)}")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
    
        # Update status
        item = self.file_list.item(self.file_list.current_index)
        if item:
            if success:
                item.setBackground(Qt.green)
            else:
                item.setBackground(Qt.red)
        
        # Move to next file
        self.file_list.current_index += 1
        
        # Get settings again in case they were changed
        try:
            quality, output_format, target_size, output_dir, prefix_template, _ = self.encoding_form.get_settings()
        except Exception as settings_error:
            logger.error(f"Error getting encoding settings: {settings_error}")
            quality, output_format, target_size, output_dir, prefix_template = "medium", "mp4", None, "", "{filename}"
        
        # Process next file or finish
        if self.file_list.current_index < self.file_list.count():
            self.process_next_file(quality, output_format, target_size, output_dir, prefix_template)
        else:
            self.encoding_finished(True, "All files processed")
    
    def encoding_finished(self, success: bool, message: str):
        """Handle completion of all encoding"""
        # Re-enable UI
        self.set_ui_enabled(True)
        
        # Update status
        self.status_label.setText(message)
        self.statusBar.showMessage(message)
        self.progress_bar.setValue(0)
        
        # Reset file list index
        self.file_list.current_index = 0
        
        # Show completion message
        if success:
            QMessageBox.information(
                self,
                "Encoding Complete",
                message
            )
    
    def stop_encoding(self):
        """Stop the encoding process"""
        if self.encoder_thread and self.encoder_thread.isRunning():
            # Cancel the thread
            self.encoder_thread.cancel()
            
            # Update status
            self.status_label.setText("Cancelling...")
            self.statusBar.showMessage("Cancelling encoding...")
    
    def set_ui_enabled(self, enabled: bool):
        """Enable or disable UI elements during encoding"""
        # File list controls
        self.file_list.setEnabled(enabled)
        self.add_file_button.setEnabled(enabled)
        self.remove_file_button.setEnabled(enabled)
        self.clear_files_button.setEnabled(enabled)
        
        # Encoding form
        self.encoding_form.setEnabled(enabled)
        
        # Action buttons
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(not enabled)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for drag and drop"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for drag and drop"""
        files = []
        for url in event.mimeData().urls():
            # Convert QUrl to local path
            file_path = url.toLocalFile()
            if os.path.isfile(file_path):
                files.append(file_path)
        
        if files:
            self.add_files_to_list(files)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save settings before closing
        self.settings.save_settings()
        
        # Check if encoding is in progress
        if self.encoder_thread and self.encoder_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "Encoding in Progress",
                "Encoding is still in progress. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Stop encoding and accept close event
                self.stop_encoding()
                event.accept()
            else:
                # Ignore close event
                event.ignore()
        else:
            # No encoding in progress, accept close event
            event.accept()


def add_directory(self):
    """Add all supported files from a directory"""
    try:
        # Get directory from encoding form
        _, _, _, _, _, input_options = self.encoding_form.get_settings()
        directory = input_options.get('directory', '')
        recursive = input_options.get('recursive', False)
        
        if not directory or not os.path.isdir(directory):
            QMessageBox.warning(self, "Invalid Directory", "Please select a valid directory first")
            return
        
        # Show loading indicator
        self.statusBar.showMessage("Scanning directory...")
        QApplication.processEvents()  # Update UI
        
        # Scan directory for supported files
        files = self.file_manager.scan_directory(directory, recursive)
        
        # Sort files alphabetically
        files.sort()
        
        # Add files to list
        self.clear_files()  # Clear existing files
        count = self.file_list.add_files(files)
        
        # Update status with count
        if count > 0:
            self.statusBar.showMessage(f"Added {count} files from directory")
            self.status_label.setText(f"Ready - {count} files loaded")
        else:
            self.statusBar.showMessage("No supported files found in directory")
            self.status_label.setText("No supported files found")
            
    except Exception as e:
        logger.error(f"Error adding directory: {e}", exc_info=True)
        self.statusBar.showMessage(f"Error scanning directory: {str(e)}")