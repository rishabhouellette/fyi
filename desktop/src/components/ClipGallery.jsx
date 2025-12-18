import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Grid3x3, 
  Play, 
  Download, 
  Share2, 
  Eye,
  Heart,
  MessageCircle,
  MoreVertical,
  Filter,
  Search,
  Clock,
  TrendingUp,
  Sparkles
} from 'lucide-react';

const ClipGallery = () => {
  const [clips, setClips] = useState([
    { id: 1, title: 'How I Made $10K in 30 Days', duration: '0:59', views: '234K', likes: '12.4K', comments: '847', score: 94, thumbnail: '🎯', platform: 'TikTok', status: 'viral' },
    { id: 2, title: 'This AI Tool Changed Everything', duration: '0:45', views: '892K', likes: '45.2K', comments: '2.3K', score: 98, thumbnail: '🤖', platform: 'Instagram', status: 'viral' },
    { id: 3, title: 'The Secret They Don\'t Tell You', duration: '1:15', views: '445K', likes: '23.1K', comments: '1.2K', score: 91, thumbnail: '🔥', platform: 'YouTube', status: 'trending' },
    { id: 4, title: 'My Daily Routine For Success', duration: '0:52', views: '156K', likes: '8.9K', comments: '456', score: 87, thumbnail: '⚡', platform: 'TikTok', status: 'active' },
    { id: 5, title: 'Why 99% of People Fail', duration: '1:02', views: '678K', likes: '34.5K', comments: '1.8K', score: 95, thumbnail: '💡', platform: 'Instagram', status: 'viral' },
    { id: 6, title: 'Transform Your Life in 7 Days', duration: '0:48', views: '289K', likes: '15.6K', comments: '789', score: 89, thumbnail: '🚀', platform: 'YouTube', status: 'trending' },
    { id: 7, title: 'The Mindset of Winners', duration: '1:08', views: '523K', likes: '28.7K', comments: '1.5K', score: 92, thumbnail: '🏆', platform: 'TikTok', status: 'viral' },
    { id: 8, title: 'Breaking Free From 9-5', duration: '0:55', views: '367K', likes: '19.2K', comments: '923', score: 88, thumbnail: '💼', platform: 'Instagram', status: 'active' }
  ]);

  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClip, setSelectedClip] = useState(null);

  const filteredClips = clips
    .filter(clip => {
      if (filter !== 'all' && clip.platform !== filter) return false;
      if (searchTerm && !clip.title.toLowerCase().includes(searchTerm.toLowerCase())) return false;
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'views':
          return parseInt(b.views) - parseInt(a.views);
        case 'score':
          return b.score - a.score;
        case 'recent':
        default:
          return b.id - a.id;
      }
    });

  const ClipCard = ({ clip, index }) => {
    const statusColors = {
      viral: 'from-cyber-green to-green-600',
      trending: 'from-yellow-500 to-orange-500',
      active: 'from-cyber-primary to-blue-600'
    };

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: index * 0.05 }}
        whileHover={{ scale: 1.05, y: -5 }}
        onClick={() => setSelectedClip(clip)}
        className="card-cyber p-0 overflow-hidden cursor-pointer group"
      >
        {/* Thumbnail */}
        <div className="relative h-48 bg-gradient-to-br from-cyber-primary/20 to-cyber-purple/20 flex items-center justify-center overflow-hidden">
          <div className="text-6xl group-hover:scale-110 transition-transform">
            {clip.thumbnail}
          </div>
          
          {/* Play Overlay */}
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <motion.div
              whileHover={{ scale: 1.2 }}
              className="w-16 h-16 rounded-full bg-cyber-primary cyber-glow flex items-center justify-center"
            >
              <Play className="w-8 h-8" fill="currentColor" />
            </motion.div>
          </div>

          {/* Status Badge */}
          <div className={`absolute top-3 right-3 px-3 py-1 rounded-full text-xs font-bold bg-gradient-to-r ${statusColors[clip.status]} cyber-glow`}>
            {clip.status.toUpperCase()}
          </div>

          {/* Duration */}
          <div className="absolute bottom-3 right-3 px-2 py-1 rounded bg-black/80 text-xs font-semibold">
            {clip.duration}
          </div>

          {/* Score */}
          <div className="absolute top-3 left-3 px-2 py-1 rounded bg-black/80 text-xs font-semibold flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-cyber-green" />
            {clip.score}
          </div>
        </div>

        {/* Info */}
        <div className="p-4">
          <h3 className="font-semibold mb-2 line-clamp-2">{clip.title}</h3>
          
          <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
            <span className="flex items-center gap-1">
              <Eye className="w-4 h-4" />
              {clip.views}
            </span>
            <span className="flex items-center gap-1">
              <Heart className="w-4 h-4" />
              {clip.likes}
            </span>
            <span className="flex items-center gap-1">
              <MessageCircle className="w-4 h-4" />
              {clip.comments}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2 py-1 rounded bg-white/5 text-xs font-semibold">
              {clip.platform}
            </span>
            <div className="flex-1" />
            <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
              <Download className="w-4 h-4" />
            </button>
            <button className="p-2 rounded-lg hover:bg-white/10 transition-colors">
              <Share2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-black mb-2 gradient-text">Clip Gallery</h1>
          <p className="text-gray-400">{filteredClips.length} viral clips ready to dominate</p>
        </div>

        <button className="btn-cyber px-6 py-3 flex items-center gap-2">
          <Play className="w-5 h-5" />
          Bulk Schedule
        </button>
      </motion.div>

      {/* Filters & Search */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-cyber p-6"
      >
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search clips..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-cyber w-full pl-10"
            />
          </div>

          {/* Platform Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-400" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="input-cyber"
            >
              <option value="all">All Platforms</option>
              <option value="TikTok">TikTok</option>
              <option value="Instagram">Instagram</option>
              <option value="YouTube">YouTube</option>
            </select>
          </div>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="input-cyber"
          >
            <option value="recent">Most Recent</option>
            <option value="views">Most Views</option>
            <option value="score">Highest Score</option>
          </select>
        </div>
      </motion.div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: 'Total Clips', value: clips.length, icon: Grid3x3, color: 'from-cyber-primary to-blue-600' },
          { label: 'Viral Clips', value: clips.filter(c => c.status === 'viral').length, icon: TrendingUp, color: 'from-cyber-green to-green-600' },
          { label: 'Total Views', value: '3.5M', icon: Eye, color: 'from-purple-500 to-pink-600' },
          { label: 'Avg Score', value: Math.round(clips.reduce((acc, c) => acc + c.score, 0) / clips.length), icon: Sparkles, color: 'from-yellow-500 to-orange-500' }
        ].map((stat, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            whileHover={{ scale: 1.05 }}
            className="card-cyber p-4 relative overflow-hidden"
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-5`} />
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400">{stat.label}</span>
                <stat.icon className="w-5 h-5 text-gray-400" />
              </div>
              <div className="text-2xl font-black gradient-text">{stat.value}</div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Clips Grid */}
      {filteredClips.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredClips.map((clip, idx) => (
            <ClipCard key={clip.id} clip={clip} index={idx} />
          ))}
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card-cyber p-12 text-center"
        >
          <Grid3x3 className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">No clips found</h3>
          <p className="text-gray-400">Try adjusting your filters or upload a new video</p>
        </motion.div>
      )}

      {/* Clip Detail Modal */}
      <AnimatePresence>
        {selectedClip && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedClip(null)}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="card-cyber max-w-4xl w-full max-h-[90vh] overflow-auto"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-black mb-2">{selectedClip.title}</h2>
                    <div className="flex items-center gap-4 text-sm text-gray-400">
                      <span>{selectedClip.platform}</span>
                      <span>•</span>
                      <span>{selectedClip.duration}</span>
                      <span>•</span>
                      <span>Score: {selectedClip.score}/100</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedClip(null)}
                    className="p-2 rounded-lg hover:bg-white/10"
                  >
                    ✕
                  </button>
                </div>

                {/* Video Preview */}
                <div className="w-full aspect-video bg-gradient-to-br from-cyber-primary/20 to-cyber-purple/20 rounded-xl flex items-center justify-center mb-6">
                  <div className="text-9xl">{selectedClip.thumbnail}</div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="card-cyber p-4 text-center">
                    <Eye className="w-6 h-6 text-cyber-primary mx-auto mb-2" />
                    <div className="text-2xl font-bold">{selectedClip.views}</div>
                    <div className="text-sm text-gray-400">Views</div>
                  </div>
                  <div className="card-cyber p-4 text-center">
                    <Heart className="w-6 h-6 text-pink-500 mx-auto mb-2" />
                    <div className="text-2xl font-bold">{selectedClip.likes}</div>
                    <div className="text-sm text-gray-400">Likes</div>
                  </div>
                  <div className="card-cyber p-4 text-center">
                    <MessageCircle className="w-6 h-6 text-cyber-green mx-auto mb-2" />
                    <div className="text-2xl font-bold">{selectedClip.comments}</div>
                    <div className="text-sm text-gray-400">Comments</div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-4">
                  <button className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2">
                    <Play className="w-5 h-5" />
                    Play Clip
                  </button>
                  <button className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2">
                    <Download className="w-5 h-5" />
                    Download
                  </button>
                  <button className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2">
                    <Share2 className="w-5 h-5" />
                    Share
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ClipGallery;
