# 🚀 Phase 2 Quick Reference - AI Engine & Video Lab

## 📋 One-Page Cheat Sheet

### Installation (One Command)
```powershell
.\setup_phase2.bat
```

---

## 🎬 Core Workflows

### 1. Process 1-Hour Video → 100+ Clips
```python
from video_lab import get_auto_editor

editor = get_auto_editor()
result = editor.process_video('video.mp4', target_clips=100)
# Output: data/clips/video_20240101/ (100 clips + manifest.json)
```

### 2. Score Video Virality
```python
from ai_engine import get_clip_scoring

scorer = get_clip_scoring()
score = scorer.score_video('clip.mp4')
# Returns: {'overall_score': 85, 'recommendations': [...]}
```

### 3. Generate Thumbnails
```python
from ai_engine import get_thumbnail_ai

thumb_ai = get_thumbnail_ai()
thumbnails = thumb_ai.generate_thumbnails('video.mp4', clip_info)
# Returns: 5 thumbnail variants with AI-generated text
```

### 4. Add Captions
```python
from video_lab import get_caption_burner

captions = get_caption_burner()
result = captions.add_word_by_word_captions(
    'video.mp4', transcript, style='alex_hormozi'
)
```

### 5. Get Growth Insights
```python
from ai_engine import get_growth_mentor

mentor = get_growth_mentor()
report = mentor.analyze_content(posts, days=7)
# Returns: {'score': 85, 'insights': [...], 'recommendations': [...]}
```

---

## 🎨 Viral Templates

### Apply Template
```python
from ai_engine import get_template_engine

templates = get_template_engine()
result = templates.apply_template('mb_challenge', video_info)
```

### Available Templates
- **MrBeast**: `mb_challenge`, `mb_comparison`, `mb_survival`
- **Ali Abdaal**: `aa_productivity`, `aa_tips`
- **Alex Hormozi**: `ah_value`, `ah_breakdown`
- **Gary Vee**: `gv_motivation`
- **MKBHD**: `mk_review`
- **Vsauce**: `vs_explainer`

---

## 🎤 Voice Cloning

### Create Voice Model
```python
from video_lab import get_voice_clone

vc = get_voice_clone()
model = vc.create_voice_model('sample_5sec.wav', 'My Voice')
```

### Generate Speech
```python
audio = vc.text_to_speech('Hello world', model['model_id'])
```

---

## 🎵 Audio Enhancement

### Add Background Music
```python
from video_lab import get_sound_detector

sound = get_sound_detector()
result = sound.add_background_music('video.mp4', volume=0.3)
```

### Normalize Audio
```python
result = sound.normalize_audio('video.mp4', target_level=-16.0)
```

---

## 🎞️ B-Roll Insertion

### Auto B-Roll (Pexels)
```python
from video_lab import get_broll_inserter

broll = get_broll_inserter()
broll.set_pexels_api_key('YOUR_KEY')  # Free at pexels.com
result = broll.add_broll('video.mp4', transcript, frequency=0.3)
```

### Manual B-Roll (User Library)
```python
mappings = [
    {'start': 10, 'end': 15, 'broll_file': 'library/clip1.mp4'},
    {'start': 30, 'end': 40, 'broll_file': 'library/clip2.mp4'}
]
result = broll.add_user_library_broll('video.mp4', mappings)
```

---

## 🤖 Ollama Management

### Setup Models (First Time)
```python
from ai_engine import get_ollama_manager

ollama = get_ollama_manager()
ollama.setup_recommended_models()
# Downloads: Llama 3.2 90B (50GB), Llama 3.2 3B (2GB), Whisper (3GB)
```

### Check Status
```python
if not ollama.is_ollama_running():
    ollama.start_ollama_server()
```

### Generate Text
```python
response = ollama.generate(
    prompt="Write a viral hook for my video",
    model='llama3.2-small',
    temperature=0.9
)
```

---

## 📊 Processing Options

### Quality Settings
```python
# High quality (CRF 18, slow)
editor.process_video('video.mp4', quality='high')

# Medium quality (CRF 23, balanced) - DEFAULT
editor.process_video('video.mp4', quality='medium')

# Low quality (CRF 28, fast)
editor.process_video('video.mp4', quality='low')
```

### Progress Tracking
```python
def progress_callback(percent, message):
    print(f"[{percent}%] {message}")

result = editor.process_video(
    'video.mp4',
    progress_callback=progress_callback
)
```

---

## 📁 Output Structure

