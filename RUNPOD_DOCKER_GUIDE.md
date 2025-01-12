# RunPod BYOC (Bring Your Own Container) Deployment Guide for FLUX-customID

This guide covers deploying FLUX-customID using RunPod's BYOC (Bring Your Own Container) workflow, which allows you to build and run your own Docker containers on RunPod's infrastructure.

## Prerequisites
- Docker installed on your machine
- RunPod account with credits
- Docker Hub account
- NVIDIA GPU (local) for testing
- Hugging Face account (for model access)

## Important Notes
- RunPod BYOC requires completely isolated container environments
- All dependencies must be included in the container
- Network Volumes are used for persistent model storage
- Container must include RunPod's serverless handler

## 1. Prepare Docker Environment

1. Clone the repository:
```bash
git clone https://github.com/jarnowu/FLUX-customID.git
cd FLUX-customID
```

2. Login to Docker Hub:
```bash
docker login
```

## 2. Build and Test Docker Image

1. Build the image locally:
```bash
# Replace 'yourusername' with your Docker Hub username
docker build -t yourusername/flux-customid:latest .
```

2. Test locally (required for RunPod validation):
```bash
# Create test directory for models
mkdir -p test_workspace/pretrained_ckpt

# Run container with test volume
docker run --gpus all \
  -v $(pwd)/test_workspace:/workspace \
  -e PYTHONUNBUFFERED=1 \
  -e CUDA_VISIBLE_DEVICES=0 \
  -p 8000:8000 \
  yourusername/flux-customid:latest

# Expected output should show:
# - "Starting Serverless Worker"
# - Model initialization logs
# - Health check endpoint available
```

Key Test Points:
- Verify handler initialization
- Check model loading process
- Confirm GPU access
- Test input/output format
- Validate error handling

3. Verify RunPod Requirements:
   - Handler initialization succeeds
   - Worker starts successfully
   - Input validation works
   - Error handling functions
   - Memory cleanup occurs
   - Health check responds

4. Push to Docker Hub:
```bash
docker push yourusername/flux-customid:latest
```

Required RunPod Components:
- CUDA-compatible base image (nvidia/cuda)
- Python runpod package installed
- Handler implementing RunPod's serverless pattern:
  ```python
  def handler(event):
      try:
          # Input validation
          input_data = event.get("input", {})
          if not input_data:
              return {"error": "No input provided"}
          
          # Process request
          result = process_request(input_data)
          
          # Return in required format
          return {
              "status": "success",
              "output": result
          }
      except Exception as e:
          return {
              "status": "error",
              "error": str(e)
          }
  ```
- Proper initialization:
  ```python
  runpod.serverless.start({
      "handler": handler,
      "init": init,
      "return_aggregate_errors": True
  })
  ```

## 3. Set Up RunPod Network Volume

RunPod uses Network Volumes for persistent storage across container instances. This is crucial for:
- Storing large model files
- Persisting data between container restarts
- Sharing data across multiple endpoints

1. Create Network Volume:
   - Go to RunPod → Storage → New Volume
   - Name: flux-models
   - Size: 80GB (minimum for required models)
   - Path: /workspace (must match handler configuration)
   
Note: Network Volumes are separate from container storage and persist independently

2. Download Models to Volume:
```bash
# Create temporary pod with volume mounted
# In pod terminal:

pip install --user huggingface-hub
export PATH="/root/.local/bin:$PATH"

# Login to Hugging Face
huggingface-cli login --token your_token_here

# Download models
cd /workspace
mkdir -p pretrained_ckpt
cd pretrained_ckpt

# CLIP model
huggingface-cli download --resume-download \
  "laion/CLIP-ViT-H-14-laion2B-s32B-b79K" \
  --local-dir openclip-vit-h-14

# FLUX.1-dev model
huggingface-cli download --resume-download \
  "black-forest-labs/FLUX.1-dev" \
  --local-dir flux.1-dev

# FLUX-customID model
huggingface-cli download --resume-download \
  "Damo-vision/FLUX-customID" \
  --local-dir . \
  --include="*.pt"
```

## 4. Create RunPod Template

A template defines how your container will run on RunPod's infrastructure.

1. Go to RunPod → Templates → New Template

2. Configure Template:
```yaml
Name: flux-customid
Image: yourusername/flux-customid:latest
Container Disk: 20GB  # Separate from Network Volume
Volume: /workspace    # Mount point for Network Volume
Environment Variables:
  - PYTHONUNBUFFERED=1            # Required for proper logging
  - CUDA_VISIBLE_DEVICES=0        # Required for GPU access
  - HUGGING_FACE_HUB_TOKEN=your_token_here  # If needed for model downloads
Docker Command: python3 -m runpod.serverless.worker --handler-path /app/handler.py --log-level debug
Health Check:  # Required for container health monitoring
  - Port: 8000
  - Path: /health
  - Initial Delay: 30s  # Allow time for model loading
  - Interval: 30s
  - Timeout: 30s
  - Retries: 3
```

