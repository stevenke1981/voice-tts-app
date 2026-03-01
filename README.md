# Steven's Voice Workspace  v1.0.0

> 自然說話，快速成文 — Python tkinter GUI + faster-whisper + Qwen3-TTS

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 功能特色

| 功能 | 說明 |
|------|------|
| 🎙️ **語音轉寫** | faster-whisper 本地推理，速度優先（int8量化 + VAD過濾） |
| ✍️ **AI 潤稿** | Ollama / OpenAI / OpenRouter，一鍵優化文字 |
| 🌐 **多語翻譯** | 英日韓法德西等 8 種語言 |
| 🔊 **Qwen3-TTS** | 多音色語音合成，支援情緒指令 |
| 📋 **歷史紀錄** | 自動儲存，可瀏覽/載入/刪除 |
| ⌨️ **熱鍵** | `Ctrl+Shift+Space` 一鍵錄音 / 停止 |
| 🖥️ **跨平台** | Windows / macOS（含 Apple Silicon）/ Linux |

---

## 介面預覽

```
┌─────────────────────────────────────────────────────────┐
│  Steven's Voice Workspace  v1.0.0                       │
├───────────┬─────────────────────────────────────────────┤
│ Steven's  │  自然說話，快速成文                          │
│  Voice    │  ┌──────┬──────┬──────┬──────┐             │
│ Workspace │  │ 狀態 │字數  │次數  │裝置  │             │
│ v1.0.0   │  └──────┴──────┴──────┴──────┘             │
│           │  [●錄音][載入][潤稿][儲存]  [翻譯來源▼][翻譯]│
│ 首頁      │  ┌原文──────┬整理後──────┬翻譯──────────┐  │
│ 輸入設定  │  │          │            │              │  │
│ TTS語音   │  │          │            │              │  │
│ 歷史紀錄  │  │          │            │              │  │
│ 字典      │  └──────────┴────────────┴──────────────┘  │
│           │  [← 暫紀錄]  [新紀錄 →]                     │
└───────────┴─────────────────────────────────────────────┘
```

---

## 快速安裝

### Windows

```cmd
# 雙擊執行，自動偵測 GPU/CPU、conda/venv
install.cmd

# 安裝完成後啟動
start.cmd
```

### macOS / Linux

```bash
# 賦予執行權限
chmod +x install.sh start.sh

# 安裝（自動偵測 Apple Silicon / NVIDIA GPU）
./install.sh

# 啟動
./start.sh
```

---

## 系統需求

| 項目 | 最低 | 建議 |
|------|------|------|
| OS | Windows 10 / macOS 12 / Ubuntu 20.04 | Windows 11 / macOS 14 / Ubuntu 22.04 |
| Python | 3.10 | 3.11 |
| RAM | 8 GB | 16 GB |
| GPU VRAM | — | 4 GB（Whisper medium） + 4 GB（TTS 0.6B） |

---

## 速度優先設定

在「輸入設定」頁面建議：

| 設定 | 建議值 | 說明 |
|------|--------|------|
| 本地模型大小 | `medium` | 精度/速度最佳平衡 |
| 量化類型 | `int8_float16` | GPU 最快；CPU 自動用 `int8` |
| Beam Size | `1` | 最快推理速度 |
| VAD 靜音過濾 | ✅ | 跳過靜音段，大幅縮短推理時間 |

---

## Qwen3-TTS 音色列表

| 音色 | 性別 | 語言特性 |
|------|------|---------|
| Vivian | 女 | 中文，明亮活潑 |
| Ryan | 男 | 英文，清晰穩重 |
| Chelsie | 女 | 英文，活潑明亮 |
| Ethan | 男 | 低沉有力 |
| Serena | 女 | 溫柔沉穩 |
| Dylan | 男 | 中文，青春自然 |
| Aiden | 男 | 英文，陽光清朗 |

---

## 手動安裝

```bash
# 1. 建立環境
conda create -n svw python=3.11 -y
conda activate svw

# 2. PyTorch（CUDA 12.4）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. macOS Apple Silicon
# pip install torch torchvision torchaudio

# 4. 相依套件
pip install -r requirements.txt
```

---

## 潤稿 API 設定

### Ollama（本地，免費）
```bash
# 安裝 Ollama: https://ollama.com/download
ollama pull gemma3:4b
# 在輸入設定頁填入：
# 本地 API URL: http://localhost:11434/v1
# Ollama 模型: gemma3:4b
```

### OpenAI
```
在輸入設定頁填入 OpenAI Key，潤稿模型填 gpt-4o-mini
```

---

## 熱鍵

| 熱鍵 | 平台 | 功能 |
|------|------|------|
| `Ctrl + Shift + Space` | Windows / Linux | 開始 / 停止錄音 |
| `Cmd + Shift + Space` | macOS | 開始 / 停止錄音 |

---

## 檔案說明

```
voice-tts-app/
├── steven_voice.py   # 主程式（跨平台）
├── requirements.txt  # Python 相依套件
├── install.cmd       # Windows 一鍵安裝
├── start.cmd         # Windows 一鍵啟動
├── install.sh        # macOS / Linux 安裝
└── start.sh          # macOS / Linux 啟動
```

---

## License

MIT © 2026 stevenke1981
