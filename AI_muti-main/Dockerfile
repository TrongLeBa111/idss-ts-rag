# ============================================================
# Dockerfile — IDSS Backend Pipeline
# Base image: python:3.11-slim  (~50MB, không CUDA)
# Final image: ~400MB total
#
# Build:  docker build -t idss-pipeline .
# Run:    docker run --rm -v %cd%/data:/app/data idss-pipeline
# ============================================================

FROM python:3.11-slim

# --- System dependencies (chỉ cần libgomp cho FAISS) ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# --- Working directory ---
WORKDIR /app

# --- Install Python dependencies TRƯỚC khi copy source ---
# (Layer caching: chỉ re-install khi requirements thay đổi)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Copy source code ---
COPY src/              ./src/
COPY tests/            ./tests/
COPY web_dashboard/    ./web_dashboard/
COPY main_pipeline.py .
COPY .env.example  .

# --- Runtime directories (mounted as volume in production) ---
RUN mkdir -p data/raw data/processed data/vector_db logs

# --- Default command: chạy full pipeline ---
CMD ["python", "main_pipeline.py"]

# --- Optional: override để chạy Streamlit dashboard ---
# CMD ["streamlit", "run", "web_dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]