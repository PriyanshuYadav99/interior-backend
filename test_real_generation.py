#!/usr/bin/env python3
"""
Real Generation Timing Test
This performs an ACTUAL image generation and times each step
"""

import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

print("\n" + "="*80)
print("REAL GENERATION TIMING TEST")
print("="*80)
print("⚠️  WARNING: This will use your Replicate API credits!")
print("This test will take 6-10 seconds and generate a real image.")
print("="*80)

response = input("\nProceed? (yes/no): ")
if response.lower() != 'yes':
    print("Test cancelled.")
    exit(0)

print("\nStarting real generation test...\n")

# Import everything
from app import (
    generate_interior_design_unified,
    load_reference_image,
    construct_prompt,
    optimize_prompt_for_gpt_image1,
    get_cached_model_version
)

# Timing breakdown
timings = {}

# ============================================================
# STEP 1: Cache check
# ============================================================
print("[STEP 1/6] Checking model version cache...")
start = time.time()
version = get_cached_model_version()
timings['cache_check'] = time.time() - start
print(f"   ✅ Cache check: {timings['cache_check']:.3f}s")
print(f"   Version: {version[:20]}...")

# ============================================================
# STEP 2: Load reference image
# ============================================================
print("\n[STEP 2/6] Loading reference image...")
start = time.time()
ref_image = load_reference_image('living_room', 'skyline')
timings['load_image'] = time.time() - start
print(f"   ✅ Image loaded: {timings['load_image']:.3f}s")
print(f"   Image size: {len(ref_image)} chars")

# ============================================================
# STEP 3: Construct prompt
# ============================================================
print("\n[STEP 3/6] Building prompt...")
start = time.time()
prompt_data = construct_prompt('living_room', 'modern', '')
prompt = prompt_data['prompt']
timings['build_prompt'] = time.time() - start
print(f"   ✅ Prompt built: {timings['build_prompt']:.3f}s")
print(f"   Length: {len(prompt)} chars")

# ============================================================
# STEP 4: Optimize prompt
# ============================================================
print("\n[STEP 4/6] Optimizing prompt...")
start = time.time()
prompt = optimize_prompt_for_gpt_image1(prompt, 'living_room')
timings['optimize_prompt'] = time.time() - start
print(f"   ✅ Prompt optimized: {timings['optimize_prompt']:.3f}s")

# ============================================================
# STEP 5: Generate image (THE BIG ONE)
# ============================================================
print("\n[STEP 5/6] 🎨 GENERATING IMAGE (this takes 6-7 seconds)...")
print("   Calling Replicate API...")

generation_start = time.time()

result = generate_interior_design_unified(
    prompt=prompt,
    reference_image_base64=ref_image,
    room_type='living_room',
    is_custom_theme=False
)

timings['generation'] = time.time() - generation_start

if result.get('success'):
    print(f"   ✅ Image generated: {timings['generation']:.2f}s")
    print(f"   Model: {result.get('model')}")
    print(f"   Method: {result.get('method')}")
else:
    print(f"   ❌ Generation failed: {result.get('error')}")
    exit(1)

# ============================================================
# STEP 6: Calculate totals
# ============================================================
print("\n[STEP 6/6] Calculating total time...")

total_time = sum(timings.values())

print("\n" + "="*80)
print("DETAILED TIMING BREAKDOWN")
print("="*80)
print(f"   1. Cache check:       {timings['cache_check']:>6.3f}s")
print(f"   2. Load image:        {timings['load_image']:>6.3f}s")
print(f"   3. Build prompt:      {timings['build_prompt']:>6.3f}s")
print(f"   4. Optimize prompt:   {timings['optimize_prompt']:>6.3f}s")
print(f"   5. Generate image:    {timings['generation']:>6.2f}s")
print("   " + "-"*35)
print(f"   TOTAL TIME:           {total_time:>6.2f}s")
print("="*80)

# Analysis
print("\nANALYSIS")
print("="*80)

pre_generation = (timings['cache_check'] + timings['load_image'] + 
                 timings['build_prompt'] + timings['optimize_prompt'])

print(f"   Pre-generation overhead:  {pre_generation:.3f}s")
print(f"   Actual generation:        {timings['generation']:.2f}s")

if total_time <= 7.5:
    print("\n   ✅ EXCELLENT! Your generation is FAST!")
    print("      Total time under 7.5 seconds.")
elif total_time <= 10:
    print("\n   ✅ GOOD! Your generation is acceptable.")
    print("      Total time under 10 seconds.")
elif total_time <= 12:
    print("\n   ⚠️  SLOW: Total time over 10 seconds.")
    if pre_generation > 1.0:
        print("      Issue: Pre-generation overhead too high")
        print("      Fix: Check image loading and prompt construction")
    else:
        print("      Issue: Replicate API slower than usual")
        print("      Fix: Check network connection or try again")
else:
    print("\n   ❌ VERY SLOW: Total time over 12 seconds!")
    if timings['cache_check'] > 1.0:
        print("      Issue: Cache not working (fetching model version)")
        print("      Fix: Check Step 1 in fix guide")
    elif timings['generation'] > 10:
        print("      Issue: Replicate API very slow")
        print("      Fix: Check Replicate status or network")
    else:
        print("      Issue: Multiple small delays adding up")
        print("      Fix: Review all pre-generation steps")

# Compare to expected
print("\n" + "="*80)
print("COMPARISON TO EXPECTED TIMES")
print("="*80)

expected = {
    'cache_check': 0.001,
    'load_image': 0.05,
    'build_prompt': 0.05,
    'optimize_prompt': 0.01,
    'generation': 6.5
}

print(f"{'Step':<20} {'Actual':>10} {'Expected':>10} {'Status':>10}")
print("-"*52)

for key, expected_time in expected.items():
    actual = timings[key]
    if actual <= expected_time * 2:
        status = "✅"
    elif actual <= expected_time * 3:
        status = "⚠️"
    else:
        status = "❌"
    
    print(f"{key:<20} {actual:>9.3f}s {expected_time:>9.3f}s {status:>10}")

print("="*80)

if total_time <= 8:
    print("\n🎉 SUCCESS! Your system is optimized!")
    print("   This is as fast as it gets with Replicate.")
else:
    print("\n📊 Check the comparison table above to see what's slow.")

print("\n" + "="*80)