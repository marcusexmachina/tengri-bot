"""NSFW detection processors. Ported from nsfw_detector."""

import gc
import io
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from transformers import pipeline

from nsfw.config import (
    FFMPEG_MAX_FRAMES,
    FFMPEG_TIMEOUT,
    IMAGE_EXTENSIONS,
    NSFW_THRESHOLD,
    VIDEO_EXTENSIONS,
)

logger = logging.getLogger(__name__)

import threading

_model_manager = None
_inference_lock = threading.Lock()
_init_lock = threading.Lock()


def _get_model_manager():
    """Lazy singleton for model pipeline."""
    global _model_manager
    with _init_lock:
        if _model_manager is None:
            _model_manager = pipeline(
                "image-classification",
                model="Falconsai/nsfw_image_detection",
                device=-1,
            )
            logger.info("NSFW model loaded")
    return _model_manager


def process_image(image: Image.Image) -> dict:
    """Classify a PIL Image. Returns {'nsfw': float, 'normal': float}."""
    pipe = _get_model_manager()
    with _inference_lock:
        result = pipe(image)
    nsfw_score = next((item["score"] for item in result if item["label"] == "nsfw"), 0.0)
    normal_score = next((item["score"] for item in result if item["label"] == "normal"), 1.0)
    gc.collect()
    return {"nsfw": nsfw_score, "normal": normal_score}


def process_video_file(video_path: str) -> dict | None:
    """Process video via ffmpeg frame extraction. Returns result or None on error."""
    temp_dir = None
    try:
        # Get video info
        duration_cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-show_entries",
            "stream=r_frame_rate",
            "-select_streams",
            "v",
            "-of",
            "json",
            video_path,
        ]
        result = subprocess.run(
            duration_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=FFMPEG_TIMEOUT,
        )
        if result.returncode != 0:
            logger.warning("ffprobe failed: %s", result.stderr.decode()[:200])
            return None

        import json

        info = json.loads(result.stdout.decode())
        duration = 0.0
        frame_rate = 25.0
        if "format" in info and "duration" in info["format"]:
            duration = float(info["format"]["duration"])
        if "streams" in info and info["streams"] and "r_frame_rate" in info["streams"][0]:
            fr_str = info["streams"][0]["r_frame_rate"]
            if "/" in fr_str:
                n, d = map(int, fr_str.split("/"))
                frame_rate = n / d if d else 25.0
            else:
                frame_rate = float(fr_str)

        temp_dir = tempfile.mkdtemp()
        interval = max(1, int(duration / FFMPEG_MAX_FRAMES)) if duration else 1
        fps = f"1/{interval}"
        frames_to_extract = min(FFMPEG_MAX_FRAMES, int(duration) if duration else 1) or 1

        extract_cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-vf",
            f"fps={fps}",
            "-vframes",
            str(frames_to_extract),
            "-q:v",
            "2",
            "-y",
            os.path.join(temp_dir, "frame-%d.jpg"),
        ]
        run = subprocess.run(
            extract_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=FFMPEG_TIMEOUT,
        )
        if run.returncode != 0:
            logger.warning("ffmpeg extract failed: %s", run.stderr.decode()[:200])
            return None

        import glob

        frame_files = sorted(glob.glob(os.path.join(temp_dir, "frame-*.jpg")))
        last_result = None
        for fp in frame_files:
            try:
                with Image.open(fp) as img:
                    r = process_image(img)
                    last_result = r
                    if r["nsfw"] > NSFW_THRESHOLD:
                        return r
            except Exception as e:
                logger.warning("Frame processing failed %s: %s", fp, e)
            gc.collect()
        return last_result
    except subprocess.TimeoutExpired:
        logger.warning("Video processing timed out")
        return None
    except Exception as e:
        logger.warning("Video processing failed: %s", e)
        return None
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning("Temp cleanup failed: %s", e)
        gc.collect()


def process_pdf_file(pdf_bytes: bytes) -> dict | None:
    """Process PDF. Returns result or None. Requires pdf2image, poppler."""
    try:
        from pdf2image import convert_from_path
    except ImportError:
        logger.debug("pdf2image not available, skipping PDF")
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            tmp_path = f.name
        pages = convert_from_path(tmp_path, dpi=150, first_page=1, last_page=5)
        last_result = None
        for img in pages:
            try:
                r = process_image(img)
                last_result = r
                if r["nsfw"] > NSFW_THRESHOLD:
                    return r
            finally:
                if hasattr(img, "close"):
                    img.close()
            gc.collect()
        return last_result
    except Exception as e:
        logger.warning("PDF processing failed: %s", e)
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        gc.collect()


def process_docx_file(content: bytes) -> dict | None:
    """Process .docx. Returns result or None."""
    try:
        from docx import Document
    except ImportError:
        logger.debug("python-docx not available")
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(content)
            tmp_path = f.name
        doc = Document(tmp_path)
        last_result = None
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    data = rel.target_part.blob
                    with Image.open(io.BytesIO(data)) as img:
                        r = process_image(img)
                        last_result = r
                        if r["nsfw"] > NSFW_THRESHOLD:
                            return r
                except Exception as e:
                    logger.debug("Docx image extract failed: %s", e)
            gc.collect()
        return last_result
    except Exception as e:
        logger.warning("DOCX processing failed: %s", e)
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        gc.collect()


def process_doc_file(content: bytes) -> dict | None:
    """Process .doc via antiword. Returns result or None."""
    try:
        result = subprocess.run(
            ["antiword", "-i", "1", "-"],
            input=content,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except FileNotFoundError:
        logger.debug("antiword not available")
        return None
    return None  # antiword extracts text, not images; skip for now


def process_archive(filepath: str, depth: int = 0, max_depth: int = 5) -> dict | None:
    """Process archive (zip/rar/7z). Returns result or None."""
    if depth > max_depth:
        return None
    try:
        from nsfw.utils import ArchiveHandler, can_process_file, sort_files_by_priority
    except ImportError:
        logger.debug("Archive utils not available")
        return None

    try:
        with ArchiveHandler(filepath) as handler:
            files = handler.list_files()
            processable = [f for f in files if can_process_file(f)]
            if not processable:
                return None
            sorted_files = sort_files_by_priority(handler, processable)
            last_result = None
            for fn in sorted_files[:20]:  # Limit files per archive
                try:
                    content = handler.extract_file(fn)
                    ext = Path(fn).suffix.lower()
                    if ext in IMAGE_EXTENSIONS:
                        with Image.open(io.BytesIO(content)) as img:
                            r = process_image(img)
                            last_result = r
                            if r["nsfw"] > NSFW_THRESHOLD:
                                return r
                    elif ext == ".pdf":
                        r = process_pdf_file(content)
                        if r:
                            last_result = r
                            if r["nsfw"] > NSFW_THRESHOLD:
                                return r
                    elif ext in VIDEO_EXTENSIONS:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tf:
                            tf.write(content)
                            tf.flush()
                            try:
                                r = process_video_file(tf.name)
                                if r:
                                    last_result = r
                                    if r["nsfw"] > NSFW_THRESHOLD:
                                        return r
                            finally:
                                os.unlink(tf.name)
                except Exception as e:
                    logger.debug("Archive file %s failed: %s", fn, e)
                gc.collect()
            return last_result
    except Exception as e:
        logger.warning("Archive processing failed: %s", e)
        return None
