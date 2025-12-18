"""
FYI Social ∞ - Ollama Manager
Auto-downloads and manages local LLM models
Llama-3.2-90B for content analysis
Whisper Turbo for transcription
"""

import subprocess
import requests
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys
import time

from backend.config import get_config

config = get_config()


class OllamaManager:
    """Manage Ollama installation and models"""
    
    OLLAMA_API = "http://localhost:11434"
    
    # Model configurations
    MODELS = {
        'llama3.2': {
            'name': 'llama3.2:90b-instruct',
            'size': '50GB',
            'use': 'Content analysis, hook generation, viral scoring'
        },
        'llama3.2-small': {
            'name': 'llama3.2:3b-instruct',
            'size': '2GB',
            'use': 'Fast analysis, captions, quick tasks'
        },
        'whisper': {
            'name': 'whisper:large',
            'size': '3GB',
            'use': 'Video transcription'
        }
    }
    
    def __init__(self):
        self.models_dir = config.DATA_DIR / "ollama_models"
        self.models_dir.mkdir(exist_ok=True)
    
    def is_ollama_installed(self) -> bool:
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(['ollama', '--version'], 
                                  capture_output=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def is_ollama_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.OLLAMA_API}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def start_ollama_server(self):
        """Start Ollama server in background"""
        if self.is_ollama_running():
            print("✅ Ollama server already running")
            return True
        
        try:
            if sys.platform == 'win32':
                subprocess.Popen(['ollama', 'serve'], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                subprocess.Popen(['ollama', 'serve'], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
            
            # Wait for server to start
            for _ in range(10):
                time.sleep(1)
                if self.is_ollama_running():
                    print("✅ Ollama server started")
                    return True
            
            return False
        except Exception as e:
            print(f"❌ Failed to start Ollama: {e}")
            return False
    
    def install_ollama(self):
        """Guide user to install Ollama"""
        print("=" * 60)
        print("🤖 Ollama Installation Required")
        print("=" * 60)
        print()
        print("Ollama provides FREE local AI models (no API keys needed!)")
        print()
        print("📥 Download Ollama:")
        print("   Windows: https://ollama.com/download/windows")
        print("   Mac: https://ollama.com/download/mac")
        print("   Linux: curl -fsSL https://ollama.com/install.sh | sh")
        print()
        print("After installation, restart FYI Social ∞")
        print()
    
    def list_installed_models(self) -> List[str]:
        """List locally installed models"""
        if not self.is_ollama_running():
            return []
        
        try:
            response = requests.get(f"{self.OLLAMA_API}/api/tags")
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except:
            return []
    
    def is_model_installed(self, model_key: str) -> bool:
        """Check if a specific model is installed"""
        model_name = self.MODELS[model_key]['name']
        installed = self.list_installed_models()
        return any(model_name in m for m in installed)
    
    def pull_model(self, model_key: str, progress_callback=None):
        """Download a model"""
        model_name = self.MODELS[model_key]['name']
        
        if not self.is_ollama_running():
            print("❌ Ollama server not running. Starting...")
            if not self.start_ollama_server():
                return False
        
        print(f"📥 Downloading {model_name} ({self.MODELS[model_key]['size']})...")
        print("   This may take a while depending on your connection.")
        
        try:
            # Use streaming API to show progress
            response = requests.post(
                f"{self.OLLAMA_API}/api/pull",
                json={'name': model_name},
                stream=True
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    status = data.get('status', '')
                    
                    if 'total' in data and 'completed' in data:
                        progress = (data['completed'] / data['total']) * 100
                        print(f"\r   Progress: {progress:.1f}%", end='', flush=True)
                        
                        if progress_callback:
                            progress_callback(progress)
                    
                    if status == 'success':
                        print(f"\n✅ {model_name} installed successfully!")
                        return True
            
            return True
            
        except Exception as e:
            print(f"\n❌ Failed to download model: {e}")
            return False
    
    def generate(self, 
                 model_key: str, 
                 prompt: str, 
                 system: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2000) -> str:
        """Generate text using a model"""
        
        if not self.is_model_installed(model_key):
            print(f"⚠️ Model {model_key} not installed. Installing...")
            if not self.pull_model(model_key):
                return ""
        
        model_name = self.MODELS[model_key]['name']
        
        payload = {
            'model': model_name,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature,
                'num_predict': max_tokens
            }
        }
        
        if system:
            payload['system'] = system
        
        try:
            response = requests.post(
                f"{self.OLLAMA_API}/api/generate",
                json=payload,
                timeout=120
            )
            
            data = response.json()
            return data.get('response', '')
            
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            return ""
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper"""
        
        if not self.is_model_installed('whisper'):
            print("📥 Installing Whisper model...")
            if not self.pull_model('whisper'):
                return {'text': '', 'segments': []}
        
        # TODO: Implement Whisper transcription
        # For now, return placeholder
        print(f"🎤 Transcribing: {audio_path}")
        return {
            'text': 'Transcription placeholder',
            'segments': []
        }
    
    def setup_recommended_models(self):
        """Setup recommended models for FYI Social"""
        print("=" * 60)
        print("🚀 Setting up AI Engine")
        print("=" * 60)
        print()
        
        # Start Ollama if not running
        if not self.is_ollama_running():
            print("Starting Ollama server...")
            if not self.start_ollama_server():
                print("❌ Could not start Ollama server")
                return False
        
        # Check which models are needed
        print("📊 Checking installed models...")
        installed = self.list_installed_models()
        print(f"   Found {len(installed)} models installed")
        
        # Recommend models
        print()
        print("💡 Recommended Models:")
        print()
        
        for key, info in self.MODELS.items():
            installed = self.is_model_installed(key)
            status = "✅ Installed" if installed else "⬜ Not installed"
            print(f"  {status} {info['name']}")
            print(f"     Size: {info['size']}")
            print(f"     Use: {info['use']}")
            print()
        
        # Offer to install
        print("To install a model, use:")
        print("  ollama_manager.pull_model('llama3.2-small')  # Fast, 2GB")
        print("  ollama_manager.pull_model('llama3.2')        # Powerful, 50GB")
        print("  ollama_manager.pull_model('whisper')         # Transcription, 3GB")
        print()
        
        return True


# Global instance
_ollama_manager = None

def get_ollama_manager() -> OllamaManager:
    """Get global Ollama manager instance"""
    global _ollama_manager
    if _ollama_manager is None:
        _ollama_manager = OllamaManager()
    return _ollama_manager
