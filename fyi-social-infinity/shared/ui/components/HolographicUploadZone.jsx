import React, { useCallback } from 'react';
import { motion } from 'framer-motion';
import { useDropzone } from 'react-dropzone';

export const HolographicUploadZone = ({ onFileUpload }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (onFileUpload) {
      onFileUpload(acceptedFiles);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'video/*': ['.mp4', '.mov', '.avi', '.mkv'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif']
    }
  });

  return (
    <motion.div
      {...getRootProps()}
      className="relative w-full h-96 flex items-center justify-center cursor-pointer"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.3 }}
    >
      <input {...getInputProps()} />
      
      {/* Massive pulsing holographic circle */}
      <motion.div
        className="absolute w-80 h-80 rounded-full border-4 border-cyber-primary"
        animate={{
          scale: isDragActive ? [1, 1.1, 1] : [1, 1.05, 1],
          boxShadow: [
            '0 0 40px rgba(0,242,255,0.4)',
            '0 0 80px rgba(0,242,255,0.8)',
            '0 0 40px rgba(0,242,255,0.4)'
          ]
        }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
      />
      
      {/* Inner circle */}
      <motion.div
        className="absolute w-64 h-64 rounded-full border-2 border-cyber-purple/50"
        animate={{
          scale: [1, 1.05, 1],
          opacity: [0.5, 0.8, 0.5]
        }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 }}
      />
      
      {/* Ripple effect on drag */}
      {isDragActive && (
        <motion.div
          className="absolute w-96 h-96 rounded-full border-4 border-cyber-green"
          initial={{ scale: 0.8, opacity: 1 }}
          animate={{ scale: 1.5, opacity: 0 }}
          transition={{ duration: 1, repeat: Infinity }}
        />
      )}
      
      {/* Center content */}
      <div className="relative z-10 text-center">
        <motion.div
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
        >
          <svg 
            className="mx-auto mb-4 w-16 h-16" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" 
              className="stroke-cyber-primary"
            />
          </svg>
        </motion.div>
        
        <h3 className="text-2xl font-satoshi font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyber-primary to-cyber-purple mb-2">
          Drop Your Content
        </h3>
        
        <p className="text-gray-400 font-satoshi">
          {isDragActive ? 
            'Release to upload' : 
            'Drag & drop videos or images here'
          }
        </p>
        
        <p className="text-sm text-gray-500 mt-2">
          Or click to browse files
        </p>
      </div>
      
      {/* Holographic grid background */}
      <div className="absolute inset-0 opacity-10 pointer-events-none">
        <div className="w-full h-full" style={{
          backgroundImage: `
            linear-gradient(rgba(0,242,255,0.2) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,242,255,0.2) 1px, transparent 1px)
          `,
          backgroundSize: '50px 50px'
        }} />
      </div>
    </motion.div>
  );
};
