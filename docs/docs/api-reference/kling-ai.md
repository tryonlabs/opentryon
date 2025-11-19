# Kling AI Virtual Try-On API

The `KlingAIVTONAdapter` provides an interface to Kling AI's Kolors Virtual Try-On API for generating realistic virtual try-on images with asynchronous processing.

## Overview

Kling AI's Kolors Virtual Try-On API combines a source image (person/model) with a reference image (garment/product) to create realistic virtual try-on results. The adapter handles authentication, image preparation, task polling, and response decoding automatically.

**API Endpoint:** `POST /v1/images/kolors-virtual-try-on`

**Reference:** [Kling AI API Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry)

## Installation

No additional installation required. The adapter uses the `requests` and `PyJWT` libraries which are included with OpenTryOn.

## Authentication

Kling AI requires both an API key (access key) and a secret key for authentication. The adapter automatically generates a JWT token using these credentials. You can provide them in two ways:

1. **Environment Variables** (Recommended):
   ```bash
   export KLING_AI_API_KEY="your_api_key"
   export KLING_AI_SECRET_KEY="your_secret_key"
   ```

2. **Constructor Parameters**:
   ```python
   adapter = KlingAIVTONAdapter(
       api_key="your_api_key",
       secret_key="your_secret_key"
   )
   ```

## Quick Start

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import KlingAIVTONAdapter

# Initialize adapter (uses KLING_AI_API_KEY and KLING_AI_SECRET_KEY from environment)
adapter = KlingAIVTONAdapter()

# Generate virtual try-on images
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/shirt.jpg"
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/result_{idx}.png")
```

## API Reference

### Class: `KlingAIVTONAdapter`

Adapter class for Kling AI Kolors Virtual Try-On API.

#### Constructor

```python
KlingAIVTONAdapter(
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    base_url: Optional[str] = None
)
```

**Parameters:**
- `api_key` (str, optional): Kling AI API key. Defaults to `KLING_AI_API_KEY` environment variable. If not provided, raises `ValueError`.
- `secret_key` (str, optional): Kling AI secret key. Defaults to `KLING_AI_SECRET_KEY` environment variable. If not provided, raises `ValueError`.
- `base_url` (str, optional): Base URL for Kling AI API. Defaults to `KLING_AI_BASE_URL` environment variable or `'https://api-singapore.klingai.com'` if not set.

**Raises:**
- `ValueError`: If API key or secret key is not provided via parameter or environment variable.

**Example:**
```python
# Using environment variables
import os
os.environ['KLING_AI_API_KEY'] = 'your_api_key'
os.environ['KLING_AI_SECRET_KEY'] = 'your_secret_key'
adapter = KlingAIVTONAdapter()

# Using parameters
adapter = KlingAIVTONAdapter(
    api_key="your_api_key",
    secret_key="your_secret_key",
    base_url="https://api-singapore.klingai.com"
)
```

#### Methods

##### `generate(source_image, reference_image, model=None, **kwargs)`

Generate virtual try-on image(s) using Kling AI API.

**Parameters:**
- `source_image` (str or io.BytesIO): Human/person image in one of these formats:
  - File path (str): Path to local image file
  - URL (str): HTTP/HTTPS URL to image
  - File-like object (io.BytesIO): BytesIO or similar
  - Base64 string (str): Base64-encoded image
- `reference_image` (str or io.BytesIO): Cloth/garment image in same formats as `source_image`
- `model` (str, optional): Model version to use. Options:
  - `'kolors-virtual-try-on-v1'`: Original model version
  - `'kolors-virtual-try-on-v1-5'`: Enhanced version
  - If not specified, uses API default
- `**kwargs`: Additional parameters for Kling AI API:
  - `webhook_url` (str, optional): URL to receive async results when task completes
  - `webhook_secret` (str, optional): Secret key for webhook authentication

**Returns:**
- `List[str]`: List of image URLs when task succeeds

**Raises:**
- `ValueError`: If images exceed size limits, required parameters are missing, API returns an error, or task fails/times out

**Note:** This method automatically polls for task completion until images are available. The polling continues until the task succeeds, fails, or times out (default: 5 minutes).

**Example:**
```python
# Using file paths
image_urls = adapter.generate(
    source_image="person.jpg",
    reference_image="hoodie.jpg"
)

