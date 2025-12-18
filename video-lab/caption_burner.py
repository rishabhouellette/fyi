"""
FYI Social ∞ - Caption Burner
Burns captions into video with viral styles
Supports: word-by-word highlighting, animations, custom fonts
"""

import subprocess
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import textwrap


class CaptionStyle:
    """Caption styling presets"""
    
    ALEX_HORMOZI = {
        'name': 'Alex Hormozi',
        'font': 'Arial-Bold',
        'font_size': 80,
        'color': 'white',
        'bg_color': 'black@0.7',
        'position': 'center',
        'animation': 'word_highlight',
        'highlight_color': 'yellow'
    }
    
    MRBEAST = {
        'name': 'MrBeast',
        'font': 'Impact',
        'font_size': 90,
        'color': 'yellow',
        'outline_color': 'black',
        'outline_width': 4,
        'position': 'center',
        'animation': 'bounce',
        'shadow': True
    }
    
    ALI_ABDAAL = {
        'name': 'Ali Abdaal',
        'font': 'Helvetica',
        'font_size': 60,
        'color': 'white',
        'bg_color': 'black@0.5',
        'position': 'bottom',
        'animation': 'fade',
        'clean': True
    }
    
    MINIMALIST = {
        'name': 'Minimalist',
        'font': 'Helvetica-Light',
        'font_size': 50,
        'color': 'white',
        'position': 'bottom_center',
        'animation': 'none',
        'clean': True
    }


class CaptionBurner:
    """Burn captions into videos with animations"""
    
    def __init__(self):
        self.output_dir = Path('data/captioned')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def add_captions(
        self,
        video_path: str,
        transcript: Dict,
        style: str = 'alex_hormozi',
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Add captions to video
        
        Args:
            video_path: Input video path
            transcript: Transcript data with timestamps
            style: Caption style name
            output_path: Output path (auto-generated if None)
        
        Returns:
            {
                'success': True,
                'output_path': 'path/to/captioned.mp4',
                'style': 'alex_hormozi'
            }
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Get style
        style_config = self._get_style(style)
        
        # Generate subtitle file
        srt_path = self._create_srt(transcript, video_path.stem)
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_captioned.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Burn captions using FFmpeg
            self._burn_captions_ffmpeg(video_path, srt_path, output_path, style_config)
            
            # Clean up SRT file
            srt_path.unlink()
            
            return {
                'success': True,
                'output_path': str(output_path),
                'style': style
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_word_by_word_captions(
        self,
        video_path: str,
        transcript: Dict,
        style: str = 'alex_hormozi',
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Add word-by-word animated captions (karaoke style)
        
        This creates more engaging captions that highlight each word as it's spoken
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Get style
        style_config = self._get_style(style)
        
        # Create word-level subtitle file
        ass_path = self._create_ass_word_by_word(transcript, video_path.stem, style_config)
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_captioned.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Burn captions using FFmpeg with ASS subtitles
            self._burn_captions_ass(video_path, ass_path, output_path)
            
            # Clean up ASS file
            ass_path.unlink()
            
            return {
                'success': True,
                'output_path': str(output_path),
                'style': f'{style} (word-by-word)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_style(self, style_name: str) -> Dict:
        """Get style configuration"""
        
        styles = {
            'alex_hormozi': CaptionStyle.ALEX_HORMOZI,
            'mrbeast': CaptionStyle.MRBEAST,
            'ali_abdaal': CaptionStyle.ALI_ABDAAL,
            'minimalist': CaptionStyle.MINIMALIST
        }
        
        return styles.get(style_name.lower(), CaptionStyle.ALEX_HORMOZI)
    
    def _create_srt(self, transcript: Dict, video_name: str) -> Path:
        """Create SRT subtitle file"""
        
        srt_path = Path(f'data/temp/{video_name}.srt')
        srt_path.parent.mkdir(parents=True, exist_ok=True)
        
        segments = transcript.get('segments', [])
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                start = segment.get('start', 0)
                end = segment.get('end', start + 3)
                text = segment.get('text', '').strip()
                
                if not text:
                    continue
                
                # Format timestamps
                start_time = self._format_srt_time(start)
                end_time = self._format_srt_time(end)
                
                # Wrap text
                wrapped = textwrap.fill(text, width=40)
                
                # Write subtitle entry
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{wrapped}\n\n")
        
        return srt_path
    
    def _create_ass_word_by_word(
        self, 
        transcript: Dict, 
        video_name: str,
        style: Dict
    ) -> Path:
        """Create ASS subtitle file with word-by-word highlighting"""
        
        ass_path = Path(f'data/temp/{video_name}.ass')
        ass_path.parent.mkdir(parents=True, exist_ok=True)
        
        # ASS header
        header = f"""[Script Info]
Title: {video_name}
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style.get('font', 'Arial')},{style.get('font_size', 80)},&H00FFFFFF,&H00FFFF00,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(header)
            
            segments = transcript.get('segments', [])
            
            for segment in segments:
                start = segment.get('start', 0)
                text = segment.get('text', '').strip()
                words = text.split()
                
                if not words:
                    continue
                
                # Estimate word timing
                segment_duration = segment.get('end', start + 3) - start
                word_duration = segment_duration / len(words)
                
                # Create word-by-word entries
                for i, word in enumerate(words):
                    word_start = start + (i * word_duration)
                    word_end = word_start + word_duration
                    
                    start_time = self._format_ass_time(word_start)
                    end_time = self._format_ass_time(word_end)
                    
                    # Create karaoke effect
                    f.write(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{{\\k{int(word_duration*100)}}}{word}\\N\n")
        
        return ass_path
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format time for SRT (00:00:00,000)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _format_ass_time(self, seconds: float) -> str:
        """Format time for ASS (0:00:00.00)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        return f"{hours}:{minutes:02d}:{secs:05.2f}"
    
    def _burn_captions_ffmpeg(
        self,
        video_path: Path,
        srt_path: Path,
        output_path: Path,
        style: Dict
    ):
        """Burn captions using FFmpeg subtitles filter"""
        
        # Build subtitles filter
        font_size = style.get('font_size', 80)
        font_color = style.get('color', 'white')
        outline_color = style.get('outline_color', 'black')
        
        # Position
        position = style.get('position', 'center')
        if position == 'bottom':
            alignment = 2  # Bottom center
        elif position == 'center':
            alignment = 5  # Center
        else:
            alignment = 2
        
        subtitle_filter = f"subtitles={srt_path}:force_style='Fontsize={font_size},PrimaryColour=&H{self._color_to_ass(font_color)},OutlineColour=&H{self._color_to_ass(outline_color)},Outline=3,Alignment={alignment}'"
        
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def _burn_captions_ass(self, video_path: Path, ass_path: Path, output_path: Path):
        """Burn ASS subtitles with advanced styling"""
        
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vf', f"ass={ass_path}",
            '-c:a', 'copy',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
    
    def _color_to_ass(self, color: str) -> str:
        """Convert color name to ASS format"""
        
        colors = {
            'white': 'FFFFFF',
            'black': '000000',
            'yellow': '00FFFF',
            'red': '0000FF',
            'blue': 'FF0000',
            'green': '00FF00'
        }
        
        return colors.get(color.lower(), 'FFFFFF')


# Global instance
_caption_burner = None

def get_caption_burner() -> CaptionBurner:
    """Get global caption burner instance"""
    global _caption_burner
    if _caption_burner is None:
        _caption_burner = CaptionBurner()
    return _caption_burner
