# Amazon Nova Canvas Virtual Try-On API

The `AmazonNovaCanvasVTONAdapter` provides an interface to Amazon Nova Canvas Virtual Try-On model through AWS Bedrock for generating realistic virtual try-on images.

## Overview

Amazon Nova Canvas Virtual Try-On combines a source image (person/model) with a reference image (garment/product) to create realistic virtual try-on results. The adapter handles AWS authentication, image preparation, and response decoding automatically.

**Service:** Amazon Bedrock Runtime API  
**Model ID:** `amazon.nova-canvas-v1:0`  
**Reference:** [Amazon Nova Canvas Documentation](https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/)

## Installation

The adapter requires `boto3` and `botocore` libraries:

```bash
pip install boto3 botocore pillow
```

## Authentication

Amazon Nova Canvas uses AWS credentials for authentication. Configure credentials using one of these methods:

1. **AWS Credentials File** (`~/.aws/credentials`):
   ```ini
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY
   aws_secret_access_key = YOUR_SECRET_KEY
   ```

2. **Environment Variables**:
   ```bash
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"
   export AWS_DEFAULT_REGION="us-east-1"
   ```

3. **IAM Role** (if running on EC2/ECS/Lambda)

**Important:** Ensure Nova Canvas model access is enabled in your AWS Bedrock console (Model access section).

## Quick Start

```python
from tryon.api import AmazonNovaCanvasVTONAdapter

# Initialize adapter
adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")

# Generate virtual try-on images
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Save results
for idx, image in enumerate(images):
    image.save(f"outputs/result_{idx}.png")
```

## API Reference

### Class: `AmazonNovaCanvasVTONAdapter`

Adapter class for Amazon Nova Canvas Virtual Try-On API.

#### Constructor

```python
AmazonNovaCanvasVTONAdapter(region: Optional[str] = None)
```

**Parameters:**
- `region` (str, optional): AWS region name. Defaults to `AMAZON_NOVA_REGION` environment variable or `'us-east-1'` if not set. Supported regions:
  - `'us-east-1'` (US East - N. Virginia) - Default
  - `'ap-northeast-1'` (Asia Pacific - Tokyo)
  - `'eu-west-1'` (Europe - Ireland)

**Example:**
```python
# Use default region (us-east-1)
adapter = AmazonNovaCanvasVTONAdapter()

# Use custom region
adapter = AmazonNovaCanvasVTONAdapter(region="ap-northeast-1")
```

#### Methods

##### `generate(source_image, reference_image, mask_type="GARMENT", garment_class="UPPER_BODY", mask_image=None)`

Generate virtual try-on image(s) using Amazon Nova Canvas.

**Parameters:**
- `source_image` (str or io.BytesIO): Source image (person/model) - file path or file-like object. Must be max 4.1M pixels (2048x2048)
- `reference_image` (str or io.BytesIO): Reference image (garment/product) - file path or file-like object. Must be max 4.1M pixels (2048x2048)
- `mask_type` (str): Type of mask to use:
  - `"GARMENT"`: Automatically detects garment area (default)
  - `"IMAGE"`: Uses custom black-and-white mask image
- `garment_class` (str, optional): Garment class for GARMENT mask type. Options:
  - `"UPPER_BODY"`: Tops, shirts, jackets, hoodies (default)
  - `"LOWER_BODY"`: Pants, skirts, shorts
  - `"FULL_BODY"`: Dresses, jumpsuits
  - `"FOOTWEAR"`: Shoes, boots
  Required when `mask_type` is `"GARMENT"`
- `mask_image` (str or io.BytesIO, optional): Mask image for IMAGE mask type. Black areas will be replaced, white areas will be preserved. Required when `mask_type` is `"IMAGE"`

**Returns:**
- `List[str]`: List of generated images as Base64 encoded strings

**Raises:**
- `ValueError`: If images exceed size limits, required parameters are missing, or API returns an error

**Example:**
```python
# Using GARMENT mask type (default)
images_base64 = adapter.generate(
    source_image="person.jpg",
    reference_image="shirt.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Using IMAGE mask type
images_base64 = adapter.generate(
    source_image="person.jpg",
    reference_image="garment.jpg",
    mask_type="IMAGE",
    mask_image="mask.png"
)
```

##### `generate_and_decode(source_image, reference_image, mask_type="GARMENT", garment_class="UPPER_BODY", mask_image=None)`

Generate virtual try-on images and decode them to PIL Image objects.

**Parameters:**
- Same as `generate()` method

**Returns:**
- `List[PIL.Image.Image]`: List of PIL Image objects ready for display or saving

**Raises:**
- `ValueError`: If images exceed size limits, required parameters are missing, or image decoding fails

**Example:**
```python
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Save all results
for idx, image in enumerate(images):
    image.save(f"outputs/vton_result_{idx}.png")
```

##### `validate_image_size(image)`

Validate that image dimensions meet Nova Canvas requirements.

**Parameters:**
- `image` (PIL.Image.Image): PIL Image object to validate

