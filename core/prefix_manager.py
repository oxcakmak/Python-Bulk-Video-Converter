#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Prefix Manager Module
Handles prefix logic for file naming in the video encoder application
"""

import os
import re
import logging
import datetime
from typing import Dict, List, Optional, Tuple, Union
from .file_manager import get_file_manager

logger = logging.getLogger('video_encoder.core.prefix_manager')


class PrefixManager:
    """Manages prefix templates and their application for output filenames"""
    
    # Default prefix templates
    DEFAULT_TEMPLATES = {
        'simple': '{filename}',
        'with_quality': '{filename}_{quality}',
        'with_date': '{filename}_{date}',
        'with_datetime': '{filename}_{datetime}',
        'with_resolution': '{filename}_{resolution}',
        'with_source': '{source}_{filename}',
        'source_quality': '{source}_{filename}_{quality}',
        'detailed': '{filename}_{quality}_{resolution}_{date}',
        'full': '{filename}_{quality}_{resolution}_{codec}_{datetime}'
    }
    
    def __init__(self):
        """Initialize the prefix manager"""
        self.file_manager = get_file_manager()
        self.custom_templates = {}
        self.load_custom_templates()
    
    def load_custom_templates(self):
        """Load custom templates from settings (placeholder for future implementation)"""
        # This would load from settings in a real implementation
        pass
    
    def save_custom_template(self, name: str, template: str) -> bool:
        """Save a custom template
        
        Args:
            name: Template name
            template: Template string with placeholders
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate template
            if not self.validate_template(template):
                logger.warning(f"Invalid template format: {template}")
                return False
            
            # Save template
            self.custom_templates[name] = template
            # This would save to settings in a real implementation
            return True
        except Exception as e:
            logger.error(f"Error saving custom template: {e}")
            return False
    
    def delete_custom_template(self, name: str) -> bool:
        """Delete a custom template
        
        Args:
            name: Template name to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if name in self.custom_templates:
                del self.custom_templates[name]
                # This would save to settings in a real implementation
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting custom template: {e}")
            return False
    
    def get_all_templates(self) -> Dict[str, str]:
        """Get all available templates (default + custom)
        
        Returns:
            Dictionary of template names and their format strings
        """
        # Combine default and custom templates
        all_templates = {}
        all_templates.update(self.DEFAULT_TEMPLATES)
        all_templates.update(self.custom_templates)
        return all_templates
    
    def validate_template(self, template: str) -> bool:
        """Validate a template string
        
        Args:
            template: Template string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check if template is empty
            if not template or not template.strip():
                return False
            
            # Check for invalid characters in template
            if re.search(r'[\\/*?:"<>|]', template):
                return False
            
            # Check for valid placeholders
            placeholders = re.findall(r'\{([^\}]+)\}', template)
            valid_placeholders = self.file_manager.get_available_placeholders().keys()
            valid_placeholders = [p.strip('{}') for p in valid_placeholders]
            
            for placeholder in placeholders:
                if placeholder not in valid_placeholders:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating template: {e}")
            return False
    
    def apply_template(self, template_name: str, file_path: str, 
                      video_info: Optional[Dict] = None,
                      quality: str = '') -> str:
        """Apply a named template to generate an output filename
        
        Args:
            template_name: Name of the template to use
            file_path: Input file path
            video_info: Optional video information dictionary
            quality: Selected quality preset
            
        Returns:
            Formatted filename string
        """
        try:
            # Get all templates
            templates = self.get_all_templates()
            
            # Check if template exists
            if template_name not in templates:
                logger.warning(f"Template '{template_name}' not found, using 'simple'")
                template_name = 'simple'
            
            # Get template string
            template = templates[template_name]
            
            # Apply template
            return self.file_manager.apply_prefix_template(
                template, file_path, video_info, quality
            )
        except Exception as e:
            logger.error(f"Error applying template: {e}")
            # Fallback to simple template
            return self.file_manager.apply_prefix_template(
                '{filename}', file_path, video_info, quality
            )
    
    def get_available_placeholders(self) -> Dict[str, str]:
        """Get dictionary of available placeholders and their descriptions"""
        return self.file_manager.get_available_placeholders()


# Singleton instance
_prefix_manager_instance = None


def get_prefix_manager() -> PrefixManager:
    """Get or create the PrefixManager singleton instance"""
    global _prefix_manager_instance
    if _prefix_manager_instance is None:
        _prefix_manager_instance = PrefixManager()
    return _prefix_manager_instance