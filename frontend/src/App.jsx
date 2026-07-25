import React, { useState, useEffect, useRef } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'vi', name: 'Vietnamese' },
  { code: 'ja', name: 'Japanese' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'zh', name: 'Chinese' }
];

const STAGES = [
  { id: 1, name: 'Loading Video' },
  { id: 2, name: 'Speech Recognition' },
  { id: 3, name: 'Translation' },
  { id: 4, name: 'Timeline Alignment' },
  { id: 5, name: 'Voice Synthesis' },
  { id: 6, name: 'Rendering Video' },
  { id: 7, name: 'Completed' }
];

export default function App() {
  const [input, setInput] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('en');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [status, setStatus] = useState('idle'); // idle | running | success | error
  const [errorMsg, setErrorMsg] = useState('');
  const [projectPath, setProjectPath] = useState('');
  const [currentStage, setCurrentStage] = useState(0);
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);

  useEffect(() => {
    // Listen to live logs emitted from Rust pipeline process
    const unlisten = listen('pipeline-log', (event) => {
      const logLine = event.payload;
      setLogs((prev) => [...prev, logLine]);

      // Parse stage progress from log lines
      if (logLine.includes('Stage 1:') || logLine.includes('Stage 2:')) {
        setCurrentStage(1);
      } else if (logLine.includes('Stage 3:')) {
        setCurrentStage(2);
      } else if (logLine.includes('Stage 4:')) {
        setCurrentStage(3);
      } else if (logLine.includes('Stage 5:')) {
        setCurrentStage(4);
      } else if (logLine.includes('Stage 6:') || logLine.includes('Stage 7:')) {
        setCurrentStage(5);
      } else if (logLine.includes('Stage 8:')) {
        setCurrentStage(6);
      } else if (logLine.includes('completed successfully')) {
        setCurrentStage(7);
      }
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);

  useEffect(() => {
    // Scroll log window to bottom when new logs arrive
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const handleBrowse = async () => {
    try {
      const selected = await invoke('select_video');
      if (selected) {
        setInput(selected);
      }
    } catch (err) {
      console.error('File browse error:', err);
    }
  };

  const handleStart = async () => {
    if (!input.trim()) {
      setErrorMsg('Please browse a video file or paste a YouTube URL.');
      setStatus('error');
      return;
    }

    setStatus('running');
    setErrorMsg('');
    setProjectPath('');
    setCurrentStage(1);
    setLogs(['[System] Initializing backend translation process...']);

    try {
      const path = await invoke('run_pipeline', {
        input: input.trim(),
        sourceLang: sourceLanguage,
        targetLang: targetLanguage
      });
      setProjectPath(path);
      setStatus('success');
      setCurrentStage(7);
    } catch (err) {
      setErrorMsg(err.toString());
      setStatus('error');
    }
  };

  const handleOpenFolder = async () => {
    if (projectPath) {
      try {
        await invoke('open_folder', { path: projectPath });
      } catch (err) {
        console.error('Failed to open folder:', err);
      }
    }
  };

  return (
    <main className="p-6 max-w-2xl mx-auto flex flex-col h-screen text-white select-none">
      {/* Title */}
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-indigo-400">AutoShort Studio</h1>
        <p className="text-gray-400 text-sm">Alpha MVP - Video Audio Translation & Subtitling</p>
      </header>

      {/* Input Selection */}
      <section className="space-y-4 mb-6 bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
        <div>
          <label className="block text-sm font-semibold text-gray-300 mb-1">
            Input Video Source
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Paste YouTube URL or browse a local file..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={status === 'running'}
              className="flex-1 px-3 py-2 bg-zinc-950 border border-zinc-800 rounded text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-50 text-gray-200"
            />
            <button
              onClick={handleBrowse}
              disabled={status === 'running'}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-sm font-medium rounded transition-colors disabled:opacity-50"
            >
              Browse
            </button>
          </div>
        </div>

        {/* Language Selection */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-1">
              Source Language
            </label>
            <select
              value={sourceLanguage}
              onChange={(e) => setSourceLanguage(e.target.value)}
              disabled={status === 'running'}
              className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-50 text-gray-200"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-300 mb-1">
              Target Language
            </label>
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              disabled={status === 'running'}
              className="w-full px-3 py-2 bg-zinc-950 border border-zinc-800 rounded text-sm focus:outline-none focus:border-indigo-500 disabled:opacity-50 text-gray-200"
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {/* Action / Trigger */}
      <section className="mb-6">
        <button
          onClick={handleStart}
          disabled={status === 'running'}
          className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded transition-colors disabled:bg-indigo-900 disabled:cursor-not-allowed text-sm"
        >
          {status === 'running' ? 'Processing Video...' : 'Start Translation'}
        </button>
      </section>

      {/* Progress Monitor */}
      {status === 'running' && (
        <section className="mb-6 bg-zinc-900/50 p-4 rounded-lg border border-zinc-800">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-3">
            Pipeline Progress
          </h2>
          <div className="space-y-2">
            {STAGES.map((stage) => {
              const isActive = currentStage === stage.id;
              const isCompleted = currentStage > stage.id;
              return (
                <div key={stage.id} className="flex items-center gap-3 text-sm">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      isActive
                        ? 'bg-indigo-400 animate-pulse'
                        : isCompleted
                        ? 'bg-emerald-500'
                        : 'bg-zinc-700'
                    }`}
                  />
                  <span
                    className={`${
                      isActive
                        ? 'text-indigo-300 font-medium'
                        : isCompleted
                        ? 'text-emerald-400'
                        : 'text-zinc-500'
                    }`}
                  >
                    {stage.name}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Success / Error Banners */}
      {status === 'success' && (
        <section className="mb-6 p-4 bg-emerald-950/50 border border-emerald-800 rounded-lg flex flex-col gap-3">
          <div>
            <h3 className="text-emerald-400 font-semibold text-sm">Success!</h3>
            <p className="text-emerald-300 text-xs mt-1">
              Video has been successfully translated and saved inside the project folder.
            </p>
          </div>
          <button
            onClick={handleOpenFolder}
            className="self-start px-3 py-1.5 bg-emerald-800 hover:bg-emerald-700 text-xs font-medium rounded text-emerald-100 transition-colors"
          >
            Open Output Folder
          </button>
        </section>
      )}

      {status === 'error' && (
        <section className="mb-6 p-4 bg-rose-950/50 border border-rose-800 rounded-lg">
          <h3 className="text-rose-400 font-semibold text-sm">Execution Failed</h3>
          <p className="text-rose-300 text-xs mt-1 break-words">{errorMsg}</p>
        </section>
      )}

      {/* Mini live log monitor for process activity feedback */}
      {status === 'running' && (
        <section className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg p-3 font-mono text-[10px] text-zinc-400 overflow-y-auto min-h-[120px]">
          <div className="space-y-1">
            {logs.map((log, idx) => (
              <div key={idx} className="break-all whitespace-pre-wrap">
                {log}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        </section>
      )}
    </main>
  );
}
