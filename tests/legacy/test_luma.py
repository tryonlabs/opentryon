from dotenv import load_dotenv
load_dotenv()

import os
from tryon.api.lumaAI import LumaAIAdapter

adapter = LumaAIAdapter()

list_of_images = []

images = adapter.generate_text_to_image(
    prompt="person with a hat",
    aspect_ratio= "16:9"
)

list_of_images.extend(images)

images = adapter.generate_with_image_reference(
    prompt="hat",
    aspect_ratio= '16:9',
    image_ref= [
      {
        "url": "https://storage.cdn-luma.com/dream_machine/7e4fe07f-1dfd-4921-bc97-4bcf5adea39a/video_0_thumb.jpg",
        "weight": 0.85
      }
    ]
)

list_of_images.extend(images)

images = adapter.generate_with_style_reference(
    prompt="tiger",
    aspect_ratio= '16:9',
    style_ref= [
      {
        "url": "https://staging.storage.cdn-luma.com/dream_machine/400460d3-cc24-47ae-a015-d4d1c6296aba/38cc78d7-95aa-4e6e-b1ac-4123ce24725e_image0c73fa8a463114bf89e30892a301c532e.jpg",
        "weight": 0.8
      }
    ]
)

list_of_images.extend(images)

images = adapter.generate_with_character_reference(
    prompt="man as a pilot",
    aspect_ratio= '16:9',
    character_ref= {
        "identity0": {
          "images": [
            "https://staging.storage.cdn-luma.com/dream_machine/400460d3-cc24-47ae-a015-d4d1c6296aba/38cc78d7-95aa-4e6e-b1ac-4123ce24725e_image0c73fa8a463114bf89e30892a301c532e.jpg"
          ]
        }
      }
)

list_of_images.extend(images)

images = adapter.generate_with_modify_image(
    prompt="transform all flowers to oranges",
    image= "https://staging.storage.cdn-luma.com/dream_machine/400460d3-cc24-47ae-a015-d4d1c6296aba/38cc78d7-95aa-4e6e-b1ac-4123ce24725e_image0c73fa8a463114bf89e30892a301c532e.jpg",
    weight= 0.9,
    aspect_ratio= '16:9'
)

list_of_images.extend(images)

os.makedirs("outputs", exist_ok=True)

for idx, img in enumerate(list_of_images):
    img.save(f"outputs/generated_{idx}.png")

print(f"Saved {len(list_of_images)} images.")