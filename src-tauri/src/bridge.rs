use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

fn project_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("src-tauri parent")
        .to_path_buf()
}

fn python_candidates() -> Vec<String> {
    let mut v = Vec::new();
    if let Ok(p) = std::env::var("CONVERT432_PYTHON") {
        v.push(p);
    }
    v.push("python".into());
    v.push("py".into());
    v.push("python3".into());
    v
}

fn run_bridge(args: &[String]) -> Result<Value, String> {
    let root = project_root();
    let script = root.join("tools").join("app_bridge.py");
    if !script.exists() {
        return Err(format!("missing {}", script.display()));
    }
    let mut last_err = String::from("no python");
    for bin in python_candidates() {
        let mut cmd = Command::new(&bin);
        if bin == "py" {
            cmd.arg("-3");
        }
        cmd.arg(&script).args(args).current_dir(&root);
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            cmd.creation_flags(0x08000000);
        }
        match cmd.output() {
            Ok(out) => {
                let stdout = String::from_utf8_lossy(&out.stdout).trim().to_string();
                let stderr = String::from_utf8_lossy(&out.stderr).trim().to_string();
                if !out.status.success() {
                    last_err = if stderr.is_empty() {
                        format!("{bin} exit {}: {stdout}", out.status)
                    } else {
                        stderr
                    };
                    continue;
                }
                return serde_json::from_str(&stdout)
                    .map_err(|e| format!("bridge json: {e} :: {stdout}"));
            }
            Err(e) => last_err = format!("{bin}: {e}"),
        }
    }
    Err(last_err)
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PrepareResult {
    pub path: String,
    pub cached: bool,
    pub ratio: f64,
}

#[tauri::command]
pub async fn pick_audio_files(window: tauri::WebviewWindow) -> Result<Vec<String>, String> {
    // Async + parent HWND. Sync rfd from a Tauri command deadlocks Windows.
    // Without set_parent the picker often never appears (or hides behind).
    let files = rfd::AsyncFileDialog::new()
        .set_parent(&window)
        .set_title("Add tracks — ShakraFyr")
        .add_filter(
            "Audio",
            &["wav", "mp3", "flac", "ogg", "m4a", "aac", "aiff", "aif"],
        )
        .pick_files()
        .await
        .unwrap_or_default();
    Ok(files
        .into_iter()
        .map(|p| p.path().to_string_lossy().into_owned())
        .collect())
}

#[tauri::command]
pub fn detect_tuning(path: String) -> Result<Value, String> {
    run_bridge(&[String::from("detect"), path])
}

#[tauri::command]
pub fn library_dir() -> Result<String, String> {
    let dir = project_root().join("ConvertedLibrary");
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.to_string_lossy().into_owned())
}

#[tauri::command]
pub fn cache_dir() -> Result<String, String> {
    let dir = std::env::temp_dir().join("convert432-play");
    std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
    Ok(dir.to_string_lossy().into_owned())
}

fn play_cache_path(src: &Path, ratio: f64) -> PathBuf {
    let mtime = src
        .metadata()
        .ok()
        .and_then(|m| m.modified().ok())
        .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let stem = src
        .file_stem()
        .unwrap_or_default()
        .to_string_lossy();
    let safe: String = stem
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
        .take(48)
        .collect();
    let cents = (1200.0 * ratio.log2()).round() as i64;
    std::env::temp_dir()
        .join("convert432-play")
        .join(format!("{safe}_{mtime}_{cents}c.wav"))
}

#[tauri::command]
pub fn prepare_play(path: String, ratio: f64) -> Result<PrepareResult, String> {
    let src = PathBuf::from(&path);
    if !src.exists() {
        return Err(format!("missing {path}"));
    }
    if !ratio.is_finite() || !(0.01..=100.0).contains(&ratio) {
        return Err(format!("bad ratio {ratio}"));
    }
    if (ratio - 1.0).abs() < 1e-9 {
        return Ok(PrepareResult {
            path,
            cached: true,
            ratio,
        });
    }
    let dest = play_cache_path(&src, ratio);
    std::fs::create_dir_all(dest.parent().unwrap()).map_err(|e| e.to_string())?;
    let src_mtime = src.metadata().and_then(|m| m.modified()).unwrap_or(SystemTime::UNIX_EPOCH);
    let reuse = dest.exists()
        && dest
            .metadata()
            .ok()
            .and_then(|m| m.modified().ok())
            .map(|t| t >= src_mtime)
            .unwrap_or(false);
    if !reuse {
        run_bridge(&[
            String::from("shift"),
            path.clone(),
            String::from("--ratio"),
            format!("{ratio:.12}"),
            String::from("--out"),
            dest.to_string_lossy().into_owned(),
        ])?;
    }
    Ok(PrepareResult {
        path: dest.to_string_lossy().into_owned(),
        cached: reuse,
        ratio,
    })
}

#[tauri::command]
pub fn convert_track(path: String, ratio: f64, dest: String) -> Result<Value, String> {
    run_bridge(&[
        String::from("shift"),
        path,
        String::from("--ratio"),
        format!("{ratio:.12}"),
        String::from("--out"),
        dest,
    ])
}

#[tauri::command]
pub fn library_filename(stem: String, preset_id: String, pc: String, hz: f64) -> Result<String, String> {
    let v = run_bridge(&[
        String::from("name"),
        stem,
        String::from("--preset-id"),
        preset_id,
        String::from("--pc"),
        pc,
        String::from("--hz"),
        format!("{hz}"),
    ])?;
    v.get("filename")
        .and_then(|x| x.as_str())
        .map(|s| s.to_string())
        .ok_or_else(|| "name failed".into())
}
