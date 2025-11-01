import os
import base64
import json
import io
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from PIL import Image
from typing import Optional, Union, List

class AmazonNovaCanvasVTONAdapter:
    """
    Adapter for Amazon Nova Canvas Virtual Try-On (VTON) model.
    
    Amazon Nova Canvas supports virtual try-on capabilities that allow you to combine
    two images: a source image (person) and a reference image (garment/product).
    The model generates realistic results showing the person wearing or using the product.
    
    Reference: https://aws.amazon.com/blogs/aws/amazon-nova-canvas-update-virtual-try-on-and-style-options-now-available/
    
    Supported regions: US East (N. Virginia), Asia Pacific (Tokyo), Europe (Ireland)
    Image size limit: Maximum 4.1M pixels (equivalent to 2,048 x 2,048)
    """
    
    MAX_IMAGE_PIXELS = 4_100_000  # 4.1M pixels as per AWS documentation
    MAX_IMAGE_DIMENSION = 2048  # 2,048 x 2,048 maximum
    
    def __init__(self, region: Optional[str] = None):
        """
        Initialize the VTON client.
        
        Args:
            region: AWS region name. Defaults to AMAZON_NOVA_REGION environment variable
                   or 'us-east-1' if not set. Supported regions: us-east-1, ap-northeast-1, eu-west-1
        """
        self.region = region or os.getenv("AMAZON_NOVA_REGION", "us-east-1")
        self.model_id = os.getenv("AMAZON_NOVA_MODEL_ID", "amazon.nova-canvas-v1:0")
        self.client = self.create_client()
        
    def create_client(self) -> boto3.client:
        """
        Create a client for the Bedrock Runtime API.
        
        Returns:
            A client for the Bedrock Runtime API.
        """
        return boto3.client("bedrock-runtime", region_name=self.region)
    
    def validate_image_size(self, image: Image.Image) -> None:
        """
        Validate that image dimensions meet Nova Canvas requirements.
        
        Args:
            image: PIL Image object to validate
            
        Raises:
            ValueError: If image exceeds size limits
        """
        width, height = image.size
        total_pixels = width * height
        
        if total_pixels > self.MAX_IMAGE_PIXELS:
            raise ValueError(
                f"Image size ({width}x{height} = {total_pixels:,} pixels) exceeds "
                f"maximum allowed ({self.MAX_IMAGE_PIXELS:,} pixels / {self.MAX_IMAGE_DIMENSION}x{self.MAX_IMAGE_DIMENSION}). "
                f"Please resize your image."
            )
        
        if width > self.MAX_IMAGE_DIMENSION or height > self.MAX_IMAGE_DIMENSION:
            raise ValueError(
                f"Image dimensions ({width}x{height}) exceed maximum allowed "
                f"({self.MAX_IMAGE_DIMENSION}x{self.MAX_IMAGE_DIMENSION}). Please resize your image."
            )
    
    def load_image_as_base64(self, image_path_or_file: Union[str, io.BytesIO]) -> str:
        """
        Helper function for preparing image data as Base64 string.
        
        Validates image size according to Nova Canvas requirements:
        - Maximum 4.1M pixels (2,048 x 2,048)
        
        Args:
            image_path_or_file: Either a file path (str) or a file-like object.
            
        Returns:
            Base64 encoded string of the image.
            
        Raises:
            ValueError: If image exceeds size limits or is invalid
        """
        # Load image to validate size
        if isinstance(image_path_or_file, str):
            # It's a file path
            image = Image.open(image_path_or_file)
            self.validate_image_size(image)
            with open(image_path_or_file, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        else:
            # It's a file-like object (e.g., from Django request.FILES)
            if hasattr(image_path_or_file, 'read'):
                image_file = image_path_or_file
                # Reset file pointer to beginning if needed
                image_file.seek(0)
                # Read and validate
                image_bytes = image_file.read()
                image_file.seek(0)  # Reset for base64 encoding
                
                # Validate image size
                image_buffer = io.BytesIO(image_bytes)
                image = Image.open(image_buffer)
                self.validate_image_size(image)
                
                return base64.b64encode(image_bytes).decode("utf-8")
            else:
                raise ValueError("Invalid image input: must be a file path or file-like object")
    
    def create_virtual_try_on_payload(self, source_image_base64: str, reference_image_base64: str, 
                                     mask_type: str = "GARMENT", garment_class: Optional[str] = "UPPER_BODY",
                                     mask_image_base64: Optional[str] = None) -> dict:
        """
        Create the payload for virtual try-on request.
        
        According to AWS documentation, Nova Canvas supports two mask types:
        1. GARMENT: Automatically detects and masks the garment area based on garment class
        2. IMAGE: Uses a black-and-white image mask (black = replace, white = preserve)
        
        Args:
            source_image_base64: Base64 encoded source image (person/model).
            reference_image_base64: Base64 encoded reference image (garment/product).
            mask_type: Type of mask to use. Options: "GARMENT", "IMAGE". Default: "GARMENT".
            garment_class: Garment class for GARMENT mask type. 
                          Options: "UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR".
                          Required when mask_type is "GARMENT".
            mask_image_base64: Base64 encoded black-and-white mask image for IMAGE mask type.
                              Required when mask_type is "IMAGE".
            
        Returns:
            Dictionary containing the inference parameters ready for API call.
            
        Raises:
            ValueError: If required parameters are missing for the selected mask type.
        """
        # Validate mask type
        valid_mask_types = {"GARMENT", "IMAGE"}
        if mask_type not in valid_mask_types:
            raise ValueError(
                f"Invalid mask_type '{mask_type}'. Must be one of: {valid_mask_types}"
            )
        
        payload = {
            "taskType": "VIRTUAL_TRY_ON",
            "virtualTryOnParams": {
                "sourceImage": source_image_base64,
                "referenceImage": reference_image_base64,
                "maskType": mask_type
            }
        }
        
        # Add configuration based on mask type
        if mask_type == "GARMENT":
            if not garment_class:
                raise ValueError("garment_class is required when mask_type is 'GARMENT'")
            payload["virtualTryOnParams"]["garmentBasedMask"] = {
                "garmentClass": garment_class
            }
        elif mask_type == "IMAGE":
            if not mask_image_base64:
                raise ValueError("mask_image_base64 is required when mask_type is 'IMAGE'")
            payload["virtualTryOnParams"]["maskImage"] = mask_image_base64
        
        return payload
    
    def generate(self, source_image: Union[str, io.BytesIO], 
                 reference_image: Union[str, io.BytesIO], 
                 mask_type: str = "GARMENT", 
                 garment_class: Optional[str] = "UPPER_BODY", 
                 mask_image: Optional[Union[str, io.BytesIO]] = None) -> List[str]:
        """
        Generate virtual try-on image(s) using Amazon Nova Canvas.
        
        This method combines a source image (person/model) with a reference image (garment/product)
        to create realistic virtual try-on results. Images are automatically validated for size limits.
        
        Example:
            >>> adapter = AmazonNovaCanvasVTONAdapter(region="us-east-1")
            >>> images = adapter.generate(
            ...     source_image="person.jpg",
            ...     reference_image="hoodie.jpg",
            ...     mask_type="GARMENT",
            ...     garment_class="UPPER_BODY"
            ... )
        
        Args:
            source_image: Source image (person/model) - file path or file-like object.
                         Must be max 4.1M pixels (2048x2048).
            reference_image: Reference image (garment/product) - file path or file-like object.
                           Must be max 4.1M pixels (2048x2048).
            mask_type: Type of mask to use:
                      - "GARMENT": Automatically detects garment area (default)
                      - "IMAGE": Uses custom black-and-white mask image
            garment_class: Garment class for GARMENT mask type. 
                          Options: "UPPER_BODY", "LOWER_BODY", "FULL_BODY", "FOOTWEAR".
                          Default: "UPPER_BODY". Required when mask_type is "GARMENT".
            mask_image: Mask image for IMAGE mask type. Black areas will be replaced,
                       white areas will be preserved. Required when mask_type is "IMAGE".
            
        Returns:
            List of generated images as Base64 encoded strings.
            
        Raises:
            ValueError: If images exceed size limits, required parameters are missing,
                       or API returns an error.
        """
        try:
            # Convert images to Base64 (with size validation)
            source_image_base64 = self.load_image_as_base64(source_image)
            reference_image_base64 = self.load_image_as_base64(reference_image)
            
            # Convert mask image if provided
            mask_image_base64 = None
            if mask_image:
                mask_image_base64 = self.load_image_as_base64(mask_image)
            
            # Create payload with all parameters
            payload = self.create_virtual_try_on_payload(
                source_image_base64=source_image_base64,
                reference_image_base64=reference_image_base64,
                mask_type=mask_type,
                garment_class=garment_class,
                mask_image_base64=mask_image_base64
            )
            
            # Convert payload to JSON
            body_json = json.dumps(payload, indent=2)
            
            # Invoke Nova Canvas API
            try:
                response = self.client.invoke_model(
                    body=body_json,
                    modelId=self.model_id,
                    accept="application/json",
                    contentType="application/json"
                )
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                
                if error_code == 'ValidationException':
                    raise ValueError(
                        f"Invalid request parameters. Model ID: {self.model_id}, Region: {self.region}. "
                        f"Please check your input parameters. Error: {error_message}"
                    )
                elif error_code == 'AccessDeniedException':
                    raise ValueError(
                        f"Access denied. Please ensure Nova Canvas is enabled in your AWS account. "
                        f"Go to Amazon Bedrock console > Model access and enable Amazon Nova Canvas "
                        f"for region {self.region}. Error: {error_message}"
                    )
                else:
                    raise ValueError(
                        f"AWS Bedrock API error ({error_code}): {error_message}. "
                        f"Model ID: {self.model_id}, Region: {self.region}."
                    )
            except BotoCoreError as e:
                raise ValueError(
                    f"AWS SDK error: {str(e)}. Please check your AWS credentials and configuration."
                )
            except Exception as invoke_error:
                error_msg = str(invoke_error)
                # Provide helpful error messages for common issues
                if "ValidationException" in error_msg or "invalid" in error_msg.lower():
                    raise ValueError(
                        f"Invalid model identifier or model not enabled. "
                        f"Model ID: {self.model_id}, Region: {self.region}. "
                        f"Please ensure Nova Canvas is enabled in your AWS account and available in region {self.region}. "
                        f"Supported regions: us-east-1, ap-northeast-1, eu-west-1. "
                        f"Original error: {error_msg}"
                    )
                raise ValueError(f"Failed to invoke AWS Bedrock: {error_msg}")
            
            # Parse response
            response_body = json.loads(response.get("body").read())
            
            # Check for errors in response
            if response_body.get("error"):
                error_info = response_body.get("error")
                raise ValueError(f"AWS Bedrock API error: {error_info}")
            
            # Extract images from response
            images = response_body.get("images", [])
            if not images:
                raise ValueError("No images returned from AWS Bedrock. Check your input images and parameters.")
            
            return images
            
        except ValueError:
            # Re-raise ValueError as-is (already formatted)
            raise
        except Exception as e:
            raise ValueError(f"Failed to generate virtual try-on: {str(e)}")
    
    def generate_and_decode(self, source_image: Union[str, io.BytesIO], 
                           reference_image: Union[str, io.BytesIO], 
                           mask_type: str = "GARMENT", 
                           garment_class: Optional[str] = "UPPER_BODY", 
                           mask_image: Optional[Union[str, io.BytesIO]] = None) -> List[Image.Image]:
        """
        Generate virtual try-on images and decode them to PIL Image objects.
        
        Convenience method that combines generate() with image decoding.
        
        Args:
            Same as generate() method.
            
        Returns:
            List of PIL Image objects ready for display or saving.
            
        Example:
            >>> adapter = AmazonNovaCanvasVTONAdapter()
            >>> images = adapter.generate_and_decode(
            ...     source_image="person.jpg",
            ...     reference_image="shirt.jpg"
            ... )
            >>> images[0].save("result.png")
        """
        images_base64 = self.generate(
            source_image=source_image,
            reference_image=reference_image,
            mask_type=mask_type,
            garment_class=garment_class,
            mask_image=mask_image
        )
        
        decoded_images = []
        for image_base64 in images_base64:
            image_bytes = base64.b64decode(image_base64)
            image_buffer = io.BytesIO(image_bytes)
            image = Image.open(image_buffer)
            decoded_images.append(image)
        
        return decoded_images
