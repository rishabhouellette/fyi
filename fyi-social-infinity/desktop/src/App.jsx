import React, { useState } from 'react';
import { SidebarInfinity } from '../../shared/ui/components/SidebarInfinity';
import { FloatingCard } from '../../shared/ui/components/FloatingCard';
import { GlowingButton } from '../../shared/ui/components/GlowingButton';
import { HolographicUploadZone } from '../../shared/ui/components/HolographicUploadZone';
import { ViralityMeter } from '../../shared/ui/components/ViralityMeter';
import { AIStatusOrb } from '../../shared/ui/components/AIStatusOrb';

export default function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');

  const handleFileUpload = (files) => {
    console.log('Files uploaded:', files);
  };

  return (
    <div className="flex min-h-screen bg-gradient-to-b from-cyber-void to-cyber-bg">
      {/* Sidebar */}
      <SidebarInfinity currentPage={currentPage} onPageChange={setCurrentPage} />
      
      {/* Main Content */}
      <main className="flex-1 p-8 overflow-auto">
        {/* Header */}
        <header className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-satoshi font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyber-primary to-cyber-purple mb-2">
              Welcome to the Future
            </h1>
            <p className="text-gray-400">
              The tool that ends every paid social media SaaS
            </p>
          </div>
          
          <AIStatusOrb status="active" label="Local Brain Active" />
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <FloatingCard delay={0.1}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-1">Total Posts</p>
                <p className="text-3xl font-satoshi font-bold text-cyber-green">1,247</p>
              </div>
              <div className="text-4xl">📊</div>
            </div>
          </FloatingCard>
          
          <FloatingCard delay={0.2}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-1">Engagement Rate</p>
                <p className="text-3xl font-satoshi font-bold text-cyber-primary">94.2%</p>
              </div>
              <div className="text-4xl">📈</div>
            </div>
          </FloatingCard>
          
          <FloatingCard delay={0.3}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 mb-1">AI Generated</p>
                <p className="text-3xl font-satoshi font-bold text-cyber-purple">832</p>
              </div>
              <div className="text-4xl">🧠</div>
            </div>
          </FloatingCard>
        </div>

        {/* Main Action Area */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Upload Zone */}
          <div className="lg:col-span-2">
            <FloatingCard delay={0.4}>
              <h2 className="text-2xl font-satoshi font-bold mb-6 text-white">
                Upload Content
              </h2>
              <HolographicUploadZone onFileUpload={handleFileUpload} />
            </FloatingCard>
          </div>
          
          {/* Virality Meter */}
          <div>
            <FloatingCard delay={0.5}>
              <h2 className="text-2xl font-satoshi font-bold mb-6 text-white text-center">
                Content Score
              </h2>
              <div className="flex justify-center">
                <ViralityMeter score={87} label="Predicted Virality" />
              </div>
            </FloatingCard>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-8">
          <GlowingButton variant="primary" size="lg">
            ⚡ Generate AI Content
          </GlowingButton>
          <GlowingButton variant="purple" size="lg">
            🎬 Schedule Posts
          </GlowingButton>
          <GlowingButton variant="green" size="lg">
            📊 View Analytics
          </GlowingButton>
        </div>

        {/* Recent Activity */}
        <FloatingCard delay={0.6}>
          <h2 className="text-2xl font-satoshi font-bold mb-6 text-white">
            Recent Activity
          </h2>
          <div className="space-y-4">
            {[
              { action: 'Posted to Instagram', time: '2 minutes ago', status: 'success' },
              { action: 'AI Generated Caption', time: '5 minutes ago', status: 'success' },
              { action: 'Scheduled 3 posts', time: '1 hour ago', status: 'pending' },
            ].map((item, i) => (
              <div 
                key={i}
                className="flex items-center justify-between p-4 rounded-lg bg-cyber-glass border border-cyber-border/30 hover:border-cyber-border hover:bg-cyber-glass/20 transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-2 h-2 rounded-full ${item.status === 'success' ? 'bg-cyber-green animate-pulse' : 'bg-cyber-primary animate-pulse'}`} />
                  <div>
                    <p className="font-satoshi font-medium text-white">{item.action}</p>
                    <p className="text-sm text-gray-500">{item.time}</p>
                  </div>
                </div>
                <span className="text-2xl">{item.status === 'success' ? '✓' : '⏱️'}</span>
              </div>
            ))}
          </div>
        </FloatingCard>
      </main>
    </div>
  );
}
