import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, 
  Film, 
  Sparkles, 
  Zap,
  CheckCircle,
  AlertCircle,
  Loader2,
  Play,
  Settings
} from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import { processVideo, scoreVideo } from '../lib/tauri';

const UploadZone = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [settings, setSettings] = useState({
    targetClips: 3,
    quality: 'high',
    scoreFirst: true
  });

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('video/')) {
      handleFileSelect(droppedFile);
    }
  }, []);

  const handleFileSelect = async (selectedFile) => {
    setFile(selectedFile);
    setResult(null);
  };

  const handleBrowse = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Video',
          extensions: ['mp4', 'mov', 'avi', 'mkv', 'webm']
        }]
      });

      if (selected) {
        setFile({ path: selected, name: selected.split(/[\\/]/).pop() });
        setResult(null);
      }
    } catch (error) {
      console.error('File selection failed:', error);
    }
  };

  const handleProcess = async () => {
    if (!file) return;

    setProcessing(true);
    setProgress(0);
    setResult(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + Math.random() * 15, 90));
      }, 500);

      // Score video first if enabled
      if (settings.scoreFirst) {
        const scoreResult = await scoreVideo(file.path || file.name);
        console.log('Video Score:', scoreResult);
      }

      // Process video
      const processResult = await processVideo(
        file.path || file.name,
        settings.targetClips,
        settings.quality
      );

      clearInterval(progressInterval);
      setProgress(100);
      setResult(processResult);
    } catch (error) {
      console.error('Processing failed:', error);
      setResult({ success: false, error: error.toString() });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-4xl font-black mb-2 gradient-text">Video Lab</h1>
        <p className="text-gray-400">Upload your video and let AI create viral clips</p>
      </motion.div>

      {/* Settings Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card-cyber p-6 flex items-center gap-6 flex-wrap"
      >
        <div className="flex items-center gap-3">
          <Settings className="w-5 h-5 text-cyber-primary" />
          <span className="font-semibold">Settings:</span>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Target Clips:</label>
          <select
            value={settings.targetClips}
            onChange={(e) => setSettings({ ...settings, targetClips: parseInt(e.target.value) })}
            className="input-cyber px-3 py-1"
          >
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(n => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-400">Quality:</label>
          <select
            value={settings.quality}
            onChange={(e) => setSettings({ ...settings, quality: e.target.value })}
            className="input-cyber px-3 py-1"
          >
            <option value="high">High (1080p)</option>
            <option value="medium">Medium (720p)</option>
            <option value="low">Low (480p)</option>
          </select>
        </div>

        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={settings.scoreFirst}
            onChange={(e) => setSettings({ ...settings, scoreFirst: e.target.checked })}
            className="w-4 h-4 rounded border-cyber-primary"
          />
          <span className="text-sm">Score video first</span>
        </label>
      </motion.div>

      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative overflow-hidden rounded-2xl border-2 border-dashed transition-all ${
          isDragging 
            ? 'border-cyber-primary bg-cyber-primary/10 scale-105' 
            : 'border-cyber-primary/30 bg-white/5'
        }`}
      >
        <div className="p-12 flex flex-col items-center justify-center gap-6">
          <motion.div
            animate={{ 
              scale: isDragging ? 1.2 : 1,
              rotate: isDragging ? 5 : 0
            }}
            className="w-24 h-24 rounded-full bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center cyber-glow"
          >
            <Upload className="w-12 h-12" />
          </motion.div>

          <div className="text-center">
            <h3 className="text-2xl font-bold mb-2">
              {isDragging ? 'Drop your video here' : 'Drag & Drop Video'}
            </h3>
            <p className="text-gray-400">
              or <button onClick={handleBrowse} className="text-cyber-primary hover:underline">browse</button> to choose a file
            </p>
            <p className="text-sm text-gray-500 mt-2">
              Supports MP4, MOV, AVI, MKV, WebM (max 2GB)
            </p>
          </div>

          {file && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card-cyber p-4 flex items-center gap-4 w-full max-w-md"
            >
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center cyber-glow">
                <Film className="w-6 h-6" />
              </div>

              <div className="flex-1">
                <div className="font-semibold">{file.name}</div>
                <div className="text-sm text-gray-400">Ready to process</div>
              </div>

              <button
                onClick={handleProcess}
                disabled={processing}
                className="btn-cyber px-6 py-2 flex items-center gap-2"
              >
                {processing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Process
                  </>
                )}
              </button>
            </motion.div>
          )}
        </div>

        {/* Animated Background */}
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 bg-gradient-to-br from-cyber-primary/20 to-cyber-purple/20 pointer-events-none"
          />
        )}
      </motion.div>

      {/* Processing Progress */}
      <AnimatePresence>
        {processing && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="card-cyber p-6"
          >
            <div className="flex items-center gap-4 mb-4">
              <Loader2 className="w-6 h-6 text-cyber-primary animate-spin" />
              <div>
                <div className="font-semibold">Processing your video...</div>
                <div className="text-sm text-gray-400">AI is analyzing and creating clips</div>
              </div>
            </div>

            <div className="relative h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyber-primary to-cyber-purple cyber-glow"
              />
            </div>

            <div className="text-sm text-gray-400 mt-2 text-right">{Math.round(progress)}%</div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`card-cyber p-6 ${result.success ? 'border-cyber-green' : 'border-red-500'}`}
          >
            <div className="flex items-start gap-4">
              {result.success ? (
                <CheckCircle className="w-6 h-6 text-cyber-green flex-shrink-0" />
              ) : (
                <AlertCircle className="w-6 h-6 text-red-500 flex-shrink-0" />
              )}

              <div className="flex-1">
                <h3 className="text-xl font-bold mb-2">
                  {result.success ? 'Processing Complete!' : 'Processing Failed'}
                </h3>

                {result.success ? (
                  <>
                    <p className="text-gray-400 mb-4">
                      Created {result.clips?.length || 0} viral clips in {result.processing_time?.toFixed(1) || 0}s
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {result.clips?.map((clip, idx) => (
                        <motion.div
                          key={idx}
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ delay: idx * 0.1 }}
                          whileHover={{ scale: 1.05 }}
                          className="card-cyber p-4"
                        >
                          <div className="w-full h-32 rounded-lg bg-gradient-to-br from-cyber-primary/20 to-cyber-purple/20 flex items-center justify-center mb-3">
                            <Play className="w-8 h-8 text-cyber-primary" />
                          </div>
                          <div className="font-semibold mb-1">Clip {idx + 1}</div>
                          <div className="text-sm text-gray-400">
                            {clip.duration?.toFixed(1) || 0}s • Score: {clip.score || 0}/100
                          </div>
                          <button className="btn-cyber w-full mt-3 py-2">
                            View Clip
                          </button>
                        </motion.div>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-red-400">{result.error}</p>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { icon: Sparkles, title: 'AI Analysis', desc: 'Detects viral moments automatically' },
          { icon: Zap, title: 'Smart Cropping', desc: 'Optimizes for each platform' },
          { icon: Film, title: 'Auto Captions', desc: 'Generates engaging subtitles' }
        ].map((feature, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            whileHover={{ scale: 1.05 }}
            className="card-cyber p-6 text-center"
          >
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center mx-auto mb-3 cyber-glow">
              <feature.icon className="w-6 h-6" />
            </div>
            <h4 className="font-bold mb-2">{feature.title}</h4>
            <p className="text-sm text-gray-400">{feature.desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default UploadZone;