Container Requirements:
- Must be self-contained with all dependencies
- Must expose health check endpoint
- Must handle GPU access properly
- Must implement RunPod's serverless handler pattern

Important Notes:
- The handler expects models in specific paths under /workspace
- Health checks ensure container readiness
- Debug logging helps troubleshoot issues
- CUDA device configuration is critical

## 5. Deploy Endpoint

RunPod serverless endpoints automatically scale based on demand.

1. Go to RunPod → Serverless → New Endpoint

2. Configure:
```yaml
Template: Your created template
GPU: NVIDIA A5000 or better
Container Disk: 20GB
Volume: flux-models mounted at /workspace
Advanced Configuration:
  - Min Instances: 0  # Scale to zero when idle
  - Max Instances: As needed  # Based on your concurrent request needs
  - Idle Timeout: 5 minutes  # Time before scaling down
  - Flash Boot: Enabled  # Faster container startup
  - Advanced Routing: Disabled  # Unless using custom domains
  - Worker Timeout: 300s  # Adjust based on model inference time
```

Deployment Checklist:
- Volume is properly mounted
- GPU is correctly specified
- Worker timeout matches your workload
- Flash boot is enabled for faster scaling
- Container health checks are configured

## 6. Test Deployment

After deployment, verify your endpoint is working correctly:

1. Basic Health Check:
```python
import requests

# Your RunPod endpoint URL
url = "https://your-endpoint.runpod.net/health"
response = requests.get(url)
print(f"Health check status: {response.status_code}")
```

2. Test Inference:
```python
import requests
import base64
import time

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def test_endpoint(url, image_path):
    try:
        # Prepare request
        payload = {
            "input": {
                "image": encode_image(image_path),
                "prompt": "professional ID photo",
                "num_samples": 1
            }
        }
        
        # Send request
        start_time = time.time()
        response = requests.post(url, json=payload)
        process_time = time.time() - start_time
        
        # Handle response
        if response.status_code == 200:
            result = response.json()
            if result["status"] == "success":
                print(f"Success! Processing time: {process_time:.2f}s")
                # Save result
                img_data = base64.b64decode(result["output"][0])
                with open("result.png", "wb") as f:
                    f.write(img_data)
            else:
                print(f"Error: {result.get('error')}")
        else:
            print(f"HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"Test failed: {str(e)}")

# Test your endpoint
test_endpoint("https://your-endpoint.runpod.net", "test.jpg")
```

Verify These Points:
- Health check responds correctly
- Model loads successfully
- Input validation works
- Error handling functions
- Response format is correct
- Processing time is acceptable

## Maintenance & Updates

1. Update image:
```bash
# Build new version
docker build -t yourusername/flux-customid:latest .

# Push update
docker push yourusername/flux-customid:latest

# Update RunPod endpoint
# Go to endpoint settings and click "Update"
```

2. Monitor logs:
   - Check container logs in RunPod dashboard
   - Monitor GPU utilization
   - Track request latencies

## Troubleshooting

1. Image Build Issues:
   - Check Docker build logs
   - Verify CUDA compatibility
   - Ensure all dependencies are included

2. Runtime Issues:
   - Check model paths in /workspace
   - Verify GPU availability
   - Monitor memory usage

3. API Issues:
   - Check request format
   - Verify input image size (max 2048x2048)
   - Check response status codes

## API Reference

Request Format:
```json
{
    "input": {
        "image": "base64_string",
        "prompt": "text",
        "num_samples": 1-4,
        "height": 512-2048,
        "width": 512-2048,
        "seed": "optional_integer",
        "num_inference_steps": "optional_integer",
        "guidance_scale": "optional_float"
    }
}
```

Response Format:
```json
{
    "status": "success",
    "output": ["base64_image_string"],
    "metrics": {
        "process_time": "float",
        "num_samples": "integer",
        "image_size": "string"
    }
}
```

## Best Practices

1. Verified RunPod Requirements:
   - Use CUDA-compatible base image
   - Install runpod Python package
   - Implement handler() and init() functions
   - Proper error handling and validation
   - GPU memory management
   - Health check endpoint
   - Debug logging

2. Handler Implementation:
   - Validate all inputs
   - Return proper response format
   - Clean up resources after use
   - Log important operations
   - Handle initialization errors

3. Docker Configuration:
   - Multi-stage builds for optimization
   - Include only necessary files
   - Set required environment variables
   - Configure health checks
   - Enable GPU support

4. Testing Requirements:
   - Verify handler initialization
   - Test input validation
   - Check error handling
   - Confirm memory cleanup
   - Validate response format
