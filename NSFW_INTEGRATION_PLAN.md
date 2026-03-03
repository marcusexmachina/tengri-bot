## NSFW Detection Integration Plan for Tengri Bot

This document summarizes the current systems, goals, architecture options, and recommended implementation plan for integrating the `nsfw_detector` project into the `tengri-bot` Telegram anti‑spam bot. It is intended as a briefing for another AI/engineer so they can quickly understand what needs to be built.

---

### 1. Existing Systems

#### 1.1 Tengri Bot (Telegram anti‑spam bot)

- Repository: `/Users/marcus/Desktop/Github/tengri-bot`
- Technology: `python-telegram-bot` (async, job-queue), Python 3.10+, Docker/Docker Compose support.
- Purpose: Anti‑spam and moderation for a single Telegram group.
- Key behavior:
  - **Spam detection (text):**
    - `spam.py`:
      - `handle_message_or_media` routes updates.
      - `handle_message` handles text in the target group.
      - Tracks per‑user, per‑text buckets in `spam_state`.
      - If the same normalized text is sent ≥ `SPAM_THRESHOLD` times within `REPEAT_WINDOW_SECONDS`, the bot:
        - Deletes those messages (bulk or fallback one‑by‑one).
        - Restricts (mutes) the user for `MUTE_SECONDS` (60s).
        - Sends a warning message (from `responses.py`).
        - Schedules auto‑delete of that warning after 30s.
  - **Media flood detection (stickers / GIFs):**
    - `handle_media_flood` in `spam.py`:
      - Tracks per‑user media buckets in `media_flood_state`.
      - If a user sends ≥ `MEDIA_FLOOD_THRESHOLD` media items within `REPEAT_WINDOW_SECONDS`, the bot:
        - Deletes those media messages.
        - Restricts (mutes) the user for `MUTE_SECONDS` (60s).
        - Sends a warning and auto‑deletes it after 30s.
  - **Manual moderation commands (`handlers/stfu.py`):**
    - `/stfu` – mute users (admins + delegated users).
    - `/unstfu` – unmute users.
    - `/grant_stfu`, `/revoke_stfu`, `/save_grants` – manage delegation.
    - Uses `restrict_chat_member` with `_mute_permissions()` and `_full_permissions()` from `permissions.py`.
    - Tracks grants in `stfu_grants` persisted via `STATE_FILE`.
  - **Armor (“stfuproof”):**
    - `/holycowshithindupajeetarmor` sets a temporary immunity to `/stfu`.
    - Immunity stored in `context.bot_data["stfuproof_immunity"]`.
    - `cmd_stfu` checks this and skips users with still‑valid immunity.
  - **Help / UX:**
    - `/tengriguideme` sends a DM panel (buttons) describing commands and usage.

- Configuration: `config.py`
  - Spam thresholds, mute durations, duration units, etc.
  - Environment variables loaded via `.env`:
    - `TELEGRAM_TOKEN`
    - `TELEGRAM_GROUP`
    - Optional: `STATE_FILE`.

- Deployment:
  - Local: `python bot.py` on MacBook Air.
  - Docker: `docker-compose.yml` with single `tengri-bot` service.

#### 1.2 NSFW Detector

- Repository: `/Users/marcus/Desktop/Github/nsfw_detector`
- Technology: Flask app + Hugging Face `transformers` + PyTorch + `pdf2image` + `python-docx` + `ffmpeg` + poppler + archive tools.
- Purpose: Detect NSFW content in local files, PDFs, videos, archives, and documents.
- Model:
  - Hosted on Hugging Face: `Falconsai/nsfw_image_detection` (based on `google/vit-base-patch16-224-in21k`, a Vision Transformer).
  - Inference via `transformers.pipeline("image-classification", model="Falconsai/nsfw_image_detection", device=-1)` (CPU only).
  - Requires ~2 GB RAM to run the model.
  - First run downloads the model once from Hugging Face; subsequent runs use local cache (`HF_HOME`).

- File types supported:
  - Images (JPG, PNG, WebP, etc.)
  - PDFs
  - Videos (many formats via `ffmpeg`)
  - Archives (zip, rar, 7z, gz, nested archives)
  - Docs: `.doc`, `.docx`

