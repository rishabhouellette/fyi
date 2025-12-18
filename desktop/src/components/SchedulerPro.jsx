import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Calendar, 
  Clock, 
  Send,
  Instagram,
  Youtube,
  Facebook,
  Linkedin,
  Twitter,
  Plus,
  Edit,
  Trash2,
  Copy,
  CheckCircle
} from 'lucide-react';
import { schedulePost } from '../lib/tauri';

const SchedulerPro = () => {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [scheduledPosts, setScheduledPosts] = useState([
    { id: 1, title: 'Morning Motivation', time: '09:00', platforms: ['Instagram', 'TikTok'], status: 'scheduled', date: '2024-01-15' },
    { id: 2, title: 'AI Tutorial Part 1', time: '12:00', platforms: ['YouTube', 'LinkedIn'], status: 'scheduled', date: '2024-01-15' },
    { id: 3, title: 'Growth Tips Thread', time: '15:00', platforms: ['Twitter', 'LinkedIn'], status: 'scheduled', date: '2024-01-15' },
    { id: 4, title: 'Evening Insights', time: '18:00', platforms: ['Instagram', 'Facebook'], status: 'scheduled', date: '2024-01-15' }
  ]);

  const [newPost, setNewPost] = useState({
    title: '',
    caption: '',
    platforms: [],
    scheduledTime: '',
    clips: []
  });

  const platformIcons = {
    Instagram: { icon: Instagram, color: 'from-pink-500 to-purple-600' },
    YouTube: { icon: Youtube, color: 'from-red-500 to-red-700' },
    Facebook: { icon: Facebook, color: 'from-blue-500 to-blue-700' },
    LinkedIn: { icon: Linkedin, color: 'from-blue-600 to-blue-800' },
    Twitter: { icon: Twitter, color: 'from-cyan-400 to-blue-500' },
    TikTok: { icon: Send, color: 'from-black to-gray-800' }
  };

  const togglePlatform = (platform) => {
    setNewPost(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }));
  };

  const handleSchedule = async () => {
    if (!newPost.title || newPost.platforms.length === 0 || !newPost.scheduledTime) {
      alert('Please fill all required fields');
      return;
    }

    const result = await schedulePost({
      platforms: newPost.platforms,
      content: {
        title: newPost.title,
        caption: newPost.caption
      },
      scheduledTime: newPost.scheduledTime,
      clips: newPost.clips
    });

    if (result.success) {
      alert('Post scheduled successfully!');
      setNewPost({ title: '', caption: '', platforms: [], scheduledTime: '', clips: [] });
    } else {
      alert(`Scheduling failed: ${result.error}`);
    }
  };

  const PostCard = ({ post, index }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02 }}
      className="card-cyber p-4 flex items-center gap-4"
    >
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center cyber-glow">
        <Clock className="w-6 h-6" />
      </div>

      <div className="flex-1">
        <div className="font-semibold mb-1">{post.title}</div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">{post.time}</span>
          <div className="flex items-center gap-1">
            {post.platforms.map(platform => {
              const PlatformIcon = platformIcons[platform]?.icon || Send;
              return (
                <div key={platform} className="w-6 h-6 rounded bg-white/10 flex items-center justify-center">
                  <PlatformIcon className="w-4 h-4" />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className="px-3 py-1 rounded-full bg-cyber-green/20 text-cyber-green text-xs font-semibold">
          {post.status}
        </span>
        <button className="p-2 rounded-lg hover:bg-white/10">
          <Edit className="w-4 h-4" />
        </button>
        <button className="p-2 rounded-lg hover:bg-white/10">
          <Trash2 className="w-4 h-4 text-red-400" />
        </button>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-black mb-2 gradient-text">Scheduler Pro</h1>
        <p className="text-gray-400">Plan and automate your content across all platforms</p>
      </motion.div>

      {/* Create New Post */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-cyber p-6"
      >
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Plus className="w-5 h-5 text-cyber-primary" />
          Schedule New Post
        </h3>

        <div className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-semibold mb-2">Post Title *</label>
            <input
              type="text"
              value={newPost.title}
              onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
              placeholder="Enter post title..."
              className="input-cyber w-full"
            />
          </div>

          {/* Caption */}
          <div>
            <label className="block text-sm font-semibold mb-2">Caption</label>
            <textarea
              value={newPost.caption}
              onChange={(e) => setNewPost({ ...newPost, caption: e.target.value })}
              placeholder="Write your caption..."
              rows={4}
              className="input-cyber w-full"
            />
          </div>

          {/* Platform Selection */}
          <div>
            <label className="block text-sm font-semibold mb-3">Select Platforms *</label>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(platformIcons).map(([platform, { icon: Icon, color }]) => {
                const isSelected = newPost.platforms.includes(platform);
                return (
                  <motion.button
                    key={platform}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => togglePlatform(platform)}
                    className={`p-4 rounded-xl border-2 transition-all relative ${
                      isSelected
                        ? 'border-cyber-primary bg-cyber-primary/10'
                        : 'border-white/10 bg-white/5 hover:border-white/30'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-2`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="text-xs font-semibold">{platform}</div>
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-cyber-green rounded-full flex items-center justify-center"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </motion.div>
                    )}
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* Date & Time */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold mb-2">Date *</label>
              <input
                type="date"
                value={newPost.scheduledTime.split('T')[0] || ''}
                onChange={(e) => setNewPost({ ...newPost, scheduledTime: e.target.value + 'T' + (newPost.scheduledTime.split('T')[1] || '12:00') })}
                className="input-cyber w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold mb-2">Time *</label>
              <input
                type="time"
                value={newPost.scheduledTime.split('T')[1] || ''}
                onChange={(e) => setNewPost({ ...newPost, scheduledTime: (newPost.scheduledTime.split('T')[0] || new Date().toISOString().split('T')[0]) + 'T' + e.target.value })}
                className="input-cyber w-full"
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4 pt-4">
            <button onClick={handleSchedule} className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2">
              <Calendar className="w-5 h-5" />
              Schedule Post
            </button>
            <button className="px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
              Save Draft
            </button>
          </div>
        </div>
      </motion.div>

      {/* Calendar View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Posts */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <Clock className="w-5 h-5 text-cyber-primary" />
            Scheduled Posts ({scheduledPosts.length})
          </h3>

          {scheduledPosts.map((post, idx) => (
            <PostCard key={post.id} post={post} index={idx} />
          ))}

          {scheduledPosts.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card-cyber p-12 text-center"
            >
              <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h4 className="text-xl font-bold mb-2">No scheduled posts</h4>
              <p className="text-gray-400">Create your first scheduled post above</p>
            </motion.div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="space-y-4">
          <h3 className="text-xl font-bold">Quick Stats</h3>

          {[
            { label: 'Posts Today', value: '4', icon: Calendar, color: 'from-cyber-primary to-blue-600' },
            { label: 'This Week', value: '23', icon: Clock, color: 'from-cyber-purple to-purple-600' },
            { label: 'This Month', value: '87', icon: Send, color: 'from-cyber-green to-green-600' }
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="card-cyber p-6 relative overflow-hidden"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-5`} />
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <stat.icon className="w-8 h-8 text-gray-400" />
                </div>
                <div className="text-3xl font-black mb-1 gradient-text">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            </motion.div>
          ))}

          <motion.div
            whileHover={{ scale: 1.05 }}
            className="card-cyber p-6 bg-gradient-to-br from-cyber-primary/10 to-cyber-purple/10 border-cyber-primary"
          >
            <h4 className="font-bold mb-2 flex items-center gap-2">
              <Copy className="w-5 h-5 text-cyber-primary" />
              Bulk Schedule
            </h4>
            <p className="text-sm text-gray-400 mb-4">
              Schedule multiple posts at once with our CSV import feature
            </p>
            <button className="btn-cyber w-full py-2">
              Import CSV
            </button>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default SchedulerPro;
