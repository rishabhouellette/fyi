import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Plus,
  Check,
  X,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  Youtube,
  Instagram,
  Facebook,
  Twitter,
  Linkedin,
  TrendingUp
} from 'lucide-react';

// API endpoint - using HTTPS for Facebook OAuth compliance
const API_BASE = 'https://localhost:8080';

const Platforms = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState(null);

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
      const response = await fetch('https://localhost:8080/api/accounts');
      
      if (response.ok) {
        const data = await response.json();
        
        // Transform backend data to UI format
        const transformed = (data.accounts || []).map(acc => ({
          id: acc.id || acc.account_id,
          platform: acc.platform,
          name: acc.platform.charAt(0).toUpperCase() + acc.platform.slice(1),
          username: acc.username || acc.account_name || `@${acc.platform}_user`,
          status: acc.status || 'connected',
          connectedAt: acc.connected_at || new Date().toISOString(),
          stats: {
            followers: acc.followers || 0,
            posts: acc.total_posts || 0
          }
        }));
        
        setAccounts(transformed);
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

  const connectAccount = (platform) => {
    setSelectedPlatform(platform);
    setShowAddModal(true);
  };

  const handleConnect = async () => {
    if (!selectedPlatform) return;

    try {
      // Start OAuth flow with Python backend
      const platformMap = {
        'youtube': 'youtube',
        'instagram': 'instagram', 
        'facebook': 'facebook',
        'twitter': 'twitter',
        'linkedin': 'linkedin',
        'tiktok': 'tiktok'
      };

      const platformKey = platformMap[selectedPlatform.id];
      
      // Call backend OAuth initiation
      const response = await fetch(`https://localhost:8080/oauth/start/${platformKey}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          account_name: `${selectedPlatform.name}_Account`,
          return_url: window.location.href 
        })
      });

      const data = await response.json();
      
      if (!response.ok) {
        // Show error message
        alert(data.error || 'Failed to initiate OAuth');
        setShowAddModal(false);
        return;
      }
      
      if (data.success && data.message) {
        // OAuth flow started successfully
        // Poll for completion
        pollForConnection(platformKey);
      }
    } catch (error) {
      console.error('OAuth error:', error);
      alert('Failed to connect account. Make sure the backend server is running on port 8080.');
    }
  };

  const pollForConnection = async (platformKey) => {
    // Poll backend for 2 minutes to check if OAuth completed
    const maxAttempts = 24; // 2 minutes (5 second intervals)
    let attempts = 0;

    const checkInterval = setInterval(async () => {
      attempts++;
      
      try {
        const response = await fetch('https://localhost:8080/api/accounts');
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
      const response = await fetch(`https://localhost:8080/api/accounts/${encodeURIComponent(identifier)}`, {
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
      const response = await fetch(`https://localhost:8080/api/accounts/${accountId}/refresh`, {
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
    const connected = accounts.find(acc => acc.platform === platform.id);

    return (
      <motion.div
        whileHover={{ scale: 1.02, y: -5 }}
        className="card-cyber p-6 relative overflow-hidden group"
      >
        {/* Gradient Background */}
        <div className={`absolute inset-0 bg-gradient-to-br ${platform.color} opacity-5 group-hover:opacity-10 transition-opacity`} />
        
        <div className="relative z-10">
          <div className="flex items-start justify-between mb-4">
            <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${platform.color} flex items-center justify-center cyber-glow`}>
              <Icon className="w-7 h-7 text-white" />
            </div>
            
            {connected ? (
              <div className="flex items-center gap-2 text-cyber-green">
                <Check className="w-5 h-5" />
                <span className="text-sm font-semibold">Connected</span>
              </div>
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

          <h3 className="text-xl font-bold mb-2">{platform.name}</h3>
          <p className="text-sm text-gray-400 mb-4">{platform.description}</p>

          {connected && (
            <div className="space-y-3 mt-4 pt-4 border-t border-gray-700/50">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Username</span>
                <span className="font-semibold text-cyber-primary">{connected.username}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Followers</span>
                <span className="font-semibold">{connected.stats.followers.toLocaleString()}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-400">Posts</span>
                <span className="font-semibold">{connected.stats.posts}</span>
              </div>

              <div className="flex gap-2 mt-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => refreshAccount(connected.id)}
                  className="flex-1 px-3 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  Refresh
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => disconnectAccount(connected)}
                  className="flex-1 px-3 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-sm font-medium flex items-center justify-center gap-2"
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
              <span className="px-2 py-1 bg-cyber-primary/10 text-cyber-primary rounded text-xs">Video</span>
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
      <div>
        <h1 className="text-4xl font-black mb-2 gradient-text">Platform Accounts</h1>
        <p className="text-gray-400">Connect and manage your social media accounts</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="card-cyber p-4"
        >
          <div className="text-3xl font-black gradient-text">{accounts.length}</div>
          <div className="text-sm text-gray-400">Connected Accounts</div>
        </motion.div>
        
        <motion.div
          whileHover={{ scale: 1.02 }}
          className="card-cyber p-4"
        >
          <div className="text-3xl font-black text-cyber-green">
            {accounts.reduce((sum, acc) => sum + acc.stats.followers, 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-400">Total Followers</div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="card-cyber p-4"
        >
          <div className="text-3xl font-black text-cyber-purple">
            {accounts.reduce((sum, acc) => sum + acc.stats.posts, 0)}
          </div>
          <div className="text-sm text-gray-400">Total Posts</div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className="card-cyber p-4"
        >
          <div className="text-3xl font-black text-cyber-primary">
            {platformsAvailable.length - accounts.length}
          </div>
          <div className="text-sm text-gray-400">Available Platforms</div>
        </motion.div>
      </div>

      {/* Info Banner */}
      {accounts.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card-cyber p-6 bg-gradient-to-r from-cyber-primary/10 to-cyber-purple/10 border-cyber-primary/30"
        >
          <div className="flex items-start gap-4">
            <AlertCircle className="w-6 h-6 text-cyber-primary flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-bold mb-2">Welcome to Platform Accounts!</h3>
              <p className="text-gray-300 mb-3">
                Connect your social media accounts to start scheduling posts, analyzing performance, and growing your audience.
              </p>
              <ul className="space-y-1 text-sm text-gray-400">
                <li>✓ Schedule posts across all platforms from one place</li>
                <li>✓ Auto-post your viral clips with AI-generated captions</li>
                <li>✓ Track performance and engagement metrics</li>
                <li>✓ Manage multiple accounts effortlessly</li>
              </ul>
            </div>
          </div>
        </motion.div>
      )}

      {/* Platforms Grid */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Available Platforms</h2>
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
      </div>

      {/* Connection Modal */}
      {showAddModal && selectedPlatform && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card-cyber p-8 max-w-md w-full"
          >
            <div className="text-center mb-6">
              {React.createElement(selectedPlatform.icon, {
                className: "w-16 h-16 mx-auto mb-4 text-cyber-primary"
              })}
              <h2 className="text-2xl font-bold mb-2">Connect {selectedPlatform.name}</h2>
              <p className="text-gray-400">{selectedPlatform.description}</p>
            </div>

            <div className="space-y-4">
              <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-sm">
                <p className="text-yellow-400">
                  <AlertCircle className="w-4 h-4 inline mr-2" />
                  You'll be redirected to {selectedPlatform.name} to authorize access.
                </p>
              </div>

              <div className="flex gap-3">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleConnect}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-cyber-primary to-cyber-purple rounded-lg font-semibold hover:shadow-lg hover:shadow-cyber-primary/50 transition-all"
                >
                  <ExternalLink className="w-4 h-4 inline mr-2" />
                  Authorize Access
                </motion.button>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => {
                    setShowAddModal(false);
                    setSelectedPlatform(null);
                  }}
                  className="px-6 py-3 bg-white/5 hover:bg-white/10 rounded-lg font-medium"
                >
                  Cancel
                </motion.button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default Platforms;
