#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Video Encoder Core Module
Handles video encoding, conversion, and compression operations
"""

import os
import sys
import logging
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

try:
    import ffmpeg
except ImportError:
    logging.error("ffmpeg-python module not found. Please install it with: pip install ffmpeg-python")

logger = logging.getLogger('video_encoder.core.encoder')


class VideoEncoder:
    """Handles video encoding operations using ffmpeg"""
    
    # Quality presets mapping
    QUALITY_PRESETS = {
        'very_low': {'crf': 35, 'preset': 'veryfast'},
        'low': {'crf': 28, 'preset': 'faster'},
        'medium': {'crf': 23, 'preset': 'medium'},
        'high': {'crf': 18, 'preset': 'slow'},
        'very_high': {'crf': 15, 'preset': 'veryslow'},
        # Standard resolution presets
        '144p': {'resolution': '256x144', 'crf': 28, 'preset': 'faster'},
        '240p': {'resolution': '426x240', 'crf': 26, 'preset': 'medium'},
        '360p': {'resolution': '640x360', 'crf': 24, 'preset': 'medium'},
        '480p': {'resolution': '854x480', 'crf': 22, 'preset': 'medium'},
        '720p': {'resolution': '1280x720', 'crf': 20, 'preset': 'medium'},
        '1080p': {'resolution': '1920x1080', 'crf': 18, 'preset': 'medium'},
        '1440p': {'resolution': '2560x1440', 'crf': 16, 'preset': 'slow'},
        '2160p': {'resolution': '3840x2160', 'crf': 15, 'preset': 'slow'}
    }
    
    # Supported input formats
    SUPPORTED_FORMATS = [
        '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
        '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2', '.mxf', '.ts'
    ]
    
    def __init__(self):
        """Initialize the encoder and verify ffmpeg installation"""
        self.ffmpeg_path = self._find_ffmpeg()
        if not self.ffmpeg_path:
            logger.warning("FFmpeg not found in PATH. Some features may not work correctly.")
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find ffmpeg executable in system PATH"""
        try:
            # Try to get ffmpeg version to check if it's installed
            result = subprocess.run(
                ['ffmpeg', '-version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if result.returncode == 0:
                return 'ffmpeg'
        except Exception as e:
            logger.debug(f"Error checking ffmpeg: {e}")
        
        # Try common installation paths
        common_paths = [
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffmpeg.exe')
        ]
        
        for path in common_paths:
            if os.path.isfile(path):
                return path
        
        return None
    
    def is_supported_format(self, file_path: str) -> bool:
        """Check if the file format is supported"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS
    
    def get_video_info(self, input_path: str) -> Dict:
        """Get video file information using ffprobe"""
        try:
            probe = ffmpeg.probe(input_path)
            video_info = next((stream for stream in probe['streams'] 
                              if stream['codec_type'] == 'video'), None)
            
            if not video_info:
                raise ValueError("No video stream found")
                
            return {
                'width': int(video_info.get('width', 0)),
                'height': int(video_info.get('height', 0)),
                'duration': float(probe.get('format', {}).get('duration', 0)),
                'bitrate': int(probe.get('format', {}).get('bit_rate', 0)),
                'size': int(probe.get('format', {}).get('size', 0)),
                'codec': video_info.get('codec_name', 'unknown'),
                'fps': self._parse_frame_rate(video_info.get('avg_frame_rate', '0/1'))
            }
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return {}
    
    def _parse_frame_rate(self, frame_rate_str: str) -> float:
        """Parse frame rate string (e.g. '24/1') to float"""
        try:
            if '/' in frame_rate_str:
                num, den = map(int, frame_rate_str.split('/'))
                return num / den if den else 0
            return float(frame_rate_str)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def convert_video(self, input_path: str, output_path: str, 
                      quality: str = 'medium', target_size: Optional[int] = None,
                      output_format: Optional[str] = None) -> Tuple[bool, str]:
        """Convert video with specified parameters
        
        Args:
            input_path: Path to input video file
            output_path: Path to save the output video
            quality: Quality preset (very_low, low, medium, high, very_high, 144p, 240p, etc.)
            target_size: Target file size in MB (if specified, overrides quality settings)
            output_format: Output format (if None, inferred from output_path)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            if not os.path.exists(input_path):
                return False, f"Input file does not exist: {input_path}"
            
            if not self.is_supported_format(input_path):
                return False, f"Unsupported input format: {os.path.splitext(input_path)[1]}"
            
            # Get quality settings
            quality_settings = self.QUALITY_PRESETS.get(quality, self.QUALITY_PRESETS['medium'])
            
            # Prepare output format
            if not output_format:
                output_format = os.path.splitext(output_path)[1].lstrip('.')
                if not output_format:
                    output_format = 'mp4'  # Default to mp4
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Start with base conversion
            stream = ffmpeg.input(input_path)
            
            # Apply encoding settings
            if target_size:
                # If target size specified, use two-pass encoding to achieve target size
                return self._encode_with_target_size(input_path, output_path, target_size, output_format, quality_settings)
            else:
                # Standard quality-based encoding
                video = stream.video.filter('fps', fps=self._get_optimal_fps(input_path))
                
                # Apply resolution if specified in quality preset
                if 'resolution' in quality_settings:
                    width, height = quality_settings['resolution'].split('x')
                    video = video.filter('scale', width, height)
                else:
                    # Just ensure even dimensions
                    video = video.filter('scale', 'trunc(iw/2)*2', 'trunc(ih/2)*2')
                
                # Apply encoding settings based on format
                if output_format in ['mp4', 'mkv', 'mov']:
                    stream = ffmpeg.output(
                        video,
                        stream.audio,
                        output_path,
                        vcodec='libx264',
                        crf=quality_settings['crf'],
                        preset=quality_settings['preset'],
                        acodec='aac',
                        audio_bitrate='128k'
                    )
                elif output_format == 'webm':
                    stream = ffmpeg.output(
                        video,
                        stream.audio,
                        output_path,
                        vcodec='libvpx-vp9',
                        crf=quality_settings['crf'],
                        preset=quality_settings['preset'],
                        acodec='libopus',
                        audio_bitrate='128k'
                    )
                else:
                    # Generic fallback
                    stream = ffmpeg.output(
                        stream.video,
                        stream.audio,
                        output_path,
                        preset=quality_settings['preset']
                    )
                
                # Run the conversion
                stream = stream.global_args('-y')  # Overwrite output files
                stream.run(capture_stdout=True, capture_stderr=True)
                
                return True, f"Successfully converted video to {output_path}"
                
        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
            logger.error(f"FFmpeg error: {error_message}")
            return False, f"FFmpeg error: {error_message}"
        except Exception as e:
            logger.error(f"Error converting video: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def _get_optimal_fps(self, input_path: str) -> int:
        """Get optimal FPS for the output based on input video"""
        try:
            info = self.get_video_info(input_path)
            original_fps = info.get('fps', 0)
            
            # Keep original FPS if it's reasonable
            if 20 <= original_fps <= 60:
                return original_fps
            elif original_fps > 60:
                return 60  # Cap at 60fps
            else:
                return 30  # Default to 30fps
        except Exception:
            return 30  # Default to 30fps on error
    
    def _encode_with_target_size(self, input_path: str, output_path: str, 
                               target_size_mb: int, output_format: str,
                               quality_settings: Dict = None) -> Tuple[bool, str]:
        """Encode video targeting a specific file size using two-pass encoding"""
        try:
            if quality_settings is None:
                quality_settings = self.QUALITY_PRESETS['medium']
                
            # Get video info
            info = self.get_video_info(input_path)
            duration = info.get('duration', 0)
            
            if duration <= 0:
                return False, "Could not determine video duration"
            
            # Calculate target bitrate (bits per second)
            # Leave ~5% for container overhead
            target_size_bits = target_size_mb * 8 * 1024 * 1024 * 0.95
            audio_bitrate_bits = 128 * 1024  # 128k audio
            video_bitrate = int((target_size_bits / duration) - audio_bitrate_bits)
            
            if video_bitrate <= 0:
                return False, "Target size too small for this video duration"
            
            # Create temporary directory for pass logs
            with tempfile.TemporaryDirectory() as temp_dir:
                pass_log_file = os.path.join(temp_dir, "ffmpeg2pass")
                
                # First pass
                stream = ffmpeg.input(input_path)
                video = stream.video.filter('fps', fps=self._get_optimal_fps(input_path))
                
                # Apply resolution if specified in quality preset
                if 'resolution' in quality_settings:
                    width, height = quality_settings['resolution'].split('x')
                    video = video.filter('scale', width, height)
                else:
                    video = video.filter('scale', 'trunc(iw/2)*2', 'trunc(ih/2)*2')
                
                # First pass - analyze only, no audio
                if output_format in ['mp4', 'mkv', 'mov']:
                    first_pass = ffmpeg.output(
                        video,
                        None,  # No audio in first pass
                        os.devnull,  # Output to nowhere
                        vcodec='libx264',
                        b=f'{video_bitrate}',
                        pass_=1,
                        f='null',
                        **{'passlogfile': pass_log_file}
                    )
                elif output_format == 'webm':
                    first_pass = ffmpeg.output(
                        video,
                        None,  # No audio in first pass
                        os.devnull,  # Output to nowhere
                        vcodec='libvpx-vp9',
                        b=f'{video_bitrate}',
                        pass_=1,
                        f='null',
                        **{'passlogfile': pass_log_file}
                    )
                else:
                    # Generic fallback
                    first_pass = ffmpeg.output(
                        video,
                        None,  # No audio in first pass
                        os.devnull,  # Output to nowhere
                        b=f'{video_bitrate}',
                        pass_=1,
                        f='null',
                        **{'passlogfile': pass_log_file}
                    )
                
                # Run first pass
                try:
                    first_pass.global_args('-y').run(capture_stdout=True, capture_stderr=True)
                except ffmpeg.Error as e:
                    error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
                    logger.error(f"First pass encoding error: {error_message}")
                    return False, f"First pass encoding error: {error_message}"
                
                # Second pass - with audio
                stream = ffmpeg.input(input_path)
                video = stream.video.filter('fps', fps=self._get_optimal_fps(input_path))
                
                # Apply resolution if specified in quality preset
                if 'resolution' in quality_settings:
                    width, height = quality_settings['resolution'].split('x')
                    video = video.filter('scale', width, height)
                else:
                    video = video.filter('scale', 'trunc(iw/2)*2', 'trunc(ih/2)*2')
                
                # Second pass with audio
                if output_format in ['mp4', 'mkv', 'mov']:
                    second_pass = ffmpeg.output(
                        video,
                        stream.audio,
                        output_path,
                        vcodec='libx264',
                        b=f'{video_bitrate}',
                        pass_=2,
                        acodec='aac',
                        audio_bitrate='128k',
                        **{'passlogfile': pass_log_file}
                    )
                elif output_format == 'webm':
                    second_pass = ffmpeg.output(
                        video,
                        stream.audio,
                        output_path,
                        vcodec='libvpx-vp9',
                        b=f'{video_bitrate}',
                        pass_=2,
                        acodec='libopus',
                        audio_bitrate='128k',
                        **{'passlogfile': pass_log_file}
                    )
                else:
                    # Generic fallback
                    second_pass = ffmpeg.output(
                        video,
                        stream.audio,
                        output_path,
                        b=f'{video_bitrate}',
                        pass_=2,
                        **{'passlogfile': pass_log_file}
                    )
                
                # Run second pass
                try:
                    second_pass.global_args('-y').run(capture_stdout=True, capture_stderr=True)
                    return True, f"Successfully converted video to {output_path} with target size {target_size_mb}MB"
                except ffmpeg.Error as e:
                    error_message = e.stderr.decode() if hasattr(e, 'stderr') else str(e)
                    logger.error(f"Second pass encoding error: {error_message}")
                    return False, f"Second pass encoding error: {error_message}"
                
        except Exception as e:
            logger.error(f"Error in target size encoding: {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def batch_convert(self, input_files: List[str], output_dir: str, 
                     quality: str = 'medium', output_format: str = 'mp4',
                     target_size: Optional[int] = None,
                     prefix_template: str = "{filename}") -> List[Dict]:
        """Convert multiple videos with the same settings
        
        Args:
            input_files: List of input video file paths
            output_dir: Directory to save output videos
            quality: Quality preset
            output_format: Output format
            target_size: Target file size in MB (if specified)
            prefix_template: Template for output filename
            
        Returns:
            List of dictionaries with conversion results
        """
        results = []
        
        for input_path in input_files:
            try:
                if not os.path.exists(input_path):
                    results.append({
                        'input': input_path,
                        'success': False,
                        'message': f"Input file does not exist"
                    })
                    continue
                
                # Generate output filename using prefix template
                try:
                    from .file_manager import FileManager
                    file_manager = FileManager()
                    
                    # Get video info for template
                    video_info = self.get_video_info(input_path)
                    
                    # Apply template - directly use the template string
                    # This allows for custom templates like "{filename} {quality}"
                    filename = file_manager.apply_prefix_template(
                        prefix_template, input_path, video_info, quality
                    )
                    
                    # Add extension
                    output_filename = f"{filename}.{output_format.lstrip('.')}"
                    output_path = os.path.join(output_dir, output_filename)
                except Exception as e:
                    logger.error(f"Error applying filename template: {e}", exc_info=True)
                    # Fallback to basic filename
                    filename = os.path.basename(input_path)
                    name, _ = os.path.splitext(filename)
                    output_filename = f"{name}.{output_format.lstrip('.')}"
                    output_path = os.path.join(output_dir, output_filename)
                
                # Convert the video
                success, message = self.convert_video(
                    input_path, output_path, quality, target_size, output_format
                )
                
                results.append({
                    'input': input_path,
                    'output': output_path if success else None,
                    'success': success,
                    'message': message
                })
                
            except Exception as e:
                logger.error(f"Error in batch conversion for {input_path}: {e}", exc_info=True)
                results.append({
                    'input': input_path,
                    'success': False,
                    'message': f"Error: {str(e)}"
                })
        
        return results


# Singleton instance
_encoder_instance = None


def get_encoder() -> VideoEncoder:
    """Get or create the VideoEncoder singleton instance"""
    global _encoder_instance
    if _encoder_instance is None:
        _encoder_instance = VideoEncoder()
    return _encoder_instance