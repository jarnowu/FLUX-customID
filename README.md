

## <img src="img/logo.png" alt="Logo" style="width: 80px; vertical-align: middle;">FLUX-customID: Realistically Customize Your Personal ID to Perfection

This repository is the official implementation of FLUX-customID. It is capable of generating images based on your face image at a level equivalent to real photographic quality. Our base model is FLUX.dev, which ensures the generation of high-quality images.

## News
- 🌟**2024-11-13**: Released the code and weights for FLUX-customID.

## Gallery
Here are some example samples generated by our method.

<center><img src="img/CustomID_img.png" style="width: 70%"></center>

## Deployment Options

### Option 1: Local Setup

#### 1. Setup Repository and Environment

```
conda create -n customID python=3.10 -y
conda activate customID
conda install pytorch==2.4.0 torchvision==0.19.0 pytorch-cuda=11.8 -c pytorch -c nvidia  -y
pip install -i https://mirrors.cloud.tencent.com/pypi/simple  diffusers==0.31.0 transformers onnxruntime-gpu insightface sentencepiece matplotlib imageio tqdm numpy einops accelerate peft
```

#### 2. Prepare Pretrained Checkpoints

```
git clone https://github.com/damo-cv/FLUX-customID.git
cd FLUX-customID

mkdir pretrained_ckpt
cd pretrained_ckpt

#Download CLIP
export HF_ENDPOINT=https://hf-mirror.com
pip install -U "huggingface_hub[cli]"

huggingface-cli download \
--resume-download "laion/CLIP-ViT-H-14-laion2B-s32B-b79K" \
--cache-dir your_dir/

ln -s your_dir/models--laion--CLIP-ViT-H-14-laion2B-s32B-b79K/snapshots/de081ac0a0ca8dc9d1533eed1ae884bb8ae1404b pretrained_ckpt/openclip-vit-h-14

#Download FLUX.1-dev
huggingface-cli download \
--resume-download "black-forest-labs/FLUX.1-dev" \
--cache-dir your_dir/

ln -s your_dir/models--black-forest-labs--FLUX.1-dev/snapshots/303875135fff3f05b6aa893d544f28833a237d58 pretrained_ckpt/flux.1-dev

#Download FLUX-customID
Download our trained checkpoint from https://huggingface.co/Damo-vision/FLUX-customID and place FLUX-customID.pt in the floder pretrained_ckpt/
```

#### 3. Quick Inference
```
run infer_customID.ipynb
```

### Option 2: RunPod Serverless Deployment

For production deployments or scaling to multiple users, we provide a RunPod serverless implementation.

#### Key Features
- Automatic scaling based on demand
- GPU acceleration with NVIDIA A5000 or better
- Persistent model storage
- RESTful API endpoint
- Detailed logging and monitoring

#### Quick Setup
1. Follow the detailed instructions in [RUNPOD_DEPLOYMENT.md](RUNPOD_DEPLOYMENT.md)
2. Key requirements:
   - RunPod account
   - 80GB storage volume for models
   - NVIDIA GPU (16GB+ VRAM)

#### API Usage
```python
import requests
import base64

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

# Replace with your endpoint URL
endpoint = "https://your-endpoint.runpod.net"
image = encode_image("path/to/your/image.jpg")

response = requests.post(endpoint, json={
    "input": {
        "image": image,
        "prompt": "professional ID photo",
        "num_samples": 1,
        "height": 1024,
        "width": 1024
    }
})

# Response includes base64-encoded generated images
result = response.json()
```

For detailed deployment instructions and troubleshooting, see [RUNPOD_DEPLOYMENT.md](RUNPOD_DEPLOYMENT.md)

## Preview for CustomAnyID
We would like to announce that we are currently working on a related project, **CustomAnyID**. Below are some preliminary experimental results:

<center><img src="img/CustomAnyID_img.png" style="width: 70%"></center>

## Preview for Controlnet
We would like to announce our Controlnet model. Below are some preliminary experimental results:
<center><img src="img/controlnet_img.png" style="width: 70%"></center>


## System Requirements

### Local Setup
- Python 3.10
- CUDA 11.8
- 16GB+ GPU VRAM
- 32GB+ System RAM

### RunPod Deployment
- NVIDIA A5000 or better GPU
- 80GB storage volume
- 20GB container disk

## Contact Us
Dongyang Li: [yingtian.ldy@alibaba-inc.com](yingtian.ldy@alibaba-inc.com)

## Acknowledgements
The partial code is implemented based on [IP-Adapter](https://github.com/tencent-ailab/IP-Adapter) and [PhotoMaker](https://github.com/TencentARC/PhotoMaker).
