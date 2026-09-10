mod bridge;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            bridge::pick_audio_files,
            bridge::detect_tuning,
            bridge::library_dir,
            bridge::cache_dir,
            bridge::prepare_play,
            bridge::convert_track,
            bridge::library_filename,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Convert432");
}
