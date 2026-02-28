import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Video, 
  Users, 
  DollarSign, 
  Eye,
  Heart,
  Share2,
  MessageCircle,
  ArrowUp,
  ArrowDown,
  Clock,
  Zap
} from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getGrowthReport, getAppConfig } from '../lib/apiClient';
import { useTheme } from '../context/ThemeContext';

const Dashboard = () => {
  const { isDark } = useTheme();
  const [stats, setStats] = useState({
    totalViews: 0,
    totalEngagement: 0,
    activeClients: 0,
    revenue: 0
  });

  const [growth, setGrowth] = useState({
    views: 0,
    engagement: 0,
    clients: 0,
    revenue: 0
  });

  // Sample recent clips for demonstration
  const [recentClips, setRecentClips] = useState([
    { id: 1, title: 'Morning Routine Tips', thumbnail: '🌅', views: '12.5K', engagement: '8.2%' },
    { id: 2, title: 'Productivity Hacks', thumbnail: '⚡', views: '8.3K', engagement: '12.1%' },
    { id: 3, title: 'Travel Vlog NYC', thumbnail: '✈️', views: '25.1K', engagement: '6.8%' },
    { id: 4, title: 'Recipe: Easy Pasta', thumbnail: '🍝', views: '15.7K', engagement: '9.4%' },
  ]);

  // Sample chart data for demonstration
  const [chartData, setChartData] = useState([
    { name: 'Mon', views: 2400, engagement: 400 },
    { name: 'Tue', views: 1398, engagement: 300 },
    { name: 'Wed', views: 9800, engagement: 600 },
    { name: 'Thu', views: 3908, engagement: 450 },
    { name: 'Fri', views: 4800, engagement: 550 },
    { name: 'Sat', views: 3800, engagement: 380 },
    { name: 'Sun', views: 4300, engagement: 420 },
  ]);

  const [appStatus, setAppStatus] = useState({
    ollama: false,
    ffmpeg: false,
    models: []
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
    loadAppStatus();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      // Get real growth report from Python backend
      const report = await getGrowthReport(30);
      
      if (report) {
        // Update stats from real data
        setStats({
          totalViews: report.total_views || 0,
          totalEngagement: report.total_engagement || 0,
          activeClients: report.active_clients || 0,
          revenue: report.revenue || 0
        });

        // Update growth percentages
        if (report.growth) {
          setGrowth({
            views: report.growth.views || 0,
            engagement: report.growth.engagement || 0,
            clients: report.growth.clients || 0,
            revenue: report.growth.revenue || 0
          });
        }

        // Update recent clips if available
        if (report.recent_content && report.recent_content.length > 0) {
          setRecentClips(report.recent_content.slice(0, 4));
        }

        // Update chart data
        if (report.daily_stats && report.daily_stats.length > 0) {
          setChartData(report.daily_stats);
        }
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAppStatus = async () => {
    try {
      const config = await getAppConfig();
      setAppStatus({
        ollama: config.ollama_installed || false,
        ffmpeg: config.ffmpeg_installed || false,
        models: config.models_installed || []
      });
    } catch (error) {
      console.error('Failed to load app status:', error);
    }
  };

  const StatCard = ({ icon: Icon, label, value, change, color }) => (
    <motion.div
      whileHover={{ scale: 1.02, y: -5 }}
      className={`p-6 relative overflow-hidden rounded-xl border transition-colors ${
        isDark 
          ? 'bg-gray-900/80 border-cyan-500/20' 
          : 'bg-white border-gray-200 shadow-lg'
      }`}
    >
      {/* Gradient Background */}
      <div className={`absolute inset-0 bg-gradient-to-br ${color} opacity-5`} />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center text-white`}>
            <Icon className="w-6 h-6" />
          </div>
          
          <div className={`flex items-center gap-1 text-sm font-semibold ${
            change >= 0 ? 'text-green-500' : 'text-red-400'
          }`}>
            {change >= 0 ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
            {Math.abs(change)}%
          </div>
        </div>

        <div className={`text-3xl font-black mb-1 ${isDark ? 'gradient-text' : 'text-gray-900'}`}>{value.toLocaleString()}</div>
        <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{label}</div>
      </div>
    </motion.div>
  );

  const ClipCard = ({ clip, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      whileHover={{ scale: 1.02 }}
      className={`p-4 flex items-center gap-4 rounded-xl border transition-colors ${
        isDark 
          ? 'bg-gray-900/80 border-cyan-500/20' 
          : 'bg-white border-gray-200 shadow-md'
      }`}
    >
      <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-cyan-500 to-purple-600 flex items-center justify-center text-3xl text-white">
        {clip.thumbnail}
      </div>

      <div className="flex-1">
        <div className={`font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{clip.title}</div>
        <div className={`flex items-center gap-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <span className="flex items-center gap-1">
            <Eye className="w-4 h-4" />
            {clip.views}
          </span>
          <span className="flex items-center gap-1">
            <Zap className="w-4 h-4 text-green-500" />
            {clip.engagement}
          </span>
        </div>
      </div>

      <button className="px-4 py-2 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold hover:opacity-90 transition-opacity">
        View
      </button>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className={`text-4xl font-black mb-2 ${isDark ? 'gradient-text' : 'text-gray-900'}`}>Dashboard</h1>
        <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>Welcome back! Here's your performance overview.</p>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={Eye} 
          label="Total Views" 
          value={stats.totalViews} 
          change={growth.views}
          color="from-cyan-500 to-blue-600"
        />
        <StatCard 
          icon={Heart} 
          label="Engagement" 
          value={stats.totalEngagement} 
          change={growth.engagement}
          color="from-pink-500 to-rose-600"
        />
        <StatCard 
          icon={Users} 
          label="Active Clients" 
          value={stats.activeClients} 
          change={growth.clients}
          color="from-purple-500 to-purple-600"
        />
        <StatCard 
          icon={DollarSign} 
          label="Revenue" 
          value={stats.revenue} 
          change={growth.revenue}
          color="from-green-500 to-green-600"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Views Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className={`p-6 rounded-xl border transition-colors ${
            isDark 
              ? 'bg-gray-900/80 border-cyan-500/20' 
              : 'bg-white border-gray-200 shadow-lg'
          }`}
        >
          <h3 className={`text-xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <TrendingUp className="w-5 h-5 text-cyan-500" />
            Weekly Views
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorViews" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f2ff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00f2ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)"} />
              <XAxis dataKey="name" stroke={isDark ? "#fff" : "#374151"} />
              <YAxis stroke={isDark ? "#fff" : "#374151"} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: isDark ? '#000' : '#fff', 
                  border: '1px solid #00f2ff',
                  borderRadius: '8px',
                  color: isDark ? '#fff' : '#000'
                }}
              />
              <Area type="monotone" dataKey="views" stroke="#00f2ff" fillOpacity={1} fill="url(#colorViews)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        {/* Engagement Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className={`p-6 rounded-xl border transition-colors ${
            isDark 
              ? 'bg-gray-900/80 border-cyan-500/20' 
              : 'bg-white border-gray-200 shadow-lg'
          }`}
        >
          <h3 className={`text-xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <Zap className="w-5 h-5 text-green-500" />
            Engagement Rate
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.1)"} />
              <XAxis dataKey="name" stroke={isDark ? "#fff" : "#374151"} />
              <YAxis stroke={isDark ? "#fff" : "#374151"} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: isDark ? '#000' : '#fff', 
                  border: '1px solid #00ff9d',
                  borderRadius: '8px',
                  color: isDark ? '#fff' : '#000'
                }}
              />
              <Bar dataKey="engagement" fill="#00ff9d" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* Recent Clips */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h3 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Video className="w-6 h-6 text-purple-500" />
          Top Performing Clips
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {recentClips.map((clip, idx) => (
            <ClipCard key={clip.id} clip={clip} index={idx} />
          ))}
        </div>
      </motion.div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-6 rounded-xl border transition-colors ${
          isDark 
            ? 'bg-gray-900/80 border-cyan-500/20' 
            : 'bg-white border-gray-200 shadow-lg'
        }`}
      >
        <h3 className={`text-xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Clock className="w-5 h-5 text-cyan-500" />
          System Status
        </h3>
        <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 ${isDark ? 'text-white' : 'text-gray-700'}`}>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${appStatus.ollama ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            <div className="flex flex-col">
              <span>Ollama AI: {appStatus.ollama ? 'Online' : 'Offline'}</span>
              {!appStatus.ollama && (
                <a 
                  href="https://ollama.com/download" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-xs text-cyan-500 hover:text-purple-500 underline"
                >
                  Download Ollama
                </a>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${appStatus.ffmpeg ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            <span>FFmpeg: {appStatus.ffmpeg ? 'Ready' : 'Not Installed'}</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <span>Backend: Online</span>
          </div>
        </div>
        
        {!appStatus.ollama && (
          <div className={`mt-4 p-3 rounded-lg text-sm ${isDark ? 'bg-yellow-500/10 border border-yellow-500/30' : 'bg-yellow-50 border border-yellow-200'}`}>
            <p className={isDark ? 'text-yellow-400' : 'text-yellow-700'}>
              💡 <strong>Tip:</strong> Install Ollama to enable AI-powered features like caption generation, 
              content analysis, and growth insights. Visit{' '}
              <a 
                href="https://ollama.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-cyan-500 hover:text-purple-500 underline font-semibold"
              >
                ollama.com
              </a>
            </p>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default Dashboard;
