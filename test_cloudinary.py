import cloudinary
import cloudinary.uploader
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Cloudinary
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)

print("🔍 Checking Cloudinary configuration...")
print(f"Cloud Name: {os.getenv('CLOUDINARY_CLOUD_NAME')}")
print(f"API Key: {os.getenv('CLOUDINARY_API_KEY')}")
print(f"API Secret: {'*' * 20} (hidden)")

if not os.getenv('CLOUDINARY_CLOUD_NAME'):
    print("\n❌ CLOUDINARY_CLOUD_NAME not found in .env!")
    print("💡 Add it to your .env file")
    exit(1)

# Create a simple test image (1x1 red pixel in base64)
test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

print("\n☁️ Testing Cloudinary upload...")

try:
    # Upload test image
    result = cloudinary.uploader.upload(
        f"data:image/png;base64,{test_image_base64}",
        folder="generated/test",
        public_id="test_image_connection",
        resource_type="image"
    )
    
    print(f"\n✅ Cloudinary Connected Successfully!")
    print(f"✅ Image URL: {result['secure_url']}")
    print(f"✅ Public ID: {result['public_id']}")
    print(f"✅ Format: {result['format']}")
    print(f"✅ Size: {result['bytes']} bytes")
    print(f"✅ Upload timestamp: {result['created_at']}")
    
    # Clean up (delete test image)
    print("\n🧹 Cleaning up test image...")
    cloudinary.uploader.destroy(result['public_id'])
    print("✅ Test image deleted")
    
    print("\n🎉 Cloudinary is working perfectly!")
    print("\n💡 You can view uploads in Cloudinary Dashboard:")
    print("   https://cloudinary.com/console/media_library")
    
except Exception as e:
    print(f"\n❌ Cloudinary Connection Failed!")
    print(f"Error: {e}\n")
    print("💡 Troubleshooting:")
    print("1. Check .env file has correct CLOUDINARY credentials")
    print("2. Make sure you clicked 'Reveal' for API Secret")
    print("3. No spaces or quotes around values in .env")
    print("4. Format: CLOUDINARY_CLOUD_NAME=value (no spaces around =)")