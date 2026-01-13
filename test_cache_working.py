import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after setting path
from dotenv import load_dotenv
load_dotenv()

# Now test the cache
print("\n" + "="*70)
print("TESTING MODEL VERSION CACHE")
print("="*70)

# Test 1: First call (should fetch - takes 2-3 seconds)
print("\nTest 1: First call (should fetch from API)...")
start1 = time.time()
from app import get_cached_model_version
version1 = get_cached_model_version()
time1 = time.time() - start1
print(f"Result: {version1[:20] if version1 else 'FAILED'}... took {time1:.2f}s")

# Test 2: Second call (should use cache - takes <0.1 seconds)
print("\nTest 2: Second call (should use cache)...")
start2 = time.time()
version2 = get_cached_model_version()
time2 = time.time() - start2
print(f"Result: {version2[:20] if version2 else 'FAILED'}... took {time2:.3f}s")

# Test 3: Third call (should still use cache)
print("\nTest 3: Third call (should still use cache)...")
start3 = time.time()
version3 = get_cached_model_version()
time3 = time.time() - start3
print(f"Result: {version3[:20] if version3 else 'FAILED'}... took {time3:.3f}s")

# Results
print("\n" + "="*70)
print("RESULTS")
print("="*70)
print(f"Call 1 (fetch): {time1:.2f}s - {'✅ OK' if time1 > 0.5 else '❌ TOO FAST'}")
print(f"Call 2 (cache): {time2:.3f}s - {'✅ OK' if time2 < 0.1 else '❌ TOO SLOW'}")
print(f"Call 3 (cache): {time3:.3f}s - {'✅ OK' if time3 < 0.1 else '❌ TOO SLOW'}")
print(f"All same: {'✅ YES' if version1 == version2 == version3 else '❌ NO'}")

if time2 < 0.1 and time3 < 0.1 and version1 == version2 == version3:
    print("\n🎉 CACHE IS WORKING PERFECTLY!")
else:
    print("\n❌ CACHE NOT WORKING - CHECK STEP 1 & 2")

print("="*70)