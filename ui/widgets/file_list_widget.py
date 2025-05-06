class FileListWidget(QListWidget):
    """Widget for displaying and managing the list of input files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_index = 0
        self.setAcceptDrops(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    def add_file(self, file_path: str) -> bool:
        """Add a file to the list
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file was added, False otherwise
        """
        try:
            # Check if file exists
            if not os.path.isfile(file_path):
                return False
            
            # Check if file is already in the list
            for i in range(self.count()):
                if self.item(i).data(Qt.UserRole) == file_path:
                    return False
            
            # Create list item
            item = QListWidgetItem(os.path.basename(file_path))
            item.setData(Qt.UserRole, file_path)
            
            # Add tooltip with full path
            item.setToolTip(file_path)
            
            # Add to list
            self.addItem(item)
            return True
        except Exception as e:
            logger.error(f"Error adding file: {e}")
            return False
    
    def has_files(self) -> bool:
        """Check if the list has any files"""
        return self.count() > 0
    
    # ... existing code ...