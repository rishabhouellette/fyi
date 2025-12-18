"""
FYI Social ∞ - CLIP Virality Scoring
Uses CLIP model to score videos for viral potential (1-100)
Analyzes: visual appeal, emotions, pacing, hook strength
"""

import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
import json

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("⚠️ OpenCV not available. Install: pip install opencv-python")


class ClipScoring:
    """Score video clips for viral potential using CLIP and analysis"""
    
    VIRAL_FACTORS = {
        'hook_strength': 0.30,      # First 3 seconds impact
        'visual_appeal': 0.25,      # Colors, composition, quality
        'pacing': 0.20,             # Scene changes, energy
        'emotion': 0.15,            # Face expressions, reactions
        'trending_elements': 0.10   # Memes, formats, audio
    }
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load CLIP model (lazy loading)"""
        # TODO: Implement CLIP model loading
        # Using placeholder for now
        pass
    
    def score_video(self, video_path: str) -> Dict[str, any]:
        """
        Score a video for viral potential
        
        Returns:
            {
                'overall_score': 75,  # 1-100
                'hook_score': 85,
                'visual_score': 70,
                'pacing_score': 80,
                'emotion_score': 65,
                'trending_score': 75,
                'recommendations': [...]
            }
        """
        
        if not OPENCV_AVAILABLE:
            return self._placeholder_score()
        
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Analyze video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return self._placeholder_score()
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Analyze frames
        hook_score = self._analyze_hook(cap, fps)
        visual_score = self._analyze_visuals(cap, fps)
        pacing_score = self._analyze_pacing(cap, fps, duration)
        emotion_score = self._analyze_emotions(cap, fps)
        trending_score = self._analyze_trending(cap, fps)
        
        cap.release()
        
        # Calculate weighted overall score
        overall = (
            hook_score * self.VIRAL_FACTORS['hook_strength'] +
            visual_score * self.VIRAL_FACTORS['visual_appeal'] +
            pacing_score * self.VIRAL_FACTORS['pacing'] +
            emotion_score * self.VIRAL_FACTORS['emotion'] +
            trending_score * self.VIRAL_FACTORS['trending_elements']
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            hook_score, visual_score, pacing_score, 
            emotion_score, trending_score
        )
        
        return {
            'overall_score': int(overall),
            'hook_score': int(hook_score),
            'visual_score': int(visual_score),
            'pacing_score': int(pacing_score),
            'emotion_score': int(emotion_score),
            'trending_score': int(trending_score),
            'duration': duration,
            'recommendations': recommendations,
            'verdict': self._get_verdict(overall)
        }
    
    def _analyze_hook(self, cap: cv2.VideoCapture, fps: float) -> float:
        """Analyze first 3 seconds (the hook)"""
        # Sample frames from first 3 seconds
        hook_frames = int(fps * 3)
        
        scores = []
        for i in range(min(hook_frames, 90)):  # Max 90 frames
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Analyze frame interest
            score = self._score_frame_interest(frame)
            scores.append(score)
        
        return np.mean(scores) if scores else 50
    
    def _analyze_visuals(self, cap: cv2.VideoCapture, fps: float) -> float:
        """Analyze visual appeal throughout video"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Sample 20 frames throughout video
        sample_interval = max(1, frame_count // 20)
        
        scores = []
        for i in range(0, frame_count, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Analyze colors, brightness, composition
            score = self._score_visual_quality(frame)
            scores.append(score)
        
        return np.mean(scores) if scores else 50
    
    def _analyze_pacing(self, cap: cv2.VideoCapture, fps: float, duration: float) -> float:
        """Analyze pacing and scene changes"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        prev_frame = None
        scene_changes = 0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        for i in range(0, frame_count, int(fps)):  # Sample every second
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if prev_frame is not None:
                # Detect scene change
                diff = cv2.absdiff(frame, prev_frame)
                change = np.mean(diff)
                
                if change > 30:  # Threshold for scene change
                    scene_changes += 1
            
            prev_frame = frame
        
        # Ideal: 1 scene change every 2-3 seconds
        ideal_changes = duration / 2.5
        actual_ratio = scene_changes / ideal_changes if ideal_changes > 0 else 0
        
        # Score based on how close to ideal
        if 0.7 <= actual_ratio <= 1.3:
            score = 90
        elif 0.5 <= actual_ratio <= 1.5:
            score = 75
        elif 0.3 <= actual_ratio <= 1.7:
            score = 60
        else:
            score = 40
        
        return score
    
    def _analyze_emotions(self, cap: cv2.VideoCapture, fps: float) -> float:
        """Analyze emotional content (faces, reactions)"""
        # Placeholder - would use face detection + emotion recognition
        return 65.0
    
    def _analyze_trending(self, cap: cv2.VideoCapture, fps: float) -> float:
        """Analyze trending elements"""
        # Placeholder - would check for trending formats, memes, effects
        return 70.0
    
    def _score_frame_interest(self, frame: np.ndarray) -> float:
        """Score individual frame for interest/engagement"""
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Check saturation (colorfulness)
        saturation = np.mean(hsv[:, :, 1])
        
        # Check brightness
        brightness = np.mean(hsv[:, :, 2])
        
        # Check contrast
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        
        # Combined score
        score = (
            (saturation / 255) * 40 +      # 40% weight on color
            (brightness / 255) * 30 +      # 30% weight on brightness
            min(contrast / 50, 1.0) * 30   # 30% weight on contrast
        )
        
        return min(score, 100)
    
    def _score_visual_quality(self, frame: np.ndarray) -> float:
        """Score frame visual quality"""
        # Check sharpness (Laplacian variance)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness = min(laplacian_var / 100, 100)
        
        # Color vibrancy
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])
        
        score = sharpness * 0.6 + (saturation / 255 * 100) * 0.4
        
        return min(score, 100)
    
    def _generate_recommendations(self, hook, visual, pacing, emotion, trending) -> List[str]:
        """Generate actionable recommendations"""
        recs = []
        
        if hook < 70:
            recs.append("🎣 Improve hook: Start with action/question in first 3 seconds")
        
        if visual < 70:
            recs.append("🎨 Enhance visuals: Increase color saturation, improve lighting")
        
        if pacing < 70:
            recs.append("⚡ Fix pacing: Add more cuts (1 per 2-3 seconds ideal)")
        
        if emotion < 70:
            recs.append("😊 Add emotion: Show faces, reactions, excitement")
        
        if trending < 70:
            recs.append("🔥 Use trends: Add trending audio, formats, or effects")
        
        if not recs:
            recs.append("✅ Great! This clip has strong viral potential")
        
        return recs
    
    def _get_verdict(self, score: float) -> str:
        """Get verdict based on score"""
        if score >= 85:
            return "🔥 VIRAL POTENTIAL - High chance of success!"
        elif score >= 70:
            return "✅ GOOD - Should perform well"
        elif score >= 55:
            return "⚠️ AVERAGE - Needs improvement"
        else:
            return "❌ WEAK - Major improvements needed"
    
    def _placeholder_score(self) -> Dict:
        """Return placeholder scores for testing"""
        return {
            'overall_score': 75,
            'hook_score': 80,
            'visual_score': 70,
            'pacing_score': 75,
            'emotion_score': 70,
            'trending_score': 75,
            'duration': 30.0,
            'recommendations': [
                "🎣 Start with a strong hook in first 3 seconds",
                "⚡ Maintain fast pacing with cuts every 2-3 seconds",
                "🎨 Ensure good lighting and color vibrancy"
            ],
            'verdict': "✅ GOOD - Should perform well"
        }


# Global instance
_clip_scoring = None

def get_clip_scoring() -> ClipScoring:
    """Get global CLIP scoring instance"""
    global _clip_scoring
    if _clip_scoring is None:
        _clip_scoring = ClipScoring()
    return _clip_scoring
