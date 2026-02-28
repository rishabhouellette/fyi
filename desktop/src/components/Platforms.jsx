import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { apiFetch } from '../lib/apiClient';
import { 
  Plus,
  Check,
  X,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  LayoutGrid,
  List,
  Minimize2,
  Maximize2,
  Youtube,
  Instagram,
  Facebook,
  Twitter,
  Linkedin,
  TrendingUp
} from 'lucide-react';

const Platforms = () => {
  const { isDark } = useTheme();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(null);
  const [activeByPlatform, setActiveByPlatform] = useState({});
  const [viewMode, setViewMode] = useState('grid'); // 'grid' | 'list'
  const [collapsedByPlatform, setCollapsedByPlatform] = useState({});

  const platformsAvailable = [
    {
      id: 'youtube',
      name: 'YouTube',
      icon: Youtube,
      color: 'from-red-500 to-red-600',
      description: 'Connect your YouTube channel',
      supportsVideo: true,
      supportsShorts: true
    },
    {
      id: 'instagram',
      name: 'Instagram',
      icon: Instagram,
      color: 'from-pink-500 via-purple-500 to-orange-500',
      description: 'Connect Instagram Business/Creator account',
      supportsVideo: true,
      supportsReels: true
    },
    {
      id: 'facebook',
      name: 'Facebook',
      icon: Facebook,
      color: 'from-blue-600 to-blue-700',
      description: 'Connect Facebook Page',
      supportsVideo: true,
      supportsStories: true
    },
    {
      id: 'twitter',
      name: 'Twitter/X',
      icon: Twitter,
      color: 'from-gray-700 to-gray-900',
      description: 'Connect Twitter account',
      supportsVideo: true,
      maxVideoDuration: 140
    },
    {
      id: 'linkedin',
      name: 'LinkedIn',
      icon: Linkedin,
      color: 'from-blue-600 to-blue-800',
      description: 'Connect LinkedIn profile or page',
      supportsVideo: true,
      professional: true
    },
    {
      id: 'tiktok',
      name: 'TikTok',
      icon: TrendingUp,
      color: 'from-black via-pink-600 to-cyan-500',
      description: 'Connect TikTok account',
      supportsVideo: true,
      maxVideoDuration: 60
    }
  ];

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      setLoading(true);
      // Load real accounts from Python backend
      const response = await apiFetch('/api/accounts');
      
      if (response.ok) {
        const data = await response.json();
        
        // Transform backend data to UI format
        const transformed = (data.accounts || []).map(acc => ({
          id: acc.id || acc.account_id,
          platform: acc.platform,
          name: acc.name || acc.account_name || (acc.platform.charAt(0).toUpperCase() + acc.platform.slice(1)),
          username: acc.username || acc.account_name || `@${acc.platform}_user`,
          status: acc.status || 'connected',
          connectedAt: acc.connected_at || new Date().toISOString(),
          stats: {
            followers: acc.followers || 0,
            posts: acc.total_posts || 0
          }
        }));
        
        setAccounts(transformed);
        // Default connected cards to the compact/minimized state.
        // Do not override any manual expand/collapse toggles already set in this session.
        setCollapsedByPlatform(prev => {
          const next = { ...prev };
          for (const p of new Set(transformed.map(a => a.platform))) {
            if (!(p in next)) next[p] = true;
          }
          return next;
        });

        // Load and/or initialize the active selection per platform.
        try {
          const activeResp = await apiFetch('/api/active-accounts');
          const activeData = activeResp.ok ? await activeResp.json() : null;
          const active = { ...(activeData?.active || {}) };

          const platforms = Array.from(new Set(transformed.map(a => a.platform)));
          const toSet = [];
          for (const p of platforms) {
            if (!active[p]) {
              const first = transformed.find(a => a.platform === p);
              if (first?.id) {
                active[p] = first.id;
                toSet.push({ platform: p, account_id: first.id });
              }
            }
          }

          // Persist defaults server-side (best effort).
          for (const item of toSet) {
            apiFetch('/api/active-accounts', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(item)
            }).catch(() => {});
          }

          setActiveByPlatform(active);
        } catch (e) {
          // Non-fatal; UI will fall back to first connected account.
          setActiveByPlatform({});
        }
      } else {
        throw new Error('Backend not responding');
      }
    } catch (error) {
      console.error('Failed to load accounts:', error);
      // Show empty state if backend unavailable
      setAccounts([]);
    } finally {
      setLoading(false);
    }
  };

  const setActiveAccount = async (platformId, accountId) => {
    try {
      setActiveByPlatform(prev => ({ ...prev, [platformId]: accountId }));
      const resp = await apiFetch('/api/active-accounts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ platform: platformId, account_id: accountId })
      });
      if (!resp.ok) {
        // Revert on failure.
        const text = await resp.text().catch(() => '');
        console.warn('Failed to persist active account:', text);
        loadAccounts();
      }
    } catch (e) {
      console.warn('Failed to set active account:', e);
      loadAccounts();
    }
  };

  const toggleCollapsed = (platformId) => {
    setCollapsedByPlatform(prev => ({ ...prev, [platformId]: !prev[platformId] }));
  };

  const connectAccount = async (platform) => {
    // Skip modal confirmation — go directly to OAuth
    setSelectedPlatform(platform);
    
    const platformMap = {
      'youtube': 'youtube',
      'instagram': 'instagram', 
      'facebook': 'facebook',
      'twitter': 'twitter',
      'linkedin': 'linkedin',
      'tiktok': 'tiktok'
    };
    const platformKey = platformMap[platform.id];
    
    try {
      const response = await apiFetch(`/oauth/start/${platformKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          account_name: `${platform.name}_Account`,
          return_url: window.location.href 
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        alert(data?.error || data?.detail || 'Failed to initiate OAuth');
        return;
      }
      
      if (data?.redirect && data?.auth_url) {
        window.open(data.auth_url, '_blank', 'noopener,noreferrer');
        pollForConnection(platformKey);
        return;
      }

      if (data?.success) {
        pollForConnection(platformKey);
      }
    } catch (error) {
      console.error('OAuth error:', error);
      alert(`Failed to connect account. Make sure the backend server is running.`);
    }
  };

  // handleConnect is now inlined into connectAccount for direct OAuth flow

  const pollForConnection = async (platformKey) => {
    // Poll backend for 2 minutes to check if OAuth completed
    const maxAttempts = 24; // 2 minutes (5 second intervals)
    let attempts = 0;

    const checkInterval = setInterval(async () => {
      attempts++;
      
      try {
        const response = await apiFetch('/api/accounts');
        const data = await response.json();
        
        // Check if new account was added for this platform
        const newAccount = data.accounts?.find(acc => 
          acc.platform === platformKey && 
          !accounts.find(existing => existing.id === acc.id)
        );

        if (newAccount) {
          clearInterval(checkInterval);
          loadAccounts(); // Reload all accounts
          setShowAddModal(false);
          setSelectedPlatform(null);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }

      if (attempts >= maxAttempts) {
        clearInterval(checkInterval);
        setShowAddModal(false);
        setSelectedPlatform(null);
      }
    }, 5000); // Check every 5 seconds
  };

  const disconnectAccount = async (account) => {
    try {
      // Use ID or fallback to username/name for old accounts
      const identifier = account.id || account.username || account.name;
      console.log('Disconnecting account:', identifier);
      
      // Call backend to disconnect
      const response = await apiFetch(`/api/accounts/${encodeURIComponent(identifier)}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) {
        console.error('Disconnect failed:', await response.text());
      }
      
      // Reload accounts
      loadAccounts();
    } catch (error) {
      console.error('Failed to disconnect account:', error);
    }
  };

  const refreshAccount = async (accountId) => {
    try {
      // Refresh account stats from backend
      const response = await apiFetch(`/api/accounts/${accountId}/refresh`, {
        method: 'POST'
      });
      
      if (response.ok) {
        loadAccounts(); // Reload all accounts
      }
    } catch (error) {
      console.error('Failed to refresh account:', error);
    }
  };

  const PlatformCard = ({ platform }) => {
    const Icon = platform.icon;
    const connectedAccounts = accounts.filter(acc => acc.platform === platform.id);
    const activeId = activeByPlatform[platform.id];
    const connected = connectedAccounts.find(a => a.id === activeId) || connectedAccounts[0];
    const isFacebook = platform.id === 'facebook';
    const isCollapsed = !!collapsedByPlatform[platform.id];
    const facebookPagesSummary = connected
      ? (connectedAccounts.length <= 1
          ? connected.name
          : `${connected.name} + ${connectedAccounts.length - 1} more`)
      : '';

    return (
      <motion.div
        whileHover={{ scale: 1.02, y: -5 }}
        className={`p-6 relative overflow-hidden group rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
      >
        {/* Gradient Background */}
        <div className={`absolute inset-0 bg-gradient-to-br ${platform.color} opacity-5 group-hover:opacity-10 transition-opacity`} />
        
        <div className="relative z-10">
          <div className="flex items-start justify-between mb-4">
            <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${platform.color} flex items-center justify-center`}>
              <Icon className="w-7 h-7 text-white" />
            </div>
            
            {connected ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-green-500">
                  <Check className="w-5 h-5" />
                  <span className="text-sm font-semibold">
                    Connected{connectedAccounts.length > 1 ? ` (${connectedAccounts.length})` : ''}
                  </span>
                </div>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => connectAccount(platform)}
                  className="px-3 py-1.5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg text-xs font-semibold text-white hover:shadow-lg transition-all flex items-center gap-1"
                  title="Connect another account"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add
                </motion.button>

                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => toggleCollapsed(platform.id)}
                  className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors ${isDark ? 'bg-white/5 hover:bg-white/10' : 'bg-gray-100 hover:bg-gray-200'}`}
                  title={isCollapsed ? 'Expand' : 'Minimize'}
                >
                  {isCollapsed ? (
                    <Maximize2 className={`w-4 h-4 ${isDark ? 'text-gray-200' : 'text-gray-600'}`} />
                  ) : (
                    <Minimize2 className={`w-4 h-4 ${isDark ? 'text-gray-200' : 'text-gray-600'}`} />
                  )}
                </motion.button>
              </div>
            ) : (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => connectAccount(platform)}
                className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-lg text-sm font-semibold text-white hover:shadow-lg transition-all"
              >
                <Plus className="w-4 h-4 inline mr-1" />
                Connect
              </motion.button>
            )}
          </div>

          <h3 className={`text-xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{platform.name}</h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{platform.description}</p>

          {connected && !isCollapsed && (
            <div className={`space-y-3 mt-4 pt-4 border-t ${isDark ? 'border-gray-700/50' : 'border-gray-200'}`}>
              <div className="flex items-center justify-between text-sm">
                <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>
                  {connectedAccounts.length > 1
                    ? (isFacebook ? 'Active Page' : 'Active Account')
                    : (isFacebook ? 'Page' : 'Account')}
                </span>
                {connectedAccounts.length > 1 ? (
                  <select
                    value={connected.id}
                    onChange={(e) => setActiveAccount(platform.id, e.target.value)}
                    className={`py-1 px-2 text-sm max-w-[60%] rounded border ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
                    title="Select which account/page to use for posting"
                  >
                    {connectedAccounts.map(a => (
                      <option key={a.id} value={a.id}>
                        {isFacebook ? a.name : `${a.name}${a.username ? ` (${a.username})` : ''}`}
                      </option>
                    ))}
                  </select>
                ) : (
                  <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{isFacebook ? facebookPagesSummary : connected.name}</span>
                )}
              </div>
              {!isFacebook && (
                <div className="flex items-center justify-between text-sm">
                  <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>Username</span>
                  <span className="font-semibold text-cyan-500">{connected.username}</span>
                </div>
              )}
              <div className="flex items-center justify-between text-sm">
                <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>Followers</span>
                <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{connected.stats.followers.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className={isDark ? 'text-gray-400' : 'text-gray-600'}>Posts</span>
                <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{connected.stats.posts}</span>
              </div>

              <div className="flex gap-2 mt-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => refreshAccount(connected.id)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors ${isDark ? 'bg-white/5 hover:bg-white/10 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => disconnectAccount(connected)}
                  className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2 ${isDark ? 'bg-red-500/10 hover:bg-red-500/20' : 'bg-red-50 hover:bg-red-100'} text-red-500`}
                >
                  <X className="w-4 h-4" />
                  Disconnect
                </motion.button>
              </div>
            </div>
          )}

          {/* Features */}
          <div className="flex flex-wrap gap-2 mt-4">
            {platform.supportsVideo && (
              <span className="px-2 py-1 bg-cyan-500/10 text-cyan-500 rounded text-xs">Video</span>
            )}
            {platform.supportsShorts && (
              <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded text-xs">Shorts</span>
            )}
            {platform.supportsReels && (
              <span className="px-2 py-1 bg-pink-500/10 text-pink-400 rounded text-xs">Reels</span>
            )}
            {platform.supportsStories && (
              <span className="px-2 py-1 bg-orange-500/10 text-orange-400 rounded text-xs">Stories</span>
            )}
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className={`text-4xl font-black mb-2 ${isDark ? 'gradient-text' : 'text-gray-900'}`}>Platform Accounts</h1>
          <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>Connect and manage your social media accounts</p>
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setViewMode(prev => (prev === 'grid' ? 'list' : 'grid'))}
          className={`w-12 h-12 rounded-xl flex items-center justify-center border transition-colors ${isDark ? 'bg-white/5 hover:bg-white/10 border-cyan-500/20' : 'bg-gray-100 hover:bg-gray-200 border-gray-300'}`}
          title={viewMode === 'grid' ? 'Switch to list view' : 'Switch to grid view'}
        >
          {viewMode === 'grid' ? (
            <List className="w-6 h-6 text-cyan-500" />
          ) : (
            <LayoutGrid className="w-6 h-6 text-cyan-500" />
          )}
        </motion.button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`p-4 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
        >
          <div className={`text-3xl font-black ${isDark ? 'gradient-text' : 'text-cyan-600'}`}>{accounts.length}</div>
          <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Connected Accounts</div>
        </motion.div>
        
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`p-4 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
        >
          <div className="text-3xl font-black text-green-500">
            {accounts.reduce((sum, acc) => sum + acc.stats.followers, 0).toLocaleString()}
          </div>
          <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Total Followers</div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`p-4 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
        >
          <div className="text-3xl font-black text-purple-500">
            {accounts.reduce((sum, acc) => sum + acc.stats.posts, 0)}
          </div>
          <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Total Posts</div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`p-4 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
        >
          <div className="text-3xl font-black text-cyan-500">
            {platformsAvailable.length - new Set(accounts.map(a => a.platform)).size}
          </div>
          <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Available Platforms</div>
        </motion.div>
      </div>

      {/* Info Banner */}
      {accounts.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-6 rounded-xl border transition-colors ${isDark ? 'bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border-cyan-500/30' : 'bg-gradient-to-r from-cyan-50 to-purple-50 border-cyan-200'}`}
        >
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-cyan-500 flex-shrink-0 mt-1" />
            <div>
              <h3 className={`text-lg font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Welcome to Platform Accounts!</h3>
              <p className={`mb-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Connect your social media accounts to start scheduling posts, analyzing performance, and growing your audience.
              </p>
              <ul className={`space-y-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <li>✓ Schedule posts across all platforms from one place</li>
                <li>✓ Auto-post your viral clips with AI-generated captions</li>
                <li>✓ Track performance and engagement metrics</li>
                <li>✓ Manage multiple accounts effortlessly</li>
              </ul>
            </div>
          </div>
        </motion.div>
      )}

      {/* Platforms */}
      <div>
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Available Platforms</h2>

        {viewMode === 'grid' ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {platformsAvailable.map((platform, idx) => (
              <motion.div
                key={platform.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.1 }}
              >
                <PlatformCard platform={platform} />
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="space-y-3">
            {platformsAvailable.map((platform, idx) => {
              const Icon = platform.icon;
              const connectedAccounts = accounts.filter(acc => acc.platform === platform.id);
              const activeId = activeByPlatform[platform.id];
              const connected = connectedAccounts.find(a => a.id === activeId) || connectedAccounts[0];
              const isFacebook = platform.id === 'facebook';
              const isCollapsed = !!collapsedByPlatform[platform.id];

              return (
                <motion.div
                  key={platform.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.05 }}
                  className="card-cyber p-4"
                >
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-4 min-w-0">
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${platform.color} flex items-center justify-center cyber-glow flex-shrink-0`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-3">
                          <h3 className="text-lg font-bold truncate">{platform.name}</h3>
                          {connected ? (
                            <span className="text-sm font-semibold text-cyber-green">
                              Connected{connectedAccounts.length > 1 ? ` (${connectedAccounts.length})` : ''}
                            </span>
                          ) : (
                            <span className="text-sm text-gray-500">Not connected</span>
                          )}
                        </div>
                        <p className="text-sm text-gray-400 truncate">{platform.description}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      {connected ? (
                        <>
                          {connectedAccounts.length > 1 && !isCollapsed && (
                            <select
                              value={connected.id}
                              onChange={(e) => setActiveAccount(platform.id, e.target.value)}
                              className="input-cyber py-1 px-2 text-sm"
                              title="Select which account/page to use for posting"
                            >
                              {connectedAccounts.map(a => (
                                <option key={a.id} value={a.id}>
                                  {isFacebook ? a.name : `${a.name}${a.username ? ` (${a.username})` : ''}`}
                                </option>
                              ))}
                            </select>
                          )}

                          <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={() => toggleCollapsed(platform.id)}
                            className="w-10 h-10 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center"
                            title={isCollapsed ? 'Expand details' : 'Minimize details'}
                          >
                            {isCollapsed ? (
                              <Maximize2 className="w-4 h-4 text-gray-200" />
                            ) : (
                              <Minimize2 className="w-4 h-4 text-gray-200" />
                            )}
                          </motion.button>

                          {!isCollapsed && (
                            <>
                              <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => refreshAccount(connected.id)}
                                className="w-10 h-10 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center"
                                title="Refresh"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </motion.button>
                              <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={() => disconnectAccount(connected)}
                                className="w-10 h-10 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 flex items-center justify-center"
                                title="Disconnect"
                              >
                                <X className="w-4 h-4" />
                              </motion.button>
                            </>
                          )}
                        </>
                      ) : (
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => connectAccount(platform)}
                          className="px-4 py-2 bg-gradient-to-r from-cyber-primary to-cyber-purple rounded-lg text-sm font-semibold hover:shadow-lg hover:shadow-cyber-primary/50 transition-all"
                        >
                          <Plus className="w-4 h-4 inline mr-1" />
                          Connect
                        </motion.button>
                      )}
                    </div>
                  </div>

                  {connected && !isCollapsed && (
                    <div className="mt-4 pt-4 border-t border-gray-700/50 grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                      <div className="flex items-center justify-between md:block">
                        <div className="text-gray-400">{isFacebook ? 'Page' : 'Account'}</div>
                        <div className="font-semibold truncate">{connected.name}</div>
                      </div>
                      {!isFacebook && (
                        <div className="flex items-center justify-between md:block">
                          <div className="text-gray-400">Username</div>
                          <div className="font-semibold text-cyber-primary truncate">{connected.username}</div>
                        </div>
                      )}
                      <div className="flex items-center justify-between md:block">
                        <div className="text-gray-400">Posts</div>
                        <div className="font-semibold">{connected.stats.posts}</div>
                      </div>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
};

export default Platforms;
