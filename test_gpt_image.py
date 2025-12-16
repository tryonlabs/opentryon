from dotenv import load_dotenv
load_dotenv()

import os
from tryon.api.openAI.image_adapter import GPTImageAdapter 

adapter = GPTImageAdapter()

list_of_images = []

# ---------- Text → Image ----------
images = adapter.generate_text_to_image(
    prompt="A person wearing a leather jacket with sun glasses",
    size="1024x1024",
    quality="high",
    n=1
)

list_of_images.extend(images)


# ---------- Image → Image ----------
images = adapter.generate_image_edit(
    images= "/home/naveen/dev/opentryon/outputs/generated_3.png",
    prompt="Make the hat red and stylish",
    size="1024x1024",
    quality="high",
    n=1
)

list_of_images.extend(images)


# ---------- Save outputs ----------
os.makedirs("outputs", exist_ok=True)

for idx, img_bytes in enumerate(list_of_images):
    with open(f"outputs/generated_{idx}.png", "wb") as f:
        f.write(img_bytes)

print(f"Saved {len(list_of_images)} images.")
