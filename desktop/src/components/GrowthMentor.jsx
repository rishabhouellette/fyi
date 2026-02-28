import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  Lightbulb, 
  Target,
  Zap,
  Brain,
  Sparkles,
  ArrowUp,
  ArrowDown,
  Calendar,
  Users,
  Eye,
  Heart,
  MessageCircle,
  Share2
} from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { getGrowthReport } from '../lib/apiClient';

const GrowthMentor = () => {
  const [timeRange, setTimeRange] = useState(30);
  const [insights, setInsights] = useState([
    { id: 1, type: 'success', title: 'Peak Engagement Time', description: 'Your audience is most active between 6-8 PM EST. Schedule more posts during this window.', impact: 'high' },
    { id: 2, type: 'warning', title: 'Content Gap Detected', description: 'You haven\'t posted educational content in 5 days. Your audience engagement drops 23% without this type.', impact: 'medium' },
    { id: 3, type: 'opportunity', title: 'Trending Topic Alert', description: 'AI automation is trending +340% in your niche. Create content around this topic now.', impact: 'high' },
    { id: 4, type: 'tip', title: 'Caption Optimization', description: 'Posts with questions in captions get 45% more comments. Try ending with "What do you think?"', impact: 'low' }
  ]);

  const [growthData, setGrowthData] = useState([
    { date: 'Jan 1', followers: 1000, engagement: 450, reach: 5000 },
    { date: 'Jan 8', followers: 1250, engagement: 580, reach: 6200 },
    { date: 'Jan 15', followers: 1600, engagement: 720, reach: 7800 },
    { date: 'Jan 22', followers: 2100, engagement: 950, reach: 10200 },
    { date: 'Jan 29', followers: 2800, engagement: 1260, reach: 14500 },
    { date: 'Feb 5', followers: 3650, engagement: 1640, reach: 18900 },
    { date: 'Feb 12', followers: 4750, engagement: 2130, reach: 24600 }
  ]);

  const [predictions, setPredictions] = useState({
    nextMonth: {
      followers: 8500,
      engagement: 3800,
      revenue: 4200
    },
    confidence: 87
  });

  useEffect(() => {
    loadGrowthReport();
  }, [timeRange]);

  const loadGrowthReport = async () => {
    try {
      const report = await getGrowthReport(timeRange);
      if (report) {
        console.log('Growth Report:', report);

        if (Array.isArray(report.insights) && report.insights.length > 0) {
          setInsights(
            report.insights.slice(0, 6).map((text, idx) => ({
              id: idx + 1,
              type: 'tip',
              title: `Insight ${idx + 1}`,
              description: String(text),
              impact: idx < 2 ? 'high' : idx < 4 ? 'medium' : 'low'
            }))
          );
        }

        if (report.predictions) {
          setPredictions(prev => ({
            ...prev,
            confidence: prev.confidence,
            nextMonth: {
              ...prev.nextMonth,
              followers: report.predictions.next_week_followers ?? prev.nextMonth.followers
            }
          }));
        }
      }
    } catch (error) {
      console.error('Failed to load growth report:', error);
    }
  };

  const InsightCard = ({ insight, index }) => {
    const typeStyles = {
      success: { color: 'from-cyber-green to-green-600', icon: Sparkles, border: 'border-cyber-green' },
      warning: { color: 'from-yellow-500 to-orange-500', icon: Zap, border: 'border-yellow-500' },
      opportunity: { color: 'from-cyber-primary to-blue-600', icon: Target, border: 'border-cyber-primary' },
      tip: { color: 'from-cyber-purple to-purple-600', icon: Lightbulb, border: 'border-cyber-purple' }
    };

    const style = typeStyles[insight.type] || typeStyles.tip;
    const Icon = style.icon;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        whileHover={{ scale: 1.02, y: -5 }}
        className={`card-cyber p-6 border-l-4 ${style.border} relative overflow-hidden`}
      >
        <div className={`absolute inset-0 bg-gradient-to-br ${style.color} opacity-5`} />
        
        <div className="relative z-10">
          <div className="flex items-start gap-4">
            <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${style.color} flex items-center justify-center cyber-glow flex-shrink-0`}>
              <Icon className="w-6 h-6" />
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h4 className="font-bold">{insight.title}</h4>
                <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                  insight.impact === 'high' ? 'bg-red-500/20 text-red-400' :
                  insight.impact === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                  'bg-green-500/20 text-green-400'
                }`}>
                  {insight.impact} impact
                </span>
              </div>
              <p className="text-sm text-gray-400 mb-3">{insight.description}</p>
              <button className="text-sm text-cyber-primary hover:underline font-semibold">
                Apply Suggestion →
              </button>
            </div>
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
          <h1 className="text-4xl font-black mb-2 gradient-text">Growth Mentor</h1>
          <p className="text-gray-400">AI-powered insights to skyrocket your growth</p>
        </div>

        <select
          value={timeRange}
          onChange={(e) => setTimeRange(parseInt(e.target.value))}
          className="input-cyber"
        >
          <option value={7}>Last 7 Days</option>
          <option value={30}>Last 30 Days</option>
          <option value={90}>Last 90 Days</option>
        </select>
      </motion.div>

      {/* AI Predictions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-cyber p-6 bg-gradient-to-br from-cyber-primary/10 to-cyber-purple/10 border-cyber-primary relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-64 h-64 bg-cyber-primary/10 rounded-full blur-3xl" />
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center cyber-glow">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-xl font-bold">AI Growth Predictions</h3>
              <p className="text-sm text-gray-400">Next 30 days forecast • {predictions.confidence}% confidence</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { label: 'Followers', value: predictions.nextMonth.followers, change: '+80%', icon: Users },
              { label: 'Engagement', value: predictions.nextMonth.engagement, change: '+65%', icon: Heart },
              { label: 'Revenue', value: `$${predictions.nextMonth.revenue}`, change: '+120%', icon: TrendingUp }
            ].map((pred, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.1 }}
                className="glass p-4 rounded-xl"
              >
                <pred.icon className="w-6 h-6 text-gray-400 mb-2" />
                <div className="text-3xl font-black gradient-text">{pred.value.toLocaleString()}</div>
                <div className="text-sm text-gray-400 mt-1">{pred.label}</div>
                <div className="flex items-center gap-1 text-cyber-green text-sm font-semibold mt-2">
                  <ArrowUp className="w-4 h-4" />
                  {pred.change}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.div>

      {/* Growth Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card-cyber p-6"
        >
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-cyber-primary" />
            Follower Growth
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={growthData}>
              <defs>
                <linearGradient id="colorFollowers" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f2ff" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#00f2ff" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="date" stroke="#fff" fontSize={12} />
              <YAxis stroke="#fff" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#000', 
                  border: '1px solid #00f2ff',
                  borderRadius: '8px'
                }}
              />
              <Area type="monotone" dataKey="followers" stroke="#00f2ff" fillOpacity={1} fill="url(#colorFollowers)" />
            </AreaChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card-cyber p-6"
        >
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Heart className="w-5 h-5 text-pink-500" />
            Engagement Trend
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="date" stroke="#fff" fontSize={12} />
              <YAxis stroke="#fff" fontSize={12} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#000', 
                  border: '1px solid #00ff9d',
                  borderRadius: '8px'
                }}
              />
              <Line type="monotone" dataKey="engagement" stroke="#00ff9d" strokeWidth={3} dot={{ fill: '#00ff9d', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      </div>

      {/* AI Insights */}
      <div>
        <motion.h3
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-2xl font-bold mb-4 flex items-center gap-2"
        >
          <Lightbulb className="w-6 h-6 text-cyber-primary" />
          AI Insights & Recommendations
        </motion.h3>

        <div className="space-y-4">
          {insights.map((insight, idx) => (
            <InsightCard key={insight.id} insight={insight} index={idx} />
          ))}
        </div>
      </div>

      {/* Performance Breakdown */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-cyber p-6"
      >
        <h3 className="text-xl font-bold mb-4">Performance Breakdown</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: 'Avg. Views', value: '45.2K', change: '+23%', up: true, icon: Eye },
            { label: 'Engagement Rate', value: '8.4%', change: '+1.2%', up: true, icon: Heart },
            { label: 'Comments', value: '1.2K', change: '-5%', up: false, icon: MessageCircle },
            { label: 'Shares', value: '847', change: '+45%', up: true, icon: Share2 }
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              whileHover={{ scale: 1.05 }}
              className="glass p-4 rounded-xl"
            >
              <div className="flex items-center justify-between mb-2">
                <stat.icon className="w-5 h-5 text-gray-400" />
                <div className={`flex items-center gap-1 text-sm font-semibold ${stat.up ? 'text-cyber-green' : 'text-red-400'}`}>
                  {stat.up ? <ArrowUp className="w-4 h-4" /> : <ArrowDown className="w-4 h-4" />}
                  {stat.change}
                </div>
              </div>
              <div className="text-2xl font-black gradient-text">{stat.value}</div>
              <div className="text-sm text-gray-400 mt-1">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Action Items */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-cyber p-6 bg-gradient-to-br from-cyber-green/10 to-green-900/10 border-cyber-green"
      >
        <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-cyber-green" />
          Quick Actions to Boost Growth
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { action: 'Post 3x Daily', impact: '+40% reach' },
            { action: 'Use Trending Sounds', impact: '+65% engagement' },
            { action: 'Reply to Comments', impact: '+30% retention' }
          ].map((item, idx) => (
            <motion.button
              key={idx}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="glass p-4 rounded-xl text-left hover:bg-white/10 transition-colors"
            >
              <div className="font-bold mb-1">{item.action}</div>
              <div className="text-sm text-cyber-green">{item.impact}</div>
            </motion.button>
          ))}
        </div>
      </motion.div>
    </div>
  );
};

export default GrowthMentor;
