import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { BarChart3, Download, RefreshCw, Calendar, Link as LinkIcon } from 'lucide-react';
import { getAnalyticsSummary, downloadAnalyticsCsv } from '../lib/apiClient';

const AnalyticsPro = () => {
  const { isDark } = useTheme();
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAnalyticsSummary(days);
      setSummary(res);
    } catch (e) {
      setError(e?.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const totalScheduled = summary?.scheduled_posts?.total ?? 0;
  const byPlatform = summary?.scheduled_posts?.by_platform || {};
  const clicksTotal = summary?.links?.clicks_total ?? 0;

  return (
    <div className="space-y-6">
      <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className={`text-4xl font-black mb-2 ${isDark ? 'gradient-text' : 'text-gray-900'}`}>Analytics</h1>
        <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>Real metrics from your portal data (scheduled posts + tracked links)</p>
      </motion.div>

      <div className={`p-6 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}>
        <div className="flex flex-col md:flex-row md:items-center gap-4 justify-between">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-cyan-500" />
            <div className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Reporting window</div>
            <select
              className={`px-4 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
              value={days}
              onChange={(e) => setDays(Number(e.target.value || 30))}
            >
              {[7, 14, 30, 60, 90].map(v => (
                <option key={v} value={v}>{v} days</option>
              ))}
            </select>
          </div>

          <div className="flex gap-3">
            <button
              onClick={load}
              className={`px-4 py-2 rounded-xl transition-colors flex items-center gap-2 ${loading ? 'opacity-60 pointer-events-none' : ''} ${isDark ? 'bg-white/5 hover:bg-white/10 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <button
              onClick={() => downloadAnalyticsCsv(days)}
              className="btn-cyber px-4 py-2 flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </div>
        </div>

        {error && (
          <div className={`mt-4 p-4 rounded-xl text-sm ${isDark ? 'bg-red-500/10 border border-red-500/30 text-red-200' : 'bg-red-50 border border-red-200 text-red-700'}`}>
            {error}
          </div>
        )}

        {summary?.note && (
          <div className={`mt-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {summary.note}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div whileHover={{ scale: 1.02 }} className={`p-6 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}>
          <div className="flex items-center justify-between mb-3">
            <div className={`flex items-center gap-2 font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <BarChart3 className="w-5 h-5 text-cyan-500" />
              Scheduled Posts
            </div>
          </div>
          <div className={`text-4xl font-black mb-2 ${isDark ? 'gradient-text' : 'text-cyan-600'}`}>{String(totalScheduled)}</div>
          <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Total scheduled in last {days} days</div>

          <div className="mt-4 space-y-2">
            {Object.keys(byPlatform).length === 0 ? (
              <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>No platform breakdown yet.</div>
            ) : (
              Object.entries(byPlatform).map(([k, v]) => (
                <div key={k} className="flex items-center justify-between text-sm">
                  <div className={isDark ? 'text-gray-300' : 'text-gray-600'}>{k}</div>
                  <div className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{String(v)}</div>
                </div>
              ))
            )}
          </div>
        </motion.div>

        <motion.div whileHover={{ scale: 1.02 }} className={`p-6 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}>
          <div className="flex items-center justify-between mb-3">
            <div className={`flex items-center gap-2 font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <LinkIcon className="w-5 h-5 text-cyan-500" />
              Link Tracking
            </div>
          </div>
          <div className={`text-4xl font-black mb-2 ${isDark ? 'gradient-text' : 'text-cyan-600'}`}>{String(clicksTotal)}</div>
          <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Total clicks across tracked links</div>
        </motion.div>
      </div>
    </div>
  );
};

export default AnalyticsPro;
