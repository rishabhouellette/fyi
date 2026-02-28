import React, { useState, useEffect } from 'react';
import { useTheme } from '../context/ThemeContext';
import {
  generateCaption,
  generateHashtags,
  generateImage,
  generateVideo,
  getVideoStatus,
  generateVoice,
  getVoices,
  createFacelessVideo,
  createFacelessVideoWithVoice,
  getTemplates,
  applyTemplate,
  ingestContent,
  repurposeContent,
  getSupportedLanguages,
  translateText
} from '../lib/apiClient';

// Tab component
function Tab({ active, onClick, children, isDark }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 rounded-t-lg font-medium transition-colors ${
        active
          ? 'bg-violet-600 text-white'
          : isDark ? 'bg-gray-700 text-gray-300 hover:bg-gray-600' : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
      }`}
    >
      {children}
    </button>
  );
}

// Caption Generator Panel
function CaptionPanel({ isDark }) {
  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('instagram');
  const [tone, setTone] = useState('casual');
  const [language, setLanguage] = useState('en');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [languages, setLanguages] = useState([]);

  useEffect(() => {
    getSupportedLanguages().then(data => setLanguages(data.languages || [])).catch(() => {});
  }, []);

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    try {
      const data = await generateCaption({
        topic: topic.trim(),
        platform,
        tone,
        include_hashtags: true,
        hashtags_count: 10
      });
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  const inputClass = `w-full rounded px-3 py-2 border transition-colors ${isDark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`;

  return (
    <div className="space-y-4">
      <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>✍️ AI Caption Generator</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className={`block text-sm mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Platform</label>
          <select
            value={platform}
            onChange={e => setPlatform(e.target.value)}
            className={inputClass}
          >
            <option value="instagram">Instagram</option>
            <option value="tiktok">TikTok</option>
            <option value="youtube">YouTube</option>
            <option value="twitter">Twitter/X</option>
            <option value="linkedin">LinkedIn</option>
            <option value="facebook">Facebook</option>
          </select>
        </div>
        
        <div>
          <label className={`block text-sm mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Tone</label>
          <select
            value={tone}
            onChange={e => setTone(e.target.value)}
            className={inputClass}
          >
            <option value="casual">Casual</option>
            <option value="professional">Professional</option>
            <option value="funny">Funny</option>
            <option value="inspirational">Inspirational</option>
            <option value="educational">Educational</option>
          </select>
        </div>
        
        <div>
          <label className={`block text-sm mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Language</label>
          <select
            value={language}
            onChange={e => setLanguage(e.target.value)}
            className={inputClass}
          >
            {languages.length > 0 ? (
              languages.map(lang => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))
            ) : (
              <option value="en">English</option>
            )}
          </select>
        </div>
      </div>
      
      <div>
        <label className={`block text-sm mb-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Topic / Description</label>
        <textarea
          value={topic}
          onChange={e => setTopic(e.target.value)}
          placeholder="e.g., Morning coffee routine with aesthetic vibes..."
          className={`${inputClass} h-24 resize-none`}
        />
      </div>
      
      <button
        onClick={handleGenerate}
        disabled={loading || !topic.trim()}
        className="px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
      >
        {loading ? 'Generating...' : '✨ Generate Caption'}
      </button>
      
      {result && (
        <div className={`rounded-lg p-4 ${isDark ? 'bg-gray-700' : 'bg-gray-100'}`}>
          {result.error ? (
            <p className="text-red-500">{result.error}</p>
          ) : (
            <div className="space-y-3">
              <div>
                <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Caption:</span>
                <p className={`mt-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{result.caption}</p>
              </div>
              {result.hashtags && result.hashtags.length > 0 && (
                <div>
                  <span className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Hashtags:</span>
                  <p className="text-violet-500 mt-1">{result.hashtags.join(' ')}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Image Generator Panel
function ImagePanel() {
  const [prompt, setPrompt] = useState('');
  const [provider, setProvider] = useState('dalle');
  const [size, setSize] = useState('1024x1024');
  const [style, setStyle] = useState('vivid');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    try {
      const data = await generateImage({ prompt: prompt.trim(), provider, size, style });
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">🎨 AI Image Generator</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Provider (BYOK)</label>
          <select
            value={provider}
            onChange={e => setProvider(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="dalle">DALL-E 3 (OpenAI)</option>
            <option value="stability">Stability AI</option>
            <option value="flux">Flux (Replicate)</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm text-gray-400 mb-1">Size</label>
          <select
            value={size}
            onChange={e => setSize(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="1024x1024">1024×1024 (Square)</option>
            <option value="1792x1024">1792×1024 (Landscape)</option>
            <option value="1024x1792">1024×1792 (Portrait)</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm text-gray-400 mb-1">Style</label>
          <select
            value={style}
            onChange={e => setStyle(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="vivid">Vivid</option>
            <option value="natural">Natural</option>
          </select>
        </div>
      </div>
      
      <div>
        <label className="block text-sm text-gray-400 mb-1">Prompt</label>
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="e.g., A serene mountain lake at sunset with vibrant colors..."
          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-24 resize-none"
        />
      </div>
      
      <button
        onClick={handleGenerate}
        disabled={loading || !prompt.trim()}
        className="px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
      >
        {loading ? 'Generating...' : '🎨 Generate Image'}
      </button>
      
      {result && (
        <div className="bg-gray-700 rounded-lg p-4">
          {result.error ? (
            <p className="text-red-400">{result.error}</p>
          ) : (
            <div className="space-y-3">
              {result.images && result.images.map((img, i) => (
                <div key={i}>
                  <img src={img.url} alt={`Generated ${i + 1}`} className="max-w-full rounded-lg" />
                </div>
              ))}
              <p className="text-sm text-gray-400">Credits used: {result.credits_used || 1}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Video Generator Panel
function VideoPanel() {
  const [prompt, setPrompt] = useState('');
  const [provider, setProvider] = useState('veo');
  const [duration, setDuration] = useState(4);
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await generateVideo({ prompt: prompt.trim(), provider, duration, aspect_ratio: aspectRatio });
      setResult(data);
      
      // If it's async, start polling
      if (data.status === 'processing' && data.job_id) {
        setPolling(true);
        pollStatus(data.job_id);
      }
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  const pollStatus = async (jobId) => {
    let attempts = 0;
    const maxAttempts = 60; // 5 minutes max
    
    const check = async () => {
      try {
        const status = await getVideoStatus(jobId);
        setResult(status);
        
        if (status.status === 'completed' || status.status === 'failed') {
          setPolling(false);
          return;
        }
        
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(check, 5000);
        } else {
          setPolling(false);
          setResult({ error: 'Timeout waiting for video generation' });
        }
      } catch (err) {
        setPolling(false);
        setResult({ error: err.message });
      }
    };
    
    setTimeout(check, 5000);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">🎬 AI Video Generator</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Provider (BYOK)</label>
          <select
            value={provider}
            onChange={e => setProvider(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="veo">Gemini Veo 2</option>
            <option value="grok_imagine">Grok Imagine</option>
            <option value="runway">Runway Gen-2</option>
            <option value="kling">Kling AI</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm text-gray-400 mb-1">Duration</label>
          <select
            value={duration}
            onChange={e => setDuration(Number(e.target.value))}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            {provider === 'veo' ? (
              <>
                <option value={5}>5 seconds</option>
                <option value={6}>6 seconds</option>
                <option value={7}>7 seconds</option>
                <option value={8}>8 seconds</option>
              </>
            ) : provider === 'grok_imagine' ? (
              <>
                <option value={5}>5 seconds</option>
                <option value={6}>6 seconds</option>
                <option value={8}>8 seconds</option>
                <option value={10}>10 seconds</option>
              </>
            ) : (
              <>
                <option value={4}>4 seconds</option>
                <option value={8}>8 seconds</option>
                <option value={16}>16 seconds</option>
              </>
            )}
          </select>
        </div>
        
        <div>
          <label className="block text-sm text-gray-400 mb-1">Aspect Ratio</label>
          <select
            value={aspectRatio}
            onChange={e => setAspectRatio(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="16:9">16:9 (Landscape)</option>
            <option value="9:16">9:16 (Portrait/TikTok)</option>
            <option value="1:1">1:1 (Square)</option>
          </select>
        </div>
      </div>
      
      <div>
        <label className="block text-sm text-gray-400 mb-1">Prompt</label>
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder="e.g., A woman walking through a neon-lit cyberpunk city at night..."
          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-24 resize-none"
        />
      </div>
      
      {provider === 'veo' && (
        <p className="text-xs text-gray-500">Powered by Google Veo 2 — uses your Gemini API key</p>
      )}
      {provider === 'grok_imagine' && (
        <p className="text-xs text-gray-500">Powered by xAI Grok Imagine — uses your xAI API key</p>
      )}

      <button
        onClick={handleGenerate}
        disabled={loading || polling || !prompt.trim()}
        className="px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
      >
        {loading ? 'Submitting...' : polling ? 'Generating... (please wait)' : '🎬 Generate Video'}
      </button>
      
      {result && (
        <div className="bg-gray-700 rounded-lg p-4">
          {result.error ? (
            <p className="text-red-400">{result.error}</p>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-gray-400">
                Status: <span className={result.status === 'completed' ? 'text-green-400' : 'text-yellow-400'}>{result.status}</span>
                {result.result?.progress > 0 && result.status !== 'completed' && (
                  <span className="ml-2 text-violet-400">({result.result.progress}%)</span>
                )}
              </p>
              {(result.result?.url || result.video_url) && (
                <video src={result.result?.url || result.video_url} controls className="max-w-full rounded-lg" />
              )}
              {result.credits_used && (
                <p className="text-sm text-gray-400">Credits used: {result.credits_used}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Voiceover Panel
function VoicePanel() {
  const [text, setText] = useState('');
  const [provider, setProvider] = useState('elevenlabs');
  const [voiceId, setVoiceId] = useState('rachel');
  const [voices, setVoices] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getVoices(provider).then(data => setVoices(data.voices || [])).catch(() => {});
  }, [provider]);

  const handleGenerate = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const data = await generateVoice({ text: text.trim(), provider, voice_id: voiceId });
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">🎙️ AI Voiceover</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Provider (BYOK)</label>
          <select
            value={provider}
            onChange={e => setProvider(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="elevenlabs">ElevenLabs</option>
            <option value="openai">OpenAI TTS</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm text-gray-400 mb-1">Voice</label>
          <select
            value={voiceId}
            onChange={e => setVoiceId(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            {voices.length > 0 ? (
              voices.map(v => (
                <option key={v.voice_id} value={v.voice_id}>{v.name}</option>
              ))
            ) : (
              <>
                <option value="rachel">Rachel (Female)</option>
                <option value="adam">Adam (Male)</option>
                <option value="bella">Bella (Female)</option>
              </>
            )}
          </select>
        </div>
      </div>
      
      <div>
        <label className="block text-sm text-gray-400 mb-1">Text to Speech</label>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Enter the text you want to convert to speech..."
          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-32 resize-none"
        />
      </div>
      
      <button
        onClick={handleGenerate}
        disabled={loading || !text.trim()}
        className="px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
      >
        {loading ? 'Generating...' : '🎙️ Generate Voiceover'}
      </button>
      
      {result && (
        <div className="bg-gray-700 rounded-lg p-4">
          {result.error ? (
            <p className="text-red-400">{result.error}</p>
          ) : (
            <div className="space-y-3">
              {result.audio_url && (
                <audio src={result.audio_url} controls className="w-full" />
              )}
              <p className="text-sm text-gray-400">Duration: {result.duration_seconds}s</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Faceless Video Panel
function FacelessPanel() {
  const [script, setScript] = useState('');
  const [useVoice, setUseVoice] = useState(false);
  const [voiceProvider, setVoiceProvider] = useState('elevenlabs');
  const [voiceId, setVoiceId] = useState('rachel');
  const [bgColor, setBgColor] = useState('black');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (!script.trim()) return;
    setLoading(true);
    try {
      const data = useVoice
        ? await createFacelessVideoWithVoice({
            script: script.trim(),
            voice_provider: voiceProvider,
            voice_id: voiceId,
            bg_color: bgColor
          })
        : await createFacelessVideo({
            script: script.trim(),
            bg_color: bgColor
          });
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">📱 Faceless Video Creator</h3>
      <p className="text-sm text-gray-400">Create TikTok/Reels style videos with captions</p>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Background</label>
          <select
            value={bgColor}
            onChange={e => setBgColor(e.target.value)}
            className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
          >
            <option value="black">Black</option>
            <option value="white">White</option>
            <option value="#1a1a2e">Dark Blue</option>
            <option value="#2d132c">Dark Purple</option>
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="useVoice"
            checked={useVoice}
            onChange={e => setUseVoice(e.target.checked)}
            className="w-4 h-4"
          />
          <label htmlFor="useVoice" className="text-sm text-gray-400">Add AI Voiceover</label>
        </div>
        
        {useVoice && (
          <div>
            <label className="block text-sm text-gray-400 mb-1">Voice</label>
            <select
              value={voiceId}
              onChange={e => setVoiceId(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
            >
              <option value="rachel">Rachel (Female)</option>
              <option value="adam">Adam (Male)</option>
            </select>
          </div>
        )}
      </div>
      
      <div>
        <label className="block text-sm text-gray-400 mb-1">Script</label>
        <textarea
          value={script}
          onChange={e => setScript(e.target.value)}
          placeholder="Enter your video script here. Each sentence will become a caption..."
          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-40 resize-none"
        />
      </div>
      
      <button
        onClick={handleGenerate}
        disabled={loading || !script.trim()}
        className="px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
      >
        {loading ? 'Creating Video...' : '📱 Create Faceless Video'}
      </button>
      
      {result && (
        <div className="bg-gray-700 rounded-lg p-4">
          {result.error ? (
            <p className="text-red-400">{result.error}</p>
          ) : (
            <div className="space-y-3">
              {result.video_path && (
                <video src={`/api/uploads/${result.video_path.split('/').pop()}`} controls className="max-w-md rounded-lg mx-auto" />
              )}
              <p className="text-green-400">✅ Video created successfully!</p>
              {result.audio_path && <p className="text-sm text-gray-400">Audio: {result.audio_path}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Templates Panel
function TemplatesPanel() {
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [variables, setVariables] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getTemplates().then(data => setTemplates(data.templates || [])).catch(() => {});
  }, []);

  const handleApply = async () => {
    if (!selectedTemplate) return;
    setLoading(true);
    try {
      const data = await applyTemplate(selectedTemplate.id, variables);
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">📋 Viral Templates</h3>
      <p className="text-sm text-gray-400">Use proven viral hooks and structures</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1">Template Category</label>
          <div className="space-y-2 max-h-64 overflow-y-auto bg-gray-800 rounded p-2">
            {templates.map(t => (
              <button
                key={t.id}
                onClick={() => {
                  setSelectedTemplate(t);
                  setVariables({});
                  setResult(null);
                }}
                className={`w-full text-left p-2 rounded ${
                  selectedTemplate?.id === t.id ? 'bg-violet-600' : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                <span className="font-medium text-white">{t.name}</span>
                <span className="text-xs text-gray-400 block">{t.category}</span>
              </button>
            ))}
          </div>
        </div>
        
        {selectedTemplate && (
          <div>
            <label className="block text-sm text-gray-400 mb-1">Template Preview</label>
            <div className="bg-gray-800 rounded p-3 text-sm text-gray-300">
              <pre className="whitespace-pre-wrap">{selectedTemplate.template}</pre>
            </div>
            
            {selectedTemplate.variables && selectedTemplate.variables.length > 0 && (
              <div className="mt-4 space-y-2">
                <label className="block text-sm text-gray-400">Fill Variables</label>
                {selectedTemplate.variables.map(v => (
                  <input
                    key={v}
                    type="text"
                    placeholder={v}
                    value={variables[v] || ''}
                    onChange={e => setVariables({ ...variables, [v]: e.target.value })}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
                  />
                ))}
              </div>
            )}
            
            <button
              onClick={handleApply}
              disabled={loading}
              className="mt-4 px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
            >
              {loading ? 'Applying...' : '✨ Apply Template'}
            </button>
          </div>
        )}
      </div>
      
      {result && (
        <div className="bg-gray-700 rounded-lg p-4">
          {result.error ? (
            <p className="text-red-400">{result.error}</p>
          ) : (
            <div>
              <span className="text-sm text-gray-400">Generated Content:</span>
              <p className="text-white mt-1 whitespace-pre-wrap">{result.result}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Content Repurposer Panel
function RepurposerPanel() {
  const [url, setUrl] = useState('');
  const [content, setContent] = useState('');
  const [targetFormats, setTargetFormats] = useState(['tweet', 'linkedin', 'caption']);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);

  const handleIngest = async () => {
    if (!url.trim()) return;
    setIngesting(true);
    try {
      const data = await ingestContent(url.trim());
      setContent(data.content || '');
    } catch (err) {
      setResult({ error: err.message });
    }
    setIngesting(false);
  };

  const handleRepurpose = async () => {
    if (!content.trim()) return;
    setLoading(true);
    try {
      const data = await repurposeContent({
        content: content.trim(),
        source_type: 'article',
        target_formats: targetFormats
      });
      setResult(data);
    } catch (err) {
      setResult({ error: err.message });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">🔄 Content Repurposer</h3>
      <p className="text-sm text-gray-400">Turn articles, videos, or podcasts into social media posts</p>
      
      <div className="flex gap-2">
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="Paste a URL (YouTube, article, etc.)"
          className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
        />
        <button
          onClick={handleIngest}
          disabled={ingesting || !url.trim()}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-700 text-white rounded"
        >
          {ingesting ? '...' : 'Extract'}
        </button>
      </div>
      
      <div>
        <label className="block text-sm text-gray-400 mb-1">Content</label>
        <textarea
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder="Paste or extract content to repurpose..."
          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-32 resize-none"
        />
      </div>
      
      <div>
        <label className="block text-sm text-gray-400 mb-1">Output Formats</label>
        <div className="flex flex-wrap gap-2">
          {['tweet', 'linkedin', 'caption', 'thread', 'script', 'carousel'].map(fmt => (
            <label key={fmt} className="flex items-center gap-1 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={targetFormats.includes(fmt)}
                onChange={e => {
                  if (e.target.checked) {
                    setTargetFormats([...targetFormats, fmt]);
                  } else {
                    setTargetFormats(targetFormats.filter(f => f !== fmt));
                  }
                }}
                className="w-4 h-4"
              />
              {fmt}
            </label>
          ))}
        </div>
      </div>
      
      <button
        onClick={handleRepurpose}
        disabled={loading || !content.trim()}
        className="px-6 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-gray-600 text-white rounded font-medium transition-colors"
      >
        {loading ? 'Repurposing...' : '🔄 Repurpose Content'}
      </button>
      
      {result && (
        <div className="bg-gray-700 rounded-lg p-4 space-y-4">
          {result.error ? (
            <p className="text-red-400">{result.error}</p>
          ) : (
            result.results && Object.entries(result.results).map(([fmt, data]) => (
              <div key={fmt}>
                <span className="text-sm text-violet-400 font-medium">{fmt.toUpperCase()}</span>
                {data.mode && <span className="text-xs text-gray-500 ml-2">({data.mode})</span>}
                <p className="text-white mt-1 whitespace-pre-wrap text-sm">{data.content || data.error || ''}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

// Main AI Studio Component
export default function AIStudio() {
  const [activeTab, setActiveTab] = useState('caption');
  const { isDark } = useTheme();

  const tabs = [
    { id: 'caption', label: '✍️ Captions' },
    { id: 'image', label: '🎨 Images' },
    { id: 'video', label: '🎬 Videos' },
    { id: 'voice', label: '🎙️ Voice' },
    { id: 'faceless', label: '📱 Faceless' },
    { id: 'templates', label: '📋 Templates' },
    { id: 'repurpose', label: '🔄 Repurpose' }
  ];

  return (
    <div className={`min-h-screen p-6 transition-colors ${isDark ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-6xl mx-auto">
        <h1 className={`text-3xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>🤖 AI Studio</h1>
        <p className={`mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Create content with AI-powered tools</p>
        
        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map(tab => (
            <Tab
              key={tab.id}
              active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              isDark={isDark}
            >
              {tab.label}
            </Tab>
          ))}
        </div>
        
        <div className={`rounded-lg p-6 transition-colors ${isDark ? 'bg-gray-800' : 'bg-white shadow-lg border border-gray-200'}`}>
          {activeTab === 'caption' && <CaptionPanel isDark={isDark} />}
          {activeTab === 'image' && <ImagePanel isDark={isDark} />}
          {activeTab === 'video' && <VideoPanel isDark={isDark} />}
          {activeTab === 'voice' && <VoicePanel isDark={isDark} />}
          {activeTab === 'faceless' && <FacelessPanel isDark={isDark} />}
          {activeTab === 'templates' && <TemplatesPanel isDark={isDark} />}
          {activeTab === 'repurpose' && <RepurposerPanel isDark={isDark} />}
        </div>
      </div>
    </div>
  );
}
