# ---- Base image
FROM python:3.11-slim

# ---- System deps (optional but helpful)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# ---- Workdir
WORKDIR /app

# ---- Copy and install deps first (better caching)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy app
COPY app.py ./app.py

# ---- Streamlit config (avoid asking to open browser)
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_PORT=8501

# ---- Expose + run
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
