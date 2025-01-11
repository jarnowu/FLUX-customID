import os
import base64
import io
import gc
import time
from pathlib import Path
import runpod
from PIL import Image
import torch
from src.customID.pipeline_flux import FluxPipeline
from src.customID.transformer_flux import FluxTransformer2DModel
from src.customID.model import CustomIDModel

DEVICE = "cuda"
DTYPE = torch.float16  # Using float16 for deployment instead of bfloat16
MODEL_PATH = "pretrained_ckpt/flux.1-dev"
TRAINED_CKPT = "pretrained_ckpt/FLUX-customID.pt"
NUM_TOKENS = 64
MAX_IMAGE_SIZE = (2048, 2048)  # Maximum input image dimensions
SUPPORTED_FORMATS = {'JPEG', 'JPG', 'PNG', 'WEBP'}

def verify_models():
    """Verify all required model files exist"""
    required_files = [
        Path(MODEL_PATH),
        Path(TRAINED_CKPT),
        Path("pretrained_ckpt/openclip-vit-h-14")
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            raise RuntimeError(f"Required model file/directory not found: {file_path}")

def init():
    """Initialize the model during cold start"""
    global model
    
    try:
        print("Verifying model files...")
        verify_models()
        
        print("Loading FLUX transformer...")
        transformer = FluxTransformer2DModel.from_pretrained(
            MODEL_PATH, 
            subfolder="transformer", 
            torch_dtype=DTYPE
        ).to(DEVICE)
        
        print("Loading FLUX pipeline...")
        pipe = FluxPipeline.from_pretrained(
            MODEL_PATH,
            transformer=transformer,
            torch_dtype=DTYPE
        ).to(DEVICE)
        
        print("Initializing CustomID model...")
        model = CustomIDModel(
            pipe,
            TRAINED_CKPT,
            DEVICE,
            DTYPE,
            NUM_TOKENS
        )
        print("Model loaded successfully")
        
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        raise RuntimeError(f"Failed to initialize model: {str(e)}")

def validate_image(image):
    """Validate image format and size"""
    if image.format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported image format: {image.format}. Supported formats: {SUPPORTED_FORMATS}")
    
    if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
        raise ValueError(f"Image dimensions exceed maximum allowed size of {MAX_IMAGE_SIZE}")

def cleanup():
    """Cleanup CUDA memory"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        gc.collect()

def handler(event):
    """Handle incoming requests"""
    start_time = time.time()
    temp_files = []
    
    try:
        # Validate input
        if not isinstance(event, dict):
            return {"error": "Invalid input format"}
        
        input_data = event.get("input", {})
        if not input_data:
            return {"error": "No input data provided"}
            
        # Get parameters from input
        image_b64 = input_data.get("image")
        if not image_b64:
            return {"error": "No input image provided"}
            
        prompt = input_data.get("prompt")
        if not prompt:
            return {"error": "No prompt provided"}
            
        # Optional parameters with defaults and validation
        num_samples = min(max(1, input_data.get("num_samples", 1)), 4)  # Limit samples
        height = min(max(512, input_data.get("height", 1024)), MAX_IMAGE_SIZE[1])
        width = min(max(512, input_data.get("width", 1024)), MAX_IMAGE_SIZE[0])
        seed = input_data.get("seed", int(time.time()))
        num_inference_steps = min(max(1, input_data.get("num_inference_steps", 28)), 50)
        guidance_scale = min(max(1.0, input_data.get("guidance_scale", 3.5)), 20.0)
        
        # Process input image
        try:
            image_data = base64.b64decode(image_b64)
            input_image = Image.open(io.BytesIO(image_data))
            validate_image(input_image)
            
            temp_path = f"/tmp/input_image_{int(time.time())}.jpg"
            temp_files.append(temp_path)
            input_image.save(temp_path)
            
        except Exception as e:
            raise ValueError(f"Error processing input image: {str(e)}")
        
        # Generate images
        try:
            generated_images = model.generate(
                pil_image=temp_path,
                prompt=prompt,
                num_samples=num_samples,
                height=height,
                width=width,
                seed=seed,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale
            )
        except Exception as e:
            raise RuntimeError(f"Error during image generation: {str(e)}")
        
        # Convert generated images to base64
        output_images = []
        for img in generated_images:
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            output_images.append(img_b64)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        return {
            "status": "success",
            "output": output_images,
            "metrics": {
                "process_time": process_time,
                "num_samples": num_samples,
                "image_size": f"{width}x{height}"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    
    finally:
        # Cleanup
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up temporary file {temp_file}: {str(e)}")
        
        cleanup()  # Clear CUDA cache

# Initialize the model
init()

# Start the runpod handler
runpod.serverless.start({"handler": handler})
