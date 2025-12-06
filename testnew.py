import requests
import base64
from PIL import Image
import io

# --------------------------------
# CONFIG
# --------------------------------
CLOUDFLARE_API_TOKEN ="ufDFoG4jkeapzzeKzarfTVDg3Ymv0iV7NTC-AtZy"
ACCOUNT_ID ="556e95c7ea24a10a158fd0fd8110b7a2"

# --------------------------------
# Load base image and convert to base64
# --------------------------------
def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

base_image_b64 = image_to_base64("images\\skyline\\skyline_bedroom.webp")   # your base room image


# --------------------------------
# CALL CLOUDLFARE SDXL IMG2IMG
# --------------------------------
url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/bytedance/sdxl-lightning-4step-img2img"

headers = {
    "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
}

payload = {
    "prompt": "modern luxury interior design, realistic lighting, elegant decor",
    "image": base_image_b64
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

print(result)

if not result.get("success"):
    print("\n❌ Cloudflare Error:")
    print(result.get("errors"))
    exit()

# --------------------------------
# Save Output Image
# --------------------------------
output_image_b64 = result["result"]["image"]
image_bytes = base64.b64decode(output_image_b64)

img = Image.open(io.BytesIO(image_bytes))
img.save("output_room.png")

print("Generated image saved as output_room.png")
