import React from 'react';
import { motion } from 'framer-motion';

export const GlowingButton = ({ 
  children, 
  onClick, 
  variant = 'primary',
  size = 'md',
  className = '',
  ...props 
}) => {
  const baseStyles = "relative font-satoshi font-medium tracking-wide transition-all duration-300 ease-out overflow-hidden";
  
  const sizeStyles = {
    sm: "px-4 py-2 text-sm",
    md: "px-6 py-3 text-base",
    lg: "px-8 py-4 text-lg"
  };
  
  const variantStyles = {
    primary: `
      border-2 border-cyber-primary
      text-cyber-primary
      hover:bg-cyber-primary hover:text-black
      shadow-[0_0_20px_rgba(0,242,255,0.4)]
      hover:shadow-[0_0_40px_rgba(0,242,255,0.8)]
    `,
    purple: `
      border-2 border-cyber-purple
      text-cyber-purple
      hover:bg-cyber-purple hover:text-white
      shadow-[0_0_20px_rgba(139,0,255,0.4)]
      hover:shadow-[0_0_40px_rgba(139,0,255,0.8)]
    `,
    green: `
      border-2 border-cyber-green
      text-cyber-green
      hover:bg-cyber-green hover:text-black
      shadow-[0_0_20px_rgba(0,255,157,0.4)]
      hover:shadow-[0_0_40px_rgba(0,255,157,0.8)]
    `
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        ${baseStyles}
        ${sizeStyles[size]}
        ${variantStyles[variant]}
        ${className}
      `}
      {...props}
    >
      {/* Pulsing border animation */}
      <motion.div
        className="absolute inset-0 border-2 border-cyber-primary rounded-inherit"
        animate={{
          boxShadow: [
            '0 0 10px rgba(0,242,255,0.3)',
            '0 0 20px rgba(0,242,255,0.6)',
            '0 0 10px rgba(0,242,255,0.3)'
          ]
        }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
      />
      
      {/* Radial gradient fill on hover */}
      <motion.div
        className="absolute inset-0 bg-gradient-radial from-cyber-primary/20 to-transparent opacity-0 hover:opacity-100"
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      />
      
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
};
