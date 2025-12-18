import React from 'react';
import { motion } from 'framer-motion';

export const ViralityMeter = ({ score = 0, label = "Virality Score" }) => {
  // Ensure score is between 0 and 100
  const normalizedScore = Math.max(0, Math.min(100, score));
  const percentage = normalizedScore / 100;
  
  // Calculate color based on score
  const getColor = (score) => {
    if (score >= 80) return '#00ff9d'; // Cyber green
    if (score >= 50) return '#00f2ff'; // Cyber cyan
    if (score >= 30) return '#8b00ff'; // Cyber purple
    return '#ff006e'; // Red for low scores
  };
  
  const color = getColor(normalizedScore);
  
  return (
    <div className="relative flex flex-col items-center">
      {/* Arc Reactor Style Ring */}
      <div className="relative w-40 h-40">
        {/* Outer rotating ring */}
        <motion.svg
          className="absolute inset-0"
          viewBox="0 0 160 160"
          animate={{ rotate: 360 }}
          transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        >
          <defs>
            <linearGradient id="viralGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.8" />
              <stop offset="100%" stopColor={color} stopOpacity="0.2" />
            </linearGradient>
            <filter id="glowFilter">
              <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
              <feMerge>
                <feMergeNode in="coloredBlur"/>
                <feMergeNode in="SourceGraphic"/>
              </feMerge>
            </filter>
          </defs>
          
          {/* Background ring */}
          <circle
            cx="80"
            cy="80"
            r="70"
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth="4"
          />
          
          {/* Progress ring with conic gradient effect */}
          <motion.circle
            cx="80"
            cy="80"
            r="70"
            fill="none"
            stroke="url(#viralGradient)"
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={`${2 * Math.PI * 70}`}
            strokeDashoffset={`${2 * Math.PI * 70 * (1 - percentage)}`}
            filter="url(#glowFilter)"
            transform="rotate(-90 80 80)"
            initial={{ strokeDashoffset: 2 * Math.PI * 70 }}
            animate={{ strokeDashoffset: 2 * Math.PI * 70 * (1 - percentage) }}
            transition={{ duration: 1.5, ease: "easeOut" }}
          />
        </motion.svg>
        
        {/* Inner pulsing core */}
        <motion.div
          className="absolute inset-0 flex items-center justify-center"
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.6, 1, 0.6]
          }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        >
          <div 
            className="w-24 h-24 rounded-full"
            style={{
              background: `radial-gradient(circle, ${color}40, transparent)`,
              boxShadow: `0 0 40px ${color}80`
            }}
          />
        </motion.div>
        
        {/* Score display */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span 
            className="text-4xl font-satoshi font-bold"
            style={{ color }}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            {normalizedScore}
          </motion.span>
          <span className="text-xs text-gray-400 mt-1">/ 100</span>
        </div>
        
        {/* Particle effects */}
        {[...Array(8)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-1 h-1 rounded-full"
            style={{
              background: color,
              left: '50%',
              top: '50%',
              boxShadow: `0 0 10px ${color}`
            }}
            animate={{
              x: [0, Math.cos(i * 45 * Math.PI / 180) * 50],
              y: [0, Math.sin(i * 45 * Math.PI / 180) * 50],
              opacity: [0, 1, 0]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: i * 0.2,
              ease: "easeOut"
            }}
          />
        ))}
      </div>
      
      {/* Label */}
      <motion.p 
        className="mt-4 text-sm font-satoshi font-medium text-gray-300"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
      >
        {label}
      </motion.p>
    </div>
  );
};
