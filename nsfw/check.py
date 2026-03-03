"""Entry point for NSFW checking. Routes Telegram media to appropriate processor."""

import io
import logging
import os
import tempfile
from pathlib import Path

from PIL import Image

from nsfw.config import (
    ARCHIVE_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    MAX_FILE_SIZE_MB,
    NSFW_THRESHOLD,
    VIDEO_EXTENSIONS,
)
from nsfw.processors import (
    process_archive,
    process_doc_file,
    process_docx_file,
    process_image,
    process_pdf_file,
    process_video_file,
)

logger = logging.getLogger(__name__)

MAX_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def check_media_nsfw(
    data: bytes | str,
    media_type: str,
    filename: str | None = None,
) -> dict | None:
    """
    Check if media is NSFW. Runs synchronously; call via asyncio.to_thread.

    Args:
        data: File bytes or path to temp file.
        media_type: One of 'image', 'video', 'pdf', 'doc', 'docx', 'archive'.
        filename: Optional original filename (for documents/archives).

    Returns:
        {'nsfw': float, 'normal': float} if detection succeeded, None on error/skip.
    """
    try:
        if isinstance(data, bytes):
            if len(data) > MAX_BYTES:
                logger.debug("File too large for NSFW check: %d bytes", len(data))
                return None
        else:
            if os.path.getsize(data) > MAX_BYTES:
                logger.debug("File too large for NSFW check")
                return None

        if media_type == "image":
            if isinstance(data, bytes):
                img = Image.open(io.BytesIO(data)).convert("RGB")
            else:
                with Image.open(data) as img:
                    img = img.convert("RGB").copy()
            return process_image(img)

        if media_type == "video":
            path = data if isinstance(data, str) else _bytes_to_temp(data, ".mp4")
            try:
                return process_video_file(path)
            finally:
                if isinstance(data, bytes) and path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception:
                        pass

        if media_type == "pdf":
            content = data if isinstance(data, bytes) else _read_file(data)
            return process_pdf_file(content)

        if media_type == "doc":
            content = data if isinstance(data, bytes) else _read_file(data)
            return process_doc_file(content)

        if media_type == "docx":
            content = data if isinstance(data, bytes) else _read_file(data)
            return process_docx_file(content)

        if media_type == "archive":
            path = data if isinstance(data, str) else _bytes_to_temp(data, ".zip")
            try:
                return process_archive(path)
            finally:
                if isinstance(data, bytes) and path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception:
                        pass

        logger.debug("Unknown media_type for NSFW: %s", media_type)
        return None
    except Exception as e:
        logger.warning("NSFW check failed: %s", e)
        return None


def _bytes_to_temp(data: bytes, suffix: str) -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, data)
        return path
    finally:
        os.close(fd)


def _read_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def get_media_type_from_document(mime_type: str | None, file_name: str | None) -> str | None:
    """Map Telegram document MIME/filename to our media_type for check_media_nsfw."""
    ext = Path(file_name or "").suffix.lower() if file_name else ""
    mime = (mime_type or "").lower()

    if mime.startswith("image/") or ext in IMAGE_EXTENSIONS:
        return "image"
    if mime.startswith("video/") or ext in VIDEO_EXTENSIONS:
        return "video"
    if mime == "application/pdf" or ext == ".pdf":
        return "pdf"
    if ext in (".doc",) or "msword" in mime:
        return "doc"
    if ext in (".docx",) or "wordprocessingml" in mime:
        return "docx"
    if ext in ARCHIVE_EXTENSIONS or "zip" in mime or "rar" in mime or "7z" in mime:
        return "archive"
    return None
