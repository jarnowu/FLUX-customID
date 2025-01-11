FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3.10 python3-pip && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir torch==2.4.0 torchvision==0.19.0 --extra-index-url https://download.pytorch.org/whl/cu118

# Install project requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt huggingface-hub runpod

# Download model checkpoints
RUN mkdir -p pretrained_ckpt && \
    cd pretrained_ckpt && \
    huggingface-cli download --resume-download "laion/CLIP-ViT-H-14-laion2B-s32B-b79K" --local-dir openclip-vit-h-14 && \
    huggingface-cli download --resume-download "black-forest-labs/FLUX.1-dev" --local-dir flux.1-dev && \
    huggingface-cli download --resume-download "Damo-vision/FLUX-customID" --local-dir . --include="*.pt"

# Copy project files
COPY . .

# RunPod entry point
CMD [ "python3", "-m", "runpod.serverless.worker", "--handler-path", "/app/handler.py" ]
