import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard, 
  Upload, 
  Grid3x3, 
  Calendar, 
  TrendingUp, 
  Users,
  Settings,
  Bell,
  Search,
  Moon,
  Sun
} from 'lucide-react';

// Import components
import Dashboard from './components/Dashboard';
import UploadZone from './components/UploadZone';
import ClipGallery from './components/ClipGallery';
import SchedulerPro from './components/SchedulerPro';
import GrowthMentor from './components/GrowthMentor';
import AgencyOS from './components/AgencyOS';
import Platforms from './components/Platforms';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [isDark, setIsDark] = useState(true);
  const [notifications, setNotifications] = useState(3);

  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'platforms', icon: Users, label: 'Accounts' },
    { id: 'upload', icon: Upload, label: 'Upload' },
    { id: 'clips', icon: Grid3x3, label: 'Clips' },
    { id: 'scheduler', icon: Calendar, label: 'Scheduler' },
    { id: 'growth', icon: TrendingUp, label: 'Growth' },
    { id: 'agency', icon: Users, label: 'Agency' }
  ];

  const renderView = () => {
    switch (activeView) {
      case 'dashboard': return <Dashboard />;
      case 'platforms': return <Platforms />;
      case 'upload': return <UploadZone />;
      case 'clips': return <ClipGallery />;
      case 'scheduler': return <SchedulerPro />;
      case 'growth': return <GrowthMentor />;
      case 'agency': return <AgencyOS />;
      default: return <Dashboard />;
    }
  };

  return (
    <div className="flex h-screen bg-cyber-bg text-white overflow-hidden">
      {/* Cyber Grid Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-cyber-bg via-gray-900 to-cyber-bg opacity-90 pointer-events-none" />
      <div className="fixed inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgwLDI0MiwyNTUsMC4xKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20 pointer-events-none" />

      {/* Sidebar */}
      <motion.div 
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        className="w-20 glass border-r border-cyber-primary/20 flex flex-col items-center py-6 gap-8 relative z-50"
      >
        {/* Logo */}
        <motion.div 
          whileHover={{ scale: 1.1, rotate: 5 }}
          className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center font-black text-xl cursor-pointer cyber-glow"
        >
          FYI
        </motion.div>

        {/* Nav Items */}
        <nav className="flex-1 flex flex-col gap-4">
          {navItems.map((item, idx) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            
            return (
              <motion.button
                key={item.id}
                initial={{ x: -50, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: idx * 0.05 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setActiveView(item.id)}
                className={`w-14 h-14 rounded-xl flex items-center justify-center transition-all relative group ${
                  isActive 
                    ? 'bg-gradient-to-br from-cyber-primary to-cyber-purple cyber-glow' 
                    : 'bg-white/5 hover:bg-white/10'
                }`}
                title={item.label}
              >
                <Icon className="w-6 h-6" />
                {isActive && (
                  <motion.div 
                    layoutId="activeIndicator"
                    className="absolute -left-1 top-1/2 -translate-y-1/2 w-1 h-8 bg-cyber-primary rounded-full"
                  />
                )}
                
                {/* Tooltip */}
                <div className="absolute left-20 bg-gray-900 text-white px-3 py-1.5 rounded-lg text-sm whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity border border-cyber-primary/30 z-[9999]">
                  {item.label}
                </div>
              </motion.button>
            );
          })}
        </nav>

        {/* Bottom Icons */}
        <div className="flex flex-col gap-4">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            className="w-14 h-14 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center relative"
          >
            <Bell className="w-6 h-6" />
            {notifications > 0 && (
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center font-bold"
              >
                {notifications}
              </motion.div>
            )}
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            className="w-14 h-14 rounded-xl bg-white/5 hover:bg-white/10 flex items-center justify-center"
          >
            <Settings className="w-6 h-6" />
          </motion.button>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* Top Bar */}
        <motion.div 
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          className="h-16 glass border-b border-cyber-primary/20 flex items-center justify-between px-6"
        >
          <div className="flex items-center gap-4 flex-1 max-w-2xl">
            <Search className="w-5 h-5 text-gray-400" />
            <input 
              type="text"
              placeholder="Search everything..."
              className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-400"
            />
          </div>

          <div className="flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsDark(!isDark)}
              className="w-10 h-10 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </motion.button>

            <motion.div
              whileHover={{ scale: 1.05 }}
              className="w-10 h-10 rounded-full bg-gradient-to-br from-cyber-primary to-cyber-purple cursor-pointer cyber-glow"
            />
          </div>
        </motion.div>

        {/* View Content */}
        <div className="flex-1 overflow-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderView()}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export default App;