# Using URLs
image_urls = adapter.generate(
    source_image="https://example.com/person.jpg",
    reference_image="https://example.com/garment.jpg",
    model="kolors-virtual-try-on-v1-5"
)
```

##### `generate_and_decode(source_image, reference_image, model=None, **kwargs)`

Generate virtual try-on images and decode them to PIL Image objects.

**Parameters:**
- `source_image` (str or io.BytesIO): Human/person image (same formats as `generate()`)
- `reference_image` (str or io.BytesIO): Cloth/garment image (same formats as `generate()`)
- `model` (str, optional): Model version to use (e.g., `'kolors-virtual-try-on-v1-5'`)
- `**kwargs`: Additional parameters for Kling AI API

**Returns:**
- `List[PIL.Image.Image]`: List of PIL Image objects ready for display or saving

**Raises:**
- `ValueError`: If images exceed size limits, required parameters are missing, API returns an error, or image decoding fails

**Example:**
```python
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg",
    model="kolors-virtual-try-on-v1-5"
)

# Save all results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
```

##### `query_task_status(task_id)`

Query the status of a virtual try-on task by task ID.

**Parameters:**
- `task_id` (str): The task ID returned from the initial API request

**Returns:**
- `dict`: Task status response containing:
  - `code`: Error code (0 = success)
  - `message`: Status message
  - `request_id`: System-generated request ID
  - `data`: Task data containing:
    - `task_id`: Task identifier
    - `task_status`: Current status (`"submitted"`, `"processing"`, `"succeed"`, `"fail"`)
    - `task_status_msg`: Additional status information
    - `created_at`: Task creation timestamp (milliseconds)
    - `updated_at`: Task update timestamp (milliseconds)
    - `task_result`: Result data (when status is `"succeed"`)
      - `images`: List of image objects with index and url

**Raises:**
- `ValueError`: If the API request fails or returns an error

**Example:**
```python
status = adapter.query_task_status("your_task_id")
print(f"Status: {status['data']['task_status']}")
```

##### `poll_task_until_complete(task_id, poll_interval=2, max_wait_time=300)`

Poll task status until completion and return image URLs.

**Parameters:**
- `task_id` (str): The task ID returned from the initial API request
- `poll_interval` (int): Number of seconds to wait between status checks. Default: `2`
- `max_wait_time` (int): Maximum time to wait for task completion in seconds. Default: `300` (5 minutes)

**Returns:**
- `List[str]`: List of image URLs when task succeeds

**Raises:**
- `ValueError`: If the task fails, times out, or encounters an error

**Example:**
```python
# Custom polling settings
image_urls = adapter.poll_task_until_complete(
    task_id="your_task_id",
    poll_interval=3,  # Check every 3 seconds
    max_wait_time=600  # Maximum 10 minutes
)
```

## Image Size Limits

Kling AI has the following image size requirements:

- **Maximum image pixels:** 16,000,000 pixels (equivalent to 4,096 x 4,096)
- **Maximum dimension:** 4,096 pixels per side
- **Supported formats:** JPG, PNG

Images are automatically validated before sending to the API. If an image exceeds these limits, a `ValueError` is raised with a helpful message.

## Model Versions

Kling AI supports multiple model versions:

- **`kolors-virtual-try-on-v1`**: Original model version
- **`kolors-virtual-try-on-v1-5`**: Enhanced version (recommended)

If not specified, the API uses the default model version.

## Asynchronous Processing

Kling AI processes virtual try-on requests asynchronously. The adapter automatically:

1. Submits the request and receives a `task_id`
2. Polls the task status endpoint until completion
3. Returns image URLs when the task succeeds
4. Raises errors if the task fails or times out (default timeout: 5 minutes)

### Custom Polling

You can customize polling behavior:

```python
# Manual polling with custom settings
task_id = "your_task_id"
image_urls = adapter.poll_task_until_complete(
    task_id=task_id,
    poll_interval=2,  # Check every 2 seconds
    max_wait_time=600  # Maximum 10 minutes
)
```

## Image Input Formats

The adapter supports multiple input formats:

### File Paths

```python
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg"
)
```

### URLs

```python
images = adapter.generate_and_decode(
    source_image="https://example.com/person.jpg",
    reference_image="https://example.com/garment.jpg"
)
```

### File-like Objects

```python
from io import BytesIO