- Key modules:
  - `app.py`:
    - Flask server with:
      - `GET /` → serves `index.html`.
      - `POST /check`:
        - Accepts either:
          - Uploaded file (`file=`), or
          - Server‑side path (`path=`).
        - Uses `magic` to detect MIME type from first 2048 bytes.
        - Maps MIME → extension via `MIME_TO_EXT` (from `config.py`).
        - Routes to appropriate processor using `process_file_by_type`.
        - Returns JSON:
          - Success: `{"status": "success", "filename": "...", "result": {"nsfw": float, "normal": float}}`
          - Errors with `status: "error"` and message.
        - Enforces `MAX_FILE_SIZE` and uses temporary files/dirs with cleanup.
  - `processors.py`:
    - `ModelManager` singleton:
      - Holds `self.pipe` (Hugging Face pipeline).
      - Tracks usage count and periodically reloads model after `reset_threshold`.
    - `process_image(image)`:
      - Takes a Pillow `Image`.
      - Runs classification; extracts scores for labels `"nsfw"` and `"normal"`.
      - Returns `{"nsfw": score, "normal": score}`.
    - `process_pdf_file(pdf_stream)`:
      - Writes a temp PDF; uses `pdf2image.convert_from_path` page‑by‑page.
      - For each page image, calls `process_image`.
      - Early exit if result `nsfw > NSFW_THRESHOLD`.
    - `VideoProcessor` + `process_video_file(path)`:
      - Uses `ffprobe`/`ffmpeg` to get metadata and extract frames (up to `FFMPEG_MAX_FRAMES`).
      - For each frame, calls `process_image`.
      - Early exit if `nsfw > NSFW_THRESHOLD`.
    - `process_doc_file(file_content)`:
      - Uses `antiword` to extract images; runs `process_image` on them.
    - `process_docx_file(file_content)`:
      - Uses `python-docx` to extract embedded images; runs `process_image`.
    - `process_archive(filepath, filename, depth=0, max_depth=100)`:
      - Uses `ArchiveHandler` to list and extract files, including nested archives.
      - Tries images, PDFs, videos, and docs (prioritized).
      - Returns first or last NSFW result.
  - `config.py`:
    - MIME/type mappings and sets of image/video/archive/document MIME types.
    - Defaults:
      - `MAX_FILE_SIZE = 20 * 1024 * 1024 * 1024` (20 GB max file size).
      - `NSFW_THRESHOLD = 0.8`.
      - `FFMPEG_MAX_FRAMES = 20`, `FFMPEG_TIMEOUT = 1800`.
      - Config overrides from `/tmp/config` when present.

- Docker image:
  - `dockerfile` installs Python, system libs (ffmpeg, poppler, unrar, 7z, antiword, etc.), and Python packages.
  - Pre‑downloads the Hugging Face model at build time.
  - Runs `python3 app.py`, exposing port `3333`.

---

### 2. High‑Level Integration Goal

Integrate NSFW detection into Tengri bot so that **any NSFW media posted in the Telegram group is automatically deleted and the sender is muted**, similar to existing spam/media flood behavior.

Target behavior examples:

1. **User sends NSFW sticker 3 times:**
   - First sticker is checked → NSFW → delete + mute (e.g. 60s).
   - Subsequent stickers (if sent before mute took effect) are also deleted and (re)trigger mute.
   - User ends up muted; all NSFW stickers removed.

2. **User sends an explicit porn image:**
   - Photo is checked → NSFW → delete + mute.
   - User is muted; photo removed.

Media types to cover (ideally):
- Stickers
- Photos
- Videos
- Animated GIFs (`animation`)
- Video notes
- Documents (images, PDFs, possibly videos/docs via Telegram `document` messages)

---

### 3. Architectural Options Considered

#### 3.1 Separate Service (HTTP, two processes/containers)

- Keep `nsfw_detector` as its own Flask app.
- Tengri bot calls `POST /check` on the detector service (e.g. `http://nsfw-detector:3333/check`).
- Communication:
  - Bot downloads media from Telegram.
  - Sends file bytes to detector via HTTP.
  - Detector responds with NSFW scores.
  - Bot deletes/mutes based on result.

Pros:
- Minimal changes to detector code.
- Clear service boundaries; easier to scale independently.

Cons:
- Adds HTTP overhead (serialization, TCP, JSON).
- Two processes (bot + detector) to run and monitor.
- Slightly more complex deployment (two containers in Compose, or two separate processes on host).

#### 3.2 Embedded Detector (single process inside Tengri bot) — **Recommended**

- Move/copy detector logic into Tengri bot repository as a local module (e.g. `nsfw/` package).
- Bot calls detector functions directly (no HTTP).
- Model loaded in‑process using Hugging Face `pipeline`.
- All processing (image/video/pdf/archive/doc) handled via in‑process calls and temporary files.

Pros:
- Lower latency (no HTTP, direct function calls).
- Simpler runtime architecture: one process, one container.
- Easier to reason about lifecycle and error handling in one codebase.

