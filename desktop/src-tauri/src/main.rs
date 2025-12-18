// FYI Social ∞ - Tauri Main Entry Point
// Prevents additional console window on Windows in release

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod cmd;

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![
            cmd::process_video,
            cmd::score_video,
            cmd::generate_thumbnails,
            cmd::get_growth_report,
            cmd::schedule_post,
            cmd::get_app_config,
            cmd::install_ollama_models,
            cmd::get_templates,
            cmd::apply_template,
        ])
        .setup(|app| {
            // Start Python desktop API server
            std::thread::spawn(|| {
                let python_path = cmd::get_python_path();
                let backend_dir = cmd::get_backend_path();
                
                std::process::Command::new(&python_path)
                    .current_dir(&backend_dir)
                    .arg("desktop_api.py")
                    .spawn()
                    .ok();
            });
            
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
