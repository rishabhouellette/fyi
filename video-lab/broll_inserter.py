"""
FYI Social ∞ - B-Roll Inserter
Automatically inserts B-roll footage from Pexels + user library
Detects keywords → Finds relevant stock → Inserts seamlessly
"""

import subprocess
import requests
from typing import List, Dict, Optional
from pathlib import Path
import json
import random


class BRollInserter:
    """Insert B-roll footage into videos"""
    
    def __init__(self):
        self.output_dir = Path('data/broll')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.library_dir = Path('data/library/broll')
        self.library_dir.mkdir(parents=True, exist_ok=True)
        
        # Pexels API (free tier)
        self.pexels_api_key = None  # User can set this
        self.pexels_base_url = 'https://api.pexels.com/v1'
    
    def set_pexels_api_key(self, api_key: str):
        """Set Pexels API key for stock footage"""
        self.pexels_api_key = api_key
    
    def add_broll(
        self,
        video_path: str,
        transcript: Dict,
        broll_frequency: float = 0.3,  # 30% of video will have B-roll
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Add B-roll to video based on keywords in transcript
        
        Args:
            video_path: Input video path
            transcript: Transcript with timestamps
            broll_frequency: Percentage of video to cover with B-roll (0-1)
            output_path: Output path (auto-generated if None)
        
        Returns:
            {
                'success': True,
                'output_path': 'path/to/video_with_broll.mp4',
                'broll_count': 5,
                'broll_segments': [...]
            }
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Extract keywords from transcript
        keywords = self._extract_keywords(transcript)
        
        # Find B-roll opportunities
        broll_segments = self._identify_broll_points(transcript, keywords, broll_frequency)
        
        # Get B-roll footage for each segment
        broll_clips = self._get_broll_clips(broll_segments)
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_with_broll.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Insert B-roll using FFmpeg
            self._insert_broll_ffmpeg(video_path, broll_clips, output_path)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'broll_count': len(broll_clips),
                'broll_segments': broll_clips
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def add_user_library_broll(
        self,
        video_path: str,
        broll_mappings: List[Dict],
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Add B-roll from user's library with manual mappings
        
        Args:
            video_path: Input video path
            broll_mappings: List of {start, end, broll_file} mappings
            output_path: Output path
        
        Returns:
            Result dict
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Validate B-roll files exist
        validated_mappings = []
        for mapping in broll_mappings:
            broll_file = Path(mapping['broll_file'])
            
            if not broll_file.exists():
                print(f"⚠️ B-roll file not found: {broll_file}")
                continue
            
            validated_mappings.append({
                'start': mapping['start'],
                'end': mapping['end'],
                'broll_path': str(broll_file),
                'duration': mapping['end'] - mapping['start']
            })
        
        if not validated_mappings:
            return {'success': False, 'error': 'No valid B-roll files found'}
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_with_broll.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Insert B-roll
            self._insert_broll_ffmpeg(video_path, validated_mappings, output_path)
            
            return {
                'success': True,
                'output_path': str(output_path),
                'broll_count': len(validated_mappings)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_keywords(self, transcript: Dict) -> List[str]:
        """Extract keywords from transcript"""
        
        # Common filler words to ignore
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'this', 'that', 'these', 'those'
        }
        
        text = transcript.get('text', '')
        words = text.lower().split()
        
        # Extract meaningful keywords
        keywords = []
        for word in words:
            # Remove punctuation
            word = word.strip('.,!?;:"\'')
            
            # Skip if stop word or too short
            if word in stop_words or len(word) < 4:
                continue
            
            if word not in keywords:
                keywords.append(word)
        
        return keywords[:20]  # Top 20 keywords
    
    def _identify_broll_points(
        self, 
        transcript: Dict, 
        keywords: List[str],
        frequency: float
    ) -> List[Dict]:
        """Identify where to insert B-roll"""
        
        segments = transcript.get('segments', [])
        
        if not segments:
            return []
        
        broll_points = []
        
        for segment in segments:
            text = segment.get('text', '').lower()
            start = segment.get('start', 0)
            end = segment.get('end', start + 3)
            
            # Check if segment contains keywords
            for keyword in keywords:
                if keyword in text:
                    broll_points.append({
                        'start': start,
                        'end': end,
                        'keyword': keyword,
                        'text': segment.get('text', '')
                    })
                    break  # One B-roll per segment
        
        # Limit by frequency
        target_count = int(len(segments) * frequency)
        
        if len(broll_points) > target_count:
            # Select random subset
            random.shuffle(broll_points)
            broll_points = broll_points[:target_count]
        
        return broll_points
    
    def _get_broll_clips(self, segments: List[Dict]) -> List[Dict]:
        """Get B-roll clips for segments"""
        
        clips = []
        
        for segment in segments:
            keyword = segment['keyword']
            duration = segment['end'] - segment['start']
            
            # Try user library first
            library_clip = self._find_in_library(keyword)
            
            if library_clip:
                clips.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'broll_path': library_clip,
                    'keyword': keyword,
                    'source': 'library',
                    'duration': duration
                })
            elif self.pexels_api_key:
                # Try Pexels
                pexels_clip = self._download_from_pexels(keyword, duration)
                
                if pexels_clip:
                    clips.append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'broll_path': pexels_clip,
                        'keyword': keyword,
                        'source': 'pexels',
                        'duration': duration
                    })
            else:
                print(f"⚠️ No B-roll found for keyword: {keyword}")
        
        return clips
    
    def _find_in_library(self, keyword: str) -> Optional[str]:
        """Find matching B-roll in user's library"""
        
        if not self.library_dir.exists():
            return None
        
        # Search for files with keyword in name
        for file in self.library_dir.glob('*.mp4'):
            if keyword.lower() in file.stem.lower():
                return str(file)
        
        return None
    
    def _download_from_pexels(self, keyword: str, duration: float) -> Optional[str]:
        """Download B-roll from Pexels"""
        
        if not self.pexels_api_key:
            return None
        
        try:
            # Search for videos
            headers = {'Authorization': self.pexels_api_key}
            
            response = requests.get(
                f'{self.pexels_base_url}/videos/search',
                headers=headers,
                params={
                    'query': keyword,
                    'per_page': 5,
                    'orientation': 'portrait'  # For vertical videos
                },
                timeout=10
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            videos = data.get('videos', [])
            
            if not videos:
                return None
            
            # Pick first video
            video = videos[0]
            
            # Get video file (prefer HD)
            video_files = video.get('video_files', [])
            
            if not video_files:
                return None
            
            # Find best quality
            hd_file = next(
                (vf for vf in video_files if vf.get('quality') == 'hd'),
                video_files[0]
            )
            
            video_url = hd_file.get('link')
            
            if not video_url:
                return None
            
            # Download video
            video_response = requests.get(video_url, timeout=30)
            
            if video_response.status_code != 200:
                return None
            
            # Save to temp directory
            temp_dir = Path('data/temp/broll')
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{keyword}_{video['id']}.mp4"
            filepath = temp_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(video_response.content)
            
            return str(filepath)
            
        except Exception as e:
            print(f"⚠️ Pexels download failed: {e}")
            return None
    
    def _insert_broll_ffmpeg(
        self,
        video_path: Path,
        broll_clips: List[Dict],
        output_path: Path
    ):
        """Insert B-roll clips using FFmpeg"""
        
        if not broll_clips:
            # No B-roll, just copy video
            subprocess.run([
                'ffmpeg',
                '-i', str(video_path),
                '-c', 'copy',
                str(output_path),
                '-y'
            ], check=True, capture_output=True)
            return
        
        # Create filter_complex for overlaying B-roll
        # This is complex - for now, just do picture-in-picture overlay
        
        # Build filter complex
        filter_parts = []
        
        for i, clip in enumerate(broll_clips):
            # Scale B-roll to fit
            filter_parts.append(f"[{i+1}:v]scale=1080:1920,setpts=PTS-STARTPTS[broll{i}]")
        
        # Overlay B-rolls at specified times
        overlay_chain = "[0:v]"
        
        for i, clip in enumerate(broll_clips):
            start = clip['start']
            duration = clip['duration']
            
            overlay_chain += f"[broll{i}]overlay=enable='between(t,{start},{start+duration})':x=0:y=0"
            
            if i < len(broll_clips) - 1:
                overlay_chain += f"[tmp{i}];[tmp{i}]"
        
        filter_complex = ';'.join(filter_parts) + ';' + overlay_chain
        
        # Build FFmpeg command
        inputs = ['-i', str(video_path)]
        
        for clip in broll_clips:
            inputs.extend(['-i', clip['broll_path']])
        
        cmd = [
            'ffmpeg',
            *inputs,
            '-filter_complex', filter_complex,
            '-c:a', 'copy',
            str(output_path),
            '-y'
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)


# Global instance
_broll_inserter = None

def get_broll_inserter() -> BRollInserter:
    """Get global B-roll inserter instance"""
    global _broll_inserter
    if _broll_inserter is None:
        _broll_inserter = BRollInserter()
    return _broll_inserter
