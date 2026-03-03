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

Media types to cover (initial scope):
- Stickers (WebP/PNG)
- Photos (Telegram photos)
- Videos (Telegram videos)
- Animated GIFs (`animation`)

Out of scope for the first implementation (can be added later in a follow‑up phase if desired):
- Video notes
- PDFs
- Archives
- Office docs (`.doc`, `.docx`, etc.)

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
- All processing (images, GIFs, stickers, and videos; optionally extended later) handled via in‑process calls and temporary files.

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

- `NSFW_ENABLED = True` (feature flag).
- Two strictness modes:
  - `NSFW_MODE = "normal"` by default (allowed: `"normal"`, `"strict"`).
  - `NSFW_THRESHOLD_NORMAL = 0.8`.
  - `NSFW_THRESHOLD_STRICT = 0.7`.
- A helper to pick the active threshold:
  - `get_nsfw_threshold(mode: str) -> float` that returns the appropriate value.
- `NSFW_MUTE_SECONDS`:
  - Configurable, **default = 600 seconds (10 minutes)**.
- Optional safety/abuse limits:
  - Per‑file size limit for Telegram downloads (e.g. rely on Telegram’s own or add local cap).
  - Per‑user rate limiting for NSFW checks if needed in the future.

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

Extend `spam.py::handle_message_or_media` with the following order of operations for relevant media:

1. **Order of operations (per incoming update in the target group):**
   1. Check `NSFW_ENABLED`. If `False`, skip NSFW detection and proceed with current logic.
   2. If message contains one of:
      - Sticker (`message.sticker`; WebP/PNG → convert to `PIL.Image`).
      - Photo (`message.photo`; choose largest size → `PIL.Image`).
      - Animation/GIF (`message.animation`; treat as short video or extract first frame via ffmpeg).
      - Video (`message.video`; pass as video file to detector).
   3. Run NSFW detection first (see below).
   4. If NSFW:
      - Delete message.
      - Mute user for `NSFW_MUTE_SECONDS` (default 10 minutes).
      - Send NSFW warning message (separate from spam warning, or reuse if desired).
      - Schedule auto‑delete of warning after 30 seconds via `_schedule_notification_delete`.
      - **Return early** – do not run spam/media flood logic for this message.
   5. If **not** NSFW:
      - Fall through to existing behavior:
        - Stickers/animations → `handle_media_flood`.
        - Text → `handle_message`.

2. **Detector call details (per media):**

   - Only run NSFW detector in the configured target group (`bot_data["target_group"]`).
   - Download the file via `await context.bot.get_file(file_id)`:
     - For images/stickers/animations:
       - Download to memory (`BytesIO`), open via `PIL.Image.open`, call `process_image(image)`.
     - For videos:
       - Download to a temp file, call `process_video_file(temp_path)` (from `processors.py`).
   - Run detector in a worker thread to avoid blocking the async event loop:
     - `result = await asyncio.to_thread(nsfw_process_function, ...)`.
   - Determine threshold from mode:
     - `threshold = get_nsfw_threshold(NSFW_MODE)` (normal/strict).
   - If `result` exists and `result["nsfw"] > threshold`:
     - Treat as NSFW and perform the actions in step 1.4 above.

3. **Error handling and timeouts (fail‑open):**
   - Enforce per‑message time limits for detection:
     - Images/stickers/GIFs: target ≤ ~3 seconds.
     - Videos: target ≤ ~10–15 seconds for short clips.
   - If the detection call:
     - Raises an exception, or
     - Exceeds an internal timeout,
     - Then:
       - Log at warning or error level with user/chat/media info.
       - **Fail open**: treat as “not NSFW” and continue with normal spam/media flood rules only.

#### 4.4 Concurrency and Thread-Safety

To ensure safe concurrent NSFW checks:
- `ModelManager` in `processors.py` already centralizes pipeline management.
- Guard inference with a single process‑wide lock:
  - Introduce a `threading.Lock` in the NSFW module and acquire it around `pipe(image)` / other model calls.
- Always invoke detection via `asyncio.to_thread` to offload blocking I/O + compute to a thread pool, so the async `python-telegram-bot` event loop is never blocked by model inference.

#### 4.5 Behavior Integration with Existing Mutes

- NSFW mutes:
  - Use the same `_mute_permissions()` as spam/stfu.
  - Use `NSFW_MUTE_SECONDS` (default 10 minutes), independent of spam mute duration (`MUTE_SECONDS`).
- If the user is already muted:
  - Use the **maximum** of existing mute expiry and new NSFW mute expiry (i.e. NSFW can only extend, never shorten).
