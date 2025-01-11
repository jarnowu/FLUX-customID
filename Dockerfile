# Builder stage
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04 as builder

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
WORKDIR /build

# Install Python and build dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch and requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir torch==2.4.0 torchvision==0.19.0 --extra-index-url https://download.pytorch.org/whl/cu118 && \
    pip3 install --no-cache-dir -r requirements.txt huggingface-hub runpod && \
    pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Final stage
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install Python and runtime dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy only necessary project files
COPY handler.py .
COPY src ./src

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')"

# RunPod entry point
CMD [ "python3", "-m", "runpod.serverless.worker", "--handler-path", "/app/handler.py", "--log-level", "debug" ]