**Raises:**
- `ValueError`: If image exceeds size limits

**Note:** This method is called automatically when loading images. You typically don't need to call it directly.

## Image Size Limits

Amazon Nova Canvas has the following image size requirements:

- **Maximum image pixels:** 4,100,000 pixels (equivalent to 2,048 x 2,048)
- **Maximum dimension:** 2,048 pixels per side
- **Supported formats:** JPG, PNG

Images are automatically validated before sending to the API. If an image exceeds these limits, a `ValueError` is raised with a helpful message.

## Mask Types

Nova Canvas supports two mask types:

### GARMENT Mask (Default)

Automatically detects and masks the garment area based on garment class. This is the recommended approach for most use cases.

**Garment Classes:**
- **`UPPER_BODY`**: Tops, shirts, jackets, hoodies
- **`LOWER_BODY`**: Pants, skirts, shorts
- **`FULL_BODY`**: Dresses, jumpsuits
- **`FOOTWEAR`**: Shoes, boots

**Example:**
```python
# Upper body garment
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="shirt.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Lower body garment
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="pants.jpg",
    mask_type="GARMENT",
    garment_class="LOWER_BODY"
)
```

### IMAGE Mask

Uses a custom black-and-white mask image where:
- **Black areas** = replaced with garment
- **White areas** = preserved from source image

**Example:**
```python
images = adapter.generate_and_decode(
    source_image="person.jpg",
    reference_image="garment.jpg",
    mask_type="IMAGE",
    mask_image="custom_mask.png"
)
```

## Supported AWS Regions

- **`us-east-1`** (US East - N. Virginia) - Default
- **`ap-northeast-1`** (Asia Pacific - Tokyo)
- **`eu-west-1`** (Europe - Ireland)

## Image Input Formats

The adapter supports multiple input formats:

### File Paths

```python
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/garment.jpg"
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

## Complete Example

```python
from tryon.api import AmazonNovaCanvasVTONAdapter
from PIL import Image

# Initialize adapter
adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")

# Generate try-on for upper body garment
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/shirt.jpg",
    mask_type="GARMENT",
    garment_class="UPPER_BODY"
)

# Generate try-on for lower body garment
images = adapter.generate_and_decode(
    source_image="data/person.jpg",
    reference_image="data/pants.jpg",
    mask_type="GARMENT",
    garment_class="LOWER_BODY"
)

# Process results
for idx, image in enumerate(images):
    # Save image
    image.save(f"outputs/result_{idx}.png")
    
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
- Missing AWS credentials
- Nova Canvas not enabled in AWS account
- Invalid image format or size
- Invalid mask type or garment class
- API request failure

## Best Practices

### AWS Credentials

Store your AWS credentials securely:

```bash
# Using AWS CLI
aws configure

# Or using environment variables
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Enable Model Access

Before using Nova Canvas, ensure model access is enabled:

1. Go to AWS Bedrock Console
2. Navigate to "Model access" section
3. Enable "Amazon Nova Canvas" for your desired region(s)

### Image Preprocessing

For best results:
- Use high-resolution images (at least 512x512)
- Ensure person image shows full body or relevant body part
- Use clear, well-lit images
- Remove background if possible
- Ensure images meet size requirements (max 4.1M pixels, 2048x2048)

### Mask Type Selection

- **Use GARMENT mask** for standard garment types (upper body, lower body, etc.)
- **Use IMAGE mask** only when you need precise control over the replacement area
- Ensure mask images are black-and-white (grayscale) for IMAGE mask type

## Troubleshooting

### AWS Credentials Issues

If you get authentication errors:

1. Verify AWS credentials are configured correctly
2. Check credentials file: `cat ~/.aws/credentials`
3. Verify environment variables: `echo $AWS_ACCESS_KEY_ID`
4. Test AWS CLI: `aws sts get-caller-identity`

### Model Access Denied

If you get "AccessDeniedException":

1. Go to AWS Bedrock Console > Model access
2. Enable "Amazon Nova Canvas" for your region
3. Wait a few minutes for changes to propagate
4. Verify region supports Nova Canvas (us-east-1, ap-northeast-1, eu-west-1)

### Image Format Issues

If images fail to process:

1. Verify image files exist and are readable
2. Check image format is supported (JPG, PNG)
3. Ensure images meet size requirements (max 4.1M pixels, 2048x2048)
4. Try converting images to RGB format

### Invalid Parameters

If you get validation errors:

1. Verify `mask_type` is either `"GARMENT"` or `"IMAGE"`
2. Ensure `garment_class` is provided when using `"GARMENT"` mask type
3. Ensure `mask_image` is provided when using `"IMAGE"` mask type
4. Check garment class is one of: `UPPER_BODY`, `LOWER_BODY`, `FULL_BODY`, `FOOTWEAR`

## See Also

- [Virtual Try-On Examples](../examples/virtual-tryon) - Usage examples
- [API Reference Overview](overview) - Complete API reference
- [Amazon Nova Canvas Documentation](https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/) - Official AWS documentation

