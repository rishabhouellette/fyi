import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { apiFetch } from '../lib/apiClient';
import {
  X,
  Bell,
  CheckCircle,
  AlertTriangle,
  Info,
  Clock,
  Trash2,
  Youtube,
  Instagram,
  Facebook,
  Upload,
  Calendar,
} from 'lucide-react';

/* ── helpers (pure, no state) ────────────────────────────────────────── */
const _buildNotifs = (posts, accounts) => {
  const now = new Date();
  const notifs = [];

  for (const post of posts) {
    const title = (post.title || post.caption || 'Untitled').slice(0, 50);
    const plats = (post.platforms || []).join(', ');
    const platform = (post.platforms || [])[0];

    if (post.status === 'failed') {
      notifs.push({
        id: `fail_${post.id}`,
        type: 'error',
        icon: AlertTriangle,
        title: 'Scheduling Failed',
        message: `"${title}" failed to post to ${plats}`,
        time: post.created_at || post.scheduled_time,
        scheduledTime: null,
        platform,
      });
    } else if (post.status === 'posted' || post.status === 'published') {
      notifs.push({
        id: `posted_${post.id}`,
        type: 'success',
        icon: CheckCircle,
        title: 'Post Published',
        message: `"${title}" posted to ${plats}`,
        time: post.posted_at || post.scheduled_time,
        scheduledTime: null,
        platform,
      });
    } else if (post.status === 'scheduled') {
      const schedTime = new Date(post.scheduled_time);
      const diffMins = (schedTime - now) / 60000;
      // Upcoming in the next 120 minutes
      if (diffMins > -5 && diffMins <= 120) {
        notifs.push({
          id: `upcoming_${post.id}`,
          type: 'info',
          icon: Clock,
          title: 'Upcoming Post',
          message: `"${title}"`,
          time: post.scheduled_time,
          scheduledTime: post.scheduled_time,      // keep raw for live countdown
          platform,
        });
      }
    }
  }

  if (accounts.length === 0) {
    notifs.push({
      id: 'no_accounts',
      type: 'warning',
      icon: Info,
      title: 'No Accounts Connected',
      message: 'Connect a social media account to start posting.',
      time: now.toISOString(),
      scheduledTime: null,
    });
  }

  notifs.sort((a, b) => {
    try { return new Date(b.time) - new Date(a.time); } catch { return 0; }
  });
  return notifs;
};

const _countBadge = (notifs) =>
  notifs.filter(n => n.type === 'error' || n.type === 'warning' || n.type === 'info').length;

