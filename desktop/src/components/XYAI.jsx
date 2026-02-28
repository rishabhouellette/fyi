import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import {
  xyaiGeneratePrompts,
  xyaiGetTrends,
  xyaiContentPlan,
  xyaiListNiches,
  xyaiChat,
  xyaiChatModels,
} from '../lib/apiClient';
import {
  Sparkles,
  TrendingUp,
  Calendar,
  Zap,
  Copy,
  Check,
  ChevronRight,
  Hash,
  Clock,
  Target,
  Lightbulb,
  BarChart3,
  RefreshCw,
  Brain,
  Flame,
  ArrowRight,
  Wand2,
  Layers,
  MessageCircle,
  Send,
  User,
  Bot,
  Trash,
} from 'lucide-react';

// ---- Tab Button ----
function Tab({ active, onClick, children, icon: Icon, isDark }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-5 py-3 rounded-xl font-semibold text-sm transition-all ${
        active
          ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/25'
          : isDark
            ? 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-900'
      }`}
    >
      {Icon && <Icon className="w-4 h-4" />}
      {children}
    </button>
  );
}

// ---- Copy Button ----
function CopyBtn({ text, isDark }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button
      onClick={handleCopy}
      className={`p-1.5 rounded-lg transition-colors ${isDark ? 'hover:bg-white/10 text-gray-400' : 'hover:bg-gray-200 text-gray-500'}`}
      title="Copy"
    >
      {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
    </button>
  );
}

// ---- Prompt Generator Panel ----
function PromptGenerator({ isDark }) {
  const [goal, setGoal] = useState('');
  const [platform, setPlatform] = useState('instagram');
  const [contentType, setContentType] = useState('post');
  const [tone, setTone] = useState('engaging');
  const [audience, setAudience] = useState('');
  const [niche, setNiche] = useState('');
  const [count, setCount] = useState(3);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const platforms = ['instagram', 'youtube', 'tiktok', 'facebook', 'twitter', 'linkedin'];
  const contentTypes = ['post', 'reel', 'story', 'tweet', 'video', 'carousel', 'thread'];
  const tones = ['engaging', 'casual', 'professional', 'funny', 'inspirational', 'educational', 'controversial', 'storytelling'];

  const handleGenerate = async () => {
    if (!goal.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await xyaiGeneratePrompts({
        goal: goal.trim(),
        platform,
        content_type: contentType,
        tone,
        audience: audience.trim(),
        niche: niche.trim(),
        count,
      });
      setResults(data);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const inputClass = `w-full rounded-xl px-4 py-3 border transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
    isDark ? 'bg-gray-800/50 border-gray-700 text-white placeholder-gray-500' : 'bg-white border-gray-200 text-gray-900 placeholder-gray-400'
  }`;
  const selectClass = `rounded-xl px-3 py-2.5 border transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
    isDark ? 'bg-gray-800/50 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'
  }`;
  const labelClass = `block text-xs font-semibold uppercase tracking-wider mb-1.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`;

  return (
    <div className="space-y-6">
      {/* Main Input */}
      <div className="relative">
        <div className={`absolute -inset-0.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 rounded-2xl opacity-20 blur`} />
        <div className={`relative p-6 rounded-2xl border ${isDark ? 'bg-gray-800/80 border-gray-700' : 'bg-white border-gray-200 shadow-sm'}`}>
          <label className={labelClass}>What's your content goal?</label>
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
            placeholder='e.g. "Promote my coffee brand", "grow my tech YouTube channel", "sell handmade jewelry"'
            className={inputClass}
          />
        </div>
      </div>

      {/* Options Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <label className={labelClass}>Platform</label>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} className={`${selectClass} w-full`}>
            {platforms.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Content Type</label>
          <select value={contentType} onChange={(e) => setContentType(e.target.value)} className={`${selectClass} w-full`}>
            {contentTypes.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Tone</label>
          <select value={tone} onChange={(e) => setTone(e.target.value)} className={`${selectClass} w-full`}>
            {tones.map(t => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Ideas Count</label>
          <select value={count} onChange={(e) => setCount(parseInt(e.target.value))} className={`${selectClass} w-full`}>
            {[1,2,3,4,5,6,7,8,9,10].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      </div>

      {/* Optional Fields */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className={labelClass}>Target Audience (optional)</label>
          <input
            type="text"
            value={audience}
            onChange={(e) => setAudience(e.target.value)}
            placeholder="e.g. Gen-Z, professionals, fitness enthusiasts"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Niche (optional)</label>
          <input
            type="text"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            placeholder="e.g. fitness, tech, food, beauty"
            className={inputClass}
          />
        </div>
      </div>

      {/* Generate Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleGenerate}
        disabled={loading || !goal.trim()}
        className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${
          loading || !goal.trim()
            ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
            : 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white hover:shadow-lg hover:shadow-violet-500/25'
        }`}
      >
        {loading ? (
          <><RefreshCw className="w-5 h-5 animate-spin" /> XY-AI is thinking...</>
        ) : (
          <><Brain className="w-5 h-5" /> Generate Content Ideas</>
        )}
      </motion.button>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">{error}</div>
      )}

      {/* Results */}
      {results?.prompts && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className={`w-5 h-5 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
            <h3 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Generated Ideas
            </h3>
            {results.mode && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${isDark ? 'bg-violet-500/20 text-violet-300' : 'bg-violet-100 text-violet-700'}`}>
                {results.mode.replace('xy-ai-', '').replace('-', ' ')}
              </span>
            )}
          </div>

          <AnimatePresence>
            {results.prompts.map((prompt, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
                className={`p-5 rounded-2xl border transition-colors ${isDark ? 'bg-gray-800/60 border-gray-700 hover:border-violet-500/50' : 'bg-white border-gray-200 hover:border-violet-300 shadow-sm'}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-7 h-7 rounded-lg bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center text-white text-xs font-bold">
                        {idx + 1}
                      </span>
                      <h4 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        {prompt.title}
                      </h4>
                    </div>

                    {prompt.hook && (
                      <div className={`flex items-start gap-2 mb-3 p-3 rounded-xl ${isDark ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-yellow-50 border border-yellow-200'}`}>
                        <Flame className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                        <p className={`text-sm font-medium ${isDark ? 'text-yellow-300' : 'text-yellow-700'}`}>{prompt.hook}</p>
                      </div>
                    )}

                    <p className={`text-sm leading-relaxed whitespace-pre-line ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      {prompt.caption}
                    </p>

                    {prompt.hashtags?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {prompt.hashtags.map((tag, i) => (
                          <span key={i} className={`text-xs px-2 py-1 rounded-lg ${isDark ? 'bg-violet-500/15 text-violet-300' : 'bg-violet-100 text-violet-700'}`}>
                            {tag.startsWith('#') ? tag : `#${tag}`}
                          </span>
                        ))}
                      </div>
                    )}

                    {prompt.format_suggestion && (
                      <div className={`flex items-center gap-1.5 mt-3 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Layers className="w-3.5 h-3.5" />
                        Format: {prompt.format_suggestion}
                      </div>
                    )}
                  </div>
                  <CopyBtn text={`${prompt.hook || ''}\n\n${prompt.caption || ''}\n\n${(prompt.hashtags || []).join(' ')}`} isDark={isDark} />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

// ---- Trend Discovery Panel ----
function TrendDiscovery({ isDark }) {
  const [niche, setNiche] = useState('');
  const [platform, setPlatform] = useState('instagram');
  const [country, setCountry] = useState('US');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [niches, setNiches] = useState([]);

  useEffect(() => {
    xyaiListNiches().then(d => setNiches(d.niches || [])).catch(() => {});
  }, []);

  const handleDiscover = async () => {
    setLoading(true);
    try {
      const data = await xyaiGetTrends({ niche: niche.trim(), platform, country });
      setResults(data);
    } catch (err) {
      setResults({ error: err.message });
    }
    setLoading(false);
  };

  const inputClass = `w-full rounded-xl px-4 py-3 border transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
    isDark ? 'bg-gray-800/50 border-gray-700 text-white placeholder-gray-500' : 'bg-white border-gray-200 text-gray-900 placeholder-gray-400'
  }`;
  const selectClass = `rounded-xl px-3 py-2.5 border transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
    isDark ? 'bg-gray-800/50 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'
  }`;
  const labelClass = `block text-xs font-semibold uppercase tracking-wider mb-1.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`;
  const cardClass = `p-5 rounded-2xl border ${isDark ? 'bg-gray-800/60 border-gray-700' : 'bg-white border-gray-200 shadow-sm'}`;

  return (
    <div className="space-y-6">
      {/* Niche quick picks */}
      <div>
        <label className={labelClass}>Quick Pick a Niche</label>
        <div className="flex flex-wrap gap-2">
          {niches.map(n => (
            <button
              key={n}
              onClick={() => setNiche(n)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                niche === n
                  ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white'
                  : isDark
                    ? 'bg-white/5 text-gray-400 hover:bg-white/10'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {n.charAt(0).toUpperCase() + n.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className={labelClass}>Or type your niche</label>
          <input
            type="text"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            placeholder="e.g. sustainable fashion"
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Platform</label>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} className={`${selectClass} w-full`}>
            {['instagram', 'youtube', 'tiktok', 'facebook', 'twitter', 'linkedin'].map(p => (
              <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className={labelClass}>Country</label>
          <select value={country} onChange={(e) => setCountry(e.target.value)} className={`${selectClass} w-full`}>
            {['US','UK','CA','AU','IN','DE','FR','BR','JP','KR','AE','SA','PK','NG'].map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleDiscover}
        disabled={loading}
        className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${
          loading ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:shadow-lg hover:shadow-emerald-500/25'
        }`}
      >
        {loading ? (
          <><RefreshCw className="w-5 h-5 animate-spin" /> Scanning trends...</>
        ) : (
          <><TrendingUp className="w-5 h-5" /> Discover Trends</>
        )}
      </motion.button>

      {results?.error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">{results.error}</div>
      )}

      {results && !results.error && (
        <div className="space-y-6">
          {/* AI Insights (if available) */}
          {results.ai_insights && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className={`${cardClass} border-violet-500/30`}>
              <div className="flex items-center gap-2 mb-4">
                <Brain className={`w-5 h-5 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
                <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>AI-Powered Insights</h3>
              </div>
              {results.ai_insights.emerging_trends && (
                <div className="mb-3">
                  <p className={`text-xs font-semibold uppercase tracking-wider mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Emerging Trends</p>
                  <div className="flex flex-wrap gap-2">
                    {results.ai_insights.emerging_trends.map((t, i) => (
                      <span key={i} className={`text-sm px-3 py-1.5 rounded-lg ${isDark ? 'bg-emerald-500/15 text-emerald-300' : 'bg-emerald-100 text-emerald-700'}`}>
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {results.ai_insights.predicted_viral && (
                <div className={`p-3 rounded-xl mb-3 ${isDark ? 'bg-yellow-500/10 border border-yellow-500/20' : 'bg-yellow-50 border border-yellow-200'}`}>
                  <p className={`text-xs font-semibold ${isDark ? 'text-yellow-400' : 'text-yellow-600'}`}>Predicted Viral Topic</p>
                  <p className={`text-sm mt-1 ${isDark ? 'text-yellow-200' : 'text-yellow-800'}`}>{results.ai_insights.predicted_viral}</p>
                </div>
              )}
              {results.ai_insights.engagement_tip && (
                <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                  <Lightbulb className="w-4 h-4 inline mr-1 text-yellow-500" />
                  {results.ai_insights.engagement_tip}
                </p>
              )}
            </motion.div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Trending Hashtags */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className={cardClass}>
              <div className="flex items-center gap-2 mb-3">
                <Hash className={`w-5 h-5 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
                <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Trending Hashtags</h3>
                <CopyBtn text={(results.trending_hashtags || []).join(' ')} isDark={isDark} />
              </div>
              <div className="flex flex-wrap gap-2">
                {(results.trending_hashtags || []).map((tag, i) => (
                  <span key={i} className={`text-sm px-2.5 py-1 rounded-lg ${isDark ? 'bg-violet-500/15 text-violet-300' : 'bg-violet-100 text-violet-700'}`}>{tag}</span>
                ))}
              </div>
            </motion.div>

            {/* Viral Hooks */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className={cardClass}>
              <div className="flex items-center gap-2 mb-3">
                <Flame className={`w-5 h-5 ${isDark ? 'text-orange-400' : 'text-orange-600'}`} />
                <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Viral Hooks</h3>
              </div>
              <ul className="space-y-2">
                {(results.viral_hooks || []).map((hook, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <ChevronRight className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isDark ? 'text-orange-400' : 'text-orange-500'}`} />
                    <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{hook}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* Trending Topics */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className={cardClass}>
              <div className="flex items-center gap-2 mb-3">
                <Zap className={`w-5 h-5 ${isDark ? 'text-yellow-400' : 'text-yellow-600'}`} />
                <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Hot Topics</h3>
              </div>
              <ul className="space-y-2">
                {(results.trending_topics || []).map((topic, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <ArrowRight className={`w-4 h-4 mt-0.5 flex-shrink-0 ${isDark ? 'text-yellow-400' : 'text-yellow-500'}`} />
                    <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{topic}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* Content Formats & Best Times */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className={cardClass}>
              <div className="flex items-center gap-2 mb-3">
                <Clock className={`w-5 h-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
                <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Best Times & Formats</h3>
              </div>
              <div className="mb-3">
                <p className={`text-xs font-semibold uppercase mb-1.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Best posting times</p>
                <div className="flex flex-wrap gap-2">
                  {(results.best_posting_times || []).map((time, i) => (
                    <span key={i} className={`text-sm px-2.5 py-1 rounded-lg ${isDark ? 'bg-blue-500/15 text-blue-300' : 'bg-blue-100 text-blue-700'}`}>{time}</span>
                  ))}
                </div>
              </div>
              <div>
                <p className={`text-xs font-semibold uppercase mb-1.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Top formats</p>
                <ul className="space-y-1">
                  {(results.content_formats || []).map((fmt, i) => (
                    <li key={i} className={`text-sm flex items-center gap-1.5 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
                      <Layers className="w-3.5 h-3.5 text-blue-400" /> {fmt}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Content Plan Panel ----
function ContentPlan({ isDark }) {
  const [niche, setNiche] = useState('');
  const [platform, setPlatform] = useState('instagram');
  const [days, setDays] = useState(7);
  const [ppd, setPpd] = useState(1);
  const [tone, setTone] = useState('engaging');
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    if (!niche.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await xyaiContentPlan({
        niche: niche.trim(),
        platform,
        days,
        posts_per_day: ppd,
        tone,
      });
      setPlan(data);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const inputClass = `w-full rounded-xl px-4 py-3 border transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
    isDark ? 'bg-gray-800/50 border-gray-700 text-white placeholder-gray-500' : 'bg-white border-gray-200 text-gray-900 placeholder-gray-400'
  }`;
  const selectClass = `rounded-xl px-3 py-2.5 border transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50 ${
    isDark ? 'bg-gray-800/50 border-gray-700 text-white' : 'bg-white border-gray-200 text-gray-900'
  }`;
  const labelClass = `block text-xs font-semibold uppercase tracking-wider mb-1.5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <label className={labelClass}>Your Niche / Brand</label>
          <input
            type="text"
            value={niche}
            onChange={(e) => setNiche(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
            placeholder='e.g. "vegan cooking", "startup SaaS", "indie game dev"'
            className={inputClass}
          />
        </div>
        <div>
          <label className={labelClass}>Platform</label>
          <select value={platform} onChange={(e) => setPlatform(e.target.value)} className={`${selectClass} w-full`}>
            {['instagram', 'youtube', 'tiktok', 'facebook', 'twitter', 'linkedin'].map(p => (
              <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className={labelClass}>Days</label>
          <select value={days} onChange={(e) => setDays(parseInt(e.target.value))} className={`${selectClass} w-full`}>
            {[3, 5, 7, 14, 21, 30].map(d => <option key={d} value={d}>{d} days</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Posts/Day</label>
          <select value={ppd} onChange={(e) => setPpd(parseInt(e.target.value))} className={`${selectClass} w-full`}>
            {[1, 2, 3].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label className={labelClass}>Tone</label>
          <select value={tone} onChange={(e) => setTone(e.target.value)} className={`${selectClass} w-full`}>
            {['engaging', 'casual', 'professional', 'educational', 'funny', 'inspirational'].map(t => (
              <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
        </div>
      </div>

      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={handleGenerate}
        disabled={loading || !niche.trim()}
        className={`w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-3 transition-all ${
          loading || !niche.trim() ? 'bg-gray-600 text-gray-400 cursor-not-allowed' : 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white hover:shadow-lg hover:shadow-blue-500/25'
        }`}
      >
        {loading ? (
          <><RefreshCw className="w-5 h-5 animate-spin" /> Planning your content...</>
        ) : (
          <><Calendar className="w-5 h-5" /> Generate {days}-Day Content Plan</>
        )}
      </motion.button>

      {error && <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">{error}</div>}

      {plan?.plan && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Calendar className={`w-5 h-5 ${isDark ? 'text-blue-400' : 'text-blue-600'}`} />
            <h3 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Your {days}-Day Content Plan
            </h3>
            {plan.mode && (
              <span className={`text-xs px-2 py-0.5 rounded-full ${isDark ? 'bg-blue-500/20 text-blue-300' : 'bg-blue-100 text-blue-700'}`}>
                {plan.mode.replace('xy-ai-', '')}
              </span>
            )}
          </div>

          <div className="space-y-3">
            {(plan.plan || []).map((day, dIdx) => (
              <motion.div
                key={dIdx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: dIdx * 0.05 }}
                className={`rounded-2xl border overflow-hidden ${isDark ? 'bg-gray-800/60 border-gray-700' : 'bg-white border-gray-200 shadow-sm'}`}
              >
                <div className={`px-5 py-3 flex items-center gap-3 ${isDark ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
                  <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center text-white text-sm font-bold">
                    {day.day}
                  </span>
                  <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Day {day.day}</span>
                </div>
                <div className="p-4 space-y-3">
                  {(day.posts || []).map((post, pIdx) => (
                    <div key={pIdx} className={`p-3 rounded-xl ${isDark ? 'bg-gray-700/30' : 'bg-gray-50'}`}>
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{post.title}</p>
                          <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{post.caption}</p>
                          {post.hashtags?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {post.hashtags.map((t, i) => (
                                <span key={i} className={`text-xs px-1.5 py-0.5 rounded ${isDark ? 'bg-blue-500/15 text-blue-300' : 'bg-blue-100 text-blue-700'}`}>{t}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          {post.best_time && (
                            <span className={`text-xs px-2 py-1 rounded-lg flex items-center gap-1 ${isDark ? 'bg-emerald-500/15 text-emerald-300' : 'bg-emerald-100 text-emerald-700'}`}>
                              <Clock className="w-3 h-3" /> {post.best_time}
                            </span>
                          )}
                          <CopyBtn text={`${post.title}\n${post.caption}\n${(post.hashtags || []).join(' ')}`} isDark={isDark} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ---- Main XY-AI Component ----

// ---- Chat Panel ----
function ChatPanel({ isDark }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState(null);
  const [selectedModel, setSelectedModel] = useState('auto');
  const [availableModels, setAvailableModels] = useState([{ id: 'auto', name: 'Auto (Best Available)', provider: 'auto' }]);
  const chatEndRef = React.useRef(null);
  const inputRef = React.useRef(null);

  // Load available models on mount
  useEffect(() => {
    xyaiChatModels().then(data => {
      if (data.models) setAvailableModels(data.models);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    // Welcome message
    setMessages([{
      role: 'assistant',
      content: "Hey! \uD83D\uDC4B I'm XY-AI, your content & marketing assistant.\n\nI can help with:\n\u2022 Content ideas & captions\n\u2022 Trending hashtags & topics\n\u2022 Posting strategies & best times\n\u2022 Platform-specific tips\n\u2022 Growth & engagement advice\n\nWhat would you like help with?",
      timestamp: new Date(),
    }]);
  }, []);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', content: text, timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      // Build history from existing messages (skip welcome)
      const history = messages
        .filter(m => m.role === 'user' || (m.role === 'assistant' && messages.indexOf(m) > 0))
        .map(m => ({ role: m.role, content: m.content }));

      const data = await xyaiChat({ message: text, history, preferred_model: selectedModel });
      setMode(data.mode || null);
      
      // Build fallback notice if model was switched
      let replyContent = data.reply || 'Sorry, I could not generate a response.';
      if (data.fallback && data.requested_model) {
        const reason = (data.fallback_reason || '').includes('429') || (data.fallback_reason || '').includes('Rate')
          ? 'rate limited'
          : 'unavailable';
        const usedLabel = data.model || 'offline fallback';
        replyContent = `⚠️ **${data.requested_model}** is ${reason}. Responded via **${usedLabel}** instead.\n\n${replyContent}`;
      }
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: replyContent,
        timestamp: new Date(),
        model: data.model,
        mode: data.mode,
        fallback: data.fallback || false,
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Oops, something went wrong. Please try again.',
        timestamp: new Date(),
        error: true,
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: "Chat cleared! \uD83D\uDD04 How can I help you?",
      timestamp: new Date(),
    }]);
    setMode(null);
  };

  const formatMessage = (text) => {
    // Simple markdown-like formatting
    return text.split('\n').map((line, i) => {
      // Bold
      line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      // Bullet points
      if (line.trim().startsWith('\u2022') || line.trim().startsWith('-') || line.trim().match(/^\d+\./)) {
        return <div key={i} className="ml-2" dangerouslySetInnerHTML={{ __html: line }} />;
      }
      return <div key={i} dangerouslySetInnerHTML={{ __html: line || '&nbsp;' }} />;
    });
  };

  return (
    <div className="flex flex-col" style={{ height: 'calc(100vh - 320px)', minHeight: '500px' }}>
      {/* Chat Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageCircle className={`w-5 h-5 ${isDark ? 'text-violet-400' : 'text-violet-600'}`} />
          <h2 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Chat with XY-AI</h2>
          {mode && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              mode.includes('gemini') ? 'bg-blue-500/20 text-blue-400' :
              mode.includes('openai') ? 'bg-emerald-500/20 text-emerald-400' :
              mode.includes('ollama') ? 'bg-orange-500/20 text-orange-400' :
              mode.includes('anthropic') ? 'bg-amber-500/20 text-amber-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {mode.includes('gemini') ? '\uD83D\uDC8E Gemini' :
               mode.includes('openai') ? '\uD83E\uDD16 OpenAI' :
               mode.includes('ollama') ? '\uD83E\uDDCA Ollama' :
               mode.includes('anthropic') ? '\uD83E\uDDE0 Claude' :
               '\u26A1 Offline'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Model Selector */}
          <select
            value={selectedModel}
            onChange={e => setSelectedModel(e.target.value)}
            className={`text-sm rounded-lg px-3 py-1.5 border transition-colors appearance-none cursor-pointer ${
              isDark
                ? 'bg-gray-800 border-gray-600 text-white hover:border-violet-500/50'
                : 'bg-white border-gray-300 text-gray-800 hover:border-violet-500'
            }`}
            title="Select AI model"
          >
            {availableModels.map(m => (
              <option key={m.id} value={m.id}>
                {m.provider !== 'auto' ? `${m.name}` : m.name}
              </option>
            ))}
          </select>
          <button
            onClick={clearChat}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              isDark ? 'bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
            }`}
            title="Clear chat"
          >
            <Trash className="w-3.5 h-3.5" />
            Clear
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className={`flex-1 overflow-y-auto rounded-xl p-4 space-y-4 ${
        isDark ? 'bg-gray-900/60 border border-gray-700/40' : 'bg-gray-50 border border-gray-200'
      }`}>
        <AnimatePresence>
          {messages.map((msg, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'assistant' && (
                <div className={`w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center ${
                  msg.error
                    ? 'bg-red-500/20'
                    : 'bg-gradient-to-br from-violet-600 to-fuchsia-600'
                }`}>
                  <Bot className={`w-4 h-4 ${msg.error ? 'text-red-400' : 'text-white'}`} />
                </div>
              )}
              <div className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                msg.role === 'user'
                  ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white'
                  : msg.error
                    ? isDark ? 'bg-red-500/10 border border-red-500/30 text-red-300' : 'bg-red-50 border border-red-200 text-red-700'
                    : isDark ? 'bg-gray-800 border border-gray-700/50 text-gray-200' : 'bg-white border border-gray-200 text-gray-800 shadow-sm'
              }`}>
                <div className="text-sm leading-relaxed whitespace-pre-wrap">
                  {formatMessage(msg.content)}
                </div>
                {msg.model && (
                  <div className={`text-xs mt-2 opacity-50`}>
                    via {msg.model}
                  </div>
                )}
              </div>
              {msg.role === 'user' && (
                <div className={`w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center ${
                  isDark ? 'bg-white/10' : 'bg-gray-200'
                }`}>
                  <User className={`w-4 h-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`} />
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-xl flex-shrink-0 flex items-center justify-center bg-gradient-to-br from-violet-600 to-fuchsia-600">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className={`rounded-2xl px-4 py-3 ${isDark ? 'bg-gray-800 border border-gray-700/50' : 'bg-white border border-gray-200 shadow-sm'}`}>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 rounded-full bg-violet-500 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={chatEndRef} />
      </div>

      {/* Quick Suggestions */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {[
            'What are the best posting times?',
            'Give me caption ideas for a coffee brand',
            'What\'s trending on Instagram?',
            'How do I grow my TikTok?',
          ].map((suggestion, i) => (
            <button
              key={i}
              onClick={() => { setInput(suggestion); }}
              className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
                isDark
                  ? 'bg-violet-500/10 text-violet-300 hover:bg-violet-500/20 border border-violet-500/20'
                  : 'bg-violet-50 text-violet-700 hover:bg-violet-100 border border-violet-200'
              }`}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input Area */}
      <div className={`mt-3 flex items-end gap-2 rounded-xl p-2 ${
        isDark ? 'bg-gray-800/80 border border-gray-700/50' : 'bg-white border border-gray-200 shadow-sm'
      }`}>
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
          placeholder="Ask XY-AI anything about content & marketing..."
          rows={1}
          className={`flex-1 resize-none px-3 py-2.5 rounded-lg text-sm focus:outline-none ${
            isDark ? 'bg-transparent text-white placeholder-gray-500' : 'bg-transparent text-gray-900 placeholder-gray-400'
          }`}
          style={{ maxHeight: '120px' }}
          onInput={(e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
          }}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className={`p-2.5 rounded-xl transition-all flex-shrink-0 ${
            input.trim() && !loading
              ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40'
              : isDark ? 'bg-white/5 text-gray-600' : 'bg-gray-100 text-gray-400'
          } disabled:cursor-not-allowed`}
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}

export default function XYAI() {
  const [activeTab, setActiveTab] = useState('prompts');
  const { isDark } = useTheme();

  const tabs = [
    { id: 'prompts', label: 'Prompt Generator', icon: Wand2 },
    { id: 'trends', label: 'Trend Discovery', icon: TrendingUp },
    { id: 'plan', label: 'Content Planner', icon: Calendar },
    { id: 'chat', label: 'Chat', icon: MessageCircle },
  ];

  return (
    <div className={`min-h-screen p-6 transition-colors ${isDark ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-2">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-600 to-fuchsia-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={`text-3xl font-black ${isDark ? 'text-white' : 'text-gray-900'}`}>
              XY-AI
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              FYIXT's AI engine — smart prompts, trending topics & content planning
            </p>
          </div>
        </div>

        {/* Powered-by badge */}
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium mb-6 ${
          isDark ? 'bg-violet-500/10 text-violet-300 border border-violet-500/20' : 'bg-violet-50 text-violet-700 border border-violet-200'
        }`}>
          <Sparkles className="w-3 h-3" />
          Powered by Ollama / OpenAI / Gemini (or works offline with smart fallback)
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {tabs.map(tab => (
            <Tab
              key={tab.id}
              active={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
              icon={tab.icon}
              isDark={isDark}
            >
              {tab.label}
            </Tab>
          ))}
        </div>

        {/* Tab Content */}
        <div className={`rounded-2xl p-6 transition-colors ${isDark ? 'bg-gray-800/40 border border-gray-700/50' : 'bg-white shadow-lg border border-gray-200'}`}>
          {activeTab === 'prompts' && <PromptGenerator isDark={isDark} />}
          {activeTab === 'trends' && <TrendDiscovery isDark={isDark} />}
          {activeTab === 'plan' && <ContentPlan isDark={isDark} />}
          {activeTab === 'chat' && <ChatPanel isDark={isDark} />}
        </div>
      </div>
    </div>
  );
}
