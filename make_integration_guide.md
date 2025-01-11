# FLUX-customID Make.com Integration Guide

This guide explains how to integrate the FLUX-customID serverless endpoint with Make.com (formerly Integromat) using the HTTP module.

## Prerequisites

- A Make.com account
- RunPod serverless endpoint URL
- Basic understanding of HTTP requests and base64 encoding

## API Specifications

### Endpoint
```
https://your-runpod-endpoint.runpod.net
```

### Request Format
- Method: POST
- Content-Type: application/json

### Input Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|--------|-------------|
| image | string | Yes | - | - | Base64 encoded image (JPEG, JPG, PNG, or WEBP format) |
| prompt | string | Yes | - | - | Text prompt for generation |
| num_samples | integer | No | 1 | 1-4 | Number of images to generate |
| height | integer | No | 1024 | 512-2048 | Output image height (max 2048) |
| width | integer | No | 1024 | 512-2048 | Output image width (max 2048) |
| seed | integer | No | current timestamp | - | Random seed for generation |
| num_inference_steps | integer | No | 28 | 1-50 | Number of denoising steps |
| guidance_scale | float | No | 3.5 | 1.0-20.0 | Guidance scale for generation |

### Image Requirements
- Supported formats: JPEG, JPG, PNG, WEBP
- Maximum dimensions: 2048x2048 pixels
- Image must be valid and properly base64 encoded

## Make.com Workflow Setup

### 1. Create New Scenario
1. Click "Create new scenario"
2. Search for and select "HTTP" module
3. Choose "Make an HTTP request"

### 2. Configure HTTP Module

#### Basic Settings
- URL: Your RunPod endpoint URL
- Method: POST
- Headers:
  ```
  Content-Type: application/json
  ```

#### Request Body
```json
{
  "input": {
    "image": "{{base64_encoded_image}}",
    "prompt": "professional ID photo",
    "num_samples": 1,
    "height": 1024,
    "width": 1024,
    "num_inference_steps": 28,
    "guidance_scale": 3.5
  }
}
```

### 3. Image Preparation
Before the HTTP module, add a module to prepare your image:
1. Use "Image to Base64" or "File to Base64" module
2. Connect its output to the HTTP request's image parameter
3. Ensure image meets requirements:
   - Supported formats: JPEG, JPG, PNG, WEBP
   - Maximum dimensions: 2048x2048 pixels

### 4. Response Handling

#### Success Response
```json
{
  "status": "success",
  "output": ["base64_encoded_image_string", ...],
  "metrics": {
    "process_time": 10.5,        // Processing time in seconds
    "num_samples": 1,            // Number of images generated
    "image_size": "1024x1024"    // Width x Height of generated images
  }
}
```

#### Error Response Types
```json
{
  "status": "error",
  "error": "Error message"
}
```

Common error messages:
- "Invalid input format" - Request body is not a valid JSON object
- "No input data provided" - Missing input object in request
- "No input image provided" - Missing image parameter
- "No prompt provided" - Missing prompt parameter
- "Unsupported image format" - Image not in JPEG, JPG, PNG, or WEBP format
- "Image dimensions exceed maximum allowed size" - Image larger than 2048x2048
- "Error processing input image" - Invalid base64 encoding or corrupted image
- "Error during image generation" - Model generation failure

To process the response:
1. Add a "JSON Parse" module after HTTP request
2. For each generated image in output array:
   - Add "Base64 to File/Image" module
   - Map the base64 string to your desired output (e.g., save to storage, send via email)

### 5. Error Handling

Add error handling routes for these scenarios:
- HTTP request failures
- Invalid input parameters
- Generation errors

Example error response:
```json
{
  "status": "error",
  "error": "Error message details"
}
```

## Best Practices

1. **Input Validation**
   - Validate image format and size before sending
   - Ensure prompt is not empty
   - Keep parameters within allowed ranges

2. **Performance Optimization**
   - Cache generated images when possible
   - Use appropriate image dimensions
   - Consider batch processing for multiple images

3. **Error Handling**
   - Add retry logic for transient failures
   - Log error responses for debugging
   - Implement fallback logic where appropriate

4. **Resource Management**
   - Monitor API usage and costs
   - Implement rate limiting if needed
   - Clean up temporary files

## Example Make.com Scenario

Here's a complete scenario flow:

1. **Trigger** (Your choice - HTTP webhook, scheduled, etc.)
2. **File/Image Preparation**
   - Convert input image to base64
   - Validate format and size
3. **HTTP Request to FLUX-customID**
   - Send prepared request
   - Handle response
4. **Process Results**
   - Convert base64 output to images
   - Store or forward as needed
5. **Error Handling**
   - Check status field
   - Process error messages
   - Implement retry logic

## Troubleshooting

Common issues and solutions:

1. **Invalid Image Format**
   - Ensure image is in supported format
   - Check base64 encoding is correct
   - Verify image dimensions

2. **Request Timeout**
   - Increase HTTP module timeout
   - Check image size and complexity
   - Monitor RunPod endpoint status

3. **Generation Failures**
   - Verify prompt formatting
   - Check parameter ranges
   - Review error messages in response

## Performance Considerations

### Hardware Requirements
- NVIDIA GPU with 16GB+ VRAM recommended (e.g., NVIDIA A5000 or better)
- Container disk: 20GB minimum
- Model storage: 80GB minimum for all models:
  - CLIP model: ~15GB
  - FLUX.1-dev: ~54GB
  - FLUX-customID: ~3.4GB

### Cold Start Performance
- First request after idle may experience longer response times
- Consider keeping minimum instances > 0 if cold starts are problematic
- Default idle timeout is 5 minutes
- Scale to zero can be enabled/disabled based on needs

### Rate Limiting and Quotas
- Monitor your RunPod usage and costs
- Implement appropriate rate limiting in Make.com
- Consider batch processing for multiple requests
- Adjust max instances based on concurrent request needs

### Monitoring
- Use RunPod dashboard to:
  - Monitor build status and logs
  - Track GPU utilization
  - Monitor endpoint health
  - View error logs
  - Track costs and usage metrics

## Security Considerations

1. **Data Protection**
   - Use secure connections (HTTPS)
   - Don't expose sensitive information in prompts
   - Clean up temporary files

2. **Access Control**
   - Protect your Make.com webhook URLs
   - Monitor API usage
   - Implement IP restrictions if needed

## Support and Resources

- RunPod Dashboard: Monitor endpoint status and logs
- Make.com Documentation: HTTP module reference
- FLUX-customID Repository: Latest updates and issues

## Testing Your Integration

1. Initial Testing
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

2. Monitor in Make.com:
   - Check scenario execution history
   - Review error logs
   - Monitor execution times
   - Track success/failure rates

3. Common Issues:
   - Cold start delays: First request after idle period
   - Timeout errors: Increase HTTP module timeout (default may be too short)
   - Memory errors: Check image sizes and batch requests
   - Rate limiting: Adjust concurrent executions in Make.com
