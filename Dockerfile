FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app

# System deps: build-essential for pip; ffmpeg/poppler for NSFW (video/PDF)
# unrar-free provides unrar command (Debian dropped proprietary unrar)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    poppler-utils \
    unrar-free \
    p7zip-full \
    antiword \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py config.py responses.py utils.py permissions.py resolvers.py grants.py spam.py state.py reputation_thresholds.py README.md config.json ./
COPY handlers/ handlers/
COPY nsfw/ nsfw/

CMD ["python", "bot.py"]

