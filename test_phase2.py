"""
FYI Social ∞ - Phase 2 Test Suite
Verify AI Engine and Video Lab functionality
"""

import sys
from pathlib import Path

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_result(test_name, passed, message=""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {test_name}")
    if message:
        print(f"      {message}")

def test_imports():
    """Test all imports"""
    print_header("Testing Imports")
    
    tests = [
        ("AI Engine - Ollama Manager", "ai_engine.ollama_manager", "get_ollama_manager"),
        ("AI Engine - Clip Scoring", "ai_engine.clip_scoring", "get_clip_scoring"),
        ("AI Engine - Hook Generator", "ai_engine.hook_generator", "get_hook_generator"),
        ("AI Engine - Thumbnail AI", "ai_engine.thumbnail_ai", "get_thumbnail_ai"),
        ("AI Engine - Growth Mentor", "ai_engine.growth_mentor", "get_growth_mentor"),
        ("AI Engine - Template Engine", "ai_engine.template_engine", "get_template_engine"),
        ("Video Lab - Auto Editor", "video_lab.auto_editor", "get_auto_editor"),
        ("Video Lab - Caption Burner", "video_lab.caption_burner", "get_caption_burner"),
        ("Video Lab - B-Roll Inserter", "video_lab.broll_inserter", "get_broll_inserter"),
        ("Video Lab - Sound Detector", "video_lab.sound_detector", "get_sound_detector"),
        ("Video Lab - Voice Clone", "video_lab.voice_clone", "get_voice_clone"),
    ]
    
    passed = 0
    for name, module, func in tests:
        try:
            mod = __import__(module, fromlist=[func])
            getattr(mod, func)
            print_result(name, True)
            passed += 1
        except Exception as e:
            print_result(name, False, str(e))
    
    return passed, len(tests)

def test_dependencies():
    """Test external dependencies"""
    print_header("Testing Dependencies")
    
    tests = []
    
    # Test numpy
    try:
        import numpy
        print_result("NumPy", True, f"Version: {numpy.__version__}")
        tests.append(True)
    except ImportError as e:
        print_result("NumPy", False, str(e))
        tests.append(False)
    
    # Test OpenCV
    try:
        import cv2
        print_result("OpenCV", True, f"Version: {cv2.__version__}")
        tests.append(True)
    except ImportError as e:
        print_result("OpenCV", False, str(e))
        tests.append(False)
    
    # Test Pillow
    try:
        from PIL import Image
        print_result("Pillow", True)
        tests.append(True)
    except ImportError as e:
        print_result("Pillow", False, str(e))
        tests.append(False)
    
    # Test requests
    try:
        import requests
        print_result("Requests", True, f"Version: {requests.__version__}")
        tests.append(True)
    except ImportError as e:
        print_result("Requests", False, str(e))
        tests.append(False)
    
    return sum(tests), len(tests)

def test_external_tools():
    """Test external tools (FFmpeg, Ollama)"""
    print_header("Testing External Tools")
    
    import subprocess
    tests = []
    
    # Test FFmpeg
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print_result("FFmpeg", True, version_line)
            tests.append(True)
        else:
            print_result("FFmpeg", False, "Not responding correctly")
            tests.append(False)
    except FileNotFoundError:
        print_result("FFmpeg", False, "Not installed - Install: winget install FFmpeg")
        tests.append(False)
    except Exception as e:
        print_result("FFmpeg", False, str(e))
        tests.append(False)
    
    # Test Ollama
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_result("Ollama", True, f"Version: {version}")
            tests.append(True)
        else:
            print_result("Ollama", False, "Not responding correctly")
            tests.append(False)
    except FileNotFoundError:
        print_result("Ollama", False, "Not installed - Download: https://ollama.ai")
        tests.append(False)
    except Exception as e:
        print_result("Ollama", False, str(e))
        tests.append(False)
    
    return sum(tests), len(tests)

def test_functionality():
    """Test basic functionality"""
    print_header("Testing Functionality")
    
    tests = []
    
    # Test Ollama Manager
    try:
        from ai_engine import get_ollama_manager
        
        ollama = get_ollama_manager()
        installed = ollama.is_ollama_installed()
        
        if installed:
            print_result("Ollama Manager - Installation Check", True)
            tests.append(True)
            
            # Check if running
            running = ollama.is_ollama_running()
            print_result("Ollama Manager - Server Running", running, 
                        "Server is running" if running else "Start with: ollama serve")
            tests.append(running)
            
        else:
            print_result("Ollama Manager - Installation Check", False, 
                        "Ollama not installed")
            tests.append(False)
            
    except Exception as e:
        print_result("Ollama Manager", False, str(e))
        tests.append(False)
    
    # Test Template Engine
    try:
        from ai_engine import get_template_engine
        
        templates = get_template_engine()
        template_list = templates.list_templates()
        
        print_result("Template Engine", True, 
                    f"Loaded {len(template_list)} templates")
        tests.append(True)
        
    except Exception as e:
        print_result("Template Engine", False, str(e))
        tests.append(False)
    
    # Test Auto Editor (basic)
    try:
        from video_lab import get_auto_editor
        
        editor = get_auto_editor()
        print_result("Auto Editor - Initialization", True)
        tests.append(True)
        
    except Exception as e:
        print_result("Auto Editor", False, str(e))
        tests.append(False)
    
    return sum(tests), len(tests)

def test_directories():
    """Test required directories exist"""
    print_header("Testing Directory Structure")
    
    dirs = [
        'data',
        'data/clips',
        'data/thumbnails',
        'data/library',
        'data/library/broll',
        'data/library/music',
        'data/temp',
        'data/growth_reports',
        'ai-engine',
        'video-lab'
    ]
    
    tests = []
    for dir_path in dirs:
        path = Path(dir_path)
        exists = path.exists()
        
        if not exists:
            # Try to create
            try:
                path.mkdir(parents=True, exist_ok=True)
                print_result(f"Directory: {dir_path}", True, "Created")
                tests.append(True)
            except Exception as e:
                print_result(f"Directory: {dir_path}", False, str(e))
                tests.append(False)
        else:
            print_result(f"Directory: {dir_path}", True, "Exists")
            tests.append(True)
    
    return sum(tests), len(tests)

def main():
    """Run all tests"""
    print_header("FYI Social ∞ - Phase 2 Test Suite")
    
    results = {}
    
    # Run tests
    results['imports'] = test_imports()
    results['dependencies'] = test_dependencies()
    results['external'] = test_external_tools()
    results['directories'] = test_directories()
    results['functionality'] = test_functionality()
    
    # Summary
    print_header("Test Summary")
    
    total_passed = 0
    total_tests = 0
    
    for category, (passed, total) in results.items():
        total_passed += passed
        total_tests += total
        percentage = (passed / total * 100) if total > 0 else 0
        status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
        print(f"{status} {category.title()}: {passed}/{total} ({percentage:.0f}%)")
    
    print()
    overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Overall: {total_passed}/{total_tests} tests passed ({overall_percentage:.0f}%)")
    
    if overall_percentage == 100:
        print("\n🎉 ALL TESTS PASSED! Phase 2 is ready to use!")
        return 0
    elif overall_percentage >= 80:
        print("\n✅ MOSTLY READY! Some optional features may not be available.")
        return 0
    else:
        print("\n⚠️ SETUP INCOMPLETE! Please install missing dependencies.")
        print("\nRun: .\\setup_phase2.bat")
        return 1

if __name__ == '__main__':
    exit(main())