/* ── component ───────────────────────────────────────────────────────── */
const NotificationPanel = ({ isOpen, onClose, onCountChange }) => {
  const { isDark } = useTheme();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [tick, setTick] = useState(0);         // drives live countdown re-render
  const panelRef = useRef(null);
  const dismissedRef = useRef(new Set());       // ids the user dismissed this session

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (panelRef.current && !panelRef.current.contains(e.target)) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  /* ── fetch & build notifications ── */
  const fetchNotifications = useCallback(async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [schedRes, accRes] = await Promise.all([
        apiFetch('/api/scheduled-posts'),
        apiFetch('/api/accounts'),
      ]);
      const posts = schedRes.ok
        ? ((await schedRes.json()).posts || (await Promise.resolve([])))  // already consumed
        : [];
      // re-fetch if needed (json already consumed above) — safer pattern:
      let parsedPosts = [];
      let parsedAccounts = [];
      try {
        const sd = await (await apiFetch('/api/scheduled-posts')).json();
        parsedPosts = sd.posts || sd.scheduled_posts || [];
      } catch { /* empty */ }
      try {
        const ad = await (await apiFetch('/api/accounts')).json();
        parsedAccounts = ad.accounts || [];
      } catch { /* empty */ }

      const notifs = _buildNotifs(parsedPosts, parsedAccounts)
        .filter(n => !dismissedRef.current.has(n.id));

      setNotifications(notifs);
      if (onCountChange) onCountChange(_countBadge(notifs));
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
    if (!silent) setLoading(false);
  }, [onCountChange]);

  // Initial load + auto-refresh when panel is open (every 15 s)
  useEffect(() => {
    if (!isOpen) return;
    fetchNotifications();
    const id = setInterval(() => fetchNotifications(true), 15_000);
    return () => clearInterval(id);
  }, [isOpen, fetchNotifications]);

  // Background badge polling every 30 s (even when panel is closed)
  useEffect(() => {
    const poll = async () => {
      try {
        const sd = await (await apiFetch('/api/scheduled-posts')).json();
        const posts = sd.posts || sd.scheduled_posts || [];
        const ad = await (await apiFetch('/api/accounts')).json();
        const accounts = ad.accounts || [];
        const notifs = _buildNotifs(posts, accounts)
          .filter(n => !dismissedRef.current.has(n.id));
        if (onCountChange) onCountChange(_countBadge(notifs));
      } catch { /* silent */ }
    };
    poll();  // run immediately on mount
    const id = setInterval(poll, 30_000);
    return () => clearInterval(id);
  }, [onCountChange]);

  // Live countdown ticker — re-renders every 30 s so "posting in X min" stays fresh
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 30_000);
    return () => clearInterval(id);
  }, []);

  const clearAll = () => {
    notifications.forEach(n => dismissedRef.current.add(n.id));
    setNotifications([]);
    if (onCountChange) onCountChange(0);
  };

  const removeNotif = (id) => {
    dismissedRef.current.add(id);
    setNotifications(prev => {
      const updated = prev.filter(n => n.id !== id);
      if (onCountChange) onCountChange(_countBadge(updated));
      return updated;
    });
  };

  const formatTime = (iso) => {
    try {
      const d = new Date(iso);
      const now = new Date();
      const diffMs = now - d;
      const diffMins = Math.floor(diffMs / 60000);
      if (diffMins < 0) return `in ${Math.abs(diffMins)} min`;
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      return d.toLocaleDateString();
    } catch {
      return '';
    }
  };

  /** Live countdown for upcoming posts — recalculated every render/tick */
  const liveCountdown = (scheduledTime) => {
    if (!scheduledTime) return null;
    const diff = (new Date(scheduledTime) - new Date()) / 60000;
    if (diff <= 0) return 'posting now';
    if (diff < 1) return 'posting in <1 min';
    return `posting in ${Math.round(diff)} min`;
  };

  const typeStyles = {
    error: {
      bg: isDark ? 'bg-red-500/10 border-red-500/30' : 'bg-red-50 border-red-200',
      icon: isDark ? 'text-red-400' : 'text-red-500',
      dot: 'bg-red-500',
    },
    warning: {
      bg: isDark ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-yellow-50 border-yellow-200',
      icon: isDark ? 'text-yellow-400' : 'text-yellow-600',
      dot: 'bg-yellow-500',
    },
    success: {
      bg: isDark ? 'bg-green-500/10 border-green-500/30' : 'bg-green-50 border-green-200',
      icon: isDark ? 'text-green-400' : 'text-green-600',
      dot: 'bg-green-500',
    },
    info: {
      bg: isDark ? 'bg-blue-500/10 border-blue-500/30' : 'bg-blue-50 border-blue-200',
      icon: isDark ? 'text-blue-400' : 'text-blue-600',
      dot: 'bg-blue-500',
    },
  };

  const getPlatformIcon = (platform) => {
    switch ((platform || '').toLowerCase()) {
      case 'youtube': case 'yt': return Youtube;
      case 'instagram': case 'ig': return Instagram;
      case 'facebook': case 'fb': return Facebook;
      default: return null;
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          ref={panelRef}
          initial={{ opacity: 0, x: -20, y: -10 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          exit={{ opacity: 0, x: -20, y: -10 }}
          transition={{ duration: 0.2 }}
          className={`absolute left-24 bottom-16 w-96 max-h-[500px] rounded-2xl border shadow-2xl z-[100] flex flex-col overflow-hidden ${
            isDark
              ? 'bg-gray-900/95 backdrop-blur-xl border-gray-700/50'
              : 'bg-white/95 backdrop-blur-xl border-gray-200'
          }`}
        >
          {/* Header */}
          <div className={`flex items-center justify-between px-5 py-4 border-b ${isDark ? 'border-gray-700/50' : 'border-gray-200'}`}>
            <div className="flex items-center gap-2">
              <Bell className={`w-5 h-5 ${isDark ? 'text-cyber-primary' : 'text-blue-600'}`} />
              <h3 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>Notifications</h3>
              {notifications.length > 0 && (
                <span className={`text-xs px-2 py-0.5 rounded-full ${isDark ? 'bg-white/10 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
                  {notifications.length}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              {notifications.length > 0 && (
                <button
                  onClick={clearAll}
                  className={`text-xs px-2 py-1 rounded-lg transition-colors ${isDark ? 'text-gray-400 hover:text-white hover:bg-white/10' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'}`}
                >
                  Clear all
                </button>
              )}
              <button
                onClick={onClose}
                className={`p-1 rounded-lg transition-colors ${isDark ? 'text-gray-400 hover:text-white hover:bg-white/10' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'}`}
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Notification List */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className={`p-8 text-center ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                Loading...
              </div>
            ) : notifications.length === 0 ? (
              <div className={`p-8 text-center ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                <Bell className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="font-medium">All caught up!</p>
                <p className="text-sm mt-1">No new notifications</p>
              </div>
            ) : (
              <div className="p-2 space-y-1">
                {notifications.map((notif) => {
                  const style = typeStyles[notif.type] || typeStyles.info;
                  const Icon = notif.icon;
                  const PlatformIcon = getPlatformIcon(notif.platform);
                  return (
                    <motion.div
                      key={notif.id}
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -50 }}
                      className={`group relative p-3 rounded-xl border transition-colors cursor-default ${style.bg}`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 ${style.icon}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>
                              {notif.title}
                            </p>
                            {PlatformIcon && (
                              <PlatformIcon className={`w-3.5 h-3.5 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                            )}
                          </div>
                          <p className={`text-xs mt-0.5 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                            {notif.scheduledTime
                              ? <>{notif.message} &mdash; <span className="font-medium">{liveCountdown(notif.scheduledTime)}</span></>
                              : notif.message}
                          </p>
                          <p className={`text-xs mt-1 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                            {formatTime(notif.time)}
                          </p>
                        </div>
                        <button
                          onClick={() => removeNotif(notif.id)}
                          className={`opacity-0 group-hover:opacity-100 p-1 rounded-lg transition-all ${isDark ? 'text-gray-500 hover:text-white hover:bg-white/10' : 'text-gray-400 hover:text-gray-700 hover:bg-gray-200'}`}
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default NotificationPanel;
