"""Archive handling and file type helpers. Simplified port from nsfw_detector."""

import gzip
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path

from nsfw.config import (
    ARCHIVE_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
)

logger = logging.getLogger(__name__)

try:
    import rarfile
except ImportError:
    rarfile = None


def _get_file_extension(filename: str | bytes) -> str:
    return Path(filename.decode() if isinstance(filename, bytes) else filename).suffix.lower()


def can_process_file(filename: str | bytes) -> bool:
    ext = _get_file_extension(filename)
    return (
        ext in IMAGE_EXTENSIONS
        or ext == ".pdf"
        or ext in VIDEO_EXTENSIONS
        or ext in DOCUMENT_EXTENSIONS
    )


def sort_files_by_priority(handler: "ArchiveHandler", files: list) -> list:
    def key(fn):
        ext = _get_file_extension(fn)
        size = handler.get_file_info(fn)
        if ext in IMAGE_EXTENSIONS:
            return (0, size)
        if ext == ".pdf":
            return (1, size)
        if ext in VIDEO_EXTENSIONS:
            return (2, size)
        if ext in DOCUMENT_EXTENSIONS:
            return (1, size)
        return (3, size)

    return sorted(files, key=key)


class ArchiveHandler:
    """Context manager for zip/rar/7z/gz. Extracts for RAR/7z, streams for zip/gz."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.archive = None
        self.type = self._determine_type()
        self.temp_dir = None
        self._extracted = {}

    def _determine_type(self) -> str | None:
        try:
            if zipfile.is_zipfile(self.filepath):
                return "zip"
            if rarfile and rarfile.is_rarfile(self.filepath):
                return "rar"
            if self._is_7z(self.filepath):
                return "7z"
            if self._is_gzip(self.filepath):
                return "gz"
        except Exception as e:
            logger.debug("Archive type detection failed: %s", e)
        return None

    def _is_7z(self, path: str) -> bool:
        try:
            r = subprocess.run(["7z", "l", path], capture_output=True, timeout=10)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _is_gzip(self, path: str) -> bool:
        try:
            with gzip.open(path, "rb") as f:
                f.read(1)
            return True
        except Exception:
            return False

    def __enter__(self):
        if self.type == "zip":
            self.archive = zipfile.ZipFile(self.filepath)
        elif self.type == "rar":
            if not rarfile:
                raise RuntimeError("rarfile not installed")
            self.archive = rarfile.RarFile(self.filepath)
            if self.archive.needs_password():
                raise ValueError("Password-protected RAR not supported")
            self.temp_dir = tempfile.mkdtemp()
            subprocess.run(
                ["unrar", "x", "-y", self.filepath, self.temp_dir + os.sep],
                capture_output=True,
                timeout=120,
                check=True,
            )
            for root, _, files in os.walk(self.temp_dir):
                for fn in files:
                    rel = os.path.relpath(os.path.join(root, fn), self.temp_dir)
                    new_name = str(uuid.uuid4()) + Path(fn).suffix
                    new_path = os.path.join(self.temp_dir, new_name)
                    os.rename(os.path.join(root, fn), new_path)
                    self._extracted[rel] = new_path
        elif self.type == "7z":
            self.temp_dir = tempfile.mkdtemp()
            subprocess.run(
                ["7z", "x", "-y", self.filepath, f"-o{self.temp_dir}"],
                capture_output=True,
                timeout=120,
                check=True,
            )
            for root, _, files in os.walk(self.temp_dir):
                for fn in files:
                    rel = os.path.relpath(os.path.join(root, fn), self.temp_dir)
                    new_name = str(uuid.uuid4()) + Path(fn).suffix
                    new_path = os.path.join(self.temp_dir, new_name)
                    os.rename(os.path.join(root, fn), new_path)
                    self._extracted[rel] = new_path
        elif self.type == "gz":
            self.archive = gzip.GzipFile(self.filepath)
        else:
            raise ValueError(f"Unsupported archive type: {self.type}")
        return self

    def __exit__(self, *args):
        if self.archive and hasattr(self.archive, "close"):
            self.archive.close()
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning("Cleanup failed: %s", e)

    def list_files(self) -> list:
        if self.type == "zip":
            return [f for f in self.archive.namelist() if not f.endswith("/")]
        if self.type in ("rar", "7z"):
            return list(self._extracted.keys())
        if self.type == "gz":
            base = os.path.basename(self.filepath)
            return [base[:-3]] if base.endswith(".gz") else ["content"]
        return []

    def get_file_info(self, filename: str) -> int:
        if self.type == "zip":
            try:
                return self.archive.getinfo(filename).file_size
            except KeyError:
                return 0
        if self.type in ("rar", "7z") and filename in self._extracted:
            return os.path.getsize(self._extracted[filename])
        if self.type == "gz":
            return getattr(self.archive, "size", 0)
        return 0

    def extract_file(self, filename: str) -> bytes:
        if self.type == "zip":
            return self.archive.read(filename)
        if self.type in ("rar", "7z") and filename in self._extracted:
            with open(self._extracted[filename], "rb") as f:
                return f.read()
        if self.type == "gz":
            return self.archive.read()
        raise ValueError(f"Cannot extract {filename}")
