import React from 'react';
import { motion } from 'framer-motion';

export const FloatingCard = ({ children, className = '', delay = 0 }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay }}
      className={`
        relative
        bg-[rgba(10,10,31,0.09)]
        backdrop-blur-xl
        border border-[rgba(0,242,255,0.4)]
        rounded-2xl
        p-6
        shadow-[0_0_30px_rgba(0,242,255,0.4)]
        hover:shadow-[0_0_50px_rgba(0,242,255,0.6)]
        hover:border-[rgba(0,242,255,0.6)]
        transition-all duration-300
        ${className}
      `}
      style={{
        animation: 'float 6s ease-in-out infinite'
      }}
    >
      {/* Inner glow effect */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyber-primary/5 to-transparent pointer-events-none" />
      
      {/* Content */}
      <div className="relative z-10">
        {children}
      </div>
      
      {/* Corner accents */}
      <div className="absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 border-cyber-primary rounded-tl-2xl" />
      <div className="absolute top-0 right-0 w-3 h-3 border-t-2 border-r-2 border-cyber-primary rounded-tr-2xl" />
      <div className="absolute bottom-0 left-0 w-3 h-3 border-b-2 border-l-2 border-cyber-primary rounded-bl-2xl" />
      <div className="absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 border-cyber-primary rounded-br-2xl" />
    </motion.div>
  );
};
