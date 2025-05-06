#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Language Manager Module
Handles language file loading with preference for US English
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger('video_encoder.config.language_manager')

class LanguageManager:
    """Manages language files with preference for US English"""
    
    def __init__(self, languages_dir=None):
        """Initialize the language manager
        
        Args:
            languages_dir: Directory containing language files (default: config/languages)
        """
        if languages_dir is None:
            # Default to the directory where this file is located
            languages_dir = Path(__file__).parent
        
        self.languages_dir = Path(languages_dir)
        self.language_data = {}
        self.loaded_language = None
    
    def get_available_languages(self):
        """Get list of available language files
        
        Returns:
            Dictionary of language codes and their file paths
        """
        languages = {}
        
        try:
            for file in self.languages_dir.glob('*.json'):
                lang_code = file.stem
                languages[lang_code] = str(file)
        except Exception as e:
            logger.error(f"Error scanning language files: {e}")
        
        return languages
    
    def load_language(self, lang_code='en'):
        """Load language file with preference for US English
        
        Args:
            lang_code: Language code to load (default: en)
            
        Returns:
            True if language was loaded successfully, False otherwise
        """
        try:
            # Check if we have a US English file
            us_file = self.languages_dir / 'us.json'
            en_file = self.languages_dir / 'en.json'
            
            # Priority: 1. us.json, 2. en.json (converted to US), 3. Requested language
            if us_file.exists():
                # Use US English file if it exists
                with open(us_file, 'r', encoding='utf-8') as f:
                    self.language_data = json.load(f)
                self.loaded_language = 'us'
                logger.info(f"Loaded US English language file")
                return True
            elif en_file.exists():
                # Use English file if it exists (treat as US)
                with open(en_file, 'r', encoding='utf-8') as f:
                    self.language_data = json.load(f)
                self.loaded_language = 'us'  # Treat as US
                logger.info(f"Loaded English language file (treating as US)")
                return True
            else:
                # Try to load requested language
                lang_file = self.languages_dir / f"{lang_code}.json"
                if lang_file.exists():
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.language_data = json.load(f)
                    self.loaded_language = lang_code
                    logger.info(f"Loaded {lang_code} language file")
                    return True
                else:
                    logger.warning(f"Language file for {lang_code} not found")
                    return False
        except Exception as e:
            logger.error(f"Error loading language file: {e}")
            return False
    
    def get_text(self, key, default=None):
        """Get translated text for a key
        
        Args:
            key: Translation key
            default: Default text if key not found
            
        Returns:
            Translated text or default
        """
        if not self.language_data:
            # Load default language if none loaded
            self.load_language()
        
        # Return text from loaded language
        return self.language_data.get(key, default if default is not None else key)
    
    def create_us_from_en(self):
        """Create a US English file from English file if it doesn't exist
        
        Returns:
            True if US file was created or already exists, False on error
        """
        try:
            us_file = self.languages_dir / 'us.json'
            en_file = self.languages_dir / 'en.json'
            
            # If US file already exists, nothing to do
            if us_file.exists():
                return True
            
            # If English file exists, copy it to US
            if en_file.exists():
                with open(en_file, 'r', encoding='utf-8') as f:
                    en_data = json.load(f)
                
                with open(us_file, 'w', encoding='utf-8') as f:
                    json.dump(en_data, f, indent=4)
                
                logger.info("Created US English file from English file")
                return True
            else:
                logger.warning("English file not found, cannot create US file")
                return False
        except Exception as e:
            logger.error(f"Error creating US English file: {e}")
            return False


# Singleton instance
_language_manager_instance = None

def get_language_manager():
    """Get or create the LanguageManager singleton instance"""
    global _language_manager_instance
    if _language_manager_instance is None:
        _language_manager_instance = LanguageManager()
    return _language_manager_instance