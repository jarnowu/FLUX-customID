FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir torch==2.4.0 torchvision==0.19.0 --extra-index-url https://download.pytorch.org/whl/cu118

# Install project requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt huggingface-hub runpod && \
    pip3 install --no-cache-dir --upgrade pip setuptools wheel

# Copy project files
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8000/health')"

# RunPod entry point
CMD [ "python3", "-m", "runpod.serverless.worker", "--handler-path", "/app/handler.py", "--log-level", "debug" ]
