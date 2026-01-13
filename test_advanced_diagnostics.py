#!/usr/bin/env python3
"""
Advanced Performance Diagnostics
Find WHERE the 15 seconds are being spent
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("\n" + "="*80)
print("ADVANCED PERFORMANCE DIAGNOSTICS")
print("="*80)

# Test 1: Import speed
print("\n[TEST 1] Import Speed Test")
print("-" * 80)
start = time.time()
from app import (
    generate_interior_design_unified,
    load_reference_image,
    construct_prompt,
    optimize_prompt_for_gpt_image1
)
import_time = time.time() - start
print(f"✅ Imports took: {import_time:.3f}s")

# Test 2: Reference image loading
print("\n[TEST 2] Reference Image Loading")
print("-" * 80)
start = time.time()
ref_image = load_reference_image('living_room', 'skyline')
load_time = time.time() - start
print(f"{'✅' if ref_image else '❌'} Image loading took: {load_time:.3f}s")
print(f"   Image size: {len(ref_image) if ref_image else 0} chars (base64)")

# Test 3: Prompt construction
print("\n[TEST 3] Prompt Construction")
print("-" * 80)
start = time.time()
prompt_data = construct_prompt('living_room', 'modern', '')
prompt_time = time.time() - start
print(f"✅ Prompt construction took: {prompt_time:.3f}s")
print(f"   Prompt length: {len(prompt_data.get('prompt', ''))} chars")

# Test 4: Prompt optimization
print("\n[TEST 4] Prompt Optimization")
print("-" * 80)
start = time.time()
optimized = optimize_prompt_for_gpt_image1(prompt_data['prompt'], 'living_room')
optimize_time = time.time() - start
print(f"✅ Prompt optimization took: {optimize_time:.3f}s")

# Test 5: Full generation simulation (WITHOUT actual API call)
print("\n[TEST 5] Pre-Generation Steps (No API Call)")
print("-" * 80)
total_start = time.time()

step1_start = time.time()
ref_image = load_reference_image('living_room', 'skyline')
step1_time = time.time() - step1_start

step2_start = time.time()
prompt_data = construct_prompt('living_room', 'modern', '')
step2_time = time.time() - step2_start

step3_start = time.time()
optimized = optimize_prompt_for_gpt_image1(prompt_data['prompt'], 'living_room')
step3_time = time.time() - step3_start

total_pre = time.time() - total_start

print(f"   1. Load image: {step1_time:.3f}s")
print(f"   2. Build prompt: {step2_time:.3f}s")
print(f"   3. Optimize prompt: {step3_time:.3f}s")
print(f"   ─────────────────────────")
print(f"   Total pre-gen: {total_pre:.3f}s")

# Test 6: Estimate full generation time
print("\n" + "="*80)
print("ESTIMATED FULL GENERATION BREAKDOWN")
print("="*80)
print(f"   Pre-generation steps: {total_pre:.2f}s")
print(f"   Model version (cached): 0.001s")
print(f"   API prediction creation: ~0.5s")
print(f"   Image generation (Replicate): ~6-7s")
print(f"   Image download: ~0.3s")
print(f"   ─────────────────────────")
print(f"   EXPECTED TOTAL: ~{total_pre + 0.001 + 0.5 + 6.5 + 0.3:.1f}s")

# Test 7: Check for hidden issues
print("\n" + "="*80)
print("CHECKING FOR COMMON SLOWDOWN ISSUES")
print("="*80)

issues_found = []

if total_pre > 1.0:
    issues_found.append(f"⚠️  Pre-generation steps too slow: {total_pre:.2f}s (should be <0.5s)")

if step1_time > 0.3:
    issues_found.append(f"⚠️  Image loading slow: {step1_time:.2f}s (should be <0.1s)")

if step2_time > 0.3:
    issues_found.append(f"⚠️  Prompt construction slow: {step2_time:.2f}s (should be <0.1s)")

# Check imports
import requests
start = time.time()
test_req = requests.get("https://www.google.com", timeout=5)
network_time = time.time() - start
print(f"   Network test (google.com): {network_time:.3f}s")

if network_time > 1.0:
    issues_found.append(f"⚠️  Slow network: {network_time:.2f}s (should be <0.5s)")

if not issues_found:
    print("   ✅ No obvious issues found")
else:
    print("\n   Issues detected:")
    for issue in issues_found:
        print(f"   {issue}")

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)

if total_pre + 6.5 > 10:
    print("❌ Your pre-generation steps are adding overhead!")
    print("   This could explain the extra 3-4 seconds.")
    print("\n   Recommendations:")
    print("   1. Check if Supabase queries are blocking")
    print("   2. Remove any synchronous database calls")
    print("   3. Disable scheduler during generation")
else:
    print("✅ Pre-generation overhead is acceptable")
    print("   If you're still seeing 15s, the issue is in:")
    print("   1. Replicate API polling (check logs for 'succeeded' time)")
    print("   2. Network latency to Replicate")
    print("   3. Background threads blocking (Cloudinary upload?)")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Make a real generation request")
print("2. Check Flask logs for these lines:")
print("   - '[CACHE] Using cached model version' (should be 0.001s)")
print("   - '[SUCCESS] ⚡ STYLE-BASED: X.XXs' (should be 6-7s)")
print("3. If still slow, the issue is in Replicate polling")
print("4. Run: python test_real_generation.py (next test)")
print("="*80)
