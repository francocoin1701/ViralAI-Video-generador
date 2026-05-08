# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

# === APIs de texto (el usuario trae la suya) ===
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")

# === Proveedores soportados ===
PROVIDERS_TEXTO = {
    "gemini":    {"nombre": "Gemini",   "modelo": "gemini-2.5-flash"},
    "claude":    {"nombre": "Claude",   "modelo": "claude-opus-4-5"},
    "openai":    {"nombre": "ChatGPT",  "modelo": "gpt-4o-mini"},
    "deepseek":  {"nombre": "DeepSeek", "modelo": "deepseek-chat",  "base_url": "https://api.deepseek.com"},
    "qwen":      {"nombre": "Qwen",     "modelo": "qwen-plus",      "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"},
}

# === Video ===
VIDEO_WIDTH = 720
VIDEO_HEIGHT = 1280
VIDEO_FPS = 30
VIDEO_DURATION_PER_IMAGE = 3
MAX_VIDEO_DURATION = 60

# === Audio ===
TTS_LANGUAGE = "es"
TTS_SLOW = False
MUSIC_VOLUME = 0.1
VOICE_VOLUME = 1.0

# === Rutas ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
OUTPUT_DIR = os.path.join(ASSETS_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
GUIONES_DIR = os.path.join(BASE_DIR, "guiones")

# === Subtítulos ===
SUBTITLE_FONT_SIZE = 60
SUBTITLE_COLOR = "white"
SUBTITLE_BG_COLOR = "black"
SUBTITLE_POSITION = "bottom"