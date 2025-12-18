import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users, 
  Plus,
  MoreVertical,
  TrendingUp,
  DollarSign,
  Calendar,
  Eye,
  Settings,
  UserCheck,
  UserX,
  Mail,
  MessageCircle,
  BarChart3,
  Crown
} from 'lucide-react';

const AgencyOS = () => {
  const [clients, setClients] = useState([
    { 
      id: 1, 
      name: 'TechStartup Inc', 
      avatar: '🚀',
      status: 'active',
      plan: 'premium',
      revenue: 2500,
      posts: 45,
      views: '2.3M',
      engagement: '94K',
      nextPost: '2024-01-15 14:00'
    },
    { 
      id: 2, 
      name: 'Fashion Brand X', 
      avatar: '👗',
      status: 'active',
      plan: 'business',
      revenue: 1800,
      posts: 32,
      views: '1.8M',
      engagement: '78K',
      nextPost: '2024-01-15 16:00'
    },
    { 
      id: 3, 
      name: 'Fitness Coach Pro', 
      avatar: '💪',
      status: 'active',
      plan: 'premium',
      revenue: 2200,
      posts: 38,
      views: '1.9M',
      engagement: '82K',
      nextPost: '2024-01-15 18:00'
    },
    { 
      id: 4, 
      name: 'Food Blogger', 
      avatar: '🍕',
      status: 'trial',
      plan: 'starter',
      revenue: 800,
      posts: 15,
      views: '450K',
      engagement: '23K',
      nextPost: '2024-01-16 10:00'
    }
  ]);

  const [selectedClient, setSelectedClient] = useState(null);
  const [showAddClient, setShowAddClient] = useState(false);

  const planColors = {
    starter: 'from-gray-500 to-gray-700',
    business: 'from-cyber-primary to-blue-600',
    premium: 'from-cyber-purple to-purple-600',
    enterprise: 'from-cyber-green to-green-600'
  };

  const ClientCard = ({ client, index }) => (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02, y: -5 }}
      onClick={() => setSelectedClient(client)}
      className="card-cyber p-6 cursor-pointer relative overflow-hidden"
    >
      {/* Status Indicator */}
      <div className={`absolute top-0 right-0 w-2 h-full ${
        client.status === 'active' ? 'bg-cyber-green' :
        client.status === 'trial' ? 'bg-yellow-500' :
        'bg-red-500'
      }`} />

      <div className="flex items-start gap-4 mb-4">
        <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center text-3xl cyber-glow">
          {client.avatar}
        </div>

        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-bold text-lg">{client.name}</h3>
            {client.plan === 'premium' && <Crown className="w-4 h-4 text-yellow-500" />}
          </div>
          <div className="flex items-center gap-2">
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold bg-gradient-to-r ${planColors[client.plan]} cyber-glow`}>
              {client.plan.toUpperCase()}
            </span>
            <span className={`w-2 h-2 rounded-full animate-pulse ${
              client.status === 'active' ? 'bg-cyber-green' : 'bg-yellow-500'
            }`} />
            <span className="text-xs text-gray-400">{client.status}</span>
          </div>
        </div>

        <button className="p-2 rounded-lg hover:bg-white/10">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="glass p-3 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Revenue</div>
          <div className="text-xl font-bold text-cyber-green">${client.revenue}</div>
        </div>
        <div className="glass p-3 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Posts</div>
          <div className="text-xl font-bold">{client.posts}</div>
        </div>
        <div className="glass p-3 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Views</div>
          <div className="text-xl font-bold text-cyber-primary">{client.views}</div>
        </div>
        <div className="glass p-3 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Engagement</div>
          <div className="text-xl font-bold text-cyber-purple">{client.engagement}</div>
        </div>
      </div>

      {/* Next Post */}
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Calendar className="w-4 h-4" />
        Next post: {new Date(client.nextPost).toLocaleString()}
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div>
          <h1 className="text-4xl font-black mb-2 gradient-text">Agency OS</h1>
          <p className="text-gray-400">Manage all your clients in one powerful dashboard</p>
        </div>

        <button 
          onClick={() => setShowAddClient(true)}
          className="btn-cyber px-6 py-3 flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Client
        </button>
      </motion.div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Total Clients', value: clients.length, icon: Users, color: 'from-cyber-primary to-blue-600' },
          { label: 'Active', value: clients.filter(c => c.status === 'active').length, icon: UserCheck, color: 'from-cyber-green to-green-600' },
          { label: 'Monthly Revenue', value: `$${clients.reduce((acc, c) => acc + c.revenue, 0)}`, icon: DollarSign, color: 'from-cyber-purple to-purple-600' },
          { label: 'Total Posts', value: clients.reduce((acc, c) => acc + c.posts, 0), icon: TrendingUp, color: 'from-pink-500 to-rose-600' }
        ].map((stat, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
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
      </div>

      {/* Client Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-2xl font-bold">Your Clients</h3>
          <div className="flex items-center gap-3">
            <select className="input-cyber">
              <option>All Clients</option>
              <option>Active</option>
              <option>Trial</option>
              <option>Paused</option>
            </select>
            <select className="input-cyber">
              <option>Sort by Revenue</option>
              <option>Sort by Posts</option>
              <option>Sort by Engagement</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {clients.map((client, idx) => (
            <ClientCard key={client.id} client={client} index={idx} />
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-cyber p-6"
      >
        <h3 className="text-xl font-bold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { icon: MessageCircle, label: 'Bulk Message', color: 'from-cyber-primary to-blue-600' },
            { icon: Calendar, label: 'Schedule Report', color: 'from-cyber-purple to-purple-600' },
            { icon: BarChart3, label: 'Generate Report', color: 'from-cyber-green to-green-600' },
            { icon: Mail, label: 'Send Invoice', color: 'from-pink-500 to-rose-600' }
          ].map((action, idx) => (
            <motion.button
              key={idx}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className={`p-6 rounded-xl bg-gradient-to-br ${action.color} text-white font-semibold hover:opacity-90 transition-opacity`}
            >
              <action.icon className="w-8 h-8 mx-auto mb-2" />
              {action.label}
            </motion.button>
          ))}
        </div>
      </motion.div>

      {/* Client Detail Modal */}
      <AnimatePresence>
        {selectedClient && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedClient(null)}
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
                {/* Header */}
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center gap-4">
                    <div className="w-20 h-20 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center text-4xl cyber-glow">
                      {selectedClient.avatar}
                    </div>
                    <div>
                      <h2 className="text-3xl font-black mb-2">{selectedClient.name}</h2>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-sm font-semibold bg-gradient-to-r ${planColors[selectedClient.plan]} cyber-glow`}>
                          {selectedClient.plan.toUpperCase()}
                        </span>
                        <span className="text-sm text-gray-400">Client since Jan 2024</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedClient(null)}
                    className="p-2 rounded-lg hover:bg-white/10"
                  >
                    ✕
                  </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-4 gap-4 mb-6">
                  {[
                    { label: 'Monthly Revenue', value: `$${selectedClient.revenue}`, icon: DollarSign },
                    { label: 'Total Posts', value: selectedClient.posts, icon: Calendar },
                    { label: 'Total Views', value: selectedClient.views, icon: Eye },
                    { label: 'Engagement', value: selectedClient.engagement, icon: TrendingUp }
                  ].map((stat, idx) => (
                    <div key={idx} className="card-cyber p-4 text-center">
                      <stat.icon className="w-6 h-6 text-cyber-primary mx-auto mb-2" />
                      <div className="text-2xl font-bold mb-1">{stat.value}</div>
                      <div className="text-xs text-gray-400">{stat.label}</div>
                    </div>
                  ))}
                </div>

                {/* Actions */}
                <div className="flex gap-4">
                  <button className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2">
                    <MessageCircle className="w-5 h-5" />
                    Message Client
                  </button>
                  <button className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2">
                    <BarChart3 className="w-5 h-5" />
                    View Analytics
                  </button>
                  <button className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2">
                    <Settings className="w-5 h-5" />
                    Settings
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Add Client Modal */}
      <AnimatePresence>
        {showAddClient && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowAddClient(false)}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-6"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="card-cyber max-w-2xl w-full"
            >
              <div className="p-6">
                <h2 className="text-2xl font-black mb-6">Add New Client</h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2">Client Name *</label>
                    <input type="text" placeholder="Enter client name..." className="input-cyber w-full" />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">Email *</label>
                    <input type="email" placeholder="client@example.com" className="input-cyber w-full" />
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">Plan *</label>
                    <select className="input-cyber w-full">
                      <option>Starter - $800/mo</option>
                      <option>Business - $1,800/mo</option>
                      <option>Premium - $2,500/mo</option>
                      <option>Enterprise - Custom</option>
                    </select>
                  </div>

                  <div className="flex gap-4 pt-4">
                    <button className="btn-cyber flex-1 py-3">
                      Add Client
                    </button>
                    <button 
                      onClick={() => setShowAddClient(false)}
                      className="px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AgencyOS;
