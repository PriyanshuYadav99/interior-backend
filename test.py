import requests
import json

# ✅ TEST YOUR MODELSLAB API KEY
MODELSLAB_API_KEY = "26cAAXB8gZeOgg5E6ls2eQzEfbSmIx4QVlvgnK7ryFdKi8lYk8B96SZggq3u"  # Replace with your actual key

# Simple test to verify if your API key works
def test_api_key():
    """Test if the API key is valid by making a simple request"""
    
    url = "https://modelslab.com/api/v5/controlnet"
    
    payload = {
        "key": MODELSLAB_API_KEY,
        "controlnet_model": "canny",
        "controlnet_type": "canny",
        "model_id": "midjourney",
        "auto_hint": "yes",
        "guess_mode": "no",
        "prompt": "a beautiful room",
        "negative_prompt": "blurry",
        "init_image": "https://huggingface.co/takuma104/controlnet_dev/resolve/main/gen_compare/control_images/converted/control_human_openpose.png",
        "mask_image": None,
        "width": "512",
        "height": "512",
        "samples": "1",
        "num_inference_steps": "30",
        "scheduler": "UniPCMultistepScheduler",
        "safety_checker": "no",
        "enhance_prompt": "no",
        "guidance_scale": 7.5,
        "strength": 0.55,
        "seed": None,
        "webhook": None,
        "track_id": None
    }
    
    print("Testing ModelsLab API key...")
    print(f"Endpoint: {url}")
    print(f"API Key (first 10 chars): {MODELSLAB_API_KEY[:10]}...")
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"\n{'='*60}")
        print(f"Status Code: {response.status_code}")
        print(f"Response Text:\n{response.text}")
        print(f"{'='*60}\n")
        
        result = response.json()
        
        if result.get("status") == "error":
            print(f"❌ ERROR: {result.get('messege', result.get('message'))}")
            print(f"Tip: {result.get('tip', 'N/A')}")
            return False
        else:
            print("✅ API Key is VALID!")
            print(f"Response keys: {list(result.keys())}")
            return True
            
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False

# Run the test
if __name__ == "__main__":
    test_api_key()