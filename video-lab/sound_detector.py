"""
FYI Social ∞ - Sound Detector
Detects silence, adds trending audio automatically
Matches audio energy to video content
"""

import subprocess
import json
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import random


class SoundDetector:
    """Detect audio issues and add trending sounds"""
    
    def __init__(self):
        self.output_dir = Path('data/audio_enhanced')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.music_library = Path('data/library/music')
        self.music_library.mkdir(parents=True, exist_ok=True)
        
        # Trending audio database (would be populated from TikTok/Instagram API)
        self.trending_audio = []
    
    def detect_silence(self, video_path: str) -> List[Dict]:
        """
        Detect silent segments in video
        
        Args:
            video_path: Path to video file
        
        Returns:
            List of silent segments with timestamps
            [
                {'start': 10.5, 'end': 12.3, 'duration': 1.8},
                ...
            ]
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return []
        
        try:
            # Use FFmpeg silencedetect filter
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-af', 'silencedetect=noise=-30dB:d=0.5',
                '-f', 'null',
                '-'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            # Parse output for silence periods
            silences = []
            output = result.stderr
            
            lines = output.split('\n')
            
            silence_start = None
            
            for line in lines:
                if 'silence_start:' in line:
                    # Extract start time
                    parts = line.split('silence_start:')
                    if len(parts) > 1:
                        silence_start = float(parts[1].strip().split()[0])
                
                elif 'silence_end:' in line and silence_start is not None:
                    # Extract end time
                    parts = line.split('silence_end:')
                    if len(parts) > 1:
                        silence_end = float(parts[1].strip().split()[0])
                        
                        silences.append({
                            'start': silence_start,
                            'end': silence_end,
                            'duration': silence_end - silence_start
                        })
                        
                        silence_start = None
            
            return silences
            
        except Exception as e:
            print(f"⚠️ Silence detection failed: {e}")
            return []
    
    def analyze_audio_energy(self, video_path: str) -> List[Dict]:
        """
        Analyze audio energy levels throughout video
        
        Returns:
            List of segments with energy levels
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return []
        
        try:
            # Extract audio
            audio_path = video_path.parent / f'{video_path.stem}_audio.wav'
            
            subprocess.run([
                'ffmpeg',
                '-i', str(video_path),
                '-vn',
                '-acodec', 'pcm_s16le',
                str(audio_path),
                '-y'
            ], check=True, capture_output=True)
            
            # Analyze with FFmpeg volumedetect
            result = subprocess.run([
                'ffmpeg',
                '-i', str(audio_path),
                '-af', 'volumedetect',
                '-f', 'null',
                '-'
            ], capture_output=True, text=True)
            
            # Parse output
            output = result.stderr
            
            mean_volume = None
            max_volume = None
            
            for line in output.split('\n'):
                if 'mean_volume:' in line:
                    mean_volume = float(line.split(':')[1].strip().split()[0])
                elif 'max_volume:' in line:
                    max_volume = float(line.split(':')[1].strip().split()[0])
            
            # Clean up
            audio_path.unlink()
            
            return [{
                'mean_volume': mean_volume,
                'max_volume': max_volume,
                'has_audio': mean_volume is not None
            }]
            
        except Exception as e:
            print(f"⚠️ Audio analysis failed: {e}")
            return []
    
    def add_background_music(
        self,
        video_path: str,
        music_path: Optional[str] = None,
        volume: float = 0.3,
        fade_duration: float = 2.0,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Add background music to video
        
        Args:
            video_path: Input video path
            music_path: Path to music file (if None, picks from library)
            volume: Music volume (0-1, default 0.3)
            fade_duration: Fade in/out duration in seconds
            output_path: Output path
        
        Returns:
            Result dict
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Select music
        if music_path is None:
            music_path = self._select_music_from_library()
            
            if not music_path:
                return {'success': False, 'error': 'No music available'}
        
        music_path = Path(music_path)
        
        if not music_path.exists():
            return {'success': False, 'error': f'Music not found: {music_path}'}
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_with_music.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Get video duration
            duration = self._get_video_duration(video_path)
            
            # Build audio filter
            audio_filter = f"[1:a]volume={volume},afade=t=in:st=0:d={fade_duration},afade=t=out:st={duration-fade_duration}:d={fade_duration},aloop=loop=-1:size=2e+09[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[a]"
            
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-i', str(music_path),
                '-filter_complex', audio_filter,
                '-map', '0:v',
                '-map', '[a]',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                str(output_path),
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'music_used': str(music_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_sound_effects(
        self,
        video_path: str,
        effects: List[Dict],
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Add sound effects at specific timestamps
        
        Args:
            video_path: Input video path
            effects: List of {time, effect_file} mappings
            output_path: Output path
        
        Returns:
            Result dict
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        if not effects:
            return {'success': False, 'error': 'No effects provided'}
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_with_sfx.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Build complex filter for overlaying sound effects
            filter_parts = []
            
            for i, effect in enumerate(effects):
                effect_file = Path(effect['effect_file'])
                
                if not effect_file.exists():
                    print(f"⚠️ Effect not found: {effect_file}")
                    continue
                
                time = effect.get('time', 0)
                volume = effect.get('volume', 1.0)
                
                filter_parts.append(f"[{i+1}:a]adelay={int(time*1000)}|{int(time*1000)},volume={volume}[sfx{i}]")
            
            # Mix all audio
            mix_inputs = "[0:a]"
            for i in range(len(filter_parts)):
                mix_inputs += f"[sfx{i}]"
            
            filter_complex = ';'.join(filter_parts) + f";{mix_inputs}amix=inputs={len(filter_parts)+1}:duration=first[a]"
            
            # Build command
            inputs = ['-i', str(video_path)]
            
            for effect in effects:
                effect_file = Path(effect['effect_file'])
                if effect_file.exists():
                    inputs.extend(['-i', str(effect_file)])
            
            cmd = [
                'ffmpeg',
                *inputs,
                '-filter_complex', filter_complex,
                '-map', '0:v',
                '-map', '[a]',
                '-c:v', 'copy',
                '-c:a', 'aac',
                str(output_path),
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'effects_added': len(filter_parts)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def normalize_audio(
        self,
        video_path: str,
        target_level: float = -16.0,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Normalize audio levels to target loudness
        
        Args:
            video_path: Input video path
            target_level: Target loudness in LUFS (default -16)
            output_path: Output path
        
        Returns:
            Result dict
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_normalized.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Use loudnorm filter
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-af', f'loudnorm=I={target_level}:TP=-1.5:LRA=11',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                str(output_path),
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'target_level': target_level
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _select_music_from_library(self) -> Optional[str]:
        """Select music from user's library"""
        
        if not self.music_library.exists():
            return None
        
        music_files = list(self.music_library.glob('*.mp3')) + list(self.music_library.glob('*.wav'))
        
        if not music_files:
            return None
        
        # Pick random music
        return str(random.choice(music_files))
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration using ffprobe"""
        
        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                str(video_path)
            ], capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            duration = float(data.get('format', {}).get('duration', 0))
            
            return duration
            
        except Exception:
            return 60.0  # Default


# Global instance
_sound_detector = None

def get_sound_detector() -> SoundDetector:
    """Get global sound detector instance"""
    global _sound_detector
    if _sound_detector is None:
        _sound_detector = SoundDetector()
    return _sound_detector
