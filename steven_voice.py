#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Steven's Voice Workspace v1.0.0
Author : stevenke1981
License: MIT
"""

import os, sys, json, logging, threading, datetime, platform, subprocess
from pathlib import Path
from typing import Optional, List, Dict

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    sys.exit("[ERROR] tkinter not found.")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

APP_TITLE   = "Steven's Voice Workspace"
APP_VERSION = "v1.1.0"
CONFIG_DIR  = Path.home() / ".stevenvoice"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_DIR = CONFIG_DIR / "history"
AUDIO_DIR   = CONFIG_DIR / "audio"
DICT_FILE   = CONFIG_DIR / "dictionary.json"

for d in (CONFIG_DIR, HISTORY_DIR, AUDIO_DIR):
    d.mkdir(parents=True, exist_ok=True)

WHISPER_MODELS = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
QUANT_TYPES    = ["float32", "float16", "int8", "int8_float16", "int8_bfloat16"]
LANGUAGES      = {
    "自動偵測": None, "中文": "zh", "English": "en",
    "日本語": "ja", "한국어": "ko", "Français": "fr",
    "Deutsch": "de", "Español": "es",
}
TRANSLATE_TARGETS = list(LANGUAGES.keys())[1:]
TTS_VOICES = ["Vivian", "Ryan", "Chelsie", "Ethan", "Serena", "Dylan", "Aiden"]

DEFAULT_CONFIG: Dict = {
    "whisper_model": "medium", "whisper_device": "auto",
    "whisper_compute_type": "int8_float16", "whisper_language": "自動偵測",
    "whisper_beam_size": 1, "whisper_vad_filter": True,
    "llm_api_url": "http://localhost:11434/v1", "llm_api_key": "",
    "llm_model": "gemma3:4b", "llm_temperature": 0.3,
    "tts_voice": "Vivian", "tts_speed": 1.0,
    "tts_api_url": "http://localhost:8000",
    "hotkey": "<Control-Shift-space>", "theme": "dark",
    "window_width": 1100, "window_height": 720,
}

def load_config() -> Dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except Exception as e:
            logger.warning("Failed to load config: %s", e)
    return dict(DEFAULT_CONFIG)

def save_config(cfg: Dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def save_history_entry(entry: Dict) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = HISTORY_DIR / f"{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    return path

def list_history() -> List[Path]:
    return sorted(HISTORY_DIR.glob("*.json"), reverse=True)

def load_history_entry(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_dictionary() -> List[Dict]:
    if DICT_FILE.exists():
        try:
            with open(DICT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_dictionary(entries: List[Dict]) -> None:
    with open(DICT_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

def apply_dictionary(text: str, entries: List[Dict]) -> str:
    for e in entries:
        if e.get("enabled", True) and e.get("old") and e.get("new") is not None:
            text = text.replace(e["old"], e["new"])
    return text


class STTEngine:
    def __init__(self, cfg: Dict):
        self.cfg = cfg
        self._model = None

    def _load_model(self):
        from faster_whisper import WhisperModel
        device = self.cfg["whisper_device"]
        if device == "auto":
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        self._model = WhisperModel(
            self.cfg["whisper_model"], device=device,
            compute_type=self.cfg["whisper_compute_type"],
        )
        logger.info("Whisper loaded: %s on %s", self.cfg["whisper_model"], device)

    def transcribe(self, audio_path: str) -> str:
        if self._model is None:
            self._load_model()
        lang = LANGUAGES.get(self.cfg["whisper_language"])
        segs, _ = self._model.transcribe(
            audio_path, language=lang,
            beam_size=int(self.cfg["whisper_beam_size"]),
            vad_filter=bool(self.cfg["whisper_vad_filter"]),
        )
        return " ".join(s.text for s in segs).strip()


class LLMEngine:
    def __init__(self, cfg: Dict):
        self.cfg = cfg

    def _client(self):
        from openai import OpenAI
        return OpenAI(
            base_url=self.cfg["llm_api_url"],
            api_key=self.cfg["llm_api_key"] or "ollama",
        )

    def polish(self, text: str) -> str:
        r = self._client().chat.completions.create(
            model=self.cfg["llm_model"],
            temperature=float(self.cfg["llm_temperature"]),
            messages=[
                {"role": "system", "content": "你是一位專業文字編輯。修正錯別字、補充標點，只輸出修改後文字，不要解釋。"},
                {"role": "user",   "content": text},
            ],
        )
        return r.choices[0].message.content.strip()

    def translate(self, text: str, target_lang: str) -> str:
        r = self._client().chat.completions.create(
            model=self.cfg["llm_model"],
            temperature=float(self.cfg["llm_temperature"]),
            messages=[
                {"role": "system", "content": f"你是專業翻譯員。翻譯成{target_lang}，只輸出翻譯結果。"},
                {"role": "user",   "content": text},
            ],
        )
        return r.choices[0].message.content.strip()


class TTSEngine:
    def __init__(self, cfg: Dict):
        self.cfg = cfg

    def synthesize(self, text: str, output_path: str) -> None:
        import requests
        r = requests.post(
            self.cfg["tts_api_url"].rstrip("/") + "/synthesize",
            json={"text": text, "voice": self.cfg["tts_voice"], "speed": float(self.cfg["tts_speed"])},
            timeout=120,
        )
        r.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(r.content)

    def play(self, audio_path: str) -> None:
        s = platform.system()
        if s == "Windows":
            os.startfile(audio_path)
        elif s == "Darwin":
            subprocess.Popen(["afplay", audio_path])
        else:
            players = {
                "aplay":  [audio_path],
                "paplay": [audio_path],
                "ffplay": ["-nodisp", "-autoexit", audio_path],
            }
            for p, args in players.items():
                if subprocess.call(["which", p], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    subprocess.Popen([p] + args,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return


class AudioRecorder:
    def __init__(self):
        self._frames: List[bytes] = []
        self._recording = False
        self._stream = self._pa = self._thread = None
        self.RATE = 16000
        self.CHUNK = 1024
        self.CHANNELS = 1

    def start(self):
        import pyaudio
        if self._recording:
            return
        self._pa = pyaudio.PyAudio()
        self._frames = []
        self._recording = True
        self._stream = self._pa.open(
            format=pyaudio.paInt16, channels=self.CHANNELS,
            rate=self.RATE, input=True, frames_per_buffer=self.CHUNK,
        )
        self._thread = threading.Thread(target=self._record, daemon=True)
        self._thread.start()

    def _record(self):
        while self._recording:
            try:
                self._frames.append(self._stream.read(self.CHUNK, exception_on_overflow=False))
            except Exception:
                break

    def stop(self) -> Optional[str]:
        if not self._recording:
            return None
        self._recording = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pa:
            self._pa.terminate()
        return self._save_wav() if self._frames else None

    def _save_wav(self) -> str:
        import wave
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = str(AUDIO_DIR / f"rec_{ts}.wav")
        with wave.open(path, "wb") as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(self.RATE)
            wf.writeframes(b"".join(self._frames))
        return path


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.recorder = AudioRecorder()
        self.stt = STTEngine(self.cfg)
        self.llm = LLMEngine(self.cfg)
        self.tts = TTSEngine(self.cfg)
        self._history_paths: List[Path] = []
        self._current_history_idx: int = -1
        self._setup_window()
        self._build_ui()
        self._register_hotkey()
        self._tick()

    def _setup_window(self):
        self.title(f"{APP_TITLE}  {APP_VERSION}")
        self.geometry(f"{int(self.cfg.get('window_width', 1100))}x{int(self.cfg.get('window_height', 720))}")
        self.minsize(800, 560)
        self.configure(bg="#1e1e2e")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        self._status_var = tk.StringVar(value="就緒")
        tk.Label(self, textvariable=self._status_var, anchor="w", padx=8, pady=3,
                 bg="#313244", fg="#cdd6f4", font=("Consolas", 9)).pack(side="bottom", fill="x")
        style = ttk.Style(self)
        style.theme_use("clam")
        self._apply_style(style)
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)
        self._build_home_tab(nb)
        self._build_input_tab(nb)
        self._build_tts_tab(nb)
        self._build_history_tab(nb)
        self._build_dict_tab(nb)

    def _apply_style(self, style):
        bg, fg, sel, acc = "#1e1e2e", "#cdd6f4", "#313244", "#89b4fa"
        style.configure("TNotebook", background=bg, borderwidth=0)
        style.configure("TNotebook.Tab", background=sel, foreground=fg, padding=[12, 6], font=("Microsoft JhengHei", 10))
        style.map("TNotebook.Tab", background=[("selected", acc)], foreground=[("selected", bg)])
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Microsoft JhengHei", 10))
        style.configure("TButton", background=sel, foreground=fg, font=("Microsoft JhengHei", 10), padding=[8, 4])
        style.map("TButton", background=[("active", acc)], foreground=[("active", bg)])
        style.configure("Accent.TButton", background=acc, foreground=bg, font=("Microsoft JhengHei", 11, "bold"), padding=[12, 6])
        style.map("Accent.TButton", background=[("active", "#74c7ec")])
        style.configure("TCombobox", fieldbackground=sel, background=sel, foreground=fg)
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.configure("TLabelframe", background=bg, foreground=acc, font=("Microsoft JhengHei", 10, "bold"))
        style.configure("TLabelframe.Label", background=bg, foreground=acc)

    def _build_home_tab(self, nb):
        self._home = ttk.Frame(nb)
        nb.add(self._home, text="  首頁  ")
        stats = ttk.Frame(self._home)
        stats.pack(fill="x", padx=10, pady=(10, 4))
        self._stat_status = self._stat_label(stats, "狀態", "就緒", 0)
        self._stat_chars  = self._stat_label(stats, "字數", "0", 1)
        self._stat_count  = self._stat_label(stats, "次數", "0", 2)
        btn_row = ttk.Frame(self._home)
        btn_row.pack(fill="x", padx=10, pady=4)
        self._rec_btn = ttk.Button(btn_row, text="● 錄音", style="Accent.TButton", command=self._toggle_record)
        self._rec_btn.pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text="📂 載入", command=self._load_audio).pack(side="left", padx=3)
        ttk.Button(btn_row, text="✏️ 潤稿", command=self._polish_async).pack(side="left", padx=3)
        ttk.Button(btn_row, text="💾 儲存", command=self._save_text).pack(side="left", padx=3)
        ttk.Button(btn_row, text="📋 複製原文", command=lambda: self._copy_text(self._txt_raw)).pack(side="left", padx=3)
        ttk.Button(btn_row, text="📋 複製整理", command=lambda: self._copy_text(self._txt_polish)).pack(side="left", padx=3)
        ttk.Button(btn_row, text="📋 複製翻譯", command=lambda: self._copy_text(self._txt_trans)).pack(side="left", padx=3)
        tr_row = ttk.Frame(self._home)
        tr_row.pack(fill="x", padx=10, pady=2)
        ttk.Label(tr_row, text="翻譯來源:").pack(side="left")
        self._translate_src = ttk.Combobox(tr_row, values=["原文", "整理後"], width=8, state="readonly")
        self._translate_src.set("整理後")
        self._translate_src.pack(side="left", padx=4)
        ttk.Label(tr_row, text="目標語言:").pack(side="left")
        self._translate_target = ttk.Combobox(tr_row, values=TRANSLATE_TARGETS, width=10, state="readonly")
        self._translate_target.set("English")
        self._translate_target.pack(side="left", padx=4)
        ttk.Button(tr_row, text="🌐 翻譯", command=self._translate_async).pack(side="left", padx=3)
        pane = tk.PanedWindow(self._home, orient="horizontal", bg="#313244", sashwidth=4, relief="flat")
        pane.pack(fill="both", expand=True, padx=10, pady=8)
        self._txt_raw    = self._text_panel(pane, "原文")
        self._txt_polish = self._text_panel(pane, "整理後")
        self._txt_trans  = self._text_panel(pane, "翻譯")
        pane.add(self._txt_raw.master,    minsize=180, width=300)
        pane.add(self._txt_polish.master, minsize=180, width=380)
        pane.add(self._txt_trans.master,  minsize=180, width=300)
        nav_row = ttk.Frame(self._home)
        nav_row.pack(pady=(0, 6))
        ttk.Button(nav_row, text="← 上筆紀錄", command=self._prev_history).pack(side="left", padx=4)
        ttk.Button(nav_row, text="新紀錄 →",   command=self._new_record).pack(side="left", padx=4)

    def _stat_label(self, parent, title, value, col):
        var = tk.StringVar(value=value)
        frm = ttk.Frame(parent)
        frm.grid(row=0, column=col, padx=8)
        ttk.Label(frm, text=title, font=("Microsoft JhengHei", 8), foreground="#6c7086").pack()
        ttk.Label(frm, textvariable=var, font=("Microsoft JhengHei", 14, "bold"), foreground="#89b4fa").pack()
        return var

    def _text_panel(self, parent, title):
        frame = ttk.LabelFrame(parent, text=title)
        txt = tk.Text(frame, wrap="word", undo=True,
                      bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
                      selectbackground="#45475a", relief="flat",
                      font=("Microsoft JhengHei", 11), padx=6, pady=6)
        sb = ttk.Scrollbar(frame, orient="vertical", command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        return txt

    def _build_input_tab(self, nb):
        frm = ttk.Frame(nb)
        nb.add(frm, text="  輸入設定  ")
        frm.columnconfigure(1, weight=1)
        r = [0]
        def add(lbl, w):
            ttk.Label(frm, text=lbl).grid(row=r[0], column=0, sticky="w", padx=16, pady=6)
            w.grid(row=r[0], column=1, sticky="ew", padx=16, pady=6)
            r[0] += 1
        self._cfg_whisper_model = ttk.Combobox(frm, values=WHISPER_MODELS, state="readonly", width=14)
        self._cfg_whisper_model.set(self.cfg["whisper_model"])
        add("本地模型大小:", self._cfg_whisper_model)
        self._cfg_compute = ttk.Combobox(frm, values=QUANT_TYPES, state="readonly", width=18)
        self._cfg_compute.set(self.cfg["whisper_compute_type"])
        add("量化類型:", self._cfg_compute)
        self._cfg_beam = tk.IntVar(value=int(self.cfg["whisper_beam_size"]))
        add("Beam Size:", ttk.Spinbox(frm, from_=1, to=10, textvariable=self._cfg_beam, width=6))
        self._cfg_lang = ttk.Combobox(frm, values=list(LANGUAGES.keys()), state="readonly", width=14)
        self._cfg_lang.set(self.cfg["whisper_language"])
        add("語言:", self._cfg_lang)
        self._cfg_vad = tk.BooleanVar(value=bool(self.cfg["whisper_vad_filter"]))
        add("VAD 靜音過濾:", ttk.Checkbutton(frm, variable=self._cfg_vad))
        self._cfg_llm_url = tk.StringVar(value=self.cfg["llm_api_url"])
        add("本地 API URL:", ttk.Entry(frm, textvariable=self._cfg_llm_url, width=40))
        self._cfg_api_key = tk.StringVar(value=self.cfg["llm_api_key"])
        add("API Key:", ttk.Entry(frm, textvariable=self._cfg_api_key, width=40, show="*"))
        self._cfg_llm_model = tk.StringVar(value=self.cfg["llm_model"])
        add("潤稿模型:", ttk.Entry(frm, textvariable=self._cfg_llm_model, width=30))
        self._cfg_temp = tk.DoubleVar(value=float(self.cfg["llm_temperature"]))
        add("Temperature:", ttk.Scale(frm, from_=0.0, to=1.0, variable=self._cfg_temp, orient="horizontal"))
        ttk.Button(frm, text="儲存設定", style="Accent.TButton",
                   command=self._save_input_settings).grid(row=r[0], column=0, columnspan=2, pady=16)

    def _build_tts_tab(self, nb):
        frm = ttk.Frame(nb)
        nb.add(frm, text="  TTS語音  ")
        row = ttk.Frame(frm)
        row.pack(fill="x", padx=16, pady=10)
        ttk.Label(row, text="音色:").pack(side="left")
        self._cfg_tts_voice = ttk.Combobox(row, values=TTS_VOICES, state="readonly", width=12)
        self._cfg_tts_voice.set(self.cfg["tts_voice"])
        self._cfg_tts_voice.pack(side="left", padx=6)
        ttk.Label(row, text="語速:").pack(side="left", padx=(12, 0))
        self._cfg_tts_speed = tk.DoubleVar(value=float(self.cfg["tts_speed"]))
        ttk.Scale(row, from_=0.5, to=2.0, variable=self._cfg_tts_speed,
                  orient="horizontal", length=160).pack(side="left", padx=4)
        row2 = ttk.Frame(frm)
        row2.pack(fill="x", padx=16, pady=6)
        ttk.Label(row2, text="TTS API URL:").pack(side="left")
        self._cfg_tts_url = tk.StringVar(value=self.cfg["tts_api_url"])
        ttk.Entry(row2, textvariable=self._cfg_tts_url, width=36).pack(side="left", padx=6)
        ttk.Label(frm, text="自訂文字:").pack(anchor="w", padx=16, pady=(12, 2))
        self._tts_text = tk.Text(frm, height=6, wrap="word",
                                 bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
                                 font=("Microsoft JhengHei", 11), padx=6, pady=6)
        self._tts_text.pack(fill="x", padx=16, pady=4)
        btn_row = ttk.Frame(frm)
        btn_row.pack(fill="x", padx=16, pady=8)
        ttk.Button(btn_row, text="🔊 合成並播放", style="Accent.TButton",
                   command=self._tts_async).pack(side="left", padx=3)
        ttk.Button(btn_row, text="儲存 TTS 設定",
                   command=self._save_tts_settings).pack(side="left", padx=3)

    def _build_history_tab(self, nb):
        frm = ttk.Frame(nb)
        nb.add(frm, text="  歷史紀錄  ")
        top = ttk.Frame(frm)
        top.pack(fill="x", padx=10, pady=6)
        ttk.Button(top, text="🔄 重新整理", command=self._refresh_history).pack(side="left")
        ttk.Button(top, text="🗑️ 刪除選取",  command=self._delete_history).pack(side="left", padx=4)
        ttk.Button(top, text="📤 載入到首頁", command=self._load_to_home).pack(side="left", padx=4)
        self._hist_list = tk.Listbox(frm, bg="#181825", fg="#cdd6f4",
                                     selectbackground="#45475a", relief="flat", font=("Consolas", 10))
        sb = ttk.Scrollbar(frm, orient="vertical", command=self._hist_list.yview)
        self._hist_list.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._hist_list.pack(fill="both", expand=True, padx=(10, 0), pady=4)
        self._hist_list.bind("<<ListboxSelect>>", self._on_hist_select)
        self._hist_preview = tk.Text(frm, height=8, wrap="word", state="disabled",
                                     bg="#181825", fg="#a6adc8", relief="flat",
                                     font=("Microsoft JhengHei", 10), padx=6)
        self._hist_preview.pack(fill="x", padx=10, pady=4)
        self._refresh_history()

    def _build_dict_tab(self, nb):
        frm = ttk.Frame(nb)
        nb.add(frm, text="  字典  ")
        top = ttk.Frame(frm)
        top.pack(fill="x", padx=10, pady=6)
        ttk.Label(top, text="自訂替換規則（語音辨識自動修正）",
                  font=("Microsoft JhengHei", 11, "bold")).pack(side="left")
        btn_row = ttk.Frame(frm)
        btn_row.pack(fill="x", padx=10, pady=4)
        ttk.Button(btn_row, text="➕ 新增規則", command=self._dict_add).pack(side="left", padx=3)
        ttk.Button(btn_row, text="🗑️ 刪除選取", command=self._dict_delete).pack(side="left", padx=3)
        ttk.Button(btn_row, text="💾 儲存字典", style="Accent.TButton",
                   command=self._dict_save).pack(side="left", padx=3)
        cols = ("enabled", "old", "new")
        self._dict_tree = ttk.Treeview(frm, columns=cols, show="headings", height=12)
        self._dict_tree.heading("enabled", text="啟用")
        self._dict_tree.heading("old", text="原始詞")
        self._dict_tree.heading("new", text="替換為")
        self._dict_tree.column("enabled", width=60, anchor="center")
        self._dict_tree.column("old", width=200)
        self._dict_tree.column("new", width=200)
        self._dict_tree.bind("<Double-1>", self._dict_edit)
        sb = ttk.Scrollbar(frm, orient="vertical", command=self._dict_tree.yview)
        self._dict_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y", padx=(0, 10))
        self._dict_tree.pack(fill="both", expand=True, padx=(10, 0), pady=4)
        add_row = ttk.Frame(frm)
        add_row.pack(fill="x", padx=10, pady=6)
        ttk.Label(add_row, text="原始詞:").pack(side="left")
        self._dict_old_var = tk.StringVar()
        ttk.Entry(add_row, textvariable=self._dict_old_var, width=20).pack(side="left", padx=4)
        ttk.Label(add_row, text="替換為:").pack(side="left", padx=(8, 0))
        self._dict_new_var = tk.StringVar()
        ttk.Entry(add_row, textvariable=self._dict_new_var, width=20).pack(side="left", padx=4)
        ttk.Button(add_row, text="加入", command=self._dict_add_from_entry).pack(side="left", padx=4)
        self._dict_load()

    def _toggle_record(self):
        if not self.recorder._recording:
            self._start_record()
        else:
            self._stop_record()

    def _start_record(self):
        try:
            self.recorder.start()
            self._rec_btn.configure(text="⏹ 停止錄音")
            self._set_status("錄音中…")
            self._stat_status.set("錄音中")
        except Exception as e:
            messagebox.showerror("錄音錯誤", str(e))

    def _stop_record(self):
        self._set_status("處理中…")
        self._rec_btn.configure(text="● 錄音")
        self._stat_status.set("處理中")
        threading.Thread(target=self._process_recording, daemon=True).start()

    def _process_recording(self):
        audio_path = self.recorder.stop()
        if not audio_path:
            self.after(0, self._set_status, "未偵測到音訊")
            return
        try:
            text = self.stt.transcribe(audio_path)
            self.after(0, self._set_raw_text, text)
        except Exception as e:
            self.after(0, messagebox.showerror, "轉寫錯誤", str(e))
        finally:
            self.after(0, self._set_status, "就緒")
            self.after(0, self._stat_status.set, "就緒")

    def _set_raw_text(self, text: str):
        entries = self._get_dict_entries()
        text = apply_dictionary(text, entries)
        self._txt_raw.delete("1.0", "end")
        self._txt_raw.insert("1.0", text)
        self._stat_chars.set(str(len(text)))
        self._stat_count.set(str(int(self._stat_count.get()) + 1))

    def _copy_text(self, widget):
        text = widget.get("1.0", "end").strip()
        if not text:
            self._set_status("無可複製的內容")
            return
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status("已複製到剪貼簿")

    def _load_audio(self):
        path = filedialog.askopenfilename(
            title="選擇音訊檔案",
            filetypes=[("Audio", "*.wav *.mp3 *.m4a *.ogg *.flac"), ("All", "*.*")],
        )
        if not path:
            return
        self._set_status("轉寫中…")
        threading.Thread(target=self._transcribe_file, args=(path,), daemon=True).start()

    def _transcribe_file(self, path: str):
        try:
            text = self.stt.transcribe(path)
            self.after(0, self._set_raw_text, text)
        except Exception as e:
            self.after(0, messagebox.showerror, "轉寫錯誤", str(e))
        finally:
            self.after(0, self._set_status, "就緒")

    def _polish_async(self):
        text = self._txt_raw.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("提示", "原文欄位為空")
            return
        self._set_status("潤稿中…")
        threading.Thread(target=self._polish_worker, args=(text,), daemon=True).start()

    def _polish_worker(self, text: str):
        try:
            result = self.llm.polish(text)
            def _update():
                self._txt_polish.delete("1.0", "end")
                self._txt_polish.insert("1.0", result)
                self._stat_chars.set(str(len(result)))
            self.after(0, _update)
        except Exception as e:
            self.after(0, messagebox.showerror, "潤稿錯誤", str(e))
        finally:
            self.after(0, self._set_status, "就緒")

    def _translate_async(self):
        src = self._translate_src.get()
        text = (self._txt_polish if src == "整理後" else self._txt_raw).get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("提示", "無可翻譯的文字")
            return
        target = self._translate_target.get()
        self._set_status(f"翻譯成 {target}…")
        threading.Thread(target=self._translate_worker, args=(text, target), daemon=True).start()

    def _translate_worker(self, text: str, target: str):
        try:
            result = self.llm.translate(text, target)
            def _update():
                self._txt_trans.delete("1.0", "end")
                self._txt_trans.insert("1.0", result)
            self.after(0, _update)
        except Exception as e:
            self.after(0, messagebox.showerror, "翻譯錯誤", str(e))
        finally:
            self.after(0, self._set_status, "就緒")

    def _tts_async(self):
        text = self._tts_text.get("1.0", "end").strip() or self._txt_polish.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("提示", "無可合成的文字")
            return
        self._set_status("語音合成中…")
        threading.Thread(target=self._tts_worker, args=(text,), daemon=True).start()

    def _tts_worker(self, text: str):
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = str(AUDIO_DIR / f"tts_{ts}.wav")
            self.tts.synthesize(text, path)
            self.tts.play(path)
        except Exception as e:
            self.after(0, messagebox.showerror, "TTS 錯誤", str(e))
        finally:
            self.after(0, self._set_status, "就緒")

    def _save_text(self):
        entry = {
            "ts":     datetime.datetime.now().isoformat(),
            "raw":    self._txt_raw.get("1.0", "end").strip(),
            "polish": self._txt_polish.get("1.0", "end").strip(),
            "trans":  self._txt_trans.get("1.0", "end").strip(),
        }
        path = save_history_entry(entry)
        self._set_status(f"已儲存：{path.name}")
        self._refresh_history()

    def _save_input_settings(self):
        self.cfg.update({
            "whisper_model":        self._cfg_whisper_model.get(),
            "whisper_compute_type": self._cfg_compute.get(),
            "whisper_beam_size":    self._cfg_beam.get(),
            "whisper_language":     self._cfg_lang.get(),
            "whisper_vad_filter":   self._cfg_vad.get(),
            "llm_api_url":          self._cfg_llm_url.get(),
            "llm_api_key":          self._cfg_api_key.get(),
            "llm_model":            self._cfg_llm_model.get(),
            "llm_temperature":      round(self._cfg_temp.get(), 2),
        })
        save_config(self.cfg)
        self.stt = STTEngine(self.cfg)
        self.llm = LLMEngine(self.cfg)
        self._set_status("輸入設定已儲存")

    def _save_tts_settings(self):
        self.cfg.update({
            "tts_voice":   self._cfg_tts_voice.get(),
            "tts_speed":   round(self._cfg_tts_speed.get(), 2),
            "tts_api_url": self._cfg_tts_url.get(),
        })
        save_config(self.cfg)
        self.tts = TTSEngine(self.cfg)
        self._set_status("TTS 設定已儲存")

    def _refresh_history(self):
        self._history_paths = list_history()
        self._hist_list.delete(0, "end")
        for p in self._history_paths:
            self._hist_list.insert("end", p.stem)

    def _on_hist_select(self, _=None):
        sel = self._hist_list.curselection()
        if not sel:
            return
        try:
            entry = load_history_entry(self._history_paths[sel[0]])
            preview = entry.get("polish") or entry.get("raw") or ""
            self._hist_preview.configure(state="normal")
            self._hist_preview.delete("1.0", "end")
            self._hist_preview.insert("1.0", preview[:500])
            self._hist_preview.configure(state="disabled")
        except Exception:
            pass

    def _delete_history(self):
        sel = self._hist_list.curselection()
        if not sel or not messagebox.askyesno("確認", "確定刪除此紀錄?"):
            return
        try:
            self._history_paths[sel[0]].unlink()
        except Exception as e:
            messagebox.showerror("刪除失敗", str(e))
        self._refresh_history()

    def _load_to_home(self):
        sel = self._hist_list.curselection()
        if not sel:
            return
        entry = load_history_entry(self._history_paths[sel[0]])
        for w, k in ((self._txt_raw, "raw"), (self._txt_polish, "polish"), (self._txt_trans, "trans")):
            w.delete("1.0", "end")
            w.insert("1.0", entry.get(k, ""))
        self._set_status("歷史紀錄已載入")

    def _prev_history(self):
        paths = list_history()
        if not paths:
            return
        self._current_history_idx = min(self._current_history_idx + 1, len(paths) - 1)
        entry = load_history_entry(paths[self._current_history_idx])
        for w, k in ((self._txt_raw, "raw"), (self._txt_polish, "polish"), (self._txt_trans, "trans")):
            w.delete("1.0", "end")
            w.insert("1.0", entry.get(k, ""))

    def _new_record(self):
        self._current_history_idx = -1
        for w in (self._txt_raw, self._txt_polish, self._txt_trans):
            w.delete("1.0", "end")

    def _dict_load(self):
        for item in self._dict_tree.get_children():
            self._dict_tree.delete(item)
        for e in load_dictionary():
            self._dict_tree.insert("", "end", values=(
                "✓" if e.get("enabled", True) else "✗",
                e.get("old", ""), e.get("new", ""),
            ))

    def _dict_add(self):
        self._dict_tree.insert("", "end", values=("✓", "", ""))

    def _dict_add_from_entry(self):
        old = self._dict_old_var.get().strip()
        new = self._dict_new_var.get().strip()
        if not old:
            messagebox.showwarning("提示", "原始詞不可為空")
            return
        self._dict_tree.insert("", "end", values=("✓", old, new))
        self._dict_old_var.set("")
        self._dict_new_var.set("")
        self._dict_save()

    def _dict_edit(self, event):
        item = self._dict_tree.identify_row(event.y)
        col = self._dict_tree.identify_column(event.x)
        if not item:
            return
        vals = list(self._dict_tree.item(item, "values"))
        if col == "#1":
            vals[0] = "✗" if vals[0] == "✓" else "✓"
            self._dict_tree.item(item, values=vals)
            return
        col_idx = int(col.replace("#", "")) - 1
        x, y, w, h = self._dict_tree.bbox(item, col)
        entry = tk.Entry(self._dict_tree, font=("Microsoft JhengHei", 10))
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, vals[col_idx])
        entry.focus_set()
        def _on_confirm(_=None):
            vals[col_idx] = entry.get()
            self._dict_tree.item(item, values=vals)
            entry.destroy()
        entry.bind("<Return>", _on_confirm)
        entry.bind("<FocusOut>", _on_confirm)

    def _dict_delete(self):
        sel = self._dict_tree.selection()
        if not sel:
            return
        for item in sel:
            self._dict_tree.delete(item)
        self._set_status("已刪除選取的規則")

    def _dict_save(self):
        entries = []
        for item in self._dict_tree.get_children():
            vals = self._dict_tree.item(item, "values")
            entries.append({"enabled": vals[0] == "✓", "old": vals[1], "new": vals[2]})
        save_dictionary(entries)
        self._set_status("字典已儲存")

    def _get_dict_entries(self) -> List[Dict]:
        return load_dictionary()

    def _register_hotkey(self):
        hk = self.cfg.get("hotkey", "<Control-Shift-space>")
        try:
            self.bind_all(hk, lambda _e: self._toggle_record())
            logger.info("Hotkey registered: %s", hk)
        except Exception as e:
            logger.warning("Hotkey failed: %s", e)

    def _set_status(self, msg: str):
        self._status_msg = msg
        self._status_var.set(f"  {msg}")

    def _tick(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base = getattr(self, "_status_msg", "就緒")
        self._status_var.set(f"  {base}   │   {now}")
        self.after(1000, self._tick)

    def _on_close(self):
        if self.recorder._recording:
            self.recorder.stop()
        save_config(self.cfg)
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
