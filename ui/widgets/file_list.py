#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File List Widget
Implements a list widget for managing video files to be encoded
"""

import os
import logging
from typing import List, Optional

from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QDragEnterEvent, QDropEvent

logger = logging.getLogger('video_encoder.ui.widgets.file_list')


class FileListWidget(QListWidget):
    """Custom list widget for managing video files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_index = 0  # Index of current file being processed
        
        # Setup widget properties
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def add_file(self, file_path: str) -> bool:
        """Add a file to the list
        
        Args:
            file_path: Path to the video file
            
        Returns:
            True if file was added, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.isfile(file_path):
                logger.warning(f"File does not exist: {file_path}")
                return False
            
            # Check if file is already in the list
            for i in range(self.count()):
                if self.item(i).data(Qt.UserRole) == file_path:
                    logger.info(f"File already in list: {file_path}")
                    return False
            
            # Create list item
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.UserRole, file_path)  # Store full path as user data
            item.setToolTip(file_path)
            
            # Add to list
            self.addItem(item)
            return True
        except Exception as e:
            logger.error(f"Error adding file: {e}")
            return False
    
    def add_files(self, file_paths: List[str]) -> int:
        """Add multiple files to the list
        
        Args:
            file_paths: List of file paths
            
        Returns:
            Number of files successfully added
        """
        count = 0
        for file_path in file_paths:
            if self.add_file(file_path):
                count += 1
        return count
    
    def remove_selected_files(self) -> int:
        """Remove selected files from the list
        
        Returns:
            Number of files removed
        """
        selected_items = self.selectedItems()
        count = len(selected_items)
        
        # Remove items in reverse order to avoid index issues
        for item in reversed(selected_items):
            row = self.row(item)
            self.takeItem(row)
            
            # Adjust current_index if needed
            if row < self.current_index:
                self.current_index -= 1
        
        # Ensure current_index is valid
        if self.current_index >= self.count():
            self.current_index = 0
        
        return count
    
    def show_context_menu(self, position):
        """Show context menu for the list"""
        menu = QMenu()
        
        # Add actions
        remove_action = QAction("Remove Selected", self)
        remove_action.triggered.connect(self.remove_selected_files)
        menu.addAction(remove_action)
        
        clear_action = QAction("Clear All", self)
        clear_action.triggered.connect(self.clear)
        menu.addAction(clear_action)
        
        # Show menu
        menu.exec_(self.mapToGlobal(position))
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for drag and drop"""
        try:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
        except Exception as e:
            logger.error(f"Error in drag enter event: {e}")
            
    def dropEvent(self, event: QDropEvent):
        """Handle drop events for drag and drop"""
        try:
            files = []
            for url in event.mimeData().urls():
                # Convert QUrl to local path
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
            
            if files and self.parent:
                self.parent.add_files_to_list(files)
        except Exception as e:
            logger.error(f"Error in drop event: {e}")
    
    def clear(self):
        """Clear all items from the list"""
        super().clear()
        self.current_index = 0