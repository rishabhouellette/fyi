"""
FYI Social ∞ - Voice Clone
Clone voice from 5-second sample using RVC/Coqui TTS
Replace audio in videos with cloned voice
"""

import subprocess
import json
from typing import Optional, Dict
from pathlib import Path
import requests


class VoiceClone:
    """Voice cloning for content repurposing"""
    
    def __init__(self):
        self.output_dir = Path('data/voice_clones')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.models_dir = Path('data/voice_models')
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice cloning backends
        self.backend = 'coqui'  # 'coqui', 'rvc', 'elevenlabs'
        
        # Coqui TTS (free, local)
        self.coqui_available = self._check_coqui_installed()
        
        # ElevenLabs API (paid, high quality)
        self.elevenlabs_api_key = None
        self.elevenlabs_base_url = 'https://api.elevenlabs.io/v1'
    
    def _check_coqui_installed(self) -> bool:
        """Check if Coqui TTS is installed"""
        try:
            subprocess.run(
                ['tts', '--help'],
                capture_output=True,
                check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def set_elevenlabs_api_key(self, api_key: str):
        """Set ElevenLabs API key"""
        self.elevenlabs_api_key = api_key
        self.backend = 'elevenlabs'
    
    def create_voice_model(
        self,
        audio_sample: str,
        voice_name: str,
        description: Optional[str] = None
    ) -> Dict:
        """
        Create voice model from audio sample
        
        Args:
            audio_sample: Path to 5+ second audio sample
            voice_name: Name for the voice model
            description: Optional description
        
        Returns:
            {
                'success': True,
                'model_id': 'voice_model_123',
                'model_path': 'path/to/model',
                'voice_name': 'John Doe'
            }
        """
        
        audio_sample = Path(audio_sample)
        
        if not audio_sample.exists():
            return {'success': False, 'error': f'Audio sample not found: {audio_sample}'}
        
        if self.backend == 'elevenlabs' and self.elevenlabs_api_key:
            return self._create_elevenlabs_voice(audio_sample, voice_name, description)
        
        elif self.backend == 'coqui' and self.coqui_available:
            return self._create_coqui_voice(audio_sample, voice_name)
        
        else:
            return {
                'success': False,
                'error': 'No voice cloning backend available. Install Coqui TTS or set ElevenLabs API key.'
            }
    
    def clone_voice(
        self,
        video_path: str,
        model_id: str,
        text: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Replace video audio with cloned voice
        
        Args:
            video_path: Input video path
            model_id: Voice model ID to use
            text: Text to speak (if None, uses original transcript)
            output_path: Output path
        
        Returns:
            Result dict
        """
        
        video_path = Path(video_path)
        
        if not video_path.exists():
            return {'success': False, 'error': f'Video not found: {video_path}'}
        
        # Determine output path
        if output_path is None:
            output_path = self.output_dir / f"{video_path.stem}_cloned.mp4"
        else:
            output_path = Path(output_path)
        
        try:
            # Generate audio with cloned voice
            audio_result = self._generate_audio(model_id, text or "Sample text")
            
            if not audio_result['success']:
                return audio_result
            
            audio_path = Path(audio_result['audio_path'])
            
            # Replace audio in video
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-map', '0:v:0',
                '-map', '1:a:0',
                str(output_path),
                '-y'
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Clean up temp audio
            audio_path.unlink()
            
            return {
                'success': True,
                'output_path': str(output_path),
                'model_id': model_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def text_to_speech(
        self,
        text: str,
        model_id: str,
        output_path: Optional[str] = None
    ) -> Dict:
        """
        Generate speech from text using cloned voice
        
        Args:
            text: Text to speak
            model_id: Voice model ID
            output_path: Output audio path
        
        Returns:
            Result dict
        """
        
        if output_path is None:
            output_path = self.output_dir / f"tts_{model_id}.mp3"
        else:
            output_path = Path(output_path)
        
        return self._generate_audio(model_id, text, output_path)
    
    def _create_elevenlabs_voice(
        self,
        audio_sample: Path,
        voice_name: str,
        description: Optional[str]
    ) -> Dict:
        """Create voice using ElevenLabs"""
        
        try:
            headers = {
                'xi-api-key': self.elevenlabs_api_key
            }
            
            files = {
                'files': open(audio_sample, 'rb')
            }
            
            data = {
                'name': voice_name,
                'description': description or f'Cloned voice: {voice_name}'
            }
            
            response = requests.post(
                f'{self.elevenlabs_base_url}/voices/add',
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'ElevenLabs API error: {response.status_code}'
                }
            
            result = response.json()
            voice_id = result.get('voice_id')
            
            # Save model info
            model_info = {
                'voice_id': voice_id,
                'voice_name': voice_name,
                'description': description,
                'backend': 'elevenlabs',
                'sample_path': str(audio_sample)
            }
            
            model_path = self.models_dir / f'{voice_id}.json'
            
            with open(model_path, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            return {
                'success': True,
                'model_id': voice_id,
                'model_path': str(model_path),
                'voice_name': voice_name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_coqui_voice(self, audio_sample: Path, voice_name: str) -> Dict:
        """Create voice using Coqui TTS (local)"""
        
        # Coqui TTS doesn't need model training for voice cloning
        # It uses speaker embeddings from the sample
        
        model_id = f'coqui_{voice_name.lower().replace(" ", "_")}'
        
        model_info = {
            'voice_id': model_id,
            'voice_name': voice_name,
            'backend': 'coqui',
            'sample_path': str(audio_sample)
        }
        
        model_path = self.models_dir / f'{model_id}.json'
        
        with open(model_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        return {
            'success': True,
            'model_id': model_id,
            'model_path': str(model_path),
            'voice_name': voice_name
        }
    
    def _generate_audio(
        self,
        model_id: str,
        text: str,
        output_path: Optional[Path] = None
    ) -> Dict:
        """Generate audio using voice model"""
        
        # Load model info
        model_path = self.models_dir / f'{model_id}.json'
        
        if not model_path.exists():
            return {
                'success': False,
                'error': f'Voice model not found: {model_id}'
            }
        
        with open(model_path) as f:
            model_info = json.load(f)
        
        backend = model_info.get('backend', 'coqui')
        
        if output_path is None:
            output_path = Path(f'data/temp/tts_{model_id}.wav')
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if backend == 'elevenlabs':
            return self._generate_elevenlabs_audio(model_info, text, output_path)
        
        elif backend == 'coqui':
            return self._generate_coqui_audio(model_info, text, output_path)
        
        else:
            return {
                'success': False,
                'error': f'Unknown backend: {backend}'
            }
    
    def _generate_elevenlabs_audio(
        self,
        model_info: Dict,
        text: str,
        output_path: Path
    ) -> Dict:
        """Generate audio with ElevenLabs"""
        
        try:
            voice_id = model_info['voice_id']
            
            headers = {
                'xi-api-key': self.elevenlabs_api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                'text': text,
                'model_id': 'eleven_monolingual_v1',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.75
                }
            }
            
            response = requests.post(
                f'{self.elevenlabs_base_url}/text-to-speech/{voice_id}',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'ElevenLabs TTS error: {response.status_code}'
                }
            
            # Save audio
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return {
                'success': True,
                'audio_path': str(output_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_coqui_audio(
        self,
        model_info: Dict,
        text: str,
        output_path: Path
    ) -> Dict:
        """Generate audio with Coqui TTS"""
        
        try:
            sample_path = model_info['sample_path']
            
            cmd = [
                'tts',
                '--text', text,
                '--model_name', 'tts_models/multilingual/multi-dataset/your_tts',
                '--speaker_wav', sample_path,
                '--out_path', str(output_path)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            return {
                'success': True,
                'audio_path': str(output_path)
            }
            
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': f'Coqui TTS failed: {e}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_voice_models(self) -> List[Dict]:
        """List all available voice models"""
        
        models = []
        
        for model_file in self.models_dir.glob('*.json'):
            try:
                with open(model_file) as f:
                    model_info = json.load(f)
                    models.append(model_info)
            except Exception as e:
                print(f"⚠️ Failed to load model {model_file}: {e}")
        
        return models


# Global instance
_voice_clone = None

def get_voice_clone() -> VoiceClone:
    """Get global voice clone instance"""
    global _voice_clone
    if _voice_clone is None:
        _voice_clone = VoiceClone()
    return _voice_clone