```
data/
├── clips/
│   └── video_20240101/
│       ├── clip_001.mp4
│       ├── clip_002.mp4
│       ├── ...
│       ├── clip_100.mp4
│       └── manifest.json
├── thumbnails/
│   ├── thumbnail_variant_1.jpg
│   ├── thumbnail_variant_2.jpg
│   └── ...
├── growth_reports/
│   └── growth_report_20240101_120000.json
└── library/
    ├── broll/
    └── music/
```

---

## ⚙️ Configuration

### Caption Styles
- `alex_hormozi` - Word highlighting, clean
- `mrbeast` - Yellow text, black outline
- `ali_abdaal` - Minimalist, bottom
- `minimalist` - Plain white text

### Thumbnail Styles (Auto-generated)
1. Classic MrBeast - Yellow ALL CAPS
2. Emotional Reaction - Red outline
3. Curiosity Gap - Cyan neon
4. Before/After Split - Green split screen
5. Minimalist Clean - Dark gray minimal

---

## 🚨 Common Issues

### FFmpeg Not Found
```powershell
winget install FFmpeg
```

### Ollama Not Running
```python
get_ollama_manager().start_ollama_server()
```

### Out of Memory
- Use `quality='low'`
- Process shorter videos
- Close other applications

### Slow Processing
- Enable GPU in Ollama
- Reduce target_clips
- Use smaller models (3B instead of 90B)

---

## 📈 Performance Tips

1. **Use GPU**: 5-10x faster processing
2. **Parallel Processing**: Already enabled (4 clips at once)
3. **Quality vs Speed**: Use 'medium' for balanced results
4. **Model Selection**: Use 3B model for faster AI tasks
5. **Disk Space**: Keep 100GB+ free for temp files

---

## 🎯 Best Practices

### Before Processing
1. Check Ollama is running
2. Verify FFmpeg installed
3. Ensure 100GB+ free space
4. Test with short video first

### During Processing
1. Don't close terminal
2. Monitor progress
3. Check temp folder size
4. Keep Ollama running

### After Processing
1. Review manifest.json
2. Test clips play correctly
3. Check thumbnail quality
4. Archive or delete temp files

---

## 📚 File Paths

### Import Paths
```python
from ai_engine import (
    get_ollama_manager,
    get_clip_scoring,
    get_hook_generator,
    get_thumbnail_ai,
    get_growth_mentor,
    get_template_engine
)

from video_lab import (
    get_auto_editor,
    get_caption_burner,
    get_broll_inserter,
    get_sound_detector,
    get_voice_clone
)
```

### Data Directories
- Clips: `data/clips/`
- Thumbnails: `data/thumbnails/`
- Reports: `data/growth_reports/`
- Library: `data/library/` (broll, music)
- Temp: `data/temp/`

---

## 🔗 External Tools

- **Ollama**: https://ollama.ai
- **FFmpeg**: https://ffmpeg.org
- **Pexels API**: https://pexels.com/api
- **ElevenLabs**: https://elevenlabs.io (optional)
- **Coqui TTS**: `pip install TTS` (optional)

---

## 💡 Pro Tips

1. **Batch Processing**: Process multiple videos overnight
2. **Template Library**: Build your own custom templates
3. **B-roll Library**: Curate high-quality B-roll clips
4. **Voice Samples**: Record multiple voice samples
5. **Music Library**: Collect royalty-free music

---

## 🎓 Quick Examples

### Example 1: Full Pipeline
```python
from video_lab import get_auto_editor, get_caption_burner
from ai_engine import get_thumbnail_ai

# 1. Process video
editor = get_auto_editor()
result = editor.process_video('long_video.mp4', target_clips=50)

# 2. Add captions to top 10 clips
captions = get_caption_burner()
for clip in result['clips'][:10]:
    captions.add_captions(clip['clip_path'], transcript)

print(f"✅ Created {result['total_clips']} clips!")
```

### Example 2: Growth Analysis
```python
from ai_engine import get_growth_mentor

mentor = get_growth_mentor()

# Load your posts (from database or API)
posts = load_posts_from_database()

# Get insights
report = mentor.analyze_content(posts, days=7)

print(f"Growth Score: {report['score']}/100")
for insight in report['insights']:
    print(f"  • {insight}")
```

### Example 3: Template Workflow
```python
from ai_engine import get_template_engine

templates = get_template_engine()

# Suggest template
video_info = {'title': 'My Video', 'duration': 60}
suggestion = templates.suggest_template(video_info)

print(f"Suggested: {suggestion['template']['name']}")
print(f"Reason: {suggestion['reason']}")

# Generate script
script = templates.generate_script(
    suggestion['template']['id'],
    video_info
)

print(script['script'])
```

---

## 🎉 You're Ready!

Everything you need to create viral content at scale!

**Questions?** Check `PHASE_2_README.md` for detailed documentation.

---

**FYI Social ∞** - Phase 2 AI Engine
