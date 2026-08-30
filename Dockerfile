FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Install system dependencies for Camoufox / Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user (Hugging Face requirement)
RUN useradd -m -u 1000 user
WORKDIR /home/user/app

# Install Python requirements
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Download Camoufox browser binaries. HOME points at the runtime user's home;
# give that user ownership so browser startup also works on Render.
RUN python -m camoufox fetch && chown -R user:user /home/user

# Copy project files
COPY --chown=user:user . .

# Switch to non-root user
USER user

# Expose port 7860 for Hugging Face
EXPOSE 7860

# Start LMArenaBridge
CMD ["python", "-m", "src.main"]