Cons:
- Requires refactoring detector code into a library‑style module.
- Adds substantial dependencies (torch, transformers, ffmpeg, etc.) to Tengri bot image/env.

#### 3.3 Single Repo, Two Services (monorepo)

- Both tengri‑bot and nsfw_detector live in the same repository but remain separate services (still HTTP).
- Single `docker-compose.yml` orchestrates both.

Pros:
- Code co‑located.
- Each app remains largely unchanged.

Cons:
- Still two processes/containers; overhead similar to option 3.1.

Overall recommendation:
- For **operational and performance efficiency**, prefer **Embedded Detector (3.2)**.
- For minimal change to detector code, 3.1 or 3.3 are alternatives, but less efficient.

---

### 4. Embedded Integration – Recommended Design

#### 4.1 Repository Layout (conceptual)

Inside `tengri-bot` repo, introduce a subpackage for NSFW detection:

```text
tengri-bot/
  bot.py
  spam.py
  config.py
  handlers/
  nsfw/
    __init__.py
    config.py          # detector-specific config
    processors.py      # ported from nsfw_detector
    utils.py           # archive helpers, etc.
  requirements.txt
  Dockerfile
  ...
```

Key idea: reuse existing `processors.py` logic from nsfw_detector, but adapt it to be imported and called from Tengri bot instead of via Flask.

#### 4.2 New/Extended Config

In Tengri’s `config.py` (or a dedicated `nsfw/config.py`), define:

- `NSFW_ENABLED = True` (feature flag, optional).
- `NSFW_THRESHOLD` (can reuse detector’s threshold; e.g. 0.8).
- Optional:
  - `NSFW_MUTE_SECONDS` (how long to mute for NSFW).
  - Limits for file sizes or per‑user checks to avoid abuse.

System-level requirements for Dockerfile:
- `ffmpeg`, `poppler-utils`, `antiword`, `unrar`, `p7zip-full`, `p7zip-rar`, `libmagic`, etc.
- Python packages:
  - `torch` (CPU wheel).
  - `transformers`.
  - `Pillow`.
  - `pdf2image`.
  - `python-docx`.
  - `python-magic`.
  - `rarfile`, `py7zr`, etc.

Hugging Face cache dir:
- Set `HF_HOME` or allow defaults (e.g. `/root/.cache/huggingface` in Docker).

#### 4.3 Bot → Detector Call Flow

Extend `spam.py::handle_message_or_media`:

1. For media types (pseudocode):

   - Stickers (`message.sticker`)
   - Photos (`message.photo`)
   - Videos (`message.video`)
   - Video notes (`message.video_note`)
   - Animations/GIFs (`message.animation`)
   - Documents (`message.document`) – where the MIME/extension suggests image/video/PDF/doc.

2. Steps per media message:

   - Check that message is in the target group (`bot_data["target_group"]`).
   - Download the file via `await context.bot.get_file(file_id)` and `download_to_memory()` or to a temp file.
   - For:
     - Images/stickers/animations: wrap bytes in `io.BytesIO`, open via `PIL.Image.open`, call `process_image(image)`.
     - Videos: write to temp file; call `process_video_file(path)`.
     - PDFs: pass bytes to `process_pdf_file(pdf_stream)`.
     - Docs: `.doc`/`.docx` pass bytes to `process_doc_file`/`process_docx_file`.
     - Others: optionally skip.
   - Run detector in a worker thread to avoid blocking the async event loop:
     - `result = await asyncio.to_thread(nsfw_process_function, ...)`.
   - If `result` exists and `result["nsfw"] > NSFW_THRESHOLD`:
     - Delete the message.
     - Mute the user for NSFW (reuse or configure a duration; likely same as spam, 60s).
     - Send a warning message (can reuse spam_warning or add NSFW-specific messages).
     - Schedule auto‑delete of the warning after 30 seconds via `_schedule_notification_delete`.
     - Return early (do not further process this message).
   - Else (not NSFW):
     - Continue with normal spam/media flood logic:
       - For stickers/animations → `handle_media_flood`.
       - For text → `handle_message`.

3. Error handling:
   - If detector errors (exception, model unavailable, etc.):
     - Log the error.
     - Optionally treat the message as not NSFW and continue with spam/media flood rules only.

#### 4.4 Concurrency and Thread-Safety

To ensure safe concurrent NSFW checks:
- `ModelManager` in `processors.py` already centralizes pipeline management.
- Add a simple lock around model inference if needed:
  - E.g., a `threading.Lock` or `asyncio.Lock` used inside a sync function (via `to_thread`).
