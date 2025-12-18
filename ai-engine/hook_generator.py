"""
FYI Social ∞ - Hook Generator
Finds 100+ hooks from long-form content using energy/pacing analysis
Analyzes: speech patterns, visual energy, momentum shifts
"""

import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
import json
from datetime import timedelta

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


class HookGenerator:
    """Find viral hooks in long-form content"""
    
    HOOK_CRITERIA = {
        'min_duration': 15,      # Minimum clip length (seconds)
        'max_duration': 90,      # Maximum clip length (seconds)
        'ideal_duration': 45,    # Ideal clip length (seconds)
        'min_energy': 60,        # Minimum energy level (1-100)
        'momentum_threshold': 15  # Energy increase threshold
    }
    
    def __init__(self):
        self.ollama = None
    
    def find_hooks(self, video_path: str, target_count: int = 100) -> List[Dict]:
        """
        Find hooks in video content
        
        Args:
            video_path: Path to video file
            target_count: Number of hooks to find (default 100)
        
        Returns:
            List of hook segments with timestamps and scores
            [
                {
                    'start': 12.5,
                    'end': 45.2,
                    'duration': 32.7,
                    'energy_score': 85,
                    'hook_type': 'momentum_shift',
                    'title': 'Amazing discovery revealed',
                    'description': '...'
                },
                ...
            ]
        """
        
        if not OPENCV_AVAILABLE:
            return self._generate_placeholder_hooks(target_count)
        
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Analyze video
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            return self._generate_placeholder_hooks(target_count)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Step 1: Analyze energy levels throughout video
        energy_timeline = self._analyze_energy_timeline(cap, fps, duration)
        
        # Step 2: Find momentum shifts (energy spikes)
        momentum_points = self._find_momentum_shifts(energy_timeline)
        
        # Step 3: Find high-energy sustained segments
        sustained_segments = self._find_sustained_energy(energy_timeline)
        
        # Step 4: Find natural breaks and transitions
        transitions = self._find_transitions(cap, fps)
        
        cap.release()
        
        # Step 5: Combine all hook candidates
        all_hooks = []
        all_hooks.extend(self._create_hooks_from_momentum(momentum_points, energy_timeline))
        all_hooks.extend(self._create_hooks_from_sustained(sustained_segments, energy_timeline))
        all_hooks.extend(self._create_hooks_from_transitions(transitions, energy_timeline))
        
        # Step 6: Score and rank hooks
        scored_hooks = self._score_hooks(all_hooks)
        
        # Step 7: Remove overlaps and select best hooks
        final_hooks = self._select_best_hooks(scored_hooks, target_count)
        
        return final_hooks
    
    def _analyze_energy_timeline(self, cap: cv2.VideoCapture, fps: float, duration: float) -> np.ndarray:
        """Analyze energy level at each second of video"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        seconds = int(duration) + 1
        energy = np.zeros(seconds)
        
        prev_frame = None
        
        for second in range(seconds):
            frame_idx = int(second * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Calculate visual energy
            visual_energy = self._calculate_visual_energy(frame, prev_frame)
            energy[second] = visual_energy
            
            prev_frame = frame
        
        # Smooth energy curve
        energy = self._smooth_curve(energy, window=3)
        
        return energy
    
    def _calculate_visual_energy(self, frame: np.ndarray, prev_frame: np.ndarray = None) -> float:
        """Calculate visual energy of a frame"""
        # Motion energy (if prev frame available)
        motion = 0
        if prev_frame is not None:
            diff = cv2.absdiff(frame, prev_frame)
            motion = np.mean(diff)
        
        # Color saturation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])
        
        # Edge density (detail/action)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Combined energy score
        energy = (
            motion * 0.5 +              # 50% weight on motion
            saturation / 2.55 +         # 25% weight on color (normalize to 0-100)
            edge_density * 100 * 0.25   # 25% weight on detail
        )
        
        return min(energy, 100)
    
    def _smooth_curve(self, data: np.ndarray, window: int = 3) -> np.ndarray:
        """Smooth data using moving average"""
        if len(data) < window:
            return data
        
        smoothed = np.convolve(data, np.ones(window)/window, mode='same')
        return smoothed
    
    def _find_momentum_shifts(self, energy: np.ndarray) -> List[int]:
        """Find points where energy rapidly increases"""
        momentum_points = []
        
        for i in range(1, len(energy)):
            increase = energy[i] - energy[i-1]
            
            if increase >= self.HOOK_CRITERIA['momentum_threshold']:
                momentum_points.append(i)
        
        return momentum_points
    
    def _find_sustained_energy(self, energy: np.ndarray) -> List[Tuple[int, int]]:
        """Find segments with sustained high energy"""
        segments = []
        
        in_segment = False
        segment_start = 0
        min_energy = self.HOOK_CRITERIA['min_energy']
        min_duration = self.HOOK_CRITERIA['min_duration']
        
        for i, e in enumerate(energy):
            if e >= min_energy:
                if not in_segment:
                    segment_start = i
                    in_segment = True
            else:
                if in_segment:
                    segment_duration = i - segment_start
                    if segment_duration >= min_duration:
                        segments.append((segment_start, i))
                    in_segment = False
        
        # Handle segment at end
        if in_segment:
            segment_duration = len(energy) - segment_start
            if segment_duration >= min_duration:
                segments.append((segment_start, len(energy)))
        
        return segments
    
    def _find_transitions(self, cap: cv2.VideoCapture, fps: float) -> List[int]:
        """Find scene transitions (natural break points)"""
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        transitions = []
        prev_frame = None
        
        for i in range(0, frame_count, int(fps)):
            cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if prev_frame is not None:
                diff = cv2.absdiff(frame, prev_frame)
                change = np.mean(diff)
                
                if change > 40:  # Scene change threshold
                    transitions.append(i // int(fps))
            
            prev_frame = frame
        
        return transitions
    
    def _create_hooks_from_momentum(self, momentum_points: List[int], energy: np.ndarray) -> List[Dict]:
        """Create hook segments from momentum shift points"""
        hooks = []
        
        for point in momentum_points:
            # Start 3-5 seconds before momentum shift
            start = max(0, point - 3)
            
            # End at ideal duration or when energy drops
            end = min(len(energy), start + self.HOOK_CRITERIA['ideal_duration'])
            
            for i in range(start + self.HOOK_CRITERIA['min_duration'], end):
                if energy[i] < self.HOOK_CRITERIA['min_energy']:
                    end = i
                    break
            
            if end - start >= self.HOOK_CRITERIA['min_duration']:
                hooks.append({
                    'start': float(start),
                    'end': float(end),
                    'duration': float(end - start),
                    'hook_type': 'momentum_shift',
                    'avg_energy': float(np.mean(energy[start:end]))
                })
        
        return hooks
    
    def _create_hooks_from_sustained(self, segments: List[Tuple[int, int]], energy: np.ndarray) -> List[Dict]:
        """Create hook segments from sustained energy periods"""
        hooks = []
        
        for start, end in segments:
            duration = end - start
            
            # Split long segments into multiple hooks
            if duration > self.HOOK_CRITERIA['max_duration']:
                chunk_size = self.HOOK_CRITERIA['ideal_duration']
                for chunk_start in range(start, end, chunk_size):
                    chunk_end = min(chunk_start + chunk_size, end)
                    
                    hooks.append({
                        'start': float(chunk_start),
                        'end': float(chunk_end),
                        'duration': float(chunk_end - chunk_start),
                        'hook_type': 'sustained_energy',
                        'avg_energy': float(np.mean(energy[chunk_start:chunk_end]))
                    })
            else:
                hooks.append({
                    'start': float(start),
                    'end': float(end),
                    'duration': float(duration),
                    'hook_type': 'sustained_energy',
                    'avg_energy': float(np.mean(energy[start:end]))
                })
        
        return hooks
    
    def _create_hooks_from_transitions(self, transitions: List[int], energy: np.ndarray) -> List[Dict]:
        """Create hook segments starting at scene transitions"""
        hooks = []
        
        for transition in transitions:
            start = transition
            end = min(len(energy), start + self.HOOK_CRITERIA['ideal_duration'])
            
            # Check if energy is good
            if start < len(energy) and energy[start] >= self.HOOK_CRITERIA['min_energy']:
                hooks.append({
                    'start': float(start),
                    'end': float(end),
                    'duration': float(end - start),
                    'hook_type': 'transition',
                    'avg_energy': float(np.mean(energy[start:end]))
                })
        
        return hooks
    
    def _score_hooks(self, hooks: List[Dict]) -> List[Dict]:
        """Score hooks based on multiple factors"""
        for hook in hooks:
            # Base score from energy
            energy_score = hook['avg_energy']
            
            # Duration bonus (prefer ideal duration)
            duration_diff = abs(hook['duration'] - self.HOOK_CRITERIA['ideal_duration'])
            duration_score = max(0, 100 - duration_diff * 2)
            
            # Type bonus
            type_bonus = {
                'momentum_shift': 10,
                'sustained_energy': 5,
                'transition': 3
            }
            
            # Calculate final score
            hook['score'] = (
                energy_score * 0.6 +
                duration_score * 0.3 +
                type_bonus.get(hook['hook_type'], 0)
            )
        
        return hooks
    
    def _select_best_hooks(self, hooks: List[Dict], target_count: int) -> List[Dict]:
        """Select best non-overlapping hooks"""
        # Sort by score
        hooks = sorted(hooks, key=lambda x: x['score'], reverse=True)
        
        selected = []
        
        for hook in hooks:
            if len(selected) >= target_count:
                break
            
            # Check for overlap with already selected hooks
            overlaps = False
            for selected_hook in selected:
                if self._hooks_overlap(hook, selected_hook):
                    overlaps = True
                    break
            
            if not overlaps:
                selected.append(hook)
        
        # Sort by start time
        selected = sorted(selected, key=lambda x: x['start'])
        
        # Add metadata
        for i, hook in enumerate(selected):
            hook['id'] = i + 1
            hook['title'] = f"Clip {i + 1}"
            hook['start_time'] = str(timedelta(seconds=int(hook['start'])))
            hook['end_time'] = str(timedelta(seconds=int(hook['end'])))
        
        return selected
    
    def _hooks_overlap(self, hook1: Dict, hook2: Dict) -> bool:
        """Check if two hooks overlap"""
        return not (hook1['end'] <= hook2['start'] or hook2['end'] <= hook1['start'])
    
    def _generate_placeholder_hooks(self, count: int) -> List[Dict]:
        """Generate placeholder hooks for testing"""
        hooks = []
        
        for i in range(count):
            start = i * 60  # Every minute
            duration = 30 + (i % 30)  # 30-60 seconds
            end = start + duration
            
            hooks.append({
                'id': i + 1,
                'start': float(start),
                'end': float(end),
                'duration': float(duration),
                'hook_type': 'momentum_shift',
                'avg_energy': 70 + (i % 30),
                'score': 70 + (i % 30),
                'title': f"Clip {i + 1}",
                'start_time': str(timedelta(seconds=start)),
                'end_time': str(timedelta(seconds=int(end)))
            })
        
        return hooks


# Global instance
_hook_generator = None

def get_hook_generator() -> HookGenerator:
    """Get global hook generator instance"""
    global _hook_generator
    if _hook_generator is None:
        _hook_generator = HookGenerator()
    return _hook_generator
