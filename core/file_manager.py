#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File Manager Module
Handles file operations and prefix logic for the video encoder application
"""

import os
import re
import time
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger('video_encoder.core.file_manager')


class FileManager:
    """Handles file operations and naming logic for the video encoder"""
    
    # Available prefix placeholders
    PREFIX_PLACEHOLDERS = {
        '{filename}': 'Original filename without extension',
        '{ext}': 'Original file extension',
        '{date}': 'Current date (YYYY-MM-DD)',
        '{time}': 'Current time (HH-MM-SS)',
        '{datetime}': 'Current date and time (YYYY-MM-DD_HH-MM-SS)',
        '{create_date}': 'File creation date (YYYY-MM-DD)',
        '{size}': 'Original file size in MB',
        '{resolution}': 'Video resolution (WIDTHxHEIGHT)',
        '{codec}': 'Original video codec',
        '{duration}': 'Video duration in seconds',
        '{counter}': 'Sequential counter (1, 2, 3...)',
        '{quality}': 'Selected quality preset',
        '{source}': 'Source directory name',
        '{source_full}': 'Full source directory path'
    }
    
    def __init__(self):
        """Initialize the file manager"""
        self.counter = 1
    
    def get_safe_filename(self, filename: str) -> str:
        """Convert a filename to a safe version (remove invalid characters)"""
        # Replace invalid characters with underscore
        safe_name = re.sub(r'[\\/*?:"<>|]', '_', filename)
        # Remove leading/trailing whitespace and dots
        safe_name = safe_name.strip('. ')
        # Ensure filename is not empty
        if not safe_name:
            safe_name = 'unnamed_file'
        return safe_name
    
    def get_file_info(self, file_path: str) -> Dict:
        """Get file information for prefix placeholders"""
        try:
            file_path = Path(file_path)
            
            # Check if file exists first
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return self._get_default_file_info(file_path)
                
            stats = file_path.stat()
            
            # Basic file info
            filename = file_path.stem
            extension = file_path.suffix.lstrip('.')
            size_mb = round(stats.st_size / (1024 * 1024), 2)
            
            # Source directory info
            source_dir = file_path.parent
            source_dir_name = source_dir.name
            
            # Creation date
            try:
                create_date = datetime.datetime.fromtimestamp(stats.st_ctime)
                create_date_str = create_date.strftime('%Y-%m-%d')
            except Exception:
                create_date_str = datetime.datetime.now().strftime('%Y-%m-%d')
            
            # Current date/time
            now = datetime.datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H-%M-%S')
            datetime_str = now.strftime('%Y-%m-%d_%H-%M-%S')
            
            return {
                'filename': filename,
                'ext': extension,
                'date': date_str,
                'time': time_str,
                'datetime': datetime_str,
                'create_date': create_date_str,
                'size': str(size_mb),
                'counter': str(self.counter),
                'source': source_dir_name,
                'source_full': str(source_dir),
                # These will be populated later if video info is available
                'resolution': '',
                'codec': '',
                'duration': '',
                'quality': ''
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return self._get_default_file_info(file_path)
    
    def _get_default_file_info(self, file_path: Path) -> Dict:
        """Get default file information when file cannot be accessed"""
        return {
            'filename': file_path.stem,
            'ext': file_path.suffix.lstrip('.'),
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.datetime.now().strftime('%H-%M-%S'),
            'datetime': datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
            'create_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'size': '0',
            'counter': str(self.counter),
            'resolution': '',
            'codec': '',
            'duration': '',
            'quality': ''
        }
    
    def apply_prefix_template(self, template: str, file_path: str, 
                            video_info: Optional[Dict] = None,
                            quality: str = '') -> str:
        """Apply prefix template to generate output filename
        
        Args:
            template: Prefix template with placeholders
            file_path: Input file path
            video_info: Optional video information dictionary
            quality: Selected quality preset
            
        Returns:
            Formatted filename string
        """
        try:
            # Get basic file info
            info = self.get_file_info(file_path)
            
            # Add video-specific info if available
            if video_info:
                if 'width' in video_info and 'height' in video_info:
                    info['resolution'] = f"{video_info['width']}x{video_info['height']}"
                if 'codec' in video_info:
                    info['codec'] = video_info['codec']
                if 'duration' in video_info:
                    info['duration'] = str(round(video_info['duration'], 1))
            
            # Add quality info
            info['quality'] = quality
            
            # Apply template
            result = template
            for placeholder, value in info.items():
                result = result.replace(f"{{{placeholder}}}", str(value))
            
            # Increment counter for next use
            self.counter += 1
            
            # Ensure filename is safe
            return self.get_safe_filename(result)
        except Exception as e:
            logger.error(f"Error applying prefix template: {e}")
            # Fallback to safe filename
            return self.get_safe_filename(Path(file_path).stem)
    
    def generate_output_path(self, input_path: str, output_dir: str, 
                           prefix_template: str, output_format: str,
                           video_info: Optional[Dict] = None,
                           quality: str = '') -> str:
        """Generate complete output path based on prefix template
        
        Args:
            input_path: Input file path
            output_dir: Output directory
            prefix_template: Prefix template with placeholders
            output_format: Output file format (without dot)
            video_info: Optional video information
            quality: Selected quality preset
            
        Returns:
            Complete output file path
        """
        try:
            # Generate filename using template
            filename = self.apply_prefix_template(
                prefix_template, input_path, video_info, quality
            )
            
            # Ensure output format has no leading dot
            output_format = output_format.lstrip('.')
            
            # Combine with output directory and format
            output_path = os.path.join(output_dir, f"{filename}.{output_format}")
            
            # Handle filename conflicts
            counter = 1
            base_path = output_path
            while os.path.exists(output_path):
                name, ext = os.path.splitext(base_path)
                output_path = f"{name}_{counter}{ext}"
                counter += 1
            
            return output_path
        except Exception as e:
            logger.error(f"Error generating output path: {e}")
            # Fallback to basic output path
            safe_name = self.get_safe_filename(Path(input_path).stem)
            return os.path.join(output_dir, f"{safe_name}.{output_format.lstrip('.')}")
    
    def ensure_directory_exists(self, directory: str) -> bool:
        """Ensure the specified directory exists, create if necessary
        
        Args:
            directory: Directory path to check/create
            
        Returns:
            True if directory exists or was created, False on error
        """
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            return False
    
    def is_path_writable(self, path: str) -> bool:
        """Check if a path is writable
        
        Args:
            path: Path to check
            
        Returns:
            True if writable, False otherwise
        """
        if os.path.isdir(path):
            # Check if directory is writable
            try:
                test_file = os.path.join(path, '.write_test')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return True
            except Exception:
                return False
        else:
            # Check if parent directory is writable
            return self.is_path_writable(os.path.dirname(path))
    
    def get_available_placeholders(self) -> Dict[str, str]:
        """Get dictionary of available placeholders and their descriptions"""
        return self.PREFIX_PLACEHOLDERS.copy()


# Singleton instance
_file_manager_instance = None


def get_file_manager() -> FileManager:
    """Get or create the FileManager singleton instance"""
    global _file_manager_instance
    if _file_manager_instance is None:
        _file_manager_instance = FileManager()
    return _file_manager_instance


def scan_directory(self, directory_path: str, recursive: bool = False) -> List[str]:
    """Scan a directory for supported video files
    
    Args:
        directory_path: Directory to scan
        recursive: Whether to scan subdirectories
        
    Returns:
        List of file paths (sorted alphabetically)
    """
    try:
        if not os.path.isdir(directory_path):
            logger.error(f"Not a valid directory: {directory_path}")
            return []
            
        supported_files = []
        
        # Get supported extensions from VideoEncoder
        from .encoder import VideoEncoder
        encoder = VideoEncoder()
        
        if recursive:
            # Walk through all subdirectories
            for root, _, files in os.walk(directory_path):
                for file in sorted(files):  # Sort files alphabetically
                    file_path = os.path.join(root, file)
                    if encoder.is_supported_format(file_path):
                        supported_files.append(file_path)
        else:
            # Just scan the top directory
            for file in sorted(os.listdir(directory_path)):  # Sort files alphabetically
                file_path = os.path.join(directory_path, file)
                if os.path.isfile(file_path) and encoder.is_supported_format(file_path):
                    supported_files.append(file_path)
        
        return supported_files
    except Exception as e:
        logger.error(f"Error scanning directory: {e}", exc_info=True)
        return []