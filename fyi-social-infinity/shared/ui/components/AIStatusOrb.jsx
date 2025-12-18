import React from 'react';
import { motion } from 'framer-motion';

export const AIStatusOrb = ({ status = 'active', label = 'Local Brain Active' }) => {
  const isActive = status === 'active';
  
  return (
    <motion.div 
      className="flex items-center gap-3"
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Pulsing Purple Orb */}
      <div className="relative w-12 h-12">
        {/* Outer glow rings */}
        <motion.div
          className="absolute inset-0 rounded-full bg-cyber-purple/20"
          animate={isActive ? {
            scale: [1, 1.5, 1],
            opacity: [0.5, 0, 0.5]
          } : {}}
          transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
        />
        
        <motion.div
          className="absolute inset-0 rounded-full bg-cyber-purple/30"
          animate={isActive ? {
            scale: [1, 1.3, 1],
            opacity: [0.6, 0, 0.6]
          } : {}}
          transition={{ duration: 2, repeat: Infinity, ease: "easeOut", delay: 0.5 }}
        />
        
        {/* Core orb */}
        <motion.div
          className="absolute inset-2 rounded-full bg-gradient-to-br from-cyber-purple to-purple-600"
          style={{
            boxShadow: '0 0 30px rgba(139, 0, 255, 0.8), inset 0 0 10px rgba(255, 255, 255, 0.3)'
          }}
          animate={isActive ? {
            boxShadow: [
              '0 0 30px rgba(139, 0, 255, 0.8), inset 0 0 10px rgba(255, 255, 255, 0.3)',
              '0 0 50px rgba(139, 0, 255, 1), inset 0 0 20px rgba(255, 255, 255, 0.5)',
              '0 0 30px rgba(139, 0, 255, 0.8), inset 0 0 10px rgba(255, 255, 255, 0.3)'
            ]
          } : {}}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        />
        
        {/* Inner light spot */}
        <div className="absolute top-3 left-3 w-2 h-2 rounded-full bg-white/80 blur-sm" />
        
        {/* Energy particles */}
        {isActive && [...Array(6)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 rounded-full bg-cyber-purple"
            style={{
              left: '50%',
              top: '50%',
            }}
            animate={{
              x: [0, (Math.cos(i * 60 * Math.PI / 180) * 20)],
              y: [0, (Math.sin(i * 60 * Math.PI / 180) * 20)],
              opacity: [1, 0]
            }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              delay: i * 0.1,
              ease: "easeOut"
            }}
          />
        ))}
      </div>
      
      {/* Status Label */}
      <div>
        <motion.p 
          className="text-sm font-satoshi font-bold text-cyber-purple"
          animate={isActive ? {
            opacity: [1, 0.7, 1]
          } : {}}
          transition={{ duration: 2, repeat: Infinity }}
        >
          {label}
        </motion.p>
        <p className="text-xs text-gray-500">
          {isActive ? 'Processing locally' : 'Standby'}
        </p>
      </div>
      
      {/* Status indicator dot */}
      <motion.div
        className={`w-2 h-2 rounded-full ${isActive ? 'bg-cyber-green' : 'bg-gray-600'}`}
        animate={isActive ? {
          opacity: [1, 0.3, 1],
          scale: [1, 1.2, 1]
        } : {}}
        transition={{ duration: 1.5, repeat: Infinity }}
        style={{
          boxShadow: isActive ? '0 0 10px rgba(0, 255, 157, 0.8)' : 'none'
        }}
      />
    </motion.div>
  );
};