- Interaction with “stfuproof”:
  - **NSFW mutes always override armor**:
    - Even if a user has active stfuproof (`/holycowshithindupajeetarmor`), NSFW detection still deletes the media and mutes the user.
    - Armor only protects against `/stfu` invocations, not NSFW enforcement.

---

### 5. Deployment & Resource Considerations

- **Environment:**
  - Primary target deployment: **Docker Compose**, with a single `tengri-bot` service that includes the embedded NSFW detector.
  - Still runnable locally on macOS via `python bot.py` as long as system dependencies are installed.
  - NSFW model memory usage: ~2 GB RAM.
  - Tengri bot itself uses relatively little (tens of MBs).
  - Combined local usage: roughly 2–2.5 GB RAM is sufficient; 8 GB RAM MacBook Air is workable, 16 GB is more comfortable.

- **Self-contained AI:**
  - Model is downloaded once from Hugging Face (`Falconsai/nsfw_image_detection`).
  - After initial download, inference runs fully locally (no external calls).
  - No API keys required for detection.
  - Expect slower cold start on first use:
    - Initial model download (if cache empty).
    - Initial model load into memory (can take several seconds).
  - Option: either load model eagerly at startup or lazily on first NSFW check; recommended to load lazily but log clearly when this happens.

- **Offline capability:**
  - After model cache is populated, both tengri‑bot and NSFW detection can run offline (beyond needing internet for Telegram itself).

---

### 6. Credentials and Configuration Needed from User

Already used by Tengri bot:
- `TELEGRAM_TOKEN` – from BotFather.
- `TELEGRAM_GROUP` – integer chat ID of the target group.
- Optional: `STATE_FILE` – for persistent `/stfu` grants.

For NSFW integration:
- `NSFW_ENABLED` (boolean, default `True`).
- `NSFW_MODE` (string, default `"normal"`, alternative `"strict"`).
- `NSFW_THRESHOLD_NORMAL` and `NSFW_THRESHOLD_STRICT` (default 0.8 and 0.7, respectively).
- `NSFW_MUTE_SECONDS` (default 600 seconds / 10 minutes).

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

1. **Goal:** Integrate an existing local NSFW image/GIF/sticker/video classifier (from `nsfw_detector`) into the `tengri-bot` Telegram anti‑spam bot so that NSFW media in a specific group is automatically deleted and its sender muted.
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
4. **Behavior:** For any relevant media (photo, sticker, GIF/animation, video) in the target group:
   - Download it.
   - Run NSFW detection with the active threshold (normal/strict).
   - If `nsfw > threshold`:
     - Delete the message.
     - Mute the sender for `NSFW_MUTE_SECONDS` (default 10 minutes), extending any existing mute.
     - Send an auto‑deleted warning.
     - Ignore armor (`/holycowshithindupajeetarmor`) for NSFW enforcement.
   - Else:
     - Proceed with existing spam/media flood logic.
5. **Constraints:**
   - Must run on a MacBook Air and in Docker.
   - Detector model uses ~2 GB RAM, but everything else is light.
   - Internet only required once to download the Hugging Face model.
- 6. **Inputs needed from user:**
   - Existing: `TELEGRAM_TOKEN`, `TELEGRAM_GROUP`.
   - New: `NSFW_ENABLED`, `NSFW_MODE` (normal/strict), `NSFW_MUTE_SECONDS` (default 600s).

This document should give enough context for another AI/engineer to design concrete code changes and implement/test the integration.

---

### 9. Rollout, Logging, and Testing Strategy

- **Rollout:**
  - NSFW enforcement is enabled immediately (no dry‑run phase) once deployed.
  - The bot owner will initially deploy and test in a separate, non‑production group chat to validate behavior before enabling in the main group.

- **Logging (verbose for debugging):**
  - Log at least one line per NSFW check (at debug or info level) with:
    - Chat ID, user ID, media type, NSFW and normal scores, mode, and decision (NSFW/not).
  - Log warnings/errors for:
    - Detection failures (exceptions, timeouts).
    - Model load issues.
  - Allow logging level to be tuned via env or config, but default to “verbose” during initial rollout.

- **Manual test cases (non‑exhaustive):**
  - Clearly NSFW image → must be deleted + user muted for ~10 minutes.
  - Clearly safe image → must remain; only spam/media flood rules apply.
  - Very borderline content (e.g. swimsuit) → verify behavior under both `normal` and `strict` modes.
  - NSFW sticker and NSFW GIF/animation → deleted + muted.
  - Short NSFW video clip → deleted + muted; processing time within expected bounds.
  - A few random benign stickers/GIFs/videos to confirm false positive rate is acceptable.
  - Behavior when detector fails (e.g. simulate exception) → message left to normal spam/media flood logic; errors logged.
