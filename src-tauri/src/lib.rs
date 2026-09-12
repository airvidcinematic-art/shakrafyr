mod bridge;

use tauri::{Emitter, Manager};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            let handle = app.handle().clone();
            if let Some(win) = app.get_webview_window("main") {
                let h = handle.clone();
                let _ = win.on_window_event(move |ev| {
                    match ev {
                        tauri::WindowEvent::DragDrop(tauri::DragDropEvent::Enter { .. })
                        | tauri::WindowEvent::DragDrop(tauri::DragDropEvent::Over { .. }) => {
                            let _ = h.emit("files-drag", true);
                        }
                        tauri::WindowEvent::DragDrop(tauri::DragDropEvent::Leave) => {
                            let _ = h.emit("files-drag", false);
                        }
                        tauri::WindowEvent::DragDrop(tauri::DragDropEvent::Drop { paths, .. }) => {
                            let list: Vec<String> = paths
                                .iter()
                                .map(|p| p.to_string_lossy().into_owned())
                                .collect();
                            let _ = h.emit("files-drag", false);
                            let _ = h.emit("files-dropped", list);
                        }
                        _ => {}
                    }
                });
            }
            Ok(())
        })
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
        .expect("error while running ShakraFyr");
}
