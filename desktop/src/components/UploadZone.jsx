import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { 
  Upload,
  Sparkles,
  Hash,
  Loader2
} from 'lucide-react';
import { uploadFileWithProgress, generateCaption, generateHashtags } from '../lib/apiClient';

const UploadZone = ({ onUploadedFileIdChange, onDraftChange, onItemsChange, actionsRef }) => {
  const { isDark } = useTheme();
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [items, setItems] = useState([]); // { key, file, uploadedFileId, caption, status, progress, error }
  const [activeKey, setActiveKey] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [applyCaptionToAll, setApplyCaptionToAll] = useState(false);
  const [appendHashtags, setAppendHashtags] = useState(false);
  const [hashtagsText, setHashtagsText] = useState('');
  const [autoUploading, setAutoUploading] = useState(false);

  const [aiTopic, setAiTopic] = useState('');
  const [aiPlatform, setAiPlatform] = useState('instagram');
  const [aiTone, setAiTone] = useState('casual');
  const [aiBusy, setAiBusy] = useState(false);
  const [aiError, setAiError] = useState('');

  const activeItem = items.find(x => x.key === activeKey) || null;
  const file = activeItem?.file || null;
  const uploadedFileId = activeItem?.uploadedFileId || null;
  const postCaption = activeItem?.caption || '';

  const setCaption = (caption) => {
    setItems(prev => prev.map(x => {
      if (applyCaptionToAll) return { ...x, caption };
      if (x.key === activeKey) return { ...x, caption };
      return x;
    }));
  };

  const fileStem = (name) => {
    const s = String(name || '').trim();
    if (!s) return '';
    return s.replace(/\.[^/.]+$/, '');
  };

  const normalizeSpaces = (s) => String(s || '').replace(/\s+/g, ' ').trim();

  useEffect(() => {
    // Auto-fill the AI topic from the active file name unless the user already typed a custom one.
    if (!activeItem?.file?.name) return;
    setAiTopic(prev => {
      const p = String(prev || '').trim();
      if (p) return prev;
      return fileStem(activeItem.file.name);
    });
  }, [activeKey]);

  const runGenerateCaption = async () => {
    if (!items.length) return;
    const topic = String(aiTopic || '').trim() || fileStem(activeItem?.file?.name || '') || 'my video';
    setAiError('');
    setAiBusy(true);
    try {
      const data = await generateCaption({
        topic,
        platform: aiPlatform,
        tone: aiTone,
        keywords: [],
        max_length: 220,
        include_hashtags: false,
        hashtags_count: 0
      });
      const caption = String(data?.caption || '').trim();
      if (caption) setCaption(caption);
    } catch (e) {
      setAiError(String(e?.message || e || 'Failed to generate caption'));
    } finally {
      setAiBusy(false);
    }
  };

  const runGenerateHashtags = async () => {
    if (!items.length) return;
    const topic = String(aiTopic || '').trim() || fileStem(activeItem?.file?.name || '') || 'my video';
    setAiError('');
    setAiBusy(true);
    try {
      const data = await generateHashtags({
        topic,
        platform: aiPlatform,
        count: 12,
        include_trending: true
      });
      const tags = Array.isArray(data?.hashtags) ? data.hashtags : [];
      const text = tags.filter(Boolean).join(' ');
      if (text) setHashtagsText(text);
    } catch (e) {
      setAiError(String(e?.message || e || 'Failed to generate hashtags'));
    } finally {
      setAiBusy(false);
    }
  };

  const computeFinalCaption = (it) => {
    const stem = fileStem(it?.file?.name || it?.filename || it?.title || '');
    const base = stem || '';
    const captionPart = normalizeSpaces(it?.caption || '');
    const tagsPart = appendHashtags ? normalizeSpaces(hashtagsText) : '';

    const parts = [base];
    if (captionPart) parts.push(captionPart);
    if (tagsPart) parts.push(tagsPart);
    return normalizeSpaces(parts.join(' '));
  };

  const formatBytes = (bytes) => {
    const b = Number(bytes || 0);
    if (!b) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.min(Math.floor(Math.log(b) / Math.log(1024)), units.length - 1);
    const v = b / Math.pow(1024, i);
    const digits = i === 0 ? 0 : 1;
    return `${v.toFixed(digits)} ${units[i]}`;
  };

  const addFiles = (files) => {
    const list = Array.from(files || []).filter(f => f && String(f.type || '').startsWith('video/'));
    if (list.length === 0) return;

    setItems(prev => {
      const existingKeys = new Set(prev.map(p => `${p.file?.name}|${p.file?.size}|${p.file?.lastModified}`));
      const toAdd = [];
      for (const f of list) {
        const dedupeKey = `${f.name}|${f.size}|${f.lastModified}`;
        if (existingKeys.has(dedupeKey)) continue;
        toAdd.push({
          key: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
          file: f,
          uploadedFileId: null,
          caption: applyCaptionToAll ? (postCaption || '') : '',
          status: 'pending',
          progress: 0,
          error: null
        });
      }
      const next = [...prev, ...toAdd];
      // If nothing active yet, activate first newly added.
      if (!activeKey && toAdd.length > 0) {
        setActiveKey(toAdd[0].key);
      }
      return next;
    });
  };

  const removeItem = (key) => {
    setItems(prev => {
      const next = prev.filter(x => x.key !== key);
      if (key === activeKey) {
        setActiveKey(next[0]?.key || null);
      }
      return next;
    });
  };

  useEffect(() => {
    if (!actionsRef) return;
    actionsRef.current = {
      removeItem,
      clearAll: () => {
        setItems([]);
        setActiveKey(null);
      }
    };
  }, [actionsRef, activeKey, items]);

  useEffect(() => {
    if (typeof onUploadedFileIdChange === 'function') {
      onUploadedFileIdChange(uploadedFileId);
    }
  }, [uploadedFileId, onUploadedFileIdChange]);

  useEffect(() => {
    if (typeof onDraftChange !== 'function') return;
    const title = (file && file.name ? file.name.replace(/\.[^/.]+$/, '') : '') || '';
    const caption = activeItem ? computeFinalCaption(activeItem) : '';
    onDraftChange({ title, caption });
  }, [file, activeItem, appendHashtags, hashtagsText, postCaption, onDraftChange]);

  useEffect(() => {
    if (typeof onItemsChange !== 'function') return;
    const payload = (items || []).map((it) => {
      const filename = it?.file?.name || '';
      const title = filename ? filename.replace(/\.[^/.]+$/, '') : '';
      return {
        key: it?.key,
        uploadedFileId: it?.uploadedFileId || null,
        filename,
        size: it?.file?.size || 0,
        caption: computeFinalCaption(it),
        title,
        status: it?.status || 'pending',
        progress: Number(it?.progress || 0),
        error: it?.error || null,
      };
    });
    onItemsChange(payload);
  }, [items, appendHashtags, hashtagsText, onItemsChange]);

  const ensureUploaded = async (itemKey) => {
    const it = items.find(x => x.key === itemKey);
    if (!it) throw new Error('Missing file item');
    if (it.uploadedFileId) return it.uploadedFileId;
    const f = it.file;
    if (!f) throw new Error('No file selected');
    if (!(f instanceof File)) throw new Error('Please select a video file from this browser session.');

    setItems(prev => prev.map(x => (x.key === itemKey ? { ...x, status: 'uploading', progress: Math.max(0, x.progress || 0), error: null } : x)));

    const upload = await uploadFileWithProgress(f, ({ percent }) => {
      setItems(prev => prev.map(x => (x.key === itemKey ? { ...x, progress: Math.max(0, Math.min(100, percent || 0)) } : x)));
    });

    const fileId = upload.file_id;
    setItems(prev => prev.map(x => (x.key === itemKey ? { ...x, uploadedFileId: fileId, status: 'uploaded', progress: 100 } : x)));
    return fileId;
  };

  // Auto-upload any pending items sequentially.
  useEffect(() => {
    if (autoUploading) return;
    const next = (items || []).find(it => (it?.status || 'pending') === 'pending');
    if (!next?.key) return;

    setAutoUploading(true);
    (async () => {
      try {
        await ensureUploaded(next.key);
      } catch (e) {
        setItems(prev => prev.map(x => (x.key === next.key ? { ...x, status: 'error', error: e?.message || String(e) } : x)));
      } finally {
        setAutoUploading(false);
      }
    })();
  }, [items, autoUploading]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);

    addFiles(e.dataTransfer.files);
  }, []);

  const handleFileSelect = async (selectedFiles) => {
    addFiles(selectedFiles);
  };

  const handleBrowse = async () => {
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
      fileInputRef.current.click();
    }
  };

  return (
    <div className="space-y-6">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="video/*"
        style={{ display: 'none' }}
        onChange={(e) => {
          const selected = e.target.files;
          if (selected && selected.length) handleFileSelect(selected);
        }}
      />
      {/* Tabs */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 flex items-center justify-between gap-3 flex-wrap rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
      >
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`px-3 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === 'upload' 
              ? (isDark ? 'bg-white/10 border border-white/20 text-white' : 'bg-gray-100 border border-gray-300 text-gray-900') 
              : (isDark ? 'bg-white/5 border border-white/10 hover:bg-white/10 text-white' : 'bg-gray-50 border border-gray-200 hover:bg-gray-100 text-gray-700')}`}
          >
            Upload
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('caption')}
            className={`px-3 py-2 rounded-lg text-sm font-semibold transition-all ${activeTab === 'caption' 
              ? (isDark ? 'bg-white/10 border border-white/20 text-white' : 'bg-gray-100 border border-gray-300 text-gray-900') 
              : (isDark ? 'bg-white/5 border border-white/10 hover:bg-white/10 text-white' : 'bg-gray-50 border border-gray-200 hover:bg-gray-100 text-gray-700')}`}
          >
            Caption
          </button>
        </div>
      </motion.div>

      {/* Upload Zone */}
      {activeTab === 'upload' && (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed transition-all ${
          isDragging 
            ? 'border-cyan-500 bg-cyan-500/10 scale-105' 
            : isDark ? 'border-cyan-500/30 bg-white/5' : 'border-gray-300 bg-gray-50'
        }`}
      >
        <div className="p-12 flex flex-col items-center justify-center gap-6">
          <motion.div
            animate={{ 
              scale: isDragging ? 1.2 : 1,
              rotate: isDragging ? 5 : 0
            }}
            className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center"
          >
            <Upload className="w-12 h-12 text-white" />
          </motion.div>

          <div className="text-center">
            <h3 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {isDragging ? 'Drop your video here' : 'Drag & Drop Video'}
            </h3>
            <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              or <button onClick={handleBrowse} className="text-cyan-500 hover:underline">browse</button> to choose a file
            </p>
            <p className={`text-sm mt-2 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
              Supports MP4, MOV, AVI, MKV, WebM (max 2GB)
            </p>
          </div>

        </div>

        {/* Animated Background */}
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 to-purple-500/20 pointer-events-none"
          />
        )}
      </motion.div>
      )}

      {/* Caption Tab */}
      {activeTab === 'caption' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-6 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
        >
          <div className="space-y-6">
            {/* AI Assist */}
            <div className={`rounded-xl border p-4 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-4 h-4 text-cyan-500" />
                <div className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>AI Assist</div>
                <div className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>(uses local Ollama if available)</div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div className="md:col-span-2">
                  <label className={`block text-xs mb-1 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>Topic</label>
                  <input
                    value={aiTopic}
                    onChange={(e) => setAiTopic(e.target.value)}
                    placeholder={items.length ? 'e.g. Tesla AI news, Gym motivation, Travel vlog…' : 'Upload a video first'}
                    className={`w-full px-3 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                    disabled={items.length === 0 || aiBusy}
                  />
                </div>

                <div>
                  <label className={`block text-xs mb-1 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>Platform</label>
                  <select
                    value={aiPlatform}
                    onChange={(e) => setAiPlatform(e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-white border-gray-300 text-gray-900'}`}
                    disabled={items.length === 0 || aiBusy}
                  >
                    <option value="instagram">Instagram</option>
                    <option value="facebook">Facebook</option>
                    <option value="tiktok">TikTok</option>
                    <option value="youtube">YouTube</option>
                  </select>
                </div>
              </div>

              <div className="flex items-end justify-between gap-3 flex-wrap mt-3">
                <div>
                  <label className="block text-xs text-gray-300 mb-1">Tone</label>
                  <select
                    value={aiTone}
                    onChange={(e) => setAiTone(e.target.value)}
                    className="input-cyber"
                    disabled={items.length === 0 || aiBusy}
                  >
                    <option value="casual">Casual</option>
                    <option value="professional">Professional</option>
                    <option value="funny">Funny</option>
                    <option value="inspirational">Inspirational</option>
                  </select>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={runGenerateCaption}
                    className="btn-cyber flex items-center gap-2"
                    disabled={items.length === 0 || aiBusy}
                    title="Generate a caption from your topic"
                    type="button"
                  >
                    {aiBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    Generate caption
                  </button>
                  <button
                    onClick={runGenerateHashtags}
                    className="btn-cyber-secondary flex items-center gap-2"
                    disabled={items.length === 0 || aiBusy}
                    title="Generate hashtags from your topic"
                    type="button"
                  >
                    {aiBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Hash className="w-4 h-4" />}
                    Generate hashtags
                  </button>
                </div>
              </div>

              {aiError ? (
                <div className="mt-3 text-xs text-red-300">{aiError}</div>
              ) : null}
            </div>

            {/* Caption section */}
            <div>
              <div className="flex items-center justify-between gap-3 flex-wrap mb-2">
                <label className="text-sm font-semibold">Caption</label>
                <label className="flex items-center gap-2 text-xs text-gray-300 select-none cursor-pointer">
                  <input
                    type="checkbox"
                    checked={applyCaptionToAll}
                    onChange={(e) => {
                      const checked = !!e.target.checked;
                      setApplyCaptionToAll(checked);
                      if (checked) {
                        // When enabling, immediately apply the active caption to all items.
                        const current = String(postCaption || '');
                        setItems(prev => prev.map(x => ({ ...x, caption: current })));
                      }
                    }}
                    className="w-4 h-4 rounded border-white/20"
                    disabled={items.length === 0}
                  />
                  Apply caption to all videos
                </label>
              </div>
              <textarea
                value={postCaption}
                onChange={(e) => setCaption(e.target.value)}
                placeholder={applyCaptionToAll ? 'This caption will be applied to all videos…' : 'Add a caption for the active video…'}
                rows={4}
                className="input-cyber w-full"
                disabled={items.length === 0}
              />
              <div className="text-xs text-gray-400 mt-2">
                Caption output always starts with the file name.
              </div>
            </div>

            {/* Hashtag section */}
            <div>
              <div className="flex items-center justify-between gap-3 flex-wrap mb-2">
                <label className="text-sm font-semibold">Hashtags</label>
                <label className="flex items-center gap-2 text-xs text-gray-300 select-none cursor-pointer">
                  <input
                    type="checkbox"
                    checked={appendHashtags}
                    onChange={(e) => setAppendHashtags(!!e.target.checked)}
                    className="w-4 h-4 rounded border-white/20"
                    disabled={items.length === 0}
                  />
                  Add hashtags to file name
                </label>
              </div>
              <textarea
                value={hashtagsText}
                onChange={(e) => setHashtagsText(e.target.value)}
                placeholder="#movie #ai #tesla"
                rows={3}
                className="input-cyber w-full"
                disabled={items.length === 0}
              />
              <div className="text-xs text-gray-400 mt-2">
                When enabled, hashtags are appended after the file name (and caption if provided).
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default UploadZone;
