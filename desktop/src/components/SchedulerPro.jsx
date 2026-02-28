import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../context/ThemeContext';
import { apiFetch } from '../lib/apiClient';
import { 
  Calendar, 
  Clock, 
  Send,
  Instagram,
  Youtube,
  Facebook,
  Linkedin,
  Twitter,
  Plus,
  Edit,
  Trash2,
  Copy,
  CheckCircle
} from 'lucide-react';
import { getScheduledPosts, schedulePost, publishInstant, getScheduleProgress, updateScheduledPost, cancelScheduledPost, getAccounts, getActiveAccounts } from '../lib/apiClient';

const SchedulerPro = ({ uploadedFileId, uploadedItems = [], embedded = false, defaultTitle = '', defaultCaption = '', onRemoveUploadedItem }) => {
  const { isDark } = useTheme();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [scheduledPosts, setScheduledPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bulkBusy, setBulkBusy] = useState(false);

  const [editing, setEditing] = useState(null);
  const [editForm, setEditForm] = useState({ title: '', caption: '', platforms: [], scheduledTime: '' });

  const [newPost, setNewPost] = useState({
    title: defaultTitle || '',
    caption: defaultCaption || '',
    platforms: [],
    scheduledTime: '',
    clips: [],
    accounts: {}
  });

  const [accounts, setAccounts] = useState([]);
  const [activeAccounts, setActiveAccounts] = useState({});

  const lastPrefillRef = useRef({ title: defaultTitle || '', caption: defaultCaption || '' });

  useEffect(() => {
    if (!embedded) return;
    const nextTitle = defaultTitle || '';
    const nextCaption = defaultCaption || '';

    setNewPost(prev => {
      const last = lastPrefillRef.current;
      const shouldUpdateTitle = !prev.title || prev.title === last.title;
      const shouldUpdateCaption = (!prev.caption && !prev.caption?.length) || prev.caption === last.caption;
      const updated = {
        ...prev,
        title: shouldUpdateTitle ? nextTitle : prev.title,
        caption: shouldUpdateCaption ? nextCaption : prev.caption,
      };
      lastPrefillRef.current = { title: nextTitle, caption: nextCaption };
      return updated;
    });
  }, [embedded, defaultTitle, defaultCaption]);

  const [smartSchedule, setSmartSchedule] = useState(false);
  const [intervalMinutes, setIntervalMinutes] = useState(60);

  const [scheduleBusy, setScheduleBusy] = useState(false);
  const [queue, setQueue] = useState([]); // { key, title, filename, status, error, remotePct, remoteMsg }
  const [selectedKeys, setSelectedKeys] = useState(new Set());
  const [queueMode, setQueueMode] = useState('schedule'); // schedule|instant

  const [captionOverrides, setCaptionOverrides] = useState({}); // { [key]: string }
  const [editingCaptionKey, setEditingCaptionKey] = useState(null);
  const [captionDrafts, setCaptionDrafts] = useState({}); // { [key]: string }

  const uploadedItemsRef = useRef([]);
  useEffect(() => {
    uploadedItemsRef.current = Array.isArray(uploadedItems) ? uploadedItems : [];
  }, [uploadedItems]);

  const fileStem = (name) => {
    const s = String(name || '').trim();
    if (!s) return '';
    return s.replace(/\.[^/.]+$/, '');
  };

  const normalizeSpaces = (s) => String(s || '').replace(/\s+/g, ' ').trim();

  const truncateLabel = (s, maxLen = 90) => {
    const v = normalizeSpaces(s);
    if (!v) return '';
    if (v.length <= maxLen) return v;
    return `${v.slice(0, Math.max(0, maxLen - 1))}…`;
  };

  const buildCaptionWithFilename = (filename, overrideCaption) => {
    const stem = fileStem(filename);
    const override = normalizeSpaces(overrideCaption);
    if (!override) return stem || '';
    if (!stem) return override;
    const lowerStem = stem.toLowerCase();
    const lowerOverride = override.toLowerCase();
    if (lowerOverride.startsWith(lowerStem)) return override;
    return normalizeSpaces(`${stem} ${override}`);
  };

  const resolveFinalCaption = (item, effectiveCaption) => {
    const key = item?.key;
    const override = key && captionOverrides && captionOverrides[key] != null
      ? normalizeSpaces(captionOverrides[key])
      : '';
    // IMPORTANT: If the user provided an override via the per-item editor, treat it as the FULL caption.
    // This prevents "original filename + edited filename" being merged.
    if (override) return override;
    return String(item?.caption || effectiveCaption || '').trim();
  };

  const platformIcons = {
    Instagram: { icon: Instagram, color: 'from-pink-500 to-purple-600' },
    YouTube: { icon: Youtube, color: 'from-red-500 to-red-700' },
    Facebook: { icon: Facebook, color: 'from-blue-500 to-blue-700' },
    LinkedIn: { icon: Linkedin, color: 'from-blue-600 to-blue-800' },
    Twitter: { icon: Twitter, color: 'from-cyan-400 to-blue-500' },
    TikTok: { icon: Send, color: 'from-black to-gray-800' }
  };

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const res = await getScheduledPosts();
        if (res?.success && Array.isArray(res.posts)) {
          setScheduledPosts(res.posts);
        }
      } catch (error) {
        console.error('Failed to load scheduled posts:', error);
      } finally {
        setLoading(false);
      }
    };
    load();

    const t = setInterval(() => {
      load();
    }, 10000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const loadAccounts = async () => {
      try {
        const [acctRes, activeRes] = await Promise.all([
          getAccounts().catch(() => null),
          getActiveAccounts().catch(() => null)
        ]);
        const list = Array.isArray(acctRes?.accounts) ? acctRes.accounts : [];
        setAccounts(list);
        setActiveAccounts(activeRes?.active && typeof activeRes.active === 'object' ? activeRes.active : {});
      } catch (e) {
        console.error('Failed to load accounts:', e);
      }
    };
    loadAccounts();
  }, []);

  useEffect(() => {
    if (!embedded) return;
    const list = Array.isArray(uploadedItems) ? uploadedItems : [];
    const uploaded = list.filter(it => !!it?.uploadedFileId);
    // Default: select all uploaded items.
    setSelectedKeys(new Set(uploaded.map(it => it.key).filter(Boolean)));
  }, [embedded, uploadedItems]);

  const platformKey = (label) => {
    const v = String(label || '').trim().toLowerCase();
    if (v === 'instagram') return 'instagram';
    if (v === 'facebook') return 'facebook';
    if (v === 'youtube') return 'youtube';
    if (v === 'linkedin') return 'linkedin';
    if (v === 'twitter') return 'twitter';
    if (v === 'tiktok') return 'tiktok';
    return v;
  };

  const accountsForPlatform = (key) => {
    const k = String(key || '').toLowerCase();
    return (accounts || []).filter(a => String(a?.platform || '').toLowerCase() === k);
  };

  const ensureDefaultAccountSelection = (platformLabel, nextPlatforms, prevAccountsMap) => {
    const key = platformKey(platformLabel);
    const next = { ...(prevAccountsMap || {}) };
    if (!nextPlatforms.includes(platformLabel)) {
      return next;
    }
    if (next[key]) {
      return next;
    }
    const active = activeAccounts?.[key];
    if (active) {
      next[key] = active;
      return next;
    }
    const list = accountsForPlatform(key);
    if (list.length > 0 && list[0]?.id) {
      next[key] = list[0].id;
    }
    return next;
  };

  const parsePostDate = (post) => {
    const iso = post?.scheduled_time || post?.scheduledTime;
    if (!iso) return null;
    const d = new Date(iso);
    if (!Number.isFinite(d.getTime())) return null;
    return d;
  };

  const isCancelled = (post) => String(post?.status || '').toLowerCase() === 'cancelled';

  const computeStats = () => {
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const startOfWeek = new Date(startOfToday);
    startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay());
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);

    let today = 0;
    let week = 0;
    let month = 0;
    for (const p of scheduledPosts) {
      if (isCancelled(p)) continue;
      const dt = parsePostDate(p);
      if (!dt) continue;
      if (dt >= startOfMonth) month += 1;
      if (dt >= startOfWeek) week += 1;
      if (dt >= startOfToday) today += 1;
    }

    return { today, week, month };
  };

  const togglePlatform = (platform) => {
    setNewPost(prev => {
      const isSelected = prev.platforms.includes(platform);
      const nextPlatforms = isSelected
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform];

      let nextAccounts = { ...(prev.accounts || {}) };
      if (isSelected) {
        // Keep selections; they may be reused.
        return { ...prev, platforms: nextPlatforms, accounts: nextAccounts };
      }

      nextAccounts = ensureDefaultAccountSelection(platform, nextPlatforms, nextAccounts);
      return { ...prev, platforms: nextPlatforms, accounts: nextAccounts };
    });
  };

  const setAccountSelection = (platformLabel, accountId) => {
    const key = platformKey(platformLabel);
    setNewPost(prev => ({
      ...prev,
      accounts: {
        ...(prev.accounts || {}),
        [key]: accountId
      }
    }));
  };

  const toggleSelectedKey = (key) => {
    if (!key) return;
    setSelectedKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const setAllSelected = (on) => {
    const list = Array.isArray(uploadedItems) ? uploadedItems : [];
    const uploaded = list.filter(it => !!it?.uploadedFileId);
    setSelectedKeys(on ? new Set(uploaded.map(it => it.key).filter(Boolean)) : new Set());
  };

  const openEdit = (post) => {
    setEditing(post);
    setEditForm({
      title: post?.title || '',
      caption: post?.caption || '',
      platforms: Array.isArray(post?.platforms) ? post.platforms : [],
      scheduledTime: post?.scheduled_time || post?.scheduledTime || ''
    });
  };

  const toggleEditPlatform = (platform) => {
    setEditForm(prev => ({
      ...prev,
      platforms: prev.platforms.includes(platform)
        ? prev.platforms.filter(p => p !== platform)
        : [...prev.platforms, platform]
    }));
  };

  const saveEdit = async () => {
    if (!editing?.id) return;
    if (!editForm.title || (editForm.platforms || []).length === 0 || !editForm.scheduledTime) {
      alert('Please fill all required fields');
      return;
    }

    try {
      await updateScheduledPost(editing.id, {
        title: editForm.title,
        caption: editForm.caption,
        platforms: editForm.platforms,
        scheduled_time: editForm.scheduledTime
      });
      setScheduledPosts(prev => prev.map(p => (p.id === editing.id ? {
        ...p,
        title: editForm.title,
        caption: editForm.caption,
        platforms: editForm.platforms,
        scheduled_time: editForm.scheduledTime,
        scheduledTime: editForm.scheduledTime
      } : p)));
      setEditing(null);
    } catch (e) {
      alert(`Update failed: ${e?.message || String(e)}`);
    }
  };

  const doCancel = async (post) => {
    if (!post?.id) return;
    const ok = confirm('Cancel this scheduled post?');
    if (!ok) return;

    try {
      await cancelScheduledPost(post.id);
      setScheduledPosts(prev => prev.map(p => (p.id === post.id ? { ...p, status: 'cancelled' } : p)));
    } catch (e) {
      alert(`Cancel failed: ${e?.message || String(e)}`);
    }
  };

  const parseCsvRows = async (file) => {
    const text = await file.text();
    const lines = text.split(/\r?\n/).filter(Boolean);
    if (lines.length === 0) return [];

    const parseLine = (line) => {
      const out = [];
      let cur = '';
      let inQuotes = false;
      for (let i = 0; i < line.length; i += 1) {
        const ch = line[i];
        if (ch === '"') {
          if (inQuotes && line[i + 1] === '"') {
            cur += '"';
            i += 1;
          } else {
            inQuotes = !inQuotes;
          }
        } else if (ch === ',' && !inQuotes) {
          out.push(cur);
          cur = '';
        } else {
          cur += ch;
        }
      }
      out.push(cur);
      return out.map(s => s.trim());
    };

    const header = parseLine(lines[0]).map(h => h.toLowerCase());
    const idx = (name) => header.indexOf(name);
    const iTitle = idx('title');
    const iCaption = idx('caption');
    const iPlatforms = idx('platforms');
    const iTime = idx('scheduled_time');
    const iFileId = idx('file_id');

    if (iTitle === -1 || iPlatforms === -1) {
      throw new Error('CSV must include headers: title, platforms (caption, file_id, scheduled_time optional)');
    }

    const rows = [];
    for (let i = 1; i < lines.length; i += 1) {
      const cols = parseLine(lines[i]);
      const title = cols[iTitle] || '';
      const caption = iCaption >= 0 ? (cols[iCaption] || '') : '';
      const platformsRaw = cols[iPlatforms] || '';
      const scheduledTime = iTime >= 0 ? (cols[iTime] || '') : '';
      const fileId = iFileId >= 0 ? (cols[iFileId] || '') : '';
      const platforms = platformsRaw
        .split(/[;|]/)
        .map(s => s.trim())
        .filter(Boolean);

      if (!title || platforms.length === 0) continue;
      rows.push({ title, caption, platforms, scheduledTime, file_id: fileId || null });
    }
    return rows;
  };

  const importCsvAndSchedule = async (file) => {
    if (!file) return;
    setBulkBusy(true);
    try {
      const rows = await parseCsvRows(file);
      if (rows.length === 0) {
        alert('No valid rows found in CSV');
        return;
      }

      // If any row omits scheduled_time, treat it as smart scheduling.
      const smart = rows.some(r => !String(r.scheduledTime || '').trim() || String(r.scheduledTime || '').trim().toUpperCase() === 'SMART');

      const resp = await apiFetch('/api/schedule/bulk', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          smart,
          interval_minutes: intervalMinutes,
          items: rows.map(r => ({
            platforms: r.platforms,
            title: r.title,
            caption: r.caption,
            file_id: r.file_id || null,
            scheduledTime: r.scheduledTime || null
          }))
        })
      });
      const data = await resp.json().catch(() => null);
      if (!resp.ok) {
        throw new Error((data && (data.detail || data.error)) || 'Bulk schedule failed');
      }

      const newItems = Array.isArray(data?.scheduled_posts) ? data.scheduled_posts : [];
      if (newItems.length > 0) {
        setScheduledPosts(prev => [...newItems, ...prev]);
      }
      alert(`Imported ${newItems.length} scheduled post(s).`);
    } catch (e) {
      alert(`CSV import failed: ${e?.message || String(e)}`);
    } finally {
      setBulkBusy(false);
    }
  };

  const handleSchedule = async () => {
    const effectiveTitle = (embedded ? (defaultTitle || newPost.title) : newPost.title) || '';
    const effectiveCaption = (embedded ? (defaultCaption || newPost.caption) : newPost.caption) || '';

    if (!effectiveTitle || newPost.platforms.length === 0 || (!smartSchedule && !newPost.scheduledTime)) {
      alert('Please fill all required fields');
      return;
    }

    // Embedded mode can schedule multiple uploaded items.
    const list = Array.isArray(uploadedItems) ? uploadedItems : [];
    const selected = embedded
      ? list.filter(it => selectedKeys.has(it?.key))
      : [];

    if (embedded) {
      if (selected.length === 0) {
        alert('Select at least one uploaded video to schedule.');
        return;
      }
      if (!smartSchedule && selected.length > 1) {
        alert('Enable Smart schedule to schedule multiple videos with an interval.');
        return;
      }
    } else {
      // Non-embedded: single schedule
      if (!uploadedFileId) {
        alert('Upload a video above first (then schedule it here).');
        return;
      }
    }

    const selectedAccounts = newPost.accounts && typeof newPost.accounts === 'object' ? newPost.accounts : {};

    const waitForUploadedFileId = async (itemKey, timeoutMs = 30 * 60 * 1000) => {
      const started = Date.now();
      // Poll until UploadZone updates uploadedItems with an uploadedFileId.
      while (Date.now() - started < timeoutMs) {
        const cur = uploadedItemsRef.current || [];
        const it = cur.find(x => x?.key === itemKey);
        const status = String(it?.status || 'pending').toLowerCase();
        if (it?.uploadedFileId) return it.uploadedFileId;
        if (status === 'error') {
          throw new Error(it?.error || 'Upload failed');
        }
        await new Promise(r => setTimeout(r, 250));
      }
      throw new Error('Timed out waiting for upload to finish');
    };

    // Multi-schedule (embedded): do sequential requests so we can show live progress.
    if (embedded) {
      setScheduleBusy(true);
      const initialQueue = selected.map(it => ({
        key: it.key,
        title: it.title || effectiveTitle || 'Untitled',
        filename: it.filename || '',
        status: it?.uploadedFileId ? 'pending' : 'uploading',
        error: null,
        remotePct: 0,
        remoteMsg: '',
        scheduledAt: ''
      }));
      setQueue(initialQueue);

      try {
        for (const it of selected) {
          // If not uploaded yet, wait while showing live percent in the queue.
          let fileId = it?.uploadedFileId || null;
          if (!fileId) {
            setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'uploading', error: null } : q)));
            try {
              fileId = await waitForUploadedFileId(it.key);
            } catch (e) {
              setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'failed', error: e?.message || String(e) } : q)));
              continue;
            }
          }

          setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'scheduling', error: null } : q)));
          try {
            const clientRequestId = `client_${Date.now()}_${Math.random().toString(16).slice(2, 10)}`;

            let stopped = false;
            const poll = async () => {
              while (!stopped) {
                try {
                  const pr = await getScheduleProgress(clientRequestId);
                  const p = pr?.progress || null;
                  const pct = Math.max(0, Math.min(100, Number(p?.percent || 0)));
                  const msg = String(p?.message || '').trim();
                  if (pct > 0 || msg) {
                    setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, remotePct: pct, remoteMsg: msg } : q)));
                  }
                  if (p?.done) return;
                } catch {
                  // 404 while progress hasn't started yet is normal.
                }
                await new Promise(r => setTimeout(r, 500));
              }
            };

            const schedulePromise = schedulePost({
              platforms: newPost.platforms,
              content: {
                title: it.title || effectiveTitle,
                caption: resolveFinalCaption(it, effectiveCaption)
              },
              scheduledTime: smartSchedule ? '' : newPost.scheduledTime,
              interval_minutes: smartSchedule ? intervalMinutes : undefined,
              file_id: fileId,
              clips: [],
              accounts: selectedAccounts,
              client_request_id: clientRequestId
            });

            // Poll progress concurrently while the schedule request is in-flight.
            await Promise.race([
              (async () => { await schedulePromise; })(),
              (async () => { await poll(); })()
            ]);

            const result = await schedulePromise;
            stopped = true;
            setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, remotePct: 0, remoteMsg: '' } : q)));

            const ok = result?.success ?? result?.ok ?? !!result?.schedule_id;
            if (ok) {
              const newItems = Array.isArray(result?.scheduled_posts) ? result.scheduled_posts : [];
              if (newItems.length > 0) {
                setScheduledPosts(prev => [...newItems, ...prev]);
              }
              const scheduledAt = String(newItems?.[0]?.scheduled_time || '').trim();
              setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'scheduled', scheduledAt: scheduledAt || q.scheduledAt || '' } : q)));
            } else {
              setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'failed', error: result?.error || 'Unknown error' } : q)));
            }
          } catch (e) {
            setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'failed', error: e?.message || String(e) } : q)));
          }
        }
      } finally {
        setScheduleBusy(false);
      }
      return;
    }

    // Single schedule
    try {
      const result = await schedulePost({
        platforms: newPost.platforms,
        content: {
          title: effectiveTitle,
          caption: effectiveCaption
        },
        scheduledTime: smartSchedule ? '' : newPost.scheduledTime,
        interval_minutes: smartSchedule ? intervalMinutes : undefined,
        file_id: uploadedFileId,
        clips: newPost.clips,
        accounts: selectedAccounts
      });

      const ok = result?.success ?? result?.ok ?? !!result?.schedule_id;
      if (ok) {
        alert('Post scheduled successfully!');
        const newItems = Array.isArray(result?.scheduled_posts) ? result.scheduled_posts : [];
        if (newItems.length > 0) {
          setScheduledPosts(prev => [...newItems, ...prev]);
        }
        setNewPost(prev => ({
          ...prev,
          platforms: [],
          scheduledTime: '',
          clips: [],
          accounts: prev.accounts || {}
        }));
      } else {
        alert(`Scheduling failed: ${result?.error || 'Unknown error'}`);
      }
    } catch (error) {
      alert(`Scheduling failed: ${error?.message || String(error)}`);
    }
  };

  const handleInstantPost = async () => {
    if (scheduleBusy) return;
    if (!newPost.platforms || newPost.platforms.length === 0) {
      alert('Select at least one platform.');
      return;
    }

    const effectiveTitle = String(newPost.title || defaultTitle || '').trim();
    const effectiveCaption = String(newPost.caption || defaultCaption || '').trim();
    const selectedAccounts = newPost.accounts && typeof newPost.accounts === 'object' ? newPost.accounts : {};

    const waitForUploadedFileId = async (itemKey, timeoutMs = 30 * 60 * 1000) => {
      const started = Date.now();
      while (Date.now() - started < timeoutMs) {
        const cur = uploadedItemsRef.current || [];
        const it = cur.find(x => x?.key === itemKey);
        const status = String(it?.status || 'pending').toLowerCase();
        if (it?.uploadedFileId) return it.uploadedFileId;
        if (status === 'error') {
          throw new Error(it?.error || 'Upload failed');
        }
        await new Promise(r => setTimeout(r, 250));
      }
      throw new Error('Timed out waiting for upload to finish');
    };

    if (embedded) {
      const list = Array.isArray(uploadedItems) ? uploadedItems : [];
      const selected = list.filter(it => it?.key && selectedKeys.has(it.key));
      if (selected.length === 0) {
        alert('Select at least one video.');
        return;
      }

      setQueueMode('instant');
      setScheduleBusy(true);
      const initialQueue = selected.map(it => ({
        key: it.key,
        title: it.title || effectiveTitle || 'Untitled',
        filename: it.filename || '',
        status: it?.uploadedFileId ? 'pending' : 'uploading',
        error: null,
        remotePct: 0,
        remoteMsg: '',
        scheduledAt: ''
      }));
      setQueue(initialQueue);

      try {
        for (const it of selected) {
          let fileId = it?.uploadedFileId || null;
          if (!fileId) {
            setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'uploading', error: null } : q)));
            try {
              fileId = await waitForUploadedFileId(it.key);
            } catch (e) {
              setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'failed', error: e?.message || String(e) } : q)));
              continue;
            }
          }

          setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'posting', error: null } : q)));
          try {
            const clientRequestId = `client_${Date.now()}_${Math.random().toString(16).slice(2, 10)}`;
            let stopped = false;

            const poll = async () => {
              while (!stopped) {
                try {
                  const pr = await getScheduleProgress(clientRequestId);
                  const p = pr?.progress || null;
                  const pct = Math.max(0, Math.min(100, Number(p?.percent || 0)));
                  const msg = String(p?.message || '').trim();
                  if (pct > 0 || msg) {
                    setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, remotePct: pct, remoteMsg: msg } : q)));
                  }
                  if (p?.done) return;
                } catch {
                  // 404 while progress hasn't started yet is normal.
                }
                await new Promise(r => setTimeout(r, 500));
              }
            };

            const publishPromise = publishInstant({
              platforms: newPost.platforms,
              content: {
                title: it.title || effectiveTitle,
                caption: resolveFinalCaption(it, effectiveCaption)
              },
              file_id: fileId,
              clips: [],
              accounts: selectedAccounts,
              client_request_id: clientRequestId
            });

            await Promise.race([
              (async () => { await publishPromise; })(),
              (async () => { await poll(); })()
            ]);

            const result = await publishPromise;
            stopped = true;
            setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, remotePct: 0, remoteMsg: '' } : q)));

            const ok = result?.success ?? result?.ok ?? !!result?.results;
            if (ok) {
              setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'posted' } : q)));
            } else {
              setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'failed', error: result?.error || 'Unknown error' } : q)));
            }
          } catch (e) {
            setQueue(prev => prev.map(q => (q.key === it.key ? { ...q, status: 'failed', error: e?.message || String(e) } : q)));
          }
        }
      } finally {
        setScheduleBusy(false);
      }
      return;
    }

    // Non-embedded: instant post single uploaded file
    if (!uploadedFileId) {
      alert('Upload a video above first (then post it here).');
      return;
    }
    try {
      setQueueMode('instant');
      setScheduleBusy(true);
      const clientRequestId = `client_${Date.now()}_${Math.random().toString(16).slice(2, 10)}`;
      await publishInstant({
        platforms: newPost.platforms,
        content: { title: effectiveTitle, caption: effectiveCaption },
        file_id: uploadedFileId,
        clips: newPost.clips,
        accounts: selectedAccounts,
        client_request_id: clientRequestId
      });
      alert('Posted successfully!');
    } catch (e) {
      alert(`Instant post failed: ${e?.message || String(e)}`);
    } finally {
      setScheduleBusy(false);
    }
  };

  const PostCard = ({ post, index }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
      whileHover={{ scale: 1.02 }}
      className="card-cyber p-4 flex items-center gap-4"
    >
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyber-primary to-cyber-purple flex items-center justify-center cyber-glow">
        <Clock className="w-6 h-6" />
      </div>

      <div className="flex-1">
        <div className="font-semibold mb-1">{post.title}</div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">{post.time}</span>
          <div className="flex items-center gap-1">
            {post.platforms.map(platform => {
              const PlatformIcon = platformIcons[platform]?.icon || Send;
              return (
                <div key={platform} className="w-6 h-6 rounded bg-white/10 flex items-center justify-center">
                  <PlatformIcon className="w-4 h-4" />
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${isCancelled(post)
          ? 'bg-red-500/15 text-red-300'
          : 'bg-cyber-green/20 text-cyber-green'
        }`}>
          {post.status}
        </span>
        <button onClick={() => openEdit(post)} className="p-2 rounded-lg hover:bg-white/10" title="Edit">
          <Edit className="w-4 h-4" />
        </button>
        <button onClick={() => doCancel(post)} className="p-2 rounded-lg hover:bg-white/10" title="Cancel">
          <Trash2 className="w-4 h-4 text-red-400" />
        </button>
      </div>
    </motion.div>
  );

  const stats = computeStats();

  return (
    <div className="space-y-6">
      {/* Header */}
      {!embedded && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h1 className={`text-4xl font-black mb-2 ${isDark ? 'gradient-text' : 'text-gray-900'}`}>Scheduler Pro</h1>
          <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>Plan and automate your content across all platforms</p>
        </motion.div>
      )}

      {/* Create New Post */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-6 rounded-xl border transition-colors ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}
      >
        <h3 className={`text-xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Plus className="w-5 h-5 text-cyan-500" />
          {embedded ? 'Schedule This Video' : 'Schedule New Post'}
        </h3>

        {embedded && (
          <div className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {uploadedFileId ? 'Using the uploaded video from Video Lab.' : 'Upload a video above to enable scheduling.'}
          </div>
        )}

        <div className="space-y-4">
          {/* Title + Caption are authored in Video Lab when embedded */}
          {!embedded && (
            <>
              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Post Title *</label>
                <input
                  type="text"
                  value={newPost.title}
                  onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                  placeholder="Enter post title..."
                  className={`w-full px-4 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
                />
              </div>

              <div>
                <label className={`block text-sm font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Caption</label>
                <textarea
                  value={newPost.caption}
                  onChange={(e) => setNewPost({ ...newPost, caption: e.target.value })}
                  placeholder="Write your caption..."
                  rows={4}
                  className={`w-full px-4 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
                />
              </div>
            </>
          )}

          {/* Platform Selection */}
          <div>
            <label className={`block text-sm font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Select Platforms *</label>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {Object.entries(platformIcons).map(([platform, { icon: Icon, color }]) => {
                const isSelected = newPost.platforms.includes(platform);
                return (
                  <motion.button
                    key={platform}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => togglePlatform(platform)}
                    className={`p-4 rounded-xl border-2 transition-all relative ${
                      isSelected
                        ? 'border-cyan-500 bg-cyan-500/10'
                        : isDark ? 'border-white/10 bg-white/5 hover:border-white/30' : 'border-gray-200 bg-gray-50 hover:border-gray-400'
                    }`}
                  >
                    <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-2`}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                    <div className={`text-xs font-semibold ${isDark ? 'text-white' : 'text-gray-700'}`}>{platform}</div>
                    {isSelected && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center"
                      >
                        <CheckCircle className="w-4 h-4 text-white" />
                      </motion.div>
                    )}
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* Account Selection */}
          {newPost.platforms.length > 0 && (
            <div>
              <label className={`block text-sm font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Post To (Connected Accounts)</label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {['Instagram', 'Facebook', 'YouTube'].filter(p => newPost.platforms.includes(p)).map((p) => {
                  const key = platformKey(p);
                  const list = accountsForPlatform(key);
                  const selectedId = (newPost.accounts || {})[key] || '';

                  return (
                    <div key={p}>
                      <label className={`block text-xs mb-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{p}</label>
                      {list.length === 0 ? (
                        <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>No connected {p} account found.</div>
                      ) : (
                        <select
                          value={selectedId || ''}
                          onChange={(e) => setAccountSelection(p, e.target.value)}
                          className={`w-full px-4 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
                        >
                          {list.map((a) => {
                            const label = a?.name || a?.username || a?.id;
                            return (
                              <option key={a.id} value={a.id}>
                                {label}
                              </option>
                            );
                          })}
                        </select>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Date & Time */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={`block text-sm font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Date *</label>
              <input
                type="date"
                value={newPost.scheduledTime.split('T')[0] || ''}
                onChange={(e) => setNewPost({ ...newPost, scheduledTime: e.target.value + 'T' + (newPost.scheduledTime.split('T')[1] || '12:00') })}
                className={`w-full px-4 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
                disabled={smartSchedule}
              />
            </div>
            <div>
              <label className={`block text-sm font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Time *</label>
              <input
                type="time"
                value={newPost.scheduledTime.split('T')[1] || ''}
                onChange={(e) => setNewPost({ ...newPost, scheduledTime: (newPost.scheduledTime.split('T')[0] || new Date().toISOString().split('T')[0]) + 'T' + e.target.value })}
                className={`w-full px-4 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
                disabled={smartSchedule}
              />
            </div>
          </div>

          {/* Smart Scheduling */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center gap-3">
              <input
                id="smartSchedule"
                type="checkbox"
                checked={smartSchedule}
                onChange={(e) => setSmartSchedule(!!e.target.checked)}
              />
              <label htmlFor="smartSchedule" className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Smart schedule (auto-pick next slot)</label>
            </div>
            <div>
              <label className={`block text-sm font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Interval (minutes)</label>
              <input
                type="number"
                min={1}
                max={1440}
                value={intervalMinutes}
                onChange={(e) => setIntervalMinutes(Number(e.target.value || 60))}
                className={`w-full px-4 py-2 rounded-lg border transition-colors ${isDark ? 'bg-gray-800 border-gray-700 text-white' : 'bg-gray-50 border-gray-300 text-gray-900'}`}
                disabled={!smartSchedule}
              />
            </div>
          </div>

          {/* Uploaded Media */}
          <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {uploadedFileId ? (
              <span>Using uploaded video from the Upload section.</span>
            ) : (
              <span>Upload a video above to enable scheduling.</span>
            )}
          </div>

          {/* Embedded multi-video selection */}
          {embedded && (
            <div className={`p-4 rounded-2xl border backdrop-blur-md ${isDark ? 'bg-gray-900/80 border-cyan-500/20' : 'bg-white border-gray-200 shadow-lg'}`}>
              <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
                <div className={`text-sm font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Videos to schedule</div>
                <div className={`flex items-center gap-3 text-xs ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                  <button type="button" className="hover:underline" onClick={() => setAllSelected(true)}>
                    Select all
                  </button>
                  <button type="button" className="hover:underline" onClick={() => setAllSelected(false)}>
                    Clear
                  </button>
                  <div className="text-gray-400">Selected: {selectedKeys.size}</div>
                </div>
              </div>

              <div className="space-y-2 max-h-56 overflow-auto">
                {(Array.isArray(uploadedItems) ? uploadedItems : []).map((it) => {
                  const checked = selectedKeys.has(it?.key);
                  const savedOverride = (captionOverrides && it?.key ? captionOverrides[it.key] : '') || '';
                  const baseLabel = it?.filename || it?.title || 'Video';
                  const fullLabel = normalizeSpaces(savedOverride) ? normalizeSpaces(savedOverride) : baseLabel;
                  const label = truncateLabel(fullLabel);
                  const uploaded = !!it?.uploadedFileId;
                  const status = String(it?.status || 'pending').toLowerCase();
                  const pct = Math.max(0, Math.min(100, Number(it?.progress || 0)));

                  const statusText = uploaded
                    ? 'Uploaded'
                    : status === 'uploading'
                      ? `Uploading ${Math.max(1, pct)}%`
                      : status === 'error'
                        ? 'Upload failed'
                        : 'Pending upload';
                  const isEditing = editingCaptionKey && editingCaptionKey === it?.key;
                  const draftValue = (captionDrafts && it?.key ? captionDrafts[it.key] : '') ?? '';

                  return (
                    <div key={it?.key} className={`p-2 rounded-lg border ${isDark ? 'bg-white/5 border-white/10' : 'bg-gray-50 border-gray-200'}`}>
                      <div className="flex items-center gap-3">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleSelectedKey(it?.key)}
                          disabled={scheduleBusy}
                        />

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2 min-w-0">
                            <div className="text-sm truncate min-w-0 flex-1" title={fullLabel}>{label}</div>
                            <button
                              type="button"
                              className={`p-1 rounded flex-shrink-0 ${isDark ? 'bg-white/5 hover:bg-white/10' : 'bg-gray-100 hover:bg-gray-200'}`}
                              onClick={() => {
                                if (!it?.key) return;
                                setEditingCaptionKey(prev => {
                                  const next = prev === it.key ? null : it.key;
                                  return next;
                                });
                                setCaptionDrafts(prev => {
                                  const next = { ...(prev || {}) };
                                  if (next[it.key] == null) {
                                    next[it.key] = savedOverride;
                                  }
                                  return next;
                                });
                              }}
                              disabled={scheduleBusy || !it?.key}
                              title="Edit caption text"
                            >
                              <Edit className="w-4 h-4" />
                            </button>

                            <button
                              type="button"
                              className={`p-1 rounded flex-shrink-0 ${isDark ? 'bg-white/5 hover:bg-white/10' : 'bg-gray-100 hover:bg-gray-200'}`}
                              onClick={async () => {
                                if (!it?.key) return;
                                if (scheduleBusy) return;
                                try {
                                  // Immediately update local UI state.
                                  setSelectedKeys(prev => {
                                    const next = new Set(prev);
                                    next.delete(it.key);
                                    return next;
                                  });
                                  setCaptionOverrides(prev => {
                                    const next = { ...(prev || {}) };
                                    delete next[it.key];
                                    return next;
                                  });
                                  setCaptionDrafts(prev => {
                                    const next = { ...(prev || {}) };
                                    delete next[it.key];
                                    return next;
                                  });
                                  if (editingCaptionKey === it.key) {
                                    setEditingCaptionKey(null);
                                  }

                                  if (typeof onRemoveUploadedItem === 'function') {
                                    await onRemoveUploadedItem(it);
                                  }
                                } catch (e) {
                                  console.error('Failed to remove item:', e);
                                }
                              }}
                              disabled={scheduleBusy || !it?.key}
                              title="Remove file"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                          <div className={`text-xs truncate ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{statusText}</div>
                        </div>

                        {isEditing ? (
                          <button
                            type="button"
                            className={`px-3 py-1 rounded-lg text-xs flex-shrink-0 ${isDark ? 'bg-white/10 hover:bg-white/15' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
                            onClick={() => {
                              if (!it?.key) return;
                              const v = String(draftValue || '');
                              setCaptionOverrides(prev => ({
                                ...(prev || {}),
                                [it.key]: v
                              }));
                              setEditingCaptionKey(null);
                            }}
                            disabled={scheduleBusy || !it?.key}
                            title="Apply changes"
                          >
                            Done
                          </button>
                        ) : (
                          <div className="w-14 flex-shrink-0" />
                        )}
                      </div>

                      {isEditing && (
                        <div className="mt-2">
                          <textarea
                            rows={3}
                            className={`w-full px-4 py-3 rounded-xl border transition-colors ${isDark ? 'bg-white/5 border-white/10 text-white placeholder-gray-400' : 'bg-gray-50 border-gray-300 text-gray-900 placeholder-gray-500'}`}
                            value={draftValue}
                            onChange={(e) => {
                              const v = e.target.value;
                              setCaptionDrafts(prev => ({ ...(prev || {}), [it.key]: v }));
                            }}
                            placeholder="Type the full caption (this replaces the default caption)…"
                          />
                          <div className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                            Will post: <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>{normalizeSpaces(draftValue) ? normalizeSpaces(draftValue) : String(it?.caption || '').trim()}</span>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-4 pt-4">
            <button
              onClick={handleInstantPost}
              disabled={scheduleBusy || (embedded ? selectedKeys.size === 0 : !uploadedFileId)}
              className={`px-6 py-3 rounded-xl transition-colors flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed ${isDark ? 'bg-white/5 hover:bg-white/10 text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}
              title="Post immediately"
            >
              <Send className="w-5 h-5" />
              Instant Post
            </button>
            <button
              onClick={handleSchedule}
              disabled={scheduleBusy || (embedded ? selectedKeys.size === 0 : !uploadedFileId)}
              className="btn-cyber flex-1 py-3 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Calendar className="w-5 h-5" />
              {scheduleBusy ? 'Scheduling…' : (embedded && selectedKeys.size > 1 ? `Schedule ${selectedKeys.size} Posts` : 'Schedule Post')}
            </button>
            {!embedded && (
              <button className="px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                Save Draft
              </button>
            )}
          </div>

          {/* Live scheduling progress */}
          {embedded && queue.length > 0 && (
            <div className="card-cyber p-4 mt-4">
              <div className="text-sm font-semibold mb-3">{queueMode === 'instant' ? 'Posting progress' : 'Scheduling progress'}</div>
              <div className="space-y-2">
                {queue.map((q) => {
                  const it = (Array.isArray(uploadedItems) ? uploadedItems : []).find(x => x?.key === q.key);
                  const pct = Math.max(0, Math.min(100, Number(it?.progress || 0)));
                  const itemStatus = String(it?.status || '').toLowerCase();
                  const isUploaded = !!it?.uploadedFileId;
                  const isUploading = !isUploaded && (q.status === 'uploading' || itemStatus === 'uploading' || pct > 0);
                  const pctLabel = `${Math.max(1, pct)}%`;

                  const remotePct = Math.max(0, Math.min(100, Number(q.remotePct || 0)));
                  const remoteMsgRaw = String(q.remoteMsg || '').trim();
                  const remoteMsg = remoteMsgRaw.replace(/\b\d{1,3}%\b/g, '').replace(/\s+/g, ' ').trim();

                  const statusLabel = isUploading
                    ? 'Uploading'
                    : q.status === 'pending'
                      ? 'Pending'
                      : q.status === 'scheduling'
                        ? 'Scheduling…'
                        : q.status === 'posting'
                          ? 'Posting…'
                        : q.status === 'scheduled'
                          ? 'Scheduled'
                          : q.status === 'posted'
                            ? 'Posted'
                          : 'Failed';

                  const scheduledAt = String(q.scheduledAt || '').trim();
                  let scheduledSuffix = '';
                  if (q.status === 'scheduled' && scheduledAt) {
                    // Keep it compact; show the HH:MM part when possible.
                    const mm = scheduledAt.match(/T(\d{2}:\d{2})/);
                    scheduledSuffix = mm ? ` • ${mm[1]}` : ` • ${scheduledAt}`;
                  }

                  // Only show a percent when we're actively waiting for the browser->app upload.
                  let rightLabel = isUploading ? `${pctLabel} • ${statusLabel}` : `${statusLabel}${scheduledSuffix}`;
                  if (!isUploading && (q.status === 'scheduling' || q.status === 'posting') && (remotePct > 0 || remoteMsg)) {
                    rightLabel = remotePct > 0
                      ? `${remotePct}% • ${remoteMsg || 'Uploading to Facebook…'}`
                      : (remoteMsg || 'Uploading to Facebook…');
                  }

                  return (
                  <div key={q.key} className="flex items-center justify-between gap-3 p-2 rounded-lg bg-white/5 border border-white/10">
                    <div className="min-w-0 flex-1">
                      <div className="text-sm truncate" title={q.filename || q.title}>{truncateLabel(q.filename || q.title)}</div>
                      {q.error && <div className="text-xs text-red-400 truncate">{q.error}</div>}
                    </div>
                    <div className="text-xs text-gray-300 flex-shrink-0 whitespace-nowrap">
                      {rightLabel}
                    </div>
                  </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </motion.div>
      {!embedded && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Posts */}
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <Clock className="w-5 h-5 text-cyber-primary" />
            Scheduled Posts ({scheduledPosts.length})
          </h3>

          {loading && (
            <div className="card-cyber p-4 text-sm text-gray-400">Loading scheduled posts…</div>
          )}

          {scheduledPosts.map((post, idx) => (
            <PostCard key={post.id} post={post} index={idx} />
          ))}

          {scheduledPosts.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="card-cyber p-12 text-center"
            >
              <Calendar className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h4 className="text-xl font-bold mb-2">No scheduled posts</h4>
              <p className="text-gray-400">Create your first scheduled post above</p>
            </motion.div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="space-y-4">
          <h3 className="text-xl font-bold">Quick Stats</h3>

          {[
            { label: 'Posts Today', value: String(stats.today), icon: Calendar, color: 'from-cyber-primary to-blue-600' },
            { label: 'This Week', value: String(stats.week), icon: Clock, color: 'from-cyber-purple to-purple-600' },
            { label: 'This Month', value: String(stats.month), icon: Send, color: 'from-cyber-green to-green-600' }
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ scale: 1.05 }}
              className="card-cyber p-6 relative overflow-hidden"
            >
              <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} opacity-5`} />
              <div className="relative z-10">
                <div className="flex items-center justify-between mb-3">
                  <stat.icon className="w-8 h-8 text-gray-400" />
                </div>
                <div className="text-3xl font-black mb-1 gradient-text">{stat.value}</div>
                <div className="text-sm text-gray-400">{stat.label}</div>
              </div>
            </motion.div>
          ))}

          <motion.div
            whileHover={{ scale: 1.05 }}
            className="card-cyber p-6 bg-gradient-to-br from-cyber-primary/10 to-cyber-purple/10 border-cyber-primary"
          >
            <h4 className="font-bold mb-2 flex items-center gap-2">
              <Copy className="w-5 h-5 text-cyber-primary" />
              Bulk Schedule
            </h4>
            <p className="text-sm text-gray-400 mb-4">
              Schedule multiple posts at once with our CSV import feature
            </p>
            <label className={`btn-cyber w-full py-2 text-center ${bulkBusy ? 'opacity-60 pointer-events-none' : ''}`}>
              {bulkBusy ? 'Importing…' : 'Import CSV'}
              <input
                type="file"
                accept=".csv,text/csv"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files && e.target.files[0];
                  e.target.value = '';
                  importCsvAndSchedule(f);
                }}
              />
            </label>
          </motion.div>
        </div>
        </div>
      )}

      {/* Edit Modal */}
      {editing && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-black/70" onClick={() => setEditing(null)} />
          <div className="relative card-cyber p-6 w-full max-w-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold">Edit Scheduled Post</h3>
              <button className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10" onClick={() => setEditing(null)}>
                Close
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2">Post Title *</label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                  className="input-cyber w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-2">Caption</label>
                <textarea
                  value={editForm.caption}
                  onChange={(e) => setEditForm({ ...editForm, caption: e.target.value })}
                  rows={4}
                  className="input-cyber w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold mb-3">Select Platforms *</label>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {Object.entries(platformIcons).map(([platform, { icon: Icon, color }]) => {
                    const isSelected = editForm.platforms.includes(platform);
                    return (
                      <motion.button
                        key={platform}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => toggleEditPlatform(platform)}
                        className={`p-4 rounded-xl border-2 transition-all relative ${
                          isSelected
                            ? 'border-cyber-primary bg-cyber-primary/10'
                            : 'border-white/10 bg-white/5 hover:border-white/30'
                        }`}
                      >
                        <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-2`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="text-xs font-semibold">{platform}</div>
                        {isSelected && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="absolute -top-2 -right-2 w-6 h-6 bg-cyber-green rounded-full flex items-center justify-center"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </motion.div>
                        )}
                      </motion.button>
                    );
                  })}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold mb-2">Date *</label>
                  <input
                    type="date"
                    value={editForm.scheduledTime.split('T')[0] || ''}
                    onChange={(e) => setEditForm({ ...editForm, scheduledTime: e.target.value + 'T' + (editForm.scheduledTime.split('T')[1] || '12:00') })}
                    className="input-cyber w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold mb-2">Time *</label>
                  <input
                    type="time"
                    value={editForm.scheduledTime.split('T')[1] || ''}
                    onChange={(e) => setEditForm({ ...editForm, scheduledTime: (editForm.scheduledTime.split('T')[0] || new Date().toISOString().split('T')[0]) + 'T' + e.target.value })}
                    className="input-cyber w-full"
                  />
                </div>
              </div>

              <div className="flex gap-4 pt-2">
                <button onClick={saveEdit} className="btn-cyber flex-1 py-3">Save Changes</button>
                <button onClick={() => setEditing(null)} className="px-6 py-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">Cancel</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchedulerPro;
