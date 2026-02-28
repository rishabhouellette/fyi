import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { apiFetch } from '../lib/apiClient';
import {
  Settings,
  Key,
  Youtube,
  Instagram,
  Facebook,
  Twitter,
  Linkedin,
  TrendingUp,
  Eye,
  EyeOff,
  Save,
  Check,
  AlertCircle,
  ExternalLink,
  Trash2,
  Users,
  Brain,
  Sparkles,
  Shield,
} from 'lucide-react';

const SettingsPanel = () => {
  const { isDark } = useTheme();
  const [activeSection, setActiveSection] = useState('social');

  // ---- Social Media Credentials State ----
  const [platformCreds, setPlatformCreds] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState({});
  const [showSecrets, setShowSecrets] = useState({});
  const [formData, setFormData] = useState({});
  const [saveSuccess, setSaveSuccess] = useState({});

  // ---- AI Keys State ----
  const [aiKeys, setAiKeys] = useState({});
  const [aiLoading, setAiLoading] = useState(true);
  const [aiFormData, setAiFormData] = useState({});
  const [aiSaving, setAiSaving] = useState({});
  const [aiSaveSuccess, setAiSaveSuccess] = useState({});
  const [aiShowSecrets, setAiShowSecrets] = useState({});

  // ---- Social Media Platform Definitions ----
  const platforms = [
    {
      id: 'youtube',
      name: 'YouTube',
      icon: Youtube,
      color: 'from-red-500 to-red-600',
      fields: [
        { key: 'client_id', label: 'Client ID', placeholder: 'Your Google OAuth Client ID' },
        { key: 'client_secret', label: 'Client Secret', placeholder: 'Your Google OAuth Client Secret', secret: true }
      ],
      helpUrl: 'https://console.cloud.google.com/apis/credentials',
      helpText: 'Create OAuth 2.0 credentials in Google Cloud Console. Enable YouTube Data API v3.'
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: Facebook,
      color: 'from-blue-600 to-blue-700',
      fields: [
        { key: 'app_id', label: 'App ID', placeholder: 'Your Facebook App ID' },
        { key: 'app_secret', label: 'App Secret', placeholder: 'Your Facebook App Secret', secret: true }
      ],
      helpUrl: 'https://developers.facebook.com/apps',
      helpText: 'Create a Facebook App and get credentials from Basic Settings.'
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: Instagram,
      color: 'from-pink-500 via-purple-500 to-orange-500',
      fields: [
        { key: 'app_id', label: 'App ID (same as Facebook)', placeholder: 'Your Facebook App ID' },
        { key: 'app_secret', label: 'App Secret (same as Facebook)', placeholder: 'Your Facebook App Secret', secret: true }
      ],
      helpUrl: 'https://developers.facebook.com/apps',
      helpText: 'Instagram uses Facebook App credentials. Make sure Instagram Basic Display is configured.'
    },
    {
      id: 'twitter',
      name: 'Twitter/X',
      icon: Twitter,
      color: 'from-gray-700 to-gray-900',
      fields: [
        { key: 'api_key', label: 'API Key', placeholder: 'Your Twitter API Key' },
        { key: 'api_secret', label: 'API Secret', placeholder: 'Your Twitter API Secret', secret: true }
      ],
      helpUrl: 'https://developer.twitter.com/en/portal/dashboard',
      helpText: 'Create a Twitter App in the Developer Portal.'
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: Linkedin,
      color: 'from-blue-600 to-blue-800',
      fields: [
        { key: 'client_id', label: 'Client ID', placeholder: 'Your LinkedIn Client ID' },
        { key: 'client_secret', label: 'Client Secret', placeholder: 'Your LinkedIn Client Secret', secret: true }
      ],
      helpUrl: 'https://www.linkedin.com/developers/apps',
      helpText: 'Create a LinkedIn App and get OAuth 2.0 credentials.'
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: TrendingUp,
      color: 'from-black via-pink-600 to-cyan-500',
      fields: [
        { key: 'client_key', label: 'Client Key', placeholder: 'Your TikTok Client Key' },
        { key: 'client_secret', label: 'Client Secret', placeholder: 'Your TikTok Client Secret', secret: true }
      ],
      helpUrl: 'https://developers.tiktok.com/',
      helpText: 'Register as a TikTok developer and create an app.'
    }
  ];

  // ---- AI Service Definitions ----
  const aiServices = [
    {
      id: 'openai',
      name: 'OpenAI',
      description: 'GPT-4o, DALL-E — captions, images, content planning',
      color: 'from-emerald-500 to-teal-600',
      emoji: '🤖',
      helpUrl: 'https://platform.openai.com/api-keys',
      placeholder: 'sk-...',
    },
    {
      id: 'gemini',
      name: 'Google Gemini',
      description: 'Gemini 2.0 Flash — prompts, trends, content plans',
      color: 'from-blue-500 to-indigo-600',
      emoji: '💎',
      helpUrl: 'https://aistudio.google.com/apikey',
      placeholder: 'AIza...',
    },
    {
      id: 'anthropic',
      name: 'Anthropic Claude',
      description: 'Claude — advanced content generation',
      color: 'from-orange-500 to-amber-600',
      emoji: '🧠',
      helpUrl: 'https://console.anthropic.com/settings/keys',
      placeholder: 'sk-ant-...',
    },
    {
      id: 'elevenlabs',
      name: 'ElevenLabs',
      description: 'AI voice generation & text-to-speech',
      color: 'from-violet-500 to-purple-600',
      emoji: '🎙️',
      helpUrl: 'https://elevenlabs.io/app/settings/api-keys',
      placeholder: 'Your ElevenLabs API Key',
    },
    {
      id: 'stability',
      name: 'Stability AI',
      description: 'Stable Diffusion — AI image generation',
      color: 'from-purple-500 to-pink-600',
      emoji: '🎨',
      helpUrl: 'https://platform.stability.ai/account/keys',
      placeholder: 'sk-...',
    },
    {
      id: 'replicate',
      name: 'Replicate',
      description: 'Run open-source AI models in the cloud',
      color: 'from-gray-600 to-gray-800',
      emoji: '🔄',
      helpUrl: 'https://replicate.com/account/api-tokens',
      placeholder: 'r8_...',
    },
    {
      id: 'runway',
      name: 'Runway ML',
      description: 'AI video generation & editing',
      color: 'from-cyan-500 to-blue-600',
      emoji: '🎬',
      helpUrl: 'https://app.runwayml.com/settings',
      placeholder: 'Your Runway API Key',
    },
    {
      id: 'flux',
      name: 'Flux',
      description: 'Advanced AI image generation',
      color: 'from-rose-500 to-red-600',
      emoji: '⚡',
      helpUrl: 'https://flux.ai',
      placeholder: 'Your Flux API Key',
    },
    {
      id: 'ideogram',
      name: 'Ideogram',
      description: 'AI image generation with text rendering',
      color: 'from-yellow-500 to-orange-600',
      emoji: '✏️',
      helpUrl: 'https://ideogram.ai/manage-api',
      placeholder: 'Your Ideogram API Key',
    },
    {
      id: 'pika',
      name: 'Pika',
      description: 'AI video creation & animation',
      color: 'from-pink-500 to-rose-600',
      emoji: '🎞️',
      helpUrl: 'https://pika.art',
      placeholder: 'Your Pika API Key',
    },
    {
      id: 'kling',
      name: 'Kling AI',
      description: 'AI video generation',
      color: 'from-indigo-500 to-violet-600',
      emoji: '📽️',
      helpUrl: 'https://klingai.com',
      placeholder: 'Your Kling API Key',
    },
    {
      id: 'xai',
      name: 'Grok (xAI)',
      description: 'Grok chat & Imagine video/image generation',
      color: 'from-gray-700 to-black',
      emoji: '𝕏',
      helpUrl: 'https://console.x.ai',
      placeholder: 'xai-...',
    },
  ];

  // =====================================================
  // Social Media Credentials Logic
  // =====================================================
  useEffect(() => {
    loadCredentials();
    loadAiKeys();
  }, []);

  const loadCredentials = async () => {
    try {
      setLoading(true);
      const response = await apiFetch('/api/platform-credentials');
      if (response.ok) {
        const data = await response.json();
        setPlatformCreds(data.platforms || {});
        const initialForm = {};
        platforms.forEach(platform => {
          initialForm[platform.id] = {};
          platform.fields.forEach(field => {
            initialForm[platform.id][field.key] = '';
          });
        });
        setFormData(initialForm);
      }
    } catch (error) {
      console.error('Failed to load credentials:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (platformId, fieldKey, value) => {
    setFormData(prev => ({
      ...prev,
      [platformId]: { ...prev[platformId], [fieldKey]: value }
    }));
  };

  const handleSave = async (platformId) => {
    const credentials = formData[platformId];
    const toSave = {};
    Object.entries(credentials).forEach(([key, value]) => {
      if (value && value.trim()) toSave[key] = value.trim();
    });
    if (Object.keys(toSave).length === 0) {
      alert('Please enter at least one credential value');
      return;
    }
    setSaving(prev => ({ ...prev, [platformId]: true }));
    try {
      const response = await apiFetch('/api/platform-credentials', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: platformId, credentials: toSave })
      });
      if (response.ok) {
        setSaveSuccess(prev => ({ ...prev, [platformId]: true }));
        setTimeout(() => setSaveSuccess(prev => ({ ...prev, [platformId]: false })), 3000);
        loadCredentials();
        setFormData(prev => ({
          ...prev,
          [platformId]: Object.fromEntries(Object.keys(prev[platformId] || {}).map(k => [k, '']))
        }));
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed to save credentials');
      }
    } catch (error) {
      alert('Failed to save credentials');
    } finally {
      setSaving(prev => ({ ...prev, [platformId]: false }));
    }
  };

  const handleDelete = async (platformId) => {
    if (!confirm(`Are you sure you want to delete ${platformId} credentials?`)) return;
    try {
      const response = await apiFetch(`/api/platform-credentials/${platformId}`, { method: 'DELETE' });
      if (response.ok) loadCredentials();
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const toggleShowSecret = (key) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // =====================================================
  // AI Keys Logic
  // =====================================================
  const loadAiKeys = async () => {
    try {
      setAiLoading(true);
      const response = await apiFetch('/api/byok/keys');
      if (response.ok) {
        const data = await response.json();
        setAiKeys(data.services || {});
      }
    } catch (error) {
      console.error('Failed to load AI keys:', error);
    } finally {
      setAiLoading(false);
    }
  };

  const handleAiInputChange = (serviceId, value) => {
    setAiFormData(prev => ({ ...prev, [serviceId]: value }));
  };

  const handleAiSave = async (serviceId) => {
    const apiKey = (aiFormData[serviceId] || '').trim();
    if (!apiKey) {
      alert('Please enter an API key');
      return;
    }
    setAiSaving(prev => ({ ...prev, [serviceId]: true }));
    try {
      const response = await apiFetch('/api/byok/keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service: serviceId, api_key: apiKey })
      });
      if (response.ok) {
        setAiSaveSuccess(prev => ({ ...prev, [serviceId]: true }));
        setTimeout(() => setAiSaveSuccess(prev => ({ ...prev, [serviceId]: false })), 3000);
        loadAiKeys();
        setAiFormData(prev => ({ ...prev, [serviceId]: '' }));
      } else {
        const err = await response.json();
        alert(err.detail || 'Failed to save API key');
      }
    } catch (error) {
      alert('Failed to save API key');
    } finally {
      setAiSaving(prev => ({ ...prev, [serviceId]: false }));
    }
  };

  const handleAiDelete = async (serviceId) => {
    if (!confirm(`Delete ${serviceId} API key?`)) return;
    try {
      const response = await apiFetch(`/api/byok/keys/${serviceId}`, { method: 'DELETE' });
      if (response.ok) loadAiKeys();
    } catch (error) {
      console.error('Failed to delete AI key:', error);
    }
  };

  // =====================================================
  // Shared Styles
  // =====================================================
  const inputClass = `w-full px-4 py-3 rounded-xl border transition-colors focus:outline-none focus:ring-2 ${
    isDark
      ? 'bg-white/5 border-white/10 text-white placeholder-gray-500 focus:border-cyan-500/50 focus:ring-cyan-500/20'
      : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-400 focus:border-blue-500 focus:ring-blue-500/20'
  }`;

  const sectionBtnClass = (isActive) =>
    `flex items-center gap-3 px-6 py-4 rounded-2xl font-semibold text-base transition-all cursor-pointer ${
      isActive
        ? isDark
          ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/40 text-white shadow-lg shadow-cyan-500/10'
          : 'bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-300 text-blue-900 shadow-md'
        : isDark
          ? 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10 hover:text-white'
          : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 hover:text-gray-900 shadow-sm'
    }`;

  // =====================================================
  // Render
  // =====================================================
  if (loading || aiLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-500" />
      </div>
    );
  }

  const configuredSocialCount = platforms.filter(p => platformCreds[p.id]?.configured).length;
  const configuredAiCount = aiServices.filter(s => aiKeys[s.id]?.configured).length;

  return (
    <div className={`min-h-screen p-6 transition-colors ${isDark ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className={`text-3xl font-bold flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <Settings className="w-8 h-8 text-cyan-500" />
            Settings
          </h1>
          <p className={`mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Manage your platform connections and AI service API keys
          </p>
        </div>

        {/* Section Tabs */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button onClick={() => setActiveSection('social')} className={sectionBtnClass(activeSection === 'social')}>
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${activeSection === 'social' ? 'bg-gradient-to-br from-cyan-500 to-blue-600' : isDark ? 'bg-white/10' : 'bg-gray-200'}`}>
              <Users className={`w-5 h-5 ${activeSection === 'social' ? 'text-white' : isDark ? 'text-gray-400' : 'text-gray-500'}`} />
            </div>
            <div className="text-left">
              <div>Social Media</div>
              <div className={`text-xs font-normal ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                {configuredSocialCount}/{platforms.length} connected
              </div>
            </div>
          </button>

          <button onClick={() => setActiveSection('ai')} className={sectionBtnClass(activeSection === 'ai')}>
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${activeSection === 'ai' ? 'bg-gradient-to-br from-violet-500 to-fuchsia-600' : isDark ? 'bg-white/10' : 'bg-gray-200'}`}>
              <Brain className={`w-5 h-5 ${activeSection === 'ai' ? 'text-white' : isDark ? 'text-gray-400' : 'text-gray-500'}`} />
            </div>
            <div className="text-left">
              <div>AI Services</div>
              <div className={`text-xs font-normal ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                {configuredAiCount}/{aiServices.length} configured
              </div>
            </div>
          </button>
        </div>

        {/* ================================= */}
        {/* SECTION 1: Social Media           */}
        {/* ================================= */}
        {activeSection === 'social' && (
          <motion.div
            key="social"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Info Banner */}
            <div className={`p-4 rounded-xl border flex items-start gap-3 ${isDark ? 'bg-blue-500/10 border-blue-500/30' : 'bg-blue-50 border-blue-200'}`}>
              <Shield className={`w-5 h-5 mt-0.5 flex-shrink-0 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
              <div>
                <p className={`text-sm font-semibold ${isDark ? 'text-blue-200' : 'text-blue-800'}`}>
                  Why do I need API credentials?
                </p>
                <p className={`text-sm mt-1 ${isDark ? 'text-blue-300/80' : 'text-blue-700'}`}>
                  Each social platform requires you to register your own app to get OAuth credentials.
                  This allows FYIXT to post on your behalf. Your credentials are stored securely on your local machine.
                </p>
              </div>
            </div>

            {/* Platform Cards */}
            <div className="grid gap-5">
              {platforms.map((platform, idx) => {
                const Icon = platform.icon;
                const creds = platformCreds[platform.id] || { configured: false, keys: {} };
                const isConfigured = creds.configured;

                return (
                  <motion.div
                    key={platform.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.05 }}
                    className={`rounded-2xl border p-6 transition-colors ${isDark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    {/* Platform Header */}
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${platform.color} flex items-center justify-center`}>
                          <Icon className="w-6 h-6 text-white" />
                        </div>
                        <div>
                          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                            {platform.name}
                          </h3>
                          {isConfigured ? (
                            <span className="flex items-center gap-1 text-green-500 text-sm">
                              <Check className="w-4 h-4" /> Configured
                            </span>
                          ) : (
                            <span className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Not configured</span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <a
                          href={platform.helpUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={`px-3 py-1.5 rounded-lg text-sm flex items-center gap-1 transition-colors ${isDark ? 'bg-white/5 hover:bg-white/10 text-cyan-400' : 'bg-gray-100 hover:bg-gray-200 text-blue-600'}`}
                        >
                          <ExternalLink className="w-4 h-4" />
                          Get Credentials
                        </a>
                        {isConfigured && (
                          <button
                            onClick={() => handleDelete(platform.id)}
                            className={`p-2 rounded-lg transition-colors ${isDark ? 'hover:bg-red-500/20 text-red-400' : 'hover:bg-red-50 text-red-500'}`}
                            title="Delete credentials"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                      {platform.helpText}
                    </p>

                    {/* Credential Fields */}
                    <div className="space-y-3">
                      {platform.fields.map((field) => {
                        const fieldCreds = creds.keys?.[field.key] || {};
                        const isFieldConfigured = fieldCreds.configured;
                        const showKey = `${platform.id}_${field.key}`;
                        return (
                          <div key={field.key}>
                            <label className={`block text-sm mb-1 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                              {field.label}
                              {isFieldConfigured && (
                                <span className={`ml-2 text-xs ${isDark ? 'text-green-400' : 'text-green-600'}`}>
                                  ({fieldCreds.source}: {fieldCreds.masked})
                                </span>
                              )}
                            </label>
                            <div className="relative">
                              <input
                                type={field.secret && !showSecrets[showKey] ? 'password' : 'text'}
                                value={formData[platform.id]?.[field.key] || ''}
                                onChange={(e) => handleInputChange(platform.id, field.key, e.target.value)}
                                placeholder={isFieldConfigured ? 'Enter new value to update...' : field.placeholder}
                                className={`${inputClass} pr-12`}
                              />
                              {field.secret && (
                                <button
                                  type="button"
                                  onClick={() => toggleShowSecret(showKey)}
                                  className={`absolute right-3 top-1/2 -translate-y-1/2 ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-700'}`}
                                >
                                  {showSecrets[showKey] ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Save Button */}
                    <div className="mt-4 flex justify-end">
                      <button
                        onClick={() => handleSave(platform.id)}
                        disabled={saving[platform.id]}
                        className={`px-6 py-2 rounded-xl font-medium transition-all flex items-center gap-2 ${
                          saveSuccess[platform.id]
                            ? 'bg-green-500 text-white'
                            : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-400 hover:to-blue-400 text-white'
                        } disabled:opacity-50`}
                      >
                        {saving[platform.id] ? (
                          <><div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" /> Saving...</>
                        ) : saveSuccess[platform.id] ? (
                          <><Check className="w-4 h-4" /> Saved!</>
                        ) : (
                          <><Save className="w-4 h-4" /> Save Credentials</>
                        )}
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}

        {/* ================================= */}
        {/* SECTION 2: AI Services            */}
        {/* ================================= */}
        {activeSection === 'ai' && (
          <motion.div
            key="ai"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Info Banner */}
            <div className={`p-4 rounded-xl border flex items-start gap-3 ${isDark ? 'bg-violet-500/10 border-violet-500/30' : 'bg-violet-50 border-violet-200'}`}>
              <Sparkles className={`w-5 h-5 mt-0.5 flex-shrink-0 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
              <div>
                <p className={`text-sm font-semibold ${isDark ? 'text-violet-200' : 'text-violet-800'}`}>
                  Bring Your Own Key (BYOK)
                </p>
                <p className={`text-sm mt-1 ${isDark ? 'text-violet-300/80' : 'text-violet-700'}`}>
                  Add your API keys to unlock AI-powered features like XY-AI prompts, image generation, video creation, and voiceovers.
                  Keys are stored locally and never shared. Without keys, XY-AI uses smart offline fallback.
                </p>
              </div>
            </div>

            {/* AI Service Cards */}
            <div className="grid gap-4">
              {aiServices.map((service, idx) => {
                const info = aiKeys[service.id] || { configured: false };
                const isConfigured = info.configured;

                return (
                  <motion.div
                    key={service.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className={`rounded-2xl border p-5 transition-colors ${isDark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <div className="flex items-start gap-4">
                      {/* Icon / Emoji */}
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${service.color} flex items-center justify-center text-xl flex-shrink-0`}>
                        {service.emoji}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div>
                            <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                              {service.name}
                            </h3>
                            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                              {service.description}
                            </p>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0 ml-4">
                            {isConfigured && (
                              <span className="flex items-center gap-1 text-green-500 text-xs font-medium">
                                <Check className="w-3.5 h-3.5" />
                                {info.source === 'env' ? 'From .env' : 'Configured'}
                              </span>
                            )}
                            <a
                              href={service.helpUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10 text-gray-500' : 'hover:bg-gray-100 text-gray-400'}`}
                              title="Get API Key"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </a>
                            {isConfigured && info.source !== 'env' && (
                              <button
                                onClick={() => handleAiDelete(service.id)}
                                className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-red-500/20 text-red-400' : 'hover:bg-red-50 text-red-500'}`}
                                title="Delete key"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                        </div>

                        {/* Masked key display */}
                        {isConfigured && info.masked && (
                          <p className={`text-xs font-mono mb-2 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                            Current: {info.masked}
                          </p>
                        )}

                        {/* Input + Save */}
                        <div className="flex items-center gap-2 mt-2">
                          <div className="relative flex-1">
                            <input
                              type={aiShowSecrets[service.id] ? 'text' : 'password'}
                              value={aiFormData[service.id] || ''}
                              onChange={(e) => handleAiInputChange(service.id, e.target.value)}
                              onKeyDown={(e) => e.key === 'Enter' && handleAiSave(service.id)}
                              placeholder={isConfigured ? 'Enter new key to update...' : service.placeholder}
                              className={`${inputClass} pr-10 text-sm`}
                            />
                            <button
                              type="button"
                              onClick={() => setAiShowSecrets(prev => ({ ...prev, [service.id]: !prev[service.id] }))}
                              className={`absolute right-3 top-1/2 -translate-y-1/2 ${isDark ? 'text-gray-500 hover:text-white' : 'text-gray-400 hover:text-gray-700'}`}
                            >
                              {aiShowSecrets[service.id] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            </button>
                          </div>
                          <button
                            onClick={() => handleAiSave(service.id)}
                            disabled={aiSaving[service.id] || !(aiFormData[service.id] || '').trim()}
                            className={`px-4 py-3 rounded-xl font-medium text-sm transition-all flex items-center gap-1.5 flex-shrink-0 ${
                              aiSaveSuccess[service.id]
                                ? 'bg-green-500 text-white'
                                : 'bg-gradient-to-r from-violet-500 to-fuchsia-600 hover:from-violet-400 hover:to-fuchsia-500 text-white'
                            } disabled:opacity-40 disabled:cursor-not-allowed`}
                          >
                            {aiSaving[service.id] ? (
                              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                            ) : aiSaveSuccess[service.id] ? (
                              <Check className="w-4 h-4" />
                            ) : (
                              <Save className="w-4 h-4" />
                            )}
                            {aiSaveSuccess[service.id] ? 'Saved' : 'Save'}
                          </button>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default SettingsPanel;