- Use `asyncio.to_thread` to offload blocking I/O + compute to a thread pool, so the async `python-telegram-bot` event loop is not blocked.

#### 4.5 Behavior Integration with Existing Mutes

- NSFW mutes:
  - Use the same `_mute_permissions()` as spam/stfu.
  - Use a similar mute duration (`MUTE_SECONDS` or `NSFW_MUTE_SECONDS`).
- Interaction with “stfuproof”:
  - Decide whether NSFW‑based mutes should respect stfuproof immunity.
  - Safer default: **NSFW mutes ignore stfuproof**, since NSFW is a stronger violation than general muting. If desired, reuse the immunity check from `cmd_stfu`.

---

### 5. Deployment & Resource Considerations

- **Environment:**
  - Current deployment: MacBook Air (local), plus Docker support.
  - NSFW model memory usage: ~2 GB RAM.
  - Tengri bot itself uses relatively little (tens of MBs).
  - Combined local usage: roughly 2–2.5 GB RAM is sufficient; 8 GB RAM MacBook Air is workable, 16 GB is more comfortable.

- **Self-contained AI:**
  - Model is downloaded once from Hugging Face (`Falconsai/nsfw_image_detection`).
  - After initial download, inference runs fully locally (no external calls).
  - No API keys required for detection.

- **Offline capability:**
  - After model cache is populated, both tengri‑bot and NSFW detection can run offline (beyond needing internet for Telegram itself).

---

### 6. Credentials and Configuration Needed from User

Already used by Tengri bot:
- `TELEGRAM_TOKEN` – from BotFather.
- `TELEGRAM_GROUP` – integer chat ID of the target group.
- Optional: `STATE_FILE` – for persistent `/stfu` grants.

For NSFW integration:
- `NSFW_THRESHOLD` (optional override; default 0.8).
- Optional:
  - `NSFW_ENABLED` boolean.
  - `NSFW_MUTE_SECONDS` if different from existing `MUTE_SECONDS`.

No additional cloud tokens/credentials required; NSFW detection is local.

---

### 7. Complexity and Confidence

- **Complexity:** Medium.
  - Estimated 1–2 days of focused engineering work for someone familiar with both codebases.
  - Main buckets of work:
    - Refactor/copy detector logic into a local `nsfw/` package.
    - Wire media message handling in `spam.py` to call the detector.
    - Extend Dockerfile + requirements to include the new dependencies.
    - Handle temp file lifecycle for video/PDF/archive/doc inputs.
    - Add configuration and basic tests/manual verification.

- **Confidence of success:** ~85–90%.
  - The detector code is already modular (`processors.py`).
  - Telegram media can be cleanly mapped to the detector’s expected inputs.
  - The main risks (thread safety, dependency setup, model load time) are well understood and have straightforward mitigations.

---

### 8. Quick Summary for Another AI/Engineer

1. **Goal:** Integrate an existing local NSFW image/video/PDF/archive/doc classifier (from `nsfw_detector`) into the `tengri-bot` Telegram anti‑spam bot so that NSFW content in a specific group is automatically deleted and its sender muted.
2. **Current state:**
   - Tengri bot already does:
     - Text spam detection.
     - Media flood detection (stickers/GIFs).
     - Manual mute/unmute commands with delegation and armor.
   - NSFW detector already does:
     - NSFW classification for images, PDFs, videos, archives, and docs via a Flask API.
3. **Chosen architecture:** Embedded detector.
   - Bring the detector’s `processors.py`/`config.py`/`utils.py` into a `nsfw/` package inside Tengri’s repo.
   - Call detector functions directly from `spam.py` for media messages, using `asyncio.to_thread` for blocking work.
4. **Behavior:** For any media (photo, sticker, GIF, video, doc, etc.) in the target group:
   - Download it.
   - Run NSFW detection.
   - If `nsfw > threshold`:
     - Delete the message.
     - Mute the sender for a configured duration.
     - Send an auto‑deleted warning.
   - Else:
     - Proceed with existing spam/media flood logic.
5. **Constraints:**
   - Must run on a MacBook Air and in Docker.
   - Detector model uses ~2 GB RAM, but everything else is light.
   - Internet only required once to download the Hugging Face model.
6. **Inputs needed from user:**
   - Existing: `TELEGRAM_TOKEN`, `TELEGRAM_GROUP`.
   - New optional: `NSFW_THRESHOLD`, `NSFW_MUTE_SECONDS`, `NSFW_ENABLED`.

This document should give enough context for another AI/engineer to design concrete code changes and implement/test the integration.

