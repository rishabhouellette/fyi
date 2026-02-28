const API_BASE = (import.meta && import.meta.env && import.meta.env.VITE_API_BASE_URL)
  ? String(import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '')
  : '';

// API token injected by the server into index.html
const API_TOKEN = (typeof window !== 'undefined' && window.__FYI_TOKEN) || '';

function apiUrl(path) {
  const p = String(path || '');
  if (!API_BASE) return p;
  // If the caller passed an absolute URL, leave it.
  if (/^https?:\/\//i.test(p)) return p;
  if (!p) return API_BASE;
  if (p.startsWith('/')) return `${API_BASE}${p}`;
  return `${API_BASE}/${p}`;
}

function _authHeaders(extra = {}) {
  const h = { 'Content-Type': 'application/json', ...extra };
  if (API_TOKEN) h['Authorization'] = `Bearer ${API_TOKEN}`;
  return h;
}

/**
 * Drop-in replacement for bare fetch() that injects the auth token.
 * Usage: `apiFetch('/api/accounts')` or `apiFetch('/api/foo', { method: 'POST', ... })`
 */
export function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (API_TOKEN && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${API_TOKEN}`;
  }
  return fetch(apiUrl(path), { ...options, headers });
}

async function apiJson(path, options = {}) {
  const response = await fetch(apiUrl(path), {
    headers: _authHeaders(options.headers),
    ...options
  });

  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }

  if (!response.ok) {
    const message = (data && (data.detail || data.error)) || response.statusText || 'Request failed';
    throw new Error(message);
  }

  return data;
}

export async function uploadFile(file) {
  return uploadFileWithProgress(file);
}

export async function deleteUpload(fileId) {
  const id = String(fileId || '').trim();
  if (!id) throw new Error('Missing file id');
  return apiJson(`/api/uploads/${encodeURIComponent(id)}`, { method: 'DELETE' });
}

export function uploadFileWithProgress(file, onProgress) {
  const form = new FormData();
  form.append('file', file);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', apiUrl('/api/upload'));
    if (API_TOKEN) xhr.setRequestHeader('Authorization', `Bearer ${API_TOKEN}`);

    if (xhr.upload && typeof onProgress === 'function') {
      xhr.upload.onprogress = (e) => {
        if (!e) return;
        const total = e.total || 0;
        const loaded = e.loaded || 0;
        const percent = total ? Math.round((loaded / total) * 100) : 0;
        try {
          onProgress({ loaded, total, percent });
        } catch {
          // ignore progress handler errors
        }
      };
    }

    xhr.onerror = () => reject(new Error('Network error during upload'));
    xhr.onreadystatechange = () => {
      if (xhr.readyState !== 4) return;
      let data = null;
      try {
        data = xhr.responseText ? JSON.parse(xhr.responseText) : null;
      } catch {
        data = { raw: xhr.responseText };
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
        return;
      }

      const message = (data && (data.detail || data.error)) || xhr.statusText || 'Upload failed';
      reject(new Error(message));
    };

    xhr.send(form);
  });
}

export async function scoreVideo(fileId) {
  return apiJson('/api/video/score', {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId })
  });
}

export async function processVideo(fileId, targetClips = 3, quality = 'high') {
  return apiJson('/api/video/process', {
    method: 'POST',
    body: JSON.stringify({ file_id: fileId, target_clips: targetClips, quality })
  });
}

export async function createFacelessVideo({ script, width = 1080, height = 1920, fps = 30, bg_color = 'black', max_words_per_caption = 7 }) {
  return apiJson('/api/video/faceless', {
    method: 'POST',
    body: JSON.stringify({
      script,
      width,
      height,
      fps,
      bg_color,
      max_words_per_caption
    })
  });
}

export async function getGrowthReport(days = 30) {
  const qs = new URLSearchParams({ days: String(days) });
  return apiJson(`/api/growth?${qs.toString()}`);
}

export async function getAppConfig() {
  return apiJson('/api/config');
}

export async function getAccounts() {
  return apiJson('/api/accounts');
}

export async function getActiveAccounts() {
  return apiJson('/api/active-accounts');
}

export async function generateCaption({ topic, platform = 'instagram', tone = 'casual', keywords = [], max_length = 220, include_hashtags = true, hashtags_count = 8 }) {
  return apiJson('/api/ai/caption', {
    method: 'POST',
    body: JSON.stringify({
      topic,
      platform,
      tone,
      keywords,
      max_length,
      include_hashtags,
      hashtags_count
    })
  });
}

export async function generateHashtags({ topic, platform = 'instagram', count = 12, include_trending = true }) {
  return apiJson('/api/ai/hashtags', {
    method: 'POST',
    body: JSON.stringify({
      topic,
      platform,
      count,
      include_trending
    })
  });
}

export async function schedulePost(request) {
  return apiJson('/api/schedule', {
    method: 'POST',
    body: JSON.stringify(request)
  });
}

export async function getScheduleProgress(jobId) {
  if (!jobId) throw new Error('Missing jobId');
  return apiJson(`/api/schedule/progress/${encodeURIComponent(jobId)}`);
}

export async function publishInstant(request) {
  return apiJson('/api/publish/instant', {
    method: 'POST',
    body: JSON.stringify(request)
  });
}

export async function getScheduledPosts(limit = 200) {
  const qs = new URLSearchParams({ limit: String(limit) });
  return apiJson(`/api/scheduled-posts?${qs.toString()}`);
}

export async function updateScheduledPost(postId, updates) {
  if (!postId) throw new Error('Missing postId');
  return apiJson(`/api/scheduled-posts/${encodeURIComponent(postId)}`, {
    method: 'PUT',
    body: JSON.stringify(updates || {})
  });
}

export async function cancelScheduledPost(postId) {
  if (!postId) throw new Error('Missing postId');
  return apiJson(`/api/scheduled-posts/${encodeURIComponent(postId)}`, {
    method: 'DELETE'
  });
}

export async function getAnalyticsSummary(days = 30) {
  const qs = new URLSearchParams({ days: String(days) });
  return apiJson(`/api/analytics/summary?${qs.toString()}`);
}

export function downloadAnalyticsCsv(days = 30) {
  const qs = new URLSearchParams({ days: String(days) });
  window.location.href = `/api/analytics/export.csv?${qs.toString()}`;
}

// ========================================
// BYOK (Bring Your Own Key) Management
// ========================================

export async function getBYOKKeys() {
  return apiJson('/api/byok/keys');
}

export async function setBYOKKey(service, apiKey) {
  return apiJson('/api/byok/keys', {
    method: 'POST',
    body: JSON.stringify({ service, api_key: apiKey })
  });
}

export async function deleteBYOKKey(service) {
  return apiJson(`/api/byok/keys/${encodeURIComponent(service)}`, {
    method: 'DELETE'
  });
}

// ========================================
// Credits / Usage Tracking
// ========================================

export async function getUsage() {
  return apiJson('/api/usage');
}

export async function resetUsage() {
  return apiJson('/api/usage/reset', { method: 'POST' });
}

// ========================================
// AI Image Generation
// ========================================

export async function generateImage({ prompt, provider = 'dalle', size = '1024x1024', style = 'vivid', n = 1 }) {
  return apiJson('/api/ai/image', {
    method: 'POST',
    body: JSON.stringify({ prompt, provider, size, style, n })
  });
}

// ========================================
// AI Video Generation
// ========================================

export async function generateVideo({ prompt, provider = 'runway', duration = 4, aspect_ratio = '16:9' }) {
  return apiJson('/api/ai/video', {
    method: 'POST',
    body: JSON.stringify({ prompt, provider, duration, aspect_ratio })
  });
}

export async function getVideoStatus(jobId) {
  return apiJson(`/api/ai/video/status/${encodeURIComponent(jobId)}`);
}

// ========================================
// AI Voiceover / TTS
// ========================================

export async function generateVoice({ text, provider = 'elevenlabs', voice_id = 'rachel', speed = 1.0, stability = 0.5, similarity_boost = 0.75 }) {
  return apiJson('/api/ai/voice', {
    method: 'POST',
    body: JSON.stringify({ text, provider, voice_id, speed, stability, similarity_boost })
  });
}

export async function getVoices(provider = 'elevenlabs') {
  const qs = new URLSearchParams({ provider });
  return apiJson(`/api/ai/voices?${qs.toString()}`);
}

// ========================================
// Faceless Video with Voiceover
// ========================================

export async function createFacelessVideoWithVoice({ script, voice_provider = 'elevenlabs', voice_id = 'rachel', width = 1080, height = 1920, fps = 30, bg_color = 'black', max_words_per_caption = 7 }) {
  return apiJson('/api/video/faceless-with-voice', {
    method: 'POST',
    body: JSON.stringify({
      script,
      voice_provider,
      voice_id,
      width,
      height,
      fps,
      bg_color,
      max_words_per_caption
    })
  });
}

// ========================================
// Viral Templates Library
// ========================================

export async function getTemplates(category = null) {
  const qs = category ? new URLSearchParams({ category }) : '';
  return apiJson(`/api/templates${qs ? '?' + qs.toString() : ''}`);
}

export async function applyTemplate(templateId, variables = {}) {
  return apiJson('/api/templates/apply', {
    method: 'POST',
    body: JSON.stringify({ template_id: templateId, variables })
  });
}

// ========================================
// Content Ingestion (URLs, YouTube, etc.)
// ========================================

export async function ingestContent(url, extractType = 'auto') {
  return apiJson('/api/content/ingest', {
    method: 'POST',
    body: JSON.stringify({ url, extract_type: extractType })
  });
}

// ========================================
// Content Repurposing
// ========================================

export async function repurposeContent({ content, source_type = 'article', target_formats = ['tweet', 'linkedin', 'caption'], language = 'en' }) {
  return apiJson('/api/content/repurpose', {
    method: 'POST',
    body: JSON.stringify({ content, source_type, target_formats, language })
  });
}

// ========================================
// Multi-Language Support
// ========================================

export async function getSupportedLanguages() {
  return apiJson('/api/languages');
}

export async function translateText({ text, target_language, source_language = 'auto' }) {
  return apiJson('/api/ai/translate', {
    method: 'POST',
    body: JSON.stringify({ text, target_language, source_language })
  });
}

// ========================================
// Social Media Guides
// ========================================

export async function getGuides() {
  return apiJson('/api/guides');
}

export async function getGuide(platform) {
  return apiJson(`/api/guides/${encodeURIComponent(platform)}`);
}

// ========================================
// XY-AI — FYIXT Smart AI Engine
// ========================================

export async function xyaiGeneratePrompts({ goal, platform = 'instagram', content_type = 'post', tone = 'engaging', audience = '', niche = '', count = 3 }) {
  return apiJson('/api/xy-ai/prompts', {
    method: 'POST',
    body: JSON.stringify({ goal, platform, content_type, tone, audience, niche, count })
  });
}

export async function xyaiGetTrends({ niche = '', platform = 'instagram', country = 'US' } = {}) {
  return apiJson('/api/xy-ai/trends', {
    method: 'POST',
    body: JSON.stringify({ niche, platform, country })
  });
}

export async function xyaiContentPlan({ niche, platform = 'instagram', days = 7, posts_per_day = 1, tone = 'engaging' }) {
  return apiJson('/api/xy-ai/content-plan', {
    method: 'POST',
    body: JSON.stringify({ niche, platform, days, posts_per_day, tone })
  });
}

export async function xyaiListNiches() {
  return apiJson('/api/xy-ai/niches');
}

export async function xyaiChat({ message, history = [], context = '', preferred_model = 'auto' }) {
  return apiJson('/api/xy-ai/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history, context, preferred_model })
  });
}

export async function xyaiChatModels() {
  return apiJson('/api/xy-ai/chat/models');
}

export default {
  uploadFile,
  deleteUpload,
  scoreVideo,
  processVideo,
  createFacelessVideo,
  getGrowthReport,
  getAppConfig,
  getAccounts,
  getActiveAccounts,
  generateCaption,
  generateHashtags,
  schedulePost,
  getScheduleProgress,
  publishInstant,
  getScheduledPosts,
  updateScheduledPost,
  cancelScheduledPost,
  getAnalyticsSummary,
  downloadAnalyticsCsv,
  // BYOK
  getBYOKKeys,
  setBYOKKey,
  deleteBYOKKey,
  // Usage
  getUsage,
  resetUsage,
  // AI Image
  generateImage,
  // AI Video
  generateVideo,
  getVideoStatus,
  // AI Voice
  generateVoice,
  getVoices,
  // Faceless with voice
  createFacelessVideoWithVoice,
  // Templates
  getTemplates,
  applyTemplate,
  // Content
  ingestContent,
  repurposeContent,
  // Languages
  getSupportedLanguages,
  translateText,
  // Guides
  getGuides,
  getGuide,
  // XY-AI
  xyaiGeneratePrompts,
  xyaiGetTrends,
  xyaiContentPlan,
  xyaiListNiches,
  xyaiChat,
  xyaiChatModels,
  // Auth-aware fetch wrapper
  apiFetch
};
