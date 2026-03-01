# Steven's Voice Workspace  v1.0.0

> 自然說話，快速成文 — Python tkinter GUI + faster-whisper + Qwen3-TTS

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 功能特色

| 功能 | 說明 |
|------|------|
| 🎙️ **語音轉寫** | faster-whisper 本地推理，速度優先（int8 量化 + VAD 過濾） |
| ✍️ **AI 潤稿** | Ollama / OpenAI / OpenRouter，一鍵優化文字 |
| 🌐 **多語翻譯** | 英日韓法德西等 8 種語言互譯 |
| 🔊 **Qwen3-TTS** | 多音色語音合成，支援情緒指令 |
| 📋 **歷史紀錄** | 自動儲存，可瀏覽 / 載入 / 刪除 |
| ⌨️ **熱鍵** | `Ctrl+Shift+Space` 一鍵錄音 / 停止 |
| 🖥️ **跨平台** | Windows / macOS（含 Apple Silicon）/ Linux |

---

## 介面預覽

```
┌─────────────────────────────────────────────────────────┐
│  Steven's Voice Workspace  v1.0.0                       │
├───────────┬─────────────────────────────────────────────┤
│ Steven's  │  自然說話，快速成文                          │
│  Voice    │  ┌──────┬──────┬──────┐                    │
│ Workspace │  │ 狀態 │字數  │次數  │                    │
│ v1.0.0   │  └──────┴──────┴──────┘                    │
│           │  [●錄音][載入][潤稿][儲存]                  │
│ 首頁      │  [翻譯來源▼] [目標語言▼] [翻譯]            │
│ 輸入設定  │  ┌原文──────┬整理後──────┬翻譯──────────┐  │
│ TTS語音   │  │          │            │              │  │
│ 歷史紀錄  │  │          │            │              │  │
│ 字典      │  └──────────┴────────────┴──────────────┘  │
│           │  [← 上筆紀錄]  [新紀錄 →]                   │
└───────────┴─────────────────────────────────────────────┘
```

---

## 快速安裝

### 方法一：Clone 後執行安裝腳本

```bash
git clone https://github.com/stevenke1981/voice-tts-app.git
cd voice-tts-app
```

#### Windows

```cmd
install.cmd
start.cmd
```

#### macOS / Linux

```bash
chmod +x install.sh start.sh
./install.sh
./start.sh
```

### 方法二：手動安裝

```bash
# 1. 建立虛擬環境
conda create -n svw python=3.11 -y
conda activate svw

# 2. 安裝 PyTorch（CUDA 12.4）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# macOS Apple Silicon 請改用：
# pip install torch torchvision torchaudio

# 3. 安裝相依套件
pip install -r requirements.txt

# 4. 啟動程式
python steven_voice.py
```

---

## 系統需求

| 項目 | 最低 | 建議 |
|------|------|------|
| OS | Windows 10 / macOS 12 / Ubuntu 20.04 | Windows 11 / macOS 14 / Ubuntu 22.04 |
| Python | 3.10 | 3.11 |
| RAM | 8 GB | 16 GB |
| GPU VRAM | — | 4 GB（Whisper medium）+ 4 GB（TTS 0.6B） |

---

## 相依套件

| 套件 | 版本 | 用途 |
|------|------|------|
| `faster-whisper` | ≥ 1.0.3 | 本地語音轉文字 |
| `pyaudio` | ≥ 0.2.14 | 麥克風錄音 |
| `openai` | ≥ 1.30.0 | LLM 潤稿 / 翻譯（OpenAI-compatible） |
| `requests` | ≥ 2.31.0 | TTS API 呼叫 |
| `numpy` | ≥ 1.24.0 | 音訊處理輔助 |

---

## 速度優先設定

在「輸入設定」頁面建議：

| 設定 | 建議值 | 說明 |
|------|--------|------|
| 本地模型大小 | `medium` | 精度 / 速度最佳平衡 |
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

## 潤稿 / 翻譯 API 設定

### Ollama（本地，免費）

```bash
# 安裝 Ollama：https://ollama.com/download
ollama pull gemma3:4b
```

在「輸入設定」頁面填入：

| 欄位 | 值 |
|------|----|
| 本地 API URL | `http://localhost:11434/v1` |
| 潤稿模型 | `gemma3:4b` |
| API Key | （留空即可） |

### OpenAI / OpenRouter

在「輸入設定」頁面填入對應的 API Key 與模型名稱，例如：
- OpenAI：`gpt-4o-mini`
- OpenRouter：`openai/gpt-4o-mini`

---

## 使用前注意事項

> ⚠️ **首次啟動**會自動下載 `medium` Whisper 模型（約 1.5 GB），請確保網路暢通。

1. **語音轉文字（STT）**：由 faster-whisper 在本地執行，不需要網路（下載後）。
2. **AI 潤稿 / 翻譯**：需先啟動 Ollama 或填入 OpenAI Key。
3. **Qwen3-TTS 語音合成**：需另外啟動 TTS API 服務（預設 `http://localhost:8000`），其餘功能不受影響。
4. **熱鍵**：`Ctrl + Shift + Space`（Windows / Linux）或 `Cmd + Shift + Space`（macOS）可直接開始 / 停止錄音。

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
├── steven_voice.py   # 主程式（tkinter 5 分頁 GUI，跨平台）
├── requirements.txt  # Python 相依套件
├── install.cmd       # Windows 一鍵安裝（自動偵測 conda / CUDA）
├── start.cmd         # Windows 一鍵啟動
├── install.sh        # macOS / Linux 安裝（自動偵測 Apple Silicon / NVIDIA）
└── start.sh          # macOS / Linux 啟動
```

---

## 主程式架構

```
steven_voice.py
├── STTEngine       → faster-whisper 語音轉文字
├── LLMEngine       → OpenAI-compatible 潤稿 / 翻譯
├── TTSEngine       → Qwen3-TTS API 語音合成
├── AudioRecorder   → 麥克風錄音（PyAudio）
└── App (tk.Tk)     → 5 分頁 GUI
    ├── 首頁         → 錄音、潤稿、翻譯、三欄文字顯示
    ├── 輸入設定     → Whisper / LLM 參數調整
    ├── TTS 語音     → 音色、語速、合成播放
    ├── 歷史紀錄     → 瀏覽 / 載入 / 刪除紀錄
    └── 字典         → 自訂替換規則（即將推出）
```

---

## License

MIT © 2026 stevenke1981