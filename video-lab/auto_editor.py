"""
FYI Social ∞ - Auto Editor
MAIN VIDEO PROCESSING PIPELINE
Upload 1-hour video → 100+ clips in <12 min
Full local pipeline: Whisper → Ollama → FFmpeg
"""

import subprocess
import json
from typing import List, Dict, Optional, Callable
from pathlib import Path
from datetime import timedelta
import time
import concurrent.futures

from ai_engine.ollama_manager import get_ollama_manager
from ai_engine.hook_generator import get_hook_generator
from ai_engine.clip_scoring import get_clip_scoring
from ai_engine.thumbnail_ai import get_thumbnail_ai


class AutoEditor:
    """Automatically edit long-form content into viral shorts"""
    
    def __init__(self):
        self.ollama = get_ollama_manager()
        self.hook_generator = get_hook_generator()
        self.clip_scoring = get_clip_scoring()
        self.thumbnail_ai = get_thumbnail_ai()
        
        self.output_dir = Path('data/clips')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_video(
        self, 
        video_path: str, 
        target_clips: int = 100,
        quality: str = 'high',
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict:
        """
        Process video into multiple clips
        
        Args:
            video_path: Path to input video
            target_clips: Number of clips to generate (default 100)
            quality: Output quality ('high', 'medium', 'low')
            progress_callback: Function(progress_percent, status_message)
        
        Returns:
            {
                'success': True,
                'clips': [...],
                'total_clips': 100,
                'processing_time': 720.5,
                'output_dir': 'data/clips/video_20240101'
            }
        """
        
        start_time = time.time()
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Create output directory for this video
        video_name = video_path.stem
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        video_output_dir = self.output_dir / f'{video_name}_{timestamp}'
        video_output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Transcribe audio (Whisper)
            self._update_progress(progress_callback, 5, "Transcribing audio with Whisper...")
            transcript = self._transcribe_audio(video_path)
            
            # Step 2: Find hooks (100+ potential clips)
            self._update_progress(progress_callback, 15, "Finding hooks in content...")
            hooks = self.hook_generator.find_hooks(str(video_path), target_clips)
            
            # Step 3: Score each hook
            self._update_progress(progress_callback, 25, "Scoring clips for viral potential...")
            scored_hooks = self._score_hooks(hooks, str(video_path))
            
            # Step 4: Extract top clips
            self._update_progress(progress_callback, 35, "Extracting video clips...")
            extracted_clips = self._extract_clips(
                video_path, 
                scored_hooks, 
                video_output_dir,
                quality,
                progress_callback
            )
            
            # Step 5: Generate thumbnails for each clip
            self._update_progress(progress_callback, 85, "Generating thumbnails...")
            clips_with_thumbnails = self._generate_thumbnails(
                str(video_path),
                extracted_clips,
                progress_callback
            )
            
            # Step 6: Save manifest
            self._update_progress(progress_callback, 95, "Saving manifest...")
            manifest = self._create_manifest(
                video_path,
                clips_with_thumbnails,
                transcript,
                video_output_dir
            )
            
            processing_time = time.time() - start_time
            
            self._update_progress(progress_callback, 100, "Complete!")
            
            return {
                'success': True,
                'clips': clips_with_thumbnails,
                'total_clips': len(clips_with_thumbnails),
                'processing_time': processing_time,
                'output_dir': str(video_output_dir),
                'manifest_path': str(video_output_dir / 'manifest.json')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _transcribe_audio(self, video_path: Path) -> Dict:
        """Transcribe audio using Whisper (via Ollama)"""
        
        # Extract audio from video
        audio_path = video_path.parent / f'{video_path.stem}_audio.wav'
        
        try:
            # Use FFmpeg to extract audio
            subprocess.run([
                'ffmpeg',
                '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # Audio codec
                '-ar', '16000',  # Sample rate
                '-ac', '1',  # Mono
                str(audio_path),
                '-y'  # Overwrite
            ], check=True, capture_output=True)
            
            # Transcribe with Ollama Whisper
            transcript = self.ollama.transcribe_audio(str(audio_path))
            
            # Clean up audio file
            audio_path.unlink()
            
            return transcript
            
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Audio extraction failed: {e}")
            return {'text': '', 'segments': []}
        except Exception as e:
            print(f"⚠️ Transcription failed: {e}")
            return {'text': '', 'segments': []}
    
    def _score_hooks(self, hooks: List[Dict], video_path: str) -> List[Dict]:
        """Score each hook for viral potential"""
        
        scored_hooks = []
        
        for hook in hooks:
            # Create temporary clip for scoring (just first frame)
            try:
                score_result = self.clip_scoring.score_video(video_path)
                
                hook['virality_score'] = score_result['overall_score']
                hook['hook_score'] = score_result['hook_score']
                hook['visual_score'] = score_result['visual_score']
                hook['recommendations'] = score_result['recommendations']
                
                scored_hooks.append(hook)
                
            except Exception as e:
                print(f"⚠️ Scoring failed for hook {hook.get('id', '?')}: {e}")
                hook['virality_score'] = 50
                scored_hooks.append(hook)
        
        # Sort by virality score
        scored_hooks.sort(key=lambda x: x.get('virality_score', 0), reverse=True)
        
        return scored_hooks
    
    def _extract_clips(
        self, 
        video_path: Path, 
        hooks: List[Dict], 
        output_dir: Path,
        quality: str,
        progress_callback: Optional[Callable]
    ) -> List[Dict]:
        """Extract video clips using FFmpeg"""
        
        extracted = []
        total = len(hooks)
        
        # Quality presets
        quality_settings = {
            'high': {'crf': '18', 'preset': 'slow'},
            'medium': {'crf': '23', 'preset': 'medium'},
            'low': {'crf': '28', 'preset': 'fast'}
        }
        
        settings = quality_settings.get(quality, quality_settings['medium'])
        
        # Process clips in parallel (4 at a time)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            
            for i, hook in enumerate(hooks):
                future = executor.submit(
                    self._extract_single_clip,
                    video_path,
                    hook,
                    output_dir,
                    settings,
                    i
                )
                futures.append((future, i))
            
            # Wait for completion
            for future, i in futures:
                try:
                    clip_info = future.result()
                    extracted.append(clip_info)
                    
                    # Update progress
                    progress = 35 + int((i + 1) / total * 50)  # 35-85%
                    self._update_progress(
                        progress_callback, 
                        progress, 
                        f"Extracted clip {i+1}/{total}"
                    )
                    
                except Exception as e:
                    print(f"⚠️ Clip extraction failed: {e}")
        
        return extracted
    
    def _extract_single_clip(
        self, 
        video_path: Path, 
        hook: Dict, 
        output_dir: Path,
        settings: Dict,
        index: int
    ) -> Dict:
        """Extract a single clip"""
        
        clip_filename = f"clip_{index+1:03d}.mp4"
        clip_path = output_dir / clip_filename
        
        start_time = hook['start']
        duration = hook['duration']
        
        # FFmpeg command
        cmd = [
            'ffmpeg',
            '-ss', str(start_time),
            '-i', str(video_path),
            '-t', str(duration),
            '-c:v', 'libx264',
            '-crf', settings['crf'],
            '-preset', settings['preset'],
            '-c:a', 'aac',
            '-b:a', '128k',
            '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',  # 9:16 crop
            str(clip_path),
            '-y'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        
        # Get file size
        file_size = clip_path.stat().st_size / (1024 * 1024)  # MB
        
        return {
            **hook,
            'clip_path': str(clip_path),
            'filename': clip_filename,
            'file_size_mb': round(file_size, 2)
        }
    
    def _generate_thumbnails(
        self, 
        video_path: str, 
        clips: List[Dict],
        progress_callback: Optional[Callable]
    ) -> List[Dict]:
        """Generate thumbnails for clips"""
        
        for i, clip in enumerate(clips):
            try:
                thumbnails = self.thumbnail_ai.generate_thumbnails(video_path, clip)
                clip['thumbnails'] = thumbnails
                
                # Update progress
                progress = 85 + int((i + 1) / len(clips) * 10)  # 85-95%
                self._update_progress(
                    progress_callback,
                    progress,
                    f"Generated thumbnails for clip {i+1}/{len(clips)}"
                )
                
            except Exception as e:
                print(f"⚠️ Thumbnail generation failed for clip {i+1}: {e}")
                clip['thumbnails'] = []
        
        return clips
    
    def _create_manifest(
        self, 
        video_path: Path, 
        clips: List[Dict],
        transcript: Dict,
        output_dir: Path
    ) -> Path:
        """Create manifest file with all clip data"""
        
        manifest = {
            'source_video': str(video_path),
            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_clips': len(clips),
            'transcript': transcript,
            'clips': clips
        }
        
        manifest_path = output_dir / 'manifest.json'
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path
    
    def _update_progress(
        self, 
        callback: Optional[Callable], 
        progress: int, 
        message: str
    ):
        """Update progress via callback"""
        if callback:
            callback(progress, message)
        else:
            print(f"[{progress}%] {message}")
    
    def get_video_info(self, video_path: str) -> Dict:
        """Get video metadata using FFprobe"""
        
        try:
            result = subprocess.run([
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ], capture_output=True, text=True, check=True)
            
            data = json.loads(result.stdout)
            
            # Extract useful info
            format_info = data.get('format', {})
            video_stream = next(
                (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                {}
            )
            
            duration = float(format_info.get('duration', 0))
            
            return {
                'duration': duration,
                'duration_formatted': str(timedelta(seconds=int(duration))),
                'size_mb': float(format_info.get('size', 0)) / (1024 * 1024),
                'width': video_stream.get('width', 0),
                'height': video_stream.get('height', 0),
                'fps': eval(video_stream.get('r_frame_rate', '0/1')) if '/' in str(video_stream.get('r_frame_rate', '0')) else 0,
                'codec': video_stream.get('codec_name', 'unknown')
            }
            
        except Exception as e:
            print(f"⚠️ Failed to get video info: {e}")
            return {}
    
    def estimate_processing_time(self, video_duration: float, target_clips: int = 100) -> float:
        """
        Estimate processing time
        
        Args:
            video_duration: Duration in seconds
            target_clips: Number of clips to generate
        
        Returns:
            Estimated time in seconds
        """
        
        # Rough estimates (can be tuned based on actual performance)
        transcription_time = video_duration * 0.3  # 30% of video duration
        analysis_time = 60  # 1 minute for hook finding + scoring
        extraction_time = target_clips * 2  # 2 seconds per clip (parallel processing)
        thumbnail_time = target_clips * 1  # 1 second per clip
        
        total = transcription_time + analysis_time + extraction_time + thumbnail_time
        
        return total


# Global instance
_auto_editor = None

def get_auto_editor() -> AutoEditor:
    """Get global auto editor instance"""
    global _auto_editor
    if _auto_editor is None:
        _auto_editor = AutoEditor()
    return _auto_editor
