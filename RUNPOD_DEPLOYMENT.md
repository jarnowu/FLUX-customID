# FLUX-customID RunPod Serverless Deployment Guide

## Prerequisites
- RunPod account
- GitHub account
- Repository access to https://github.com/jarnowu/FLUX-customID.git
- NVIDIA GPU (16GB+ VRAM recommended)

## Important Note
This guide focuses on deploying via RunPod's GitHub integration, which is the recommended deployment method. RunPod manages the container registry and docker build process, enabling:
- Automatic code and Dockerfile pulls
- Container image building with layer caching
- Secure container registry storage
- Seamless endpoint deployment

## Deployment Steps

### 1. Connect GitHub to RunPod
1. Go to RunPod's Serverless section
2. Click "+ New Endpoint"
3. Choose "GitHub Repo"
4. Authorize RunPod's GitHub integration:
   - You can authorize through settings page or during first deployment
   - Choose between "All repositories" or "Only select repositories"
   - Only one GitHub account can be connected per RunPod account
5. Select the FLUX-customID repository (https://github.com/jarnowu/FLUX-customID.git)

### 2. Configure Deployment
- **Branch**: Select your deployment branch (e.g., main)
- **Dockerfile Path**: `Dockerfile` (root directory)
- **Environment Variables**: None required

Note: Your first build will take some time, but subsequent builds will be faster due to RunPod's intelligent layer caching.

### Model Storage Setup
Before deploying the endpoint, you need to set up persistent storage for the models:

1. Create a RunPod Storage Volume:
   - Go to Storage > New Volume
   - Name: flux-models
   - Size: 80GB minimum (required for all models):
     - CLIP model: ~15GB
     - FLUX.1-dev: ~54GB
     - FLUX-customID: ~3.4GB
   - Container Path: /workspace (IMPORTANT: This exact path is required)

Note: The /workspace path is critical as the handler expects models in specific locations:
- /workspace/pretrained_ckpt/flux.1-dev/
- /workspace/pretrained_ckpt/openclip-vit-h-14/
- /workspace/pretrained_ckpt/FLUX-customID.pt

2. Create a One-Time Pod:
   - Select any GPU (e.g., NVIDIA A5000)
   - Attach the created volume to /workspace
   - Start the pod and open the terminal

3. Install and Configure Hugging Face CLI:
   ```bash
   # Install huggingface-hub
   pip install --user huggingface-hub

   # Add to PATH
   export PATH="/root/.local/bin:$PATH"

   # Login to Hugging Face (replace with your token)
   huggingface-cli login --token hf_xxxxxxxxxxxxxxxxxxxx
   ```

4. Download Models to Volume:
   ```bash
   # Create directory for models
   cd /workspace
   mkdir -p pretrained_ckpt
   cd pretrained_ckpt

   # Download CLIP model (~15GB)
   huggingface-cli download --resume-download "laion/CLIP-ViT-H-14-laion2B-s32B-b79K" --local-dir openclip-vit-h-14

   # Download FLUX.1-dev model (~54GB)
   huggingface-cli download --resume-download "black-forest-labs/FLUX.1-dev" --local-dir flux.1-dev

   # Download FLUX-customID model (~3.4GB)
   huggingface-cli download --resume-download "Damo-vision/FLUX-customID" --local-dir . --include="*.pt"
   ```

   Note: The FLUX.1-dev model requires Hugging Face authentication. You can get your token from https://huggingface.co/settings/tokens

5. Verify Downloads:
   ```bash
   # Check space usage
   df -h
   du -sh /workspace/pretrained_ckpt/*
   ```

6. Configure Endpoint:
   - When creating serverless endpoint, attach the volume
   - Mount path: /workspace
   
Note: RunPod handles all aspects of volume mounting automatically at runtime, including directory creation. No special configuration is needed in the Dockerfile.

The Dockerfile should contain:
```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y python3.10 python3-pip && rm -rf /var/lib/apt/lists/*

# Install PyTorch with CUDA support
RUN pip3 install --no-cache-dir torch==2.4.0 torchvision==0.19.0 --extra-index-url https://download.pytorch.org/whl/cu118

# Install project requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt huggingface-hub runpod

# Copy project files
COPY . .

# RunPod entry point
CMD [ "python3", "-m", "runpod.serverless.worker", "--handler-path", "/app/handler.py" ]
```

This Dockerfile:
- Uses CUDA runtime base image for smaller size
- Installs Python 3.10 and pip
- Sets up PyTorch with CUDA support
- Installs project requirements including runpod
- Sets up the RunPod serverless worker

Note: Models are not downloaded during container build but are accessed from the mounted volume, which:
- Speeds up deployments significantly
- Makes builds more reliable
- Reduces bandwidth usage
- Improves cold start times

### 7. Configure Compute
Recommended settings:
- **GPU**: NVIDIA A5000 or better
- **Container Disk**: 20GB
- **Scale to Zero**: Enabled
- **Idle timeout**: 5 minutes
- **Min Instances**: 0
- **Max Instances**: Based on your needs
- **Volume**: Attach flux-models volume at /workspace

Note: Ensure the volume containing the models is attached to enable the endpoint to access the required model files.

## API Schema

### Input Format
```json
{
  "input": {
    "image": "base64_encoded_image_string",
    "prompt": "string",
    "num_samples": "integer (optional, default: 1, max: 4)",
    "height": "integer (optional, default: 1024, range: 512-2048)",
    "width": "integer (optional, default: 1024, range: 512-2048)",
    "seed": "integer (optional)",
    "num_inference_steps": "integer (optional, default: 28, range: 1-50)",
    "guidance_scale": "float (optional, default: 3.5, range: 1.0-20.0)"
  }
}
```

### Output Format
```json
{
  "status": "success|error",
  "output": ["base64_encoded_image_string", ...],
  "metrics": {
    "process_time": "float",
    "num_samples": "integer",
    "image_size": "string"
  }
}
```

### Error Response
```json
{
  "status": "error",
  "error": "error_message"
}
```

## Testing and Troubleshooting

### Testing the Endpoint
1. Once deployed, get your endpoint URL from RunPod dashboard
2. Test using the following curl command (replace with your endpoint URL):
```bash
curl -X POST "https://your-endpoint.runpod.net" \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "image": "base64_encoded_image",
         "prompt": "professional ID photo"
       }
     }'
```

### Common Issues and Solutions

1. Worker Initialization Failures:
   - Check logs for "Workspace directory not found" - Ensure volume is mounted at /workspace
   - Check logs for "Required model file/directory not found" - Verify all models are in correct paths
   - Check CUDA/GPU availability in logs
   - Verify model file permissions

2. Request Timeouts:
   - Increase worker timeout settings if needed
   - Monitor GPU memory usage
   - Check for model loading delays

3. Image Processing Errors:
   - Verify input image format (supported: JPEG, JPG, PNG, WEBP)
   - Check image dimensions (max: 2048x2048)
   - Monitor temp directory space

### Log Monitoring
The worker now provides detailed logging at each initialization step:
- Workspace directory verification
- Model path validation
- Transformer loading
- Pipeline initialization
- Model initialization

Monitor these logs in the RunPod dashboard for troubleshooting.

## Monitoring and Build Status
Monitor your deployment in the RunPod dashboard. The worker provides detailed logging for debugging. Builds can have the following statuses:
- **Building**: Container is currently building
- **Failed**: Build failed - check logs for details
- **Pending**: Build is scheduled
- **Uploading**: Container is uploading to registry
- **Completed**: Build and upload successful

You can:
- Monitor builds in the RunPod dashboard
- View logs for debugging
- Track GPU utilization and costs

## Multiple Environments (Optional)
You can maintain separate environments by:
1. Cloning your endpoint
2. Connecting different branches (e.g., main for production, dev for staging)
3. Configuring separate GPU and worker settings per environment

## Best Practices
1. Keep container size optimized
2. Monitor cold start performance
3. Adjust compute settings based on usage
4. Use appropriate timeout settings
5. Monitor costs and adjust scaling accordingly
6. Regularly check worker logs for issues
7. Verify model file integrity after volume updates
8. Monitor GPU memory usage
9. Keep track of request latencies
10. Set up alerts for worker failures