with open("person.jpg", "rb") as f:
    person_bytes = BytesIO(f.read())

with open("garment.jpg", "rb") as f:
    garment_bytes = BytesIO(f.read())

images = adapter.generate_and_decode(
    source_image=person_bytes,
    reference_image=garment_bytes
)
```

### Base64 Strings

```python
import base64

with open("person.jpg", "rb") as f:
    person_b64 = base64.b64encode(f.read()).decode()

with open("garment.jpg", "rb") as f:
    garment_b64 = base64.b64encode(f.read()).decode()

images = adapter.generate_and_decode(
    source_image=person_b64,
    reference_image=garment_b64
)
```

## Supported Base URLs

- **`https://api-singapore.klingai.com`** (Singapore) - Default
- Other regional endpoints may be available (check Kling AI documentation)

## Complete Example

```python
from dotenv import load_dotenv
load_dotenv()

from tryon.api import KlingAIVTONAdapter
from PIL import Image

# Initialize adapter
adapter = KlingAIVTONAdapter()

# Generate virtual try-on
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/shirt.jpg",
    model="kolors-virtual-try-on-v1-5"
)

# Process results
for idx, image in enumerate(images):
    # Save image
    image.save(f"outputs/vton_result_{idx}.png")
    
    # Display image (if in Jupyter)
    # display(image)
    
    # Get image info
    print(f"Image {idx}: {image.size} ({image.mode})")
```

## Error Handling

The adapter raises `ValueError` for common errors:

```python
try:
    images = adapter.generate_and_decode(
        source_image="person.jpg",
        reference_image="garment.jpg"
    )
except ValueError as e:
    print(f"Error: {e}")
    # Handle error...
```

Common errors:
- Missing API key or secret key
- Invalid image format or size
- API request failure
- Task timeout or failure
- Invalid parameters

## Best Practices

### Use Environment Variables

Store your API credentials securely using environment variables:

```bash
# .env file
KLING_AI_API_KEY=your_api_key_here
KLING_AI_SECRET_KEY=your_secret_key_here
```

```python
from dotenv import load_dotenv
load_dotenv()

adapter = KlingAIVTONAdapter()  # Uses environment variables
```

### Image Preprocessing

For best results:
- Use high-resolution images (at least 512x512)
- Ensure person image shows full body or relevant body part
- Use clear, well-lit images
- Remove background if possible
- Ensure images meet size requirements (max 16M pixels)

### Task Polling

- Default polling interval (2 seconds) is usually sufficient
- Increase `max_wait_time` for longer processing tasks
- Monitor task status for debugging:
  ```python
  status = adapter.query_task_status(task_id)
  print(f"Status: {status['data']['task_status']}")
  ```

## Troubleshooting

### API Key Issues

If you get an authentication error:

1. Verify your API key and secret key are correct
2. Check environment variables are set: `echo $KLING_AI_API_KEY`
3. Ensure API key has sufficient credits/quota
4. Verify JWT token generation is working

### Image Format Issues

If images fail to process:

1. Verify image files exist and are readable
2. Check image format is supported (JPG, PNG)
3. Ensure images meet size requirements (max 16M pixels, 4096x4096)
4. Try converting images to RGB format

### Task Timeout

If tasks timeout:

1. Increase `max_wait_time` parameter
2. Check task status manually: `adapter.query_task_status(task_id)`
3. Verify API service status
4. Check for rate limiting

### Rate Limiting

If you encounter rate limiting:

1. Reduce request frequency
2. Implement retry logic with exponential backoff
3. Check your API plan limits
4. Contact Kling AI support for higher limits

## See Also

- [Virtual Try-On Examples](../examples/virtual-tryon) - Usage examples
- [API Reference Overview](overview) - Complete API reference
- [Kling AI Documentation](https://app.klingai.com/global/dev/document-api/apiReference/model/functionalityTry) - Official API docs

