use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader};
use tauri::{AppHandle, Emitter};

fn find_workspace_root() -> Option<std::path::PathBuf> {
  let mut dir = std::env::current_dir().ok()?;
  loop {
    if dir.join("backend").join("venv").exists() {
      return Some(dir);
    }
    if !dir.pop() {
      break;
    }
  }
  None
}

#[tauri::command]
fn select_video() -> Option<String> {
  let file = rfd::FileDialog::new()
    .add_filter("Video Files", &["mp4", "mkv", "avi", "mov"])
    .pick_file();
  file.map(|p| p.to_string_lossy().to_string())
}

#[tauri::command]
fn open_folder(path: String) -> Result<(), String> {
  #[cfg(target_os = "windows")]
  {
    Command::new("explorer")
      .arg(&path)
      .spawn()
      .map_err(|e| e.to_string())?;
  }
  #[cfg(not(target_os = "windows"))]
  {
    Command::new("open")
      .arg(&path)
      .spawn()
      .map_err(|e| e.to_string())?;
  }
  Ok(())
}

#[tauri::command]
async fn run_pipeline(
  app: AppHandle,
  input: String,
  source_lang: String,
  target_lang: String,
) -> Result<String, String> {
  let workspace_root = find_workspace_root()
    .ok_or_else(|| "Could not find workspace root containing backend/venv".to_string())?;
  
  let python_exe = if cfg!(target_os = "windows") {
    workspace_root.join("backend").join("venv").join("Scripts").join("python.exe")
  } else {
    workspace_root.join("backend").join("venv").join("bin").join("python")
  };
  
  if !python_exe.exists() {
    return Err(format!("Python executable not found at: {:?}", python_exe));
  }

  let mut child = Command::new(python_exe)
    .current_dir(&workspace_root)
    .args([
      "-m", "backend.run_pipeline",
      "--input", &input,
      "--source-language", &source_lang,
      "--target-language", &target_lang,
    ])
    .stdout(Stdio::piped())
    .stderr(Stdio::piped())
    .spawn()
    .map_err(|e| format!("Failed to spawn pipeline process: {}", e))?;

  let stdout = child.stdout.take().ok_or("Failed to open stdout")?;
  let stderr = child.stderr.take().ok_or("Failed to open stderr")?;

  let app_clone = app.clone();
  let thread_handle = std::thread::spawn(move || {
    let reader = BufReader::new(stdout);
    for line in reader.lines() {
      if let Ok(l) = line {
        let _ = app_clone.emit("pipeline-log", l);
      }
    }
  });

  let app_clone_err = app.clone();
  let thread_handle_err = std::thread::spawn(move || {
    let reader_err = BufReader::new(stderr);
    for line in reader_err.lines() {
      if let Ok(l) = line {
        let _ = app_clone_err.emit("pipeline-log", l);
      }
    }
  });

  let status = child.wait().map_err(|e| format!("Process wait failed: {}", e))?;
  
  let _ = thread_handle.join();
  let _ = thread_handle_err.join();

  if status.success() {
    let projects_dir = workspace_root.join("projects");
    if let Ok(entries) = std::fs::read_dir(&projects_dir) {
      let mut latest_dir = None;
      let mut latest_time = std::time::SystemTime::UNIX_EPOCH;
      for entry in entries.flatten() {
        if let Ok(metadata) = entry.metadata() {
          if metadata.is_dir() {
            if let Ok(modified) = metadata.modified() {
              if modified > latest_time {
                latest_time = modified;
                latest_dir = Some(entry.path());
              }
            }
          }
        }
      }
      if let Some(path) = latest_dir {
        return Ok(path.to_string_lossy().to_string());
      }
    }
    Ok(projects_dir.to_string_lossy().to_string())
  } else {
    Err("Pipeline process exited with non-zero status.".to_string())
  }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![
      run_pipeline,
      select_video,
      open_folder
    ])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
