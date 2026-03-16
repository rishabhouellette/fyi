import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { 
  LayoutDashboard, 
  Upload, 
  Grid3x3, 
  Calendar, 
  TrendingUp, 
  Sparkles,
  Users,
  Settings,
  Bell,
  Search,
  Moon,
  Sun,
  Brain,
  LogOut,
  User,
  ChevronDown
} from 'lucide-react';
import { useTheme } from './context/ThemeContext';
import logoImg from '/logo.png?url';

// Import components
import Dashboard from './components/Dashboard';
import UploadZone from './components/UploadZone';
import ClipGallery from './components/ClipGallery';
import UploadScheduler from './components/UploadScheduler';
import AnalyticsPro from './components/AnalyticsPro';
import AgencyOS from './components/AgencyOS';
import Platforms from './components/Platforms';
import AIStudio from './components/AIStudio';
import XYAI from './components/XYAI';
import SettingsPanel from './components/SettingsPanel';
import NotificationPanel from './components/NotificationPanel';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const { isDark, toggleTheme } = useTheme();
  const [notifications, setNotifications] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [user] = useState({
    name: 'User Account',
    email: 'user@viralclip.tech',
    initials: 'UA'
  });

  const navItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'platforms', icon: Users, label: 'Accounts' },
    { id: 'upload', icon: Upload, label: 'Upload' },
    { id: 'clips', icon: Grid3x3, label: 'Clips' },
    { id: 'studio', icon: Sparkles, label: 'AI Studio' },
    { id: 'xyai', icon: Brain, label: 'XY-AI' },
    { id: 'growth', icon: TrendingUp, label: 'Analytics' },
    { id: 'agency', icon: Users, label: 'Agency' },
  ];

  // All views defined once — they stay mounted so state persists across tab switches
  const allViews = useMemo(() => [
    { id: 'dashboard', component: <Dashboard /> },
    { id: 'platforms', component: <Platforms /> },
    { id: 'upload', component: <UploadScheduler /> },
    { id: 'clips', component: <ClipGallery /> },
    { id: 'studio', component: <AIStudio /> },
    { id: 'xyai', component: <XYAI /> },
    { id: 'growth', component: <AnalyticsPro /> },
    { id: 'agency', component: <AgencyOS /> },
    { id: 'settings', component: <SettingsPanel /> },
  ], []);

  return (
    <div className={`flex h-screen overflow-hidden transition-colors duration-300 ${isDark ? 'bg-cyber-bg text-white' : 'bg-gray-100 text-gray-900'}`}>
      {/* Cyber Grid Background - only show in dark mode */}
      {isDark && (
        <>
          <div className="fixed inset-0 bg-gradient-to-br from-cyber-bg via-gray-900 to-cyber-bg opacity-90 pointer-events-none" />
          <div className="fixed inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgwLDI0MiwyNTUsMC4xKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-20 pointer-events-none" />
        </>
      )}

      {/* Sidebar */}
      <motion.div 
        initial={{ x: -300 }}
        animate={{ x: 0 }}
        className={`w-20 border-r flex flex-col items-center py-6 gap-8 relative z-50 transition-colors duration-300 ${isDark ? 'glass border-cyber-primary/20' : 'bg-white border-gray-200 shadow-lg'}`}
      >
        {/* Logo - Home Button */}
        <motion.button 
          whileHover={{ scale: 1.1, rotate: 5 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setActiveView('dashboard')}
          className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center font-black text-xs cursor-pointer cyber-glow overflow-hidden"
          title="Home - ViralClip.tech"
        >
          <img 
            src={logoImg} 
            alt="ViralClip Logo" 
            className="w-10 h-10 object-contain"
          />
        </motion.button>

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
                    ? 'bg-gradient-to-br from-cyber-primary to-cyber-purple cyber-glow text-white' 
                    : isDark 
                      ? 'bg-white/5 hover:bg-white/10 text-white' 
                      : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
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
                <div className={`absolute left-20 px-3 py-1.5 rounded-lg text-sm whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-[9999] ${isDark ? 'bg-gray-900 text-white border border-cyber-primary/30' : 'bg-gray-800 text-white'}`}>
                  {item.label}
                </div>
              </motion.button>
            );
          })}
        </nav>

        {/* Bottom Icons */}
        <div className="flex flex-col gap-4">
          <div className="relative">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowNotifications(prev => !prev)}
              className={`w-14 h-14 rounded-xl flex items-center justify-center relative transition-colors ${isDark ? 'bg-white/5 hover:bg-white/10 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
            >
              <Bell className="w-6 h-6" />
              {notifications > 0 && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center font-bold text-white"
                >
                  {notifications}
                </motion.div>
              )}
            </motion.button>
            <NotificationPanel
              isOpen={showNotifications}
              onClose={() => setShowNotifications(false)}
              onCountChange={(count) => setNotifications(count)}
            />
          </div>
          
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setActiveView('settings')}
            className={`w-14 h-14 rounded-xl flex items-center justify-center transition-colors ${
              activeView === 'settings'
                ? 'bg-gradient-to-br from-cyber-primary to-cyber-purple cyber-glow text-white'
                : isDark 
                  ? 'bg-white/5 hover:bg-white/10 text-white' 
                  : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
            title="Settings"
          >
            <Settings className="w-6 h-6" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              if (confirm('Are you sure you want to logout?')) {
                localStorage.clear();
                sessionStorage.clear();
                window.location.href = '/';
              }
            }}
            className={`w-14 h-14 rounded-xl flex items-center justify-center transition-colors ${isDark ? 'bg-red-500/10 hover:bg-red-500/20 text-red-400' : 'bg-red-50 hover:bg-red-100 text-red-600'}`}
            title="Logout"
          >
            <LogOut className="w-6 h-6" />
          </motion.button>
        </div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative z-10">
        {/* Top Bar */}
        <motion.div 
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          className={`h-16 border-b flex items-center justify-between px-6 transition-colors duration-300 overflow-visible ${isDark ? 'glass border-cyber-primary/20' : 'bg-white border-gray-200 shadow-sm'}`}
          style={{ position: 'relative', zIndex: 100 }}
        >
          <div className="flex items-center gap-4 flex-1 max-w-2xl">
            <Search className={`w-5 h-5 ${isDark ? 'text-gray-400' : 'text-gray-500'}`} />
            <input 
              type="text"
              placeholder="Search everything..."
              className={`flex-1 bg-transparent border-none outline-none ${isDark ? 'text-white placeholder-gray-400' : 'text-gray-900 placeholder-gray-500'}`}
            />
          </div>

          <div className="flex items-center gap-4">
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              onClick={toggleTheme}
              className={`w-10 h-10 rounded-lg flex items-center justify-center transition-colors ${isDark ? 'bg-white/5 hover:bg-white/10 text-yellow-400' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </motion.button>

            <div className="relative">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowProfileMenu(!showProfileMenu)}
                className="w-10 h-10 rounded-full bg-gradient-to-br from-cyber-primary to-cyber-purple cursor-pointer cyber-glow flex items-center justify-center font-bold text-white text-sm transition-all"
                title="Profile"
              >
                {user.initials}
              </motion.button>
              
              {/* Profile Dropdown Menu */}
              {showProfileMenu && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className={`absolute right-0 mt-2 w-56 rounded-xl shadow-2xl z-[99999] border top-full ${isDark ? 'glass border-cyber-primary/20 bg-gray-900/95' : 'bg-white border-gray-200'}`}
                  style={{ position: 'absolute', zIndex: 99999 }}
                >
                  {/* User Info */}
                  <div className={`p-4 border-b ${isDark ? 'border-gray-700' : 'border-gray-100'}`}>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center font-bold text-white text-sm">
                        {user.initials}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`font-semibold text-sm truncate ${isDark ? 'text-white' : 'text-gray-900'}`}>
                          {user.name}
                        </p>
                        <p className={`text-xs truncate ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                          {user.email}
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Menu Items */}
                  <div className="p-2">
                    <motion.button
                      whileHover={{ backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
                      onClick={() => {
                        setActiveView('settings');
                        setShowProfileMenu(false);
                      }}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'}`}
                    >
                      <Settings className="w-4 h-4" />
                      <span>Settings</span>
                    </motion.button>
                    
                    <motion.button
                      whileHover={{ backgroundColor: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
                      onClick={() => {
                        setShowProfileMenu(false);
                      }}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'}`}
                    >
                      <User className="w-4 h-4" />
                      <span>Account</span>
                    </motion.button>
                    
                    <div className={`my-1 border-t ${isDark ? 'border-gray-700' : 'border-gray-100'}`} />
                    
                    <motion.button
                      whileHover={{ backgroundColor: 'rgba(239, 68, 68, 0.1)' }}
                      onClick={() => {
                        if (confirm('Are you sure you want to logout?')) {
                          localStorage.clear();
                          sessionStorage.clear();
                          window.location.href = '/';
                        }
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-red-400 hover:text-red-500 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Logout</span>
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>

        {/* View Content — all views stay mounted, only active one is visible */}
        <div className={`flex-1 overflow-auto p-6 transition-colors duration-300 ${isDark ? '' : 'bg-gray-50'}`}>
          {allViews.map(({ id, component }) => (
            <div
              key={id}
              style={{ display: activeView === id ? 'block' : 'none' }}
            >
              {component}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
