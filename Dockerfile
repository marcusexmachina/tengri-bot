FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app

# Base system deps (build-essential for some pip wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Optional: NSFW deps (~4GB). Only when building with --build-arg INSTALL_NSFW=true
ARG INSTALL_NSFW=false
COPY requirements-nsfw.txt ./
RUN if [ "$INSTALL_NSFW" = "true" ]; then \
    apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg poppler-utils unrar-free p7zip-full antiword \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements-nsfw.txt; \
    fi \
    && rm -f requirements-nsfw.txt

COPY bot.py config.py commands_menu.py responses.py utils.py permissions.py resolvers.py grants.py spam.py state.py reputation_thresholds.py README.md config.json ./
COPY handlers/ handlers/
COPY nsfw/ nsfw/

CMD ["python", "bot.py"]

