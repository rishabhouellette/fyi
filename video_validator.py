"""
Video validation for different platforms
"""
from pathlib import Path
from typing import Tuple, Optional, Dict
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    
from logger_config import get_logger

logger = get_logger(__name__)

class VideoValidator:
    """Validate videos before upload"""
    
    # Platform-specific limits
    LIMITS = {
        'facebook': {
            'max_size_mb': 10240,  # 10GB
            'max_duration_sec': 7200,  # 2 hours
            'min_duration_sec': 1,
            'supported_formats': ['.mp4', '.mov', '.avi'],
        },
        'instagram': {
            'max_size_mb': 350,
            'max_duration_sec': 90,  # Reels limit
            'min_duration_sec': 3,
            'supported_formats': ['.mp4', '.mov'],
            'aspect_ratio_range': (0.5, 0.6),  # 9:16 with tolerance
        },
        'youtube': {
            'max_size_mb': 256000,  # 256GB (but practically limited)
            'max_duration_sec': 43200,  # 12 hours
            'min_duration_sec': 1,
            'supported_formats': ['.mp4', '.mov', '.avi', '.wmv', '.flv', '.mkv'],
        }
    }
    
    @staticmethod
    def validate(video_path: str, platform: str) -> Tuple[bool, Optional[str]]:
        """
        Validate video for platform
        
        Args:
            video_path: Path to video file
            platform: Target platform (facebook/instagram/youtube)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(video_path)
        
        # Check file exists
        if not path.exists():
            return False, "Video file not found"
        
        platform = platform.lower()
        if platform not in VideoValidator.LIMITS:
            return False, f"Unknown platform: {platform}"
        
        limits = VideoValidator.LIMITS[platform]
        
        # Check file format
        if path.suffix.lower() not in limits['supported_formats']:
            return False, f"Unsupported format: {path.suffix}. Supported: {', '.join(limits['supported_formats'])}"
        
        # Check file size
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > limits['max_size_mb']:
            return False, f"File too large: {size_mb:.1f}MB (max: {limits['max_size_mb']}MB)"
        
        if size_mb == 0:
            return False, "File is empty"
        
        # Check video properties with OpenCV if available
        if OPENCV_AVAILABLE:
            try:
                cap = cv2.VideoCapture(str(path))
                if not cap.isOpened():
                    return False, "Could not open video file"
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                duration = frame_count / fps if fps > 0 else 0
                
                cap.release()
                
                # Duration check
                if duration < limits['min_duration_sec']:
                    return False, f"Video too short: {duration:.1f}s (min: {limits['min_duration_sec']}s)"
                if duration > limits['max_duration_sec']:
                    return False, f"Video too long: {duration:.1f}s (max: {limits['max_duration_sec']}s)"
                
                # Resolution check
                if width == 0 or height == 0:
                    return False, "Invalid video resolution"
                
                # Instagram-specific aspect ratio check
                if platform == 'instagram' and 'aspect_ratio_range' in limits:
                    aspect = width / height if height > 0 else 0
                    min_aspect, max_aspect = limits['aspect_ratio_range']
                    
                    if not (min_aspect <= aspect <= max_aspect):
                        return False, (
                            f"Invalid aspect ratio for Instagram Reels: {width}x{height} ({aspect:.2f}). "
                            f"Required: Vertical video (9:16 ≈ 0.56)"
                        )
                
                logger.info(f"✓ Video validated: {path.name} | {width}x{height} | {duration:.1f}s | {size_mb:.1f}MB")
                
            except Exception as e:
                logger.warning(f"OpenCV validation failed, skipping detailed checks: {e}")
        
        return True, None
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict:
        """
        Get detailed video information
        
        Args:
            video_path: Path to video file
        
        Returns:
            Dictionary with video properties
        """
        path = Path(video_path)
        info = {
            'filename': path.name,
            'size_mb': path.stat().st_size / (1024 * 1024),
            'format': path.suffix,
            'path': str(path),
        }
        
        if OPENCV_AVAILABLE:
            try:
                cap = cv2.VideoCapture(str(path))
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    
                    info.update({
                        'width': width,
                        'height': height,
                        'fps': fps,
                        'frame_count': int(frame_count),
                        'duration_sec': frame_count / fps if fps > 0 else 0,
                        'aspect_ratio': width / height if height > 0 else 0,
                    })
                    cap.release()
            except Exception as e:
                logger.warning(f"Could not read video properties: {e}")
        
        return info
