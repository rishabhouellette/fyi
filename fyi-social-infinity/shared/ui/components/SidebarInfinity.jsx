import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const menuItems = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'upload', label: 'Upload', icon: '⬆️' },
  { id: 'content', label: 'Content', icon: '🎬' },
  { id: 'analytics', label: 'Analytics', icon: '📈' },
  { id: 'ai-brain', label: 'AI Brain', icon: '🧠' },
  { id: 'calendar', label: 'Calendar', icon: '📅' },
  { id: 'team', label: 'Team', icon: '👥' },
  { id: 'settings', label: 'Settings', icon: '⚙️' }
];

export const SidebarInfinity = ({ currentPage = 'dashboard', onPageChange }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <motion.div
      className="relative h-screen bg-cyber-void/50 backdrop-blur-xl border-r border-cyber-border"
      initial={{ width: 280 }}
      animate={{ width: isCollapsed ? 80 : 280 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      onMouseEnter={() => setIsCollapsed(false)}
      onMouseLeave={() => setIsCollapsed(true)}
    >
      {/* Logo Section */}
      <div className="flex items-center justify-center h-20 border-b border-cyber-border">
        <AnimatePresence mode="wait">
          {isCollapsed ? (
            // Glowing ∞ Symbol
            <motion.div
              key="infinity"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.5 }}
              transition={{ duration: 0.2 }}
              className="relative"
            >
              <motion.svg
                width="40"
                height="40"
                viewBox="0 0 100 100"
                animate={{
                  filter: [
                    'drop-shadow(0 0 10px rgba(0,242,255,0.8))',
                    'drop-shadow(0 0 20px rgba(0,242,255,1))',
                    'drop-shadow(0 0 10px rgba(0,242,255,0.8))'
                  ]
                }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <defs>
                  <linearGradient id="infinityGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#00f2ff" />
                    <stop offset="100%" stopColor="#8b00ff" />
                  </linearGradient>
                </defs>
                <path
                  d="M30 50 C30 30, 20 20, 10 20 C0 20, 0 30, 0 50 C0 70, 0 80, 10 80 C20 80, 30 70, 30 50 M30 50 C30 70, 40 80, 50 80 C60 80, 70 70, 70 50 C70 30, 60 20, 50 20 C40 20, 30 30, 30 50"
                  transform="translate(15, 0)"
                  fill="none"
                  stroke="url(#infinityGradient)"
                  strokeWidth="8"
                  strokeLinecap="round"
                />
              </motion.svg>
            </motion.div>
          ) : (
            // Full Logo
            <motion.div
              key="full-logo"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex items-center gap-3"
            >
              <svg width="36" height="36" viewBox="0 0 100 100">
                <defs>
                  <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#00f2ff" />
                    <stop offset="100%" stopColor="#8b00ff" />
                  </linearGradient>
                </defs>
                <path
                  d="M30 50 C30 30, 20 20, 10 20 C0 20, 0 30, 0 50 C0 70, 0 80, 10 80 C20 80, 30 70, 30 50 M30 50 C30 70, 40 80, 50 80 C60 80, 70 70, 70 50 C70 30, 60 20, 50 20 C40 20, 30 30, 30 50"
                  transform="translate(15, 0)"
                  fill="none"
                  stroke="url(#logoGradient)"
                  strokeWidth="8"
                  strokeLinecap="round"
                />
              </svg>
              <div>
                <h1 className="text-xl font-satoshi font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyber-primary to-cyber-purple">
                  FYI Social
                </h1>
                <p className="text-xs text-gray-500">∞ Infinite Reach</p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation Items */}
      <nav className="py-4">
        {menuItems.map((item, index) => {
          const isActive = currentPage === item.id;
          
          return (
            <motion.button
              key={item.id}
              onClick={() => onPageChange?.(item.id)}
              className={`
                w-full flex items-center gap-4 px-6 py-3
                transition-all duration-300
                ${isActive ? 'bg-cyber-primary/10 border-r-2 border-cyber-primary' : 'hover:bg-cyber-primary/5'}
              `}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              whileHover={{ x: 5 }}
            >
              <span className="text-2xl">{item.icon}</span>
              
              <AnimatePresence>
                {!isCollapsed && (
                  <motion.span
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: 'auto' }}
                    exit={{ opacity: 0, width: 0 }}
                    className={`
                      font-satoshi font-medium
                      ${isActive ? 'text-cyber-primary' : 'text-gray-400'}
                    `}
                  >
                    {item.label}
                  </motion.span>
                )}
              </AnimatePresence>
              
              {isActive && (
                <motion.div
                  layoutId="activeIndicator"
                  className="absolute right-0 w-1 h-8 bg-cyber-primary rounded-l-full"
                  style={{ boxShadow: '0 0 10px rgba(0,242,255,0.8)' }}
                />
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Bottom Section - User Profile */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-cyber-border">
        <motion.div 
          className="flex items-center gap-3"
          animate={{ x: isCollapsed ? -10 : 0 }}
        >
          <div className="relative">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyber-primary to-cyber-purple" />
            <div className="absolute bottom-0 right-0 w-3 h-3 bg-cyber-green rounded-full border-2 border-cyber-void" />
          </div>
          
          <AnimatePresence>
            {!isCollapsed && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <p className="text-sm font-satoshi font-medium text-white">Free Forever</p>
                <p className="text-xs text-gray-500">∞ Plan</p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </motion.div>
  );
};
