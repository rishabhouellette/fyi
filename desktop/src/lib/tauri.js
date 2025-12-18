// Tauri Bridge - JavaScript wrapper for Rust commands
import { invoke } from '@tauri-apps/api/core';

/**
 * Process video into viral clips using AI
 * @param {string} videoPath - Full path to video file
 * @param {number} targetClips - Number of clips to generate (1-10)
 * @param {string} quality - Video quality: 'high' | 'medium' | 'low'
 * @returns {Promise<{success: boolean, clips: Array, processing_time: number, error?: string}>}
 */
export async function processVideo(videoPath, targetClips = 3, quality = 'high') {
  try {
    const result = await invoke('process_video', {
      videoPath,
      targetClips,
      quality
    });
    return result;
  } catch (error) {
    console.error('Video processing failed:', error);
    return { success: false, error: error.toString(), clips: [] };
  }
}

/**
 * Score video for viral potential (0-100)
 * @param {string} videoPath - Full path to video file
 * @returns {Promise<{score: number, breakdown: object, suggestions: Array}>}
 */
export async function scoreVideo(videoPath) {
  try {
    const result = await invoke('score_video', { videoPath });
    return result;
  } catch (error) {
    console.error('Video scoring failed:', error);
    return { score: 0, breakdown: {}, suggestions: [], error: error.toString() };
  }
}

/**
 * Generate AI thumbnails for video clips
 * @param {string} videoPath - Full path to video file
 * @param {object} clipInfo - Clip metadata {start, end, duration}
 * @returns {Promise<Array<{path: string, score: number, style: string}>>}
 */
export async function generateThumbnails(videoPath, clipInfo) {
  try {
    const result = await invoke('generate_thumbnails', {
      videoPath,
      clipInfo: JSON.stringify(clipInfo)
    });
    return result;
  } catch (error) {
    console.error('Thumbnail generation failed:', error);
    return [];
  }
}

/**
 * Get growth analytics report
 * @param {number} days - Number of days to analyze (7, 30, 90)
 * @returns {Promise<{metrics: object, insights: Array, predictions: object}>}
 */
export async function getGrowthReport(days = 30) {
  try {
    const result = await invoke('get_growth_report', { days });
    return result;
  } catch (error) {
    console.error('Growth report failed:', error);
    return { metrics: {}, insights: [], predictions: {}, error: error.toString() };
  }
}

/**
 * Schedule post across platforms
 * @param {object} request - {platforms: Array, content: object, scheduledTime: string, clips: Array}
 * @returns {Promise<{success: boolean, scheduled_posts: Array, error?: string}>}
 */
export async function schedulePost(request) {
  try {
    const result = await invoke('schedule_post', {
      request: JSON.stringify(request)
    });
    return result;
  } catch (error) {
    console.error('Post scheduling failed:', error);
    return { success: false, scheduled_posts: [], error: error.toString() };
  }
}

/**
 * Get app configuration and dependency status
 * @returns {Promise<{ollama_installed: boolean, ffmpeg_installed: boolean, models: Array}>}
 */
export async function getAppConfig() {
  try {
    const result = await invoke('get_app_config');
    return result;
  } catch (error) {
    console.error('Config check failed:', error);
    return { ollama_installed: false, ffmpeg_installed: false, models: [], error: error.toString() };
  }
}

/**
 * Install required Ollama AI models
 * @returns {Promise<{success: boolean, installed_models: Array, error?: string}>}
 */
export async function installOllamaModels() {
  try {
    const result = await invoke('install_ollama_models');
    return result;
  } catch (error) {
    console.error('Model installation failed:', error);
    return { success: false, installed_models: [], error: error.toString() };
  }
}

/**
 * Get viral video templates
 * @returns {Promise<Array<{id: string, name: string, description: string, metrics: object}>>}
 */
export async function getTemplates() {
  try {
    const result = await invoke('get_templates');
    return result;
  } catch (error) {
    console.error('Template fetch failed:', error);
    return [];
  }
}

/**
 * Apply viral template to video
 * @param {string} templateId - Template ID to apply
 * @param {object} videoInfo - Video metadata
 * @returns {Promise<{success: boolean, customization: object, error?: string}>}
 */
export async function applyTemplate(templateId, videoInfo) {
  try {
    const result = await invoke('apply_template', {
      templateId,
      videoInfo: JSON.stringify(videoInfo)
    });
    return result;
  } catch (error) {
    console.error('Template application failed:', error);
    return { success: false, customization: {}, error: error.toString() };
  }
}

// Export all functions
export default {
  processVideo,
  scoreVideo,
  generateThumbnails,
  getGrowthReport,
  schedulePost,
  getAppConfig,
  installOllamaModels,
  getTemplates,
  applyTemplate
};
