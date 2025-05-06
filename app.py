#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Video Encoder Application
Main entry point for the application
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, 'app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('video_encoder')

# Import required modules with better error handling
required_modules = {
    'PyQt5.QtWidgets': ['QApplication', 'QMainWindow', 'QWidget'],
    'PyQt5.QtCore': ['QTranslator', 'QLocale'],
    'PyQt5.QtGui': ['QDragEnterEvent', 'QDropEvent'],
    'ui.main_window': ['MainWindow'],
    'config.settings': ['Settings']
}

missing_modules = []
for module, classes in required_modules.items():
    try:
        if module == 'PyQt5.QtWidgets':
            from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
        elif module == 'PyQt5.QtCore':
            from PyQt5.QtCore import QTranslator, QLocale
        elif module == 'PyQt5.QtGui':
            from PyQt5.QtGui import QDragEnterEvent, QDropEvent
        elif module == 'ui.main_window':
            from ui.main_window import MainWindow
        elif module == 'config.settings':
            from config.settings import Settings
    except ImportError as e:
        logger.error(f"Failed to import from {module}: {e}")
        missing_modules.append(f"{module} ({', '.join(classes)})")

if missing_modules:
    error_msg = f"Failed to import required modules: {', '.join(missing_modules)}"
    logger.critical(error_msg)
    print(f"Error: {error_msg}\nPlease install required dependencies with: pip install -r requirements.txt")
    sys.exit(1)


def setup_exception_handling():
    """Set up global exception handling to prevent crashes"""
    def exception_hook(exctype, value, traceback):
        logger.error(f"Uncaught exception", exc_info=(exctype, value, traceback))
        sys.__excepthook__(exctype, value, traceback)
    
    sys.excepthook = exception_hook


def main():
    """Main application entry point"""
    try:
        # Initialize application
        app = QApplication(sys.argv)
        app.setApplicationName("Video Encoder")
        app.setOrganizationName("VideoEncoder")
        
        # Set default font to Arial or system default
        try:
            font = app.font()
            font.setFamily("Arial")
            app.setFont(font)
        except Exception as e:
            logger.warning(f"Could not set application font: {e}")
        
        # Load settings
        try:
            settings = Settings()
        except Exception as e:
            logger.critical(f"Failed to load settings: {e}")
            print(f"Critical error loading settings: {e}")
            # Create default settings as fallback
            settings = Settings()
            settings.reset()
        
        # Setup translation
        try:
            translator = QTranslator()
            locale = settings.get('language', QLocale.system().name())
            translator_path = os.path.join(project_root, 'config', 'languages', f"{locale}.qm")
            
            if os.path.exists(translator_path):
                translator.load(translator_path)
                app.installTranslator(translator)
        except Exception as e:
            logger.warning(f"Failed to load translations: {e}")
        
        # Create and show main window
        try:
            window = MainWindow(settings)
            window.show()
        except Exception as e:
            logger.critical(f"Failed to create main window: {e}", exc_info=True)
            QMessageBox.critical(None, "Error", f"Failed to start application: {e}")
            return 1
        
        # Start event loop
        return app.exec_()
    
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        print(f"Critical error: {e}")
        return 1


if __name__ == "__main__":
    # Setup exception handling
    setup_exception_handling()
    
    # Create necessary directories if they don't exist
    for directory in ['config/languages', 'core', 'ui/widgets', 'utils']:
        os.makedirs(os.path.join(project_root, directory), exist_ok=True)
    
    # Run the application
    sys.exit(main())