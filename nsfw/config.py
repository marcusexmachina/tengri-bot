"""NSFW detector configuration. Loaded from env with safe defaults."""

import os

# Ensure .env is loaded before reading (config may be imported before bot.py load_env)
from dotenv import load_dotenv

load_dotenv()

NSFW_ENABLED = os.getenv("NSFW_ENABLED", "false").lower() in ("true", "1", "yes")
NSFW_THRESHOLD = float(os.getenv("NSFW_THRESHOLD", "0.8"))
# NSFW_MUTE_SECONDS: use MUTE_SECONDS from main config if not set
_NSFW_MUTE = os.getenv("NSFW_MUTE_SECONDS")
NSFW_MUTE_SECONDS = int(_NSFW_MUTE) if _NSFW_MUTE else None  # None = use main MUTE_SECONDS

# Detector internals (from nsfw_detector)
FFMPEG_MAX_FRAMES = 20
FFMPEG_TIMEOUT = 1800
MAX_FILE_SIZE_MB = 50  # Telegram file limit ~20MB for bots; cap for safety

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tga"}
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm", ".flv", ".3gp", ".m4v", ".mpg", ".mpeg"}
ARCHIVE_EXTENSIONS = {".7z", ".rar", ".zip", ".gz"}
DOCUMENT_EXTENSIONS = {".doc", ".docx"}
