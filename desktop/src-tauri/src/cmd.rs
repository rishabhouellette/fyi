// FYI Social ∞ - Tauri Backend Commands
// Bridge between Rust/Tauri and Python backend

use serde::{Deserialize, Serialize};
use std::process::Command;
use std::path::PathBuf;

#[derive(Debug, Serialize, Deserialize)]
pub struct VideoProcessRequest {
    pub video_path: String,
    pub target_clips: u32,
    pub quality: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct VideoProcessResponse {
    pub success: bool,
    pub clips: Vec<ClipInfo>,
    pub total_clips: u32,
    pub processing_time: f64,
    pub output_dir: String,
    pub error: Option<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ClipInfo {
    pub id: u32,
    pub start: f64,
    pub end: f64,
    pub duration: f64,
    pub clip_path: String,
    pub virality_score: u32,
    pub thumbnails: Vec<ThumbnailInfo>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ThumbnailInfo {
    pub style: String,
    pub text: String,
    pub image_path: String,
    pub score: u32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SchedulePostRequest {
    pub platform: String,
    pub clip_path: String,
    pub caption: String,
    pub scheduled_time: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GrowthReport {
    pub period: String,
    pub total_posts: u32,
    pub insights: Vec<String>,
    pub recommendations: Vec<Recommendation>,
    pub score: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Recommendation {
    pub category: String,
    pub priority: String,
    pub action: String,
    pub reason: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AppConfig {
    pub ollama_installed: bool,
    pub ffmpeg_installed: bool,
    pub python_version: String,
    pub models_installed: Vec<String>,
}

// Helper: Get Python executable path (venv)
pub fn get_python_path() -> PathBuf {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop(); // desktop/src-tauri -> desktop
    path.pop(); // desktop -> FYIUploader
    path.push("venv");
    path.push("Scripts");
    path.push("python.exe");
    path
}

// Helper: Get backend directory path
pub fn get_backend_path() -> PathBuf {
    let mut path = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    path.pop(); // desktop/src-tauri -> desktop
    path.pop(); // desktop -> FYIUploader
    path
}

// Helper: Execute Python command with proper environment
fn run_python_command(python_code: &str) -> Result<std::process::Output, String> {
    let python_exe = get_python_path();
    let backend_dir = get_backend_path();
    
    Command::new(&python_exe)
        .current_dir(&backend_dir)
        .arg("-c")
        .arg(python_code)
        .output()
        .map_err(|e| format!("Failed to execute Python at {:?}: {}", python_exe, e))
}

// Command: Process video into clips
#[tauri::command]
pub async fn process_video(
    video_path: String,
    target_clips: u32,
    quality: String,
) -> Result<VideoProcessResponse, String> {
    // Call Python backend
    let output = run_python_command(&format!(
        "from video_lab import get_auto_editor; \
         import json; \
         editor = get_auto_editor(); \
         result = editor.process_video('{}', target_clips={}, quality='{}'); \
         print(json.dumps(result))",
        video_path, target_clips, quality
    ))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: VideoProcessResponse = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(response)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Python error: {}", stderr))
    }
}

// Command: Score video virality
#[tauri::command]
pub async fn score_video(video_path: String) -> Result<serde_json::Value, String> {
    let output = run_python_command(&format!(
        "from ai_engine import get_clip_scoring; \
         import json; \
         scorer = get_clip_scoring(); \
         result = scorer.score_video('{}'); \
         print(json.dumps(result))",
        video_path
    ))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: serde_json::Value = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(response)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Python error: {}", stderr))
    }
}

// Command: Generate thumbnails
#[tauri::command]
pub async fn generate_thumbnails(
    video_path: String,
    clip_info: ClipInfo,
) -> Result<Vec<ThumbnailInfo>, String> {
    let clip_json = serde_json::to_string(&clip_info)
        .map_err(|e| format!("Failed to serialize clip info: {}", e))?;

    let output = run_python_command(&format!(
        "from ai_engine import get_thumbnail_ai; \
         import json; \
         thumb_ai = get_thumbnail_ai(); \
         clip_info = json.loads('{}'); \
         result = thumb_ai.generate_thumbnails('{}', clip_info); \
         print(json.dumps(result))",
        clip_json.replace("'", "\\'"),
        video_path
    ))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: Vec<ThumbnailInfo> = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(response)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Python error: {}", stderr))
    }
}

// Command: Get growth report
#[tauri::command]
pub async fn get_growth_report(days: u32) -> Result<GrowthReport, String> {
    let output = run_python_command(&format!(
        "from ai_engine import get_dashboard_data; \
         import json; \
         report = get_dashboard_data(days={}); \
         print(json.dumps(report))",
        days
    ))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: GrowthReport = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(response)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Python error: {}", stderr))
    }
}

// Command: Schedule post
#[tauri::command]
pub async fn schedule_post(request: SchedulePostRequest) -> Result<serde_json::Value, String> {
    let request_json = serde_json::to_string(&request)
        .map_err(|e| format!("Failed to serialize request: {}", e))?;

    let output = Command::new("python")
        .arg("-c")
        .arg(format!(
            "from scheduler_engine import schedule_post; \
             import json; \
             request = json.loads('{}'); \
             result = schedule_post(request['platform'], request['clip_path'], request['caption'], request['scheduled_time']); \
             print(json.dumps(result))",
            request_json.replace("'", "\\'")
        ))
        .output()
        .map_err(|e| format!("Failed to execute Python: {}", e))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: serde_json::Value = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(response)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Python error: {}", stderr))
    }
}

// Command: Get app configuration status
#[tauri::command]
pub async fn get_app_config() -> Result<AppConfig, String> {
    let output = run_python_command(
        "from ai_engine import get_ollama_manager; \
         import json; \
         import sys; \
         import shutil; \
         ollama = get_ollama_manager(); \
         config = { \
             'ollama_installed': ollama.is_ollama_installed(), \
             'ffmpeg_installed': shutil.which('ffmpeg') is not None, \
             'python_version': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}', \
             'models_installed': ollama.list_installed_models() if ollama.is_ollama_installed() else [] \
         }; \
         print(json.dumps(config))"
    )?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: AppConfig = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(response)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Python error: {}", stderr))
    }
}

// Command: Install Ollama models
#[tauri::command]
pub async fn install_ollama_models() -> Result<String, String> {
    let output = run_python_command(
        "from ai_engine import get_ollama_manager; \
         ollama = get_ollama_manager(); \
         ollama.setup_recommended_models(); \
         print('Models installed successfully')"
    )?;

    if output.status.success() {
        Ok("Models installed successfully".to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Installation failed: {}", stderr))
    }
}

// Command: Get viral templates
#[tauri::command]
pub async fn get_templates() -> Result<Vec<serde_json::Value>, String> {
    // Return mock templates for now
    let templates = vec![
        serde_json::json!({
            "id": "mr-beast",
            "name": "Mr. Beast Style",
            "description": "High-energy, engaging content with bold text and excitement"
        }),
        serde_json::json!({
            "id": "educational",
            "name": "Educational",
            "description": "Informative content with clear explanations"
        })
    ];
    Ok(templates)
}

// Command: Apply viral template
#[tauri::command]
pub async fn apply_template(
    template_id: String,
    video_info: serde_json::Value,
) -> Result<serde_json::Value, String> {
    let video_json = serde_json::to_string(&video_info)
        .map_err(|e| format!("Failed to serialize video info: {}", e))?;

    let output = run_python_command(&format!(
        "from ai_engine import get_template_engine; \
         import json; \
         templates = get_template_engine(); \
         video_info = json.loads('{}'); \
         result = templates.apply_template('{}', video_info); \
         print(json.dumps(result))",
        video_json.replace("'", "\\'"),
        template_id
    ))?;

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let response: serde_json::Value = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse response: {}", e))?;
        Ok(response)
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr);
        Err(format!("Python error: {}", stderr))
    }
}
