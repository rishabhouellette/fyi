import React, { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, Hash, Copy, Sparkles } from 'lucide-react';
import { generateCaption, generateHashtags } from '../lib/apiClient';

const AITools = () => {
  const [activeTab, setActiveTab] = useState('caption');

  const [topic, setTopic] = useState('');
  const [platform, setPlatform] = useState('instagram');
  const [tone, setTone] = useState('casual');
  const [keywords, setKeywords] = useState('');
  const [maxLen, setMaxLen] = useState(220);
  const [includeHashtags, setIncludeHashtags] = useState(true);
  const [hashtagsCount, setHashtagsCount] = useState(8);

  const [captionResult, setCaptionResult] = useState({ caption: '', hashtags: [], mode: null, model: null });
  const [hashtagsResult, setHashtagsResult] = useState({ hashtags: [], mode: null, model: null });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const keywordList = useMemo(() => {
    return (keywords || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
      .slice(0, 20);
  }, [keywords]);

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // ignore; some environments block clipboard
    }
  };

  const onGenerateCaption = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await generateCaption({
        topic,
        platform,
        tone,
        keywords: keywordList,
        max_length: Number(maxLen) || 220,
        include_hashtags: Boolean(includeHashtags),
        hashtags_count: Number(hashtagsCount) || 8
      });
      setCaptionResult({
        caption: res?.caption || '',
        hashtags: Array.isArray(res?.hashtags) ? res.hashtags : [],
        mode: res?.mode || null,
        model: res?.model || null
      });
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const onGenerateHashtags = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await generateHashtags({
        topic,
        platform,
        count: Number(hashtagsCount) || 12,
        include_trending: true
      });
      setHashtagsResult({
        hashtags: Array.isArray(res?.hashtags) ? res.hashtags : [],
        mode: res?.mode || null,
        model: res?.model || null
      });
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const TabButton = ({ id, icon: Icon, label }) => {
    const isActive = activeTab === id;
    return (
      <button
        onClick={() => setActiveTab(id)}
        className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-all ${
          isActive ? 'bg-gradient-to-br from-cyber-primary to-cyber-purple cyber-glow' : 'bg-white/5 hover:bg-white/10'
        }`}
      >
        <Icon className="w-4 h-4" />
        <span className="text-sm font-semibold">{label}</span>
      </button>
    );
  };

  const modeLabel = (mode, model) => {
    if (!mode) return '';
    if (mode === 'ollama') return model ? `Ollama (${model})` : 'Ollama';
    return 'Fallback';
  };

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-4xl font-black mb-2 gradient-text">AI Tools</h1>
        <p className="text-gray-400">Generate captions and hashtags for your posts.</p>
      </motion.div>

      <div className="card-cyber p-6">
        <div className="flex flex-wrap gap-3 mb-6">
          <TabButton id="caption" icon={Sparkles} label="Caption Generator" />
          <TabButton id="hashtags" icon={Hash} label="Hashtag Generator" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Inputs */}
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Topic / Context</label>
              <textarea
                className="input-cyber w-full"
                rows={5}
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="What is the post about? (e.g., new product launch, behind-the-scenes, tutorial...)"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-semibold mb-2">Platform</label>
                <select className="input-cyber w-full" value={platform} onChange={(e) => setPlatform(e.target.value)}>
                  <option value="instagram">Instagram</option>
                  <option value="facebook">Facebook</option>
                  <option value="youtube">YouTube</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Tone</label>
                <select className="input-cyber w-full" value={tone} onChange={(e) => setTone(e.target.value)}>
                  <option value="casual">Casual</option>
                  <option value="professional">Professional</option>
                  <option value="funny">Funny</option>
                  <option value="inspirational">Inspirational</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold mb-2">Keywords (comma-separated)</label>
              <input
                className="input-cyber w-full"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="e.g., creator economy, short-form, workflow"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold mb-2">Max Length</label>
                <input
                  className="input-cyber w-full"
                  type="number"
                  min={40}
                  max={1000}
                  value={maxLen}
                  onChange={(e) => setMaxLen(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Hashtag Count</label>
                <input
                  className="input-cyber w-full"
                  type="number"
                  min={1}
                  max={30}
                  value={hashtagsCount}
                  onChange={(e) => setHashtagsCount(e.target.value)}
                />
              </div>

              <div className="flex items-end">
                <label className="flex items-center gap-2 text-sm text-gray-300">
                  <input
                    type="checkbox"
                    checked={includeHashtags}
                    onChange={(e) => setIncludeHashtags(e.target.checked)}
                  />
                  Include hashtags
                </label>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                {error}
              </div>
            )}

            <div className="flex gap-3">
              {activeTab === 'caption' ? (
                <button
                  className="btn-cyber px-5 py-3 flex items-center gap-2"
                  disabled={loading || !topic.trim()}
                  onClick={onGenerateCaption}
                >
                  <Brain className="w-5 h-5" />
                  {loading ? 'Generating…' : 'Generate Caption'}
                </button>
              ) : (
                <button
                  className="btn-cyber px-5 py-3 flex items-center gap-2"
                  disabled={loading || !topic.trim()}
                  onClick={onGenerateHashtags}
                >
                  <Hash className="w-5 h-5" />
                  {loading ? 'Generating…' : 'Generate Hashtags'}
                </button>
              )}
            </div>
          </div>

          {/* Outputs */}
          <div className="space-y-4">
            {activeTab === 'caption' ? (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold">Caption</h3>
                  <div className="text-xs text-gray-400">{modeLabel(captionResult.mode, captionResult.model)}</div>
                </div>
                <textarea
                  className="input-cyber w-full"
                  rows={6}
                  value={captionResult.caption}
                  readOnly
                  placeholder="Generated caption will appear here"
                />
                <div className="flex gap-3">
                  <button
                    className="btn-cyber px-4 py-2 flex items-center gap-2"
                    disabled={!captionResult.caption}
                    onClick={() => copyToClipboard(captionResult.caption)}
                  >
                    <Copy className="w-4 h-4" />
                    Copy caption
                  </button>
                </div>

                <div className="flex items-center justify-between mt-4">
                  <h3 className="text-lg font-bold">Hashtags</h3>
                </div>
                <textarea
                  className="input-cyber w-full"
                  rows={4}
                  value={(captionResult.hashtags || []).join(' ')}
                  readOnly
                  placeholder="Hashtags will appear here"
                />
                <div className="flex gap-3">
                  <button
                    className="btn-cyber px-4 py-2 flex items-center gap-2"
                    disabled={!captionResult.hashtags?.length}
                    onClick={() => copyToClipboard((captionResult.hashtags || []).join(' '))}
                  >
                    <Copy className="w-4 h-4" />
                    Copy hashtags
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold">Hashtags</h3>
                  <div className="text-xs text-gray-400">{modeLabel(hashtagsResult.mode, hashtagsResult.model)}</div>
                </div>
                <textarea
                  className="input-cyber w-full"
                  rows={10}
                  value={(hashtagsResult.hashtags || []).join(' ')}
                  readOnly
                  placeholder="Generated hashtags will appear here"
                />
                <div className="flex gap-3">
                  <button
                    className="btn-cyber px-4 py-2 flex items-center gap-2"
                    disabled={!hashtagsResult.hashtags?.length}
                    onClick={() => copyToClipboard((hashtagsResult.hashtags || []).join(' '))}
                  >
                    <Copy className="w-4 h-4" />
                    Copy hashtags
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AITools;
