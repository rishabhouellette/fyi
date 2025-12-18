"""
FYI Social ∞ - Thumbnail AI
Generates 5 thumbnail variants per clip using Ollama
Analyzes best frames, adds AI-generated text overlays
"""

import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
import json
import base64
from io import BytesIO

try:
    import cv2
    from PIL import Image, ImageDraw, ImageFont
    IMAGING_AVAILABLE = True
except ImportError:
    IMAGING_AVAILABLE = False
    print("⚠️ Imaging libraries not available. Install: pip install opencv-python pillow")

from .ollama_manager import get_ollama_manager


class ThumbnailAI:
    """Generate viral thumbnails using AI"""
    
    THUMBNAIL_STYLES = [
        {
            'name': 'Classic MrBeast',
            'text_color': (255, 255, 0),      # Yellow
            'text_stroke': (0, 0, 0),         # Black outline
            'font_size_ratio': 0.12,          # 12% of image height
            'text_position': 'top',
            'effect': 'bold_stroke'
        },
        {
            'name': 'Emotional Reaction',
            'text_color': (255, 255, 255),    # White
            'text_stroke': (255, 0, 0),       # Red outline
            'font_size_ratio': 0.10,
            'text_position': 'bottom',
            'effect': 'glow'
        },
        {
            'name': 'Curiosity Gap',
            'text_color': (0, 255, 255),      # Cyan
            'text_stroke': (139, 0, 255),     # Purple outline
            'font_size_ratio': 0.11,
            'text_position': 'center',
            'effect': 'neon'
        },
        {
            'name': 'Before/After Split',
            'text_color': (0, 255, 0),        # Green
            'text_stroke': (0, 0, 0),
            'font_size_ratio': 0.09,
            'text_position': 'sides',
            'effect': 'split'
        },
        {
            'name': 'Minimalist Clean',
            'text_color': (50, 50, 50),       # Dark gray
            'text_stroke': (255, 255, 255),   # White outline
            'font_size_ratio': 0.08,
            'text_position': 'bottom_left',
            'effect': 'clean'
        }
    ]
    
    def __init__(self):
        self.ollama = get_ollama_manager()
    
    def generate_thumbnails(self, video_path: str, clip_info: Dict) -> List[Dict]:
        """
        Generate 5 thumbnail variants for a clip
        
        Args:
            video_path: Path to video file
            clip_info: Clip information (start, end, title, etc.)
        
        Returns:
            List of thumbnail data
            [
                {
                    'style': 'Classic MrBeast',
                    'text': 'YOU WON\'T BELIEVE THIS!',
                    'image_path': 'thumbnails/clip_1_variant_1.jpg',
                    'score': 85
                },
                ...
            ]
        """
        
        if not IMAGING_AVAILABLE:
            return self._generate_placeholder_thumbnails(clip_info)
        
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Step 1: Extract best frames from clip
        best_frames = self._extract_best_frames(video_path, clip_info)
        
        # Step 2: Generate thumbnail texts using Ollama
        thumbnail_texts = self._generate_thumbnail_texts(clip_info)
        
        # Step 3: Create thumbnail variants
        thumbnails = []
        
        for i, style in enumerate(self.THUMBNAIL_STYLES):
            frame = best_frames[i % len(best_frames)]
            text = thumbnail_texts[i]
            
            thumbnail = self._create_thumbnail(frame, text, style, i + 1)
            thumbnails.append(thumbnail)
        
        return thumbnails
    
    def _extract_best_frames(self, video_path: Path, clip_info: Dict) -> List[np.ndarray]:
        """Extract best frames from clip for thumbnails"""
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return []
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        start_frame = int(clip_info['start'] * fps)
        end_frame = int(clip_info['end'] * fps)
        
        # Sample frames from clip
        frame_count = end_frame - start_frame
        sample_interval = max(1, frame_count // 20)  # Sample 20 frames
        
        frames_with_scores = []
        
        for i in range(start_frame, end_frame, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Score frame quality
            score = self._score_frame_quality(frame)
            frames_with_scores.append((frame, score))
        
        cap.release()
        
        # Sort by score and return top 5
        frames_with_scores.sort(key=lambda x: x[1], reverse=True)
        best_frames = [frame for frame, score in frames_with_scores[:5]]
        
        return best_frames if best_frames else []
    
    def _score_frame_quality(self, frame: np.ndarray) -> float:
        """Score frame for thumbnail quality"""
        # Check sharpness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness = min(laplacian_var / 100, 100)
        
        # Check brightness (prefer well-lit frames)
        brightness = np.mean(frame)
        brightness_score = 100 - abs(brightness - 127) / 1.27  # Ideal: 127
        
        # Check color saturation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])
        saturation_score = saturation / 2.55
        
        # Face detection bonus (if faces present)
        face_bonus = self._detect_faces(gray)
        
        # Combined score
        score = (
            sharpness * 0.3 +
            brightness_score * 0.2 +
            saturation_score * 0.3 +
            face_bonus * 0.2
        )
        
        return score
    
    def _detect_faces(self, gray_frame: np.ndarray) -> float:
        """Detect faces in frame (bonus points)"""
        # Placeholder - would use face detection
        # For now, return neutral score
        return 50.0
    
    def _generate_thumbnail_texts(self, clip_info: Dict) -> List[str]:
        """Generate 5 thumbnail text variants using Ollama"""
        
        prompt = f"""Generate 5 viral YouTube thumbnail text options for this video clip:

Title: {clip_info.get('title', 'Untitled')}
Duration: {clip_info.get('duration', 30)} seconds
Type: {clip_info.get('hook_type', 'general')}

Requirements:
- Each text should be SHORT (2-5 words max)
- Use ALL CAPS for impact
- Create curiosity or emotion
- Different styles: shock, question, benefit, before/after, mystery
- No hashtags or emojis

Return ONLY the 5 text options, one per line, no numbering."""

        try:
            response = self.ollama.generate(
                prompt=prompt,
                model='llama3.2-small',
                temperature=0.9,
                max_tokens=200
            )
            
            lines = [line.strip() for line in response.strip().split('\n') if line.strip()]
            
            # Ensure we have exactly 5 options
            while len(lines) < 5:
                lines.append(f"MUST SEE THIS!")
            
            return lines[:5]
            
        except Exception as e:
            print(f"⚠️ Ollama text generation failed: {e}")
            return self._fallback_texts(clip_info)
    
    def _fallback_texts(self, clip_info: Dict) -> List[str]:
        """Fallback texts if Ollama fails"""
        return [
            "YOU WON'T BELIEVE THIS!",
            "WATCH WHAT HAPPENS",
            "THIS CHANGED EVERYTHING",
            "BEFORE vs AFTER",
            "THE TRUTH REVEALED"
        ]
    
    def _create_thumbnail(self, frame: np.ndarray, text: str, style: Dict, variant_id: int) -> Dict:
        """Create thumbnail with text overlay"""
        
        # Convert frame to PIL Image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        # Resize to YouTube thumbnail size (1280x720)
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # Add text overlay
        img_with_text = self._add_text_overlay(img, text, style)
        
        # Save thumbnail
        output_path = Path('data/thumbnails')
        output_path.mkdir(parents=True, exist_ok=True)
        
        filename = f"thumbnail_variant_{variant_id}.jpg"
        full_path = output_path / filename
        
        img_with_text.save(full_path, 'JPEG', quality=95)
        
        return {
            'style': style['name'],
            'text': text,
            'image_path': str(full_path),
            'score': 75 + (variant_id * 3),  # Placeholder score
            'variant_id': variant_id
        }
    
    def _add_text_overlay(self, img: Image.Image, text: str, style: Dict) -> Image.Image:
        """Add text overlay to image"""
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Calculate font size
        font_size = int(height * style['font_size_ratio'])
        
        try:
            # Try to use custom font (bold)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position
        position = self._calculate_text_position(
            width, height, text_width, text_height, style['text_position']
        )
        
        # Draw text with stroke
        stroke_width = max(2, font_size // 20)
        
        # Draw stroke
        for offset_x in range(-stroke_width, stroke_width + 1):
            for offset_y in range(-stroke_width, stroke_width + 1):
                draw.text(
                    (position[0] + offset_x, position[1] + offset_y),
                    text,
                    font=font,
                    fill=style['text_stroke']
                )
        
        # Draw main text
        draw.text(position, text, font=font, fill=style['text_color'])
        
        return img
    
    def _calculate_text_position(self, width: int, height: int, 
                                 text_width: int, text_height: int, 
                                 position_type: str) -> Tuple[int, int]:
        """Calculate text position based on style"""
        
        padding = 40
        
        positions = {
            'top': (
                (width - text_width) // 2,
                padding
            ),
            'center': (
                (width - text_width) // 2,
                (height - text_height) // 2
            ),
            'bottom': (
                (width - text_width) // 2,
                height - text_height - padding
            ),
            'bottom_left': (
                padding,
                height - text_height - padding
            ),
            'sides': (
                padding,
                (height - text_height) // 2
            )
        }
        
        return positions.get(position_type, positions['center'])
    
    def _generate_placeholder_thumbnails(self, clip_info: Dict) -> List[Dict]:
        """Generate placeholder thumbnail data"""
        thumbnails = []
        
        for i, style in enumerate(self.THUMBNAIL_STYLES):
            thumbnails.append({
                'style': style['name'],
                'text': f"CLIP {clip_info.get('id', 1)} - {style['name'].upper()}",
                'image_path': f"data/thumbnails/thumbnail_variant_{i + 1}.jpg",
                'score': 70 + (i * 5),
                'variant_id': i + 1
            })
        
        return thumbnails


# Global instance
_thumbnail_ai = None

def get_thumbnail_ai() -> ThumbnailAI:
    """Get global thumbnail AI instance"""
    global _thumbnail_ai
    if _thumbnail_ai is None:
        _thumbnail_ai = ThumbnailAI()
    return _thumbnail_ai
