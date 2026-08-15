#!/usr/bin/env python3
"""
Quick diagnostic: Find where cache variables are defined in app.py
"""

import os

app_file = 'app.py'

if not os.path.exists(app_file):
    print("❌ app.py not found in current directory")
    exit(1)

print("\n" + "="*70)
print("SEARCHING FOR CACHE VARIABLE LOCATIONS IN app.py")
print("="*70)

with open(app_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find cache-related lines
found_cache_vars = False
found_cloudinary = False
found_flask_init = False

cloudinary_line = None
flask_line = None
cache_line = None

for i, line in enumerate(lines, 1):
    # Find Cloudinary config
    if 'cloudinary.config' in line:
        cloudinary_line = i
        found_cloudinary = True
        print(f"\n✅ Found Cloudinary config at line {i}")
    
    # Find Flask init
    if 'app = Flask(__name__)' in line and not found_flask_init:
        flask_line = i
        found_flask_init = True
        print(f"✅ Found Flask initialization at line {i}")
    
    # Find cache variables
    if '_cached_model_version = None' in line:
        cache_line = i
        found_cache_vars = True
        print(f"✅ Found cache variables at line {i}")

print("\n" + "="*70)
print("ANALYSIS")
print("="*70)

if not found_cache_vars:
    print("❌ CRITICAL: Cache variables NOT FOUND!")
    print("   You need to add these 3 lines:")
    print("   _cached_model_version = None")
    print("   _version_cache_time = None")
    print("   VERSION_CACHE_DURATION = 3600")
elif cache_line and cloudinary_line and flask_line:
    print(f"\nCloudinary config:     line {cloudinary_line}")
    print(f"Flask initialization:  line {flask_line}")
    print(f"Cache variables:       line {cache_line}")
    
    # Check if cache is in correct position
    if cloudinary_line < cache_line < flask_line:
        print("\n✅ CORRECT POSITION!")
        print("   Cache variables are between Cloudinary and Flask init")
        print("   This is the right place.")
    elif cache_line < cloudinary_line:
        print("\n⚠️  ACCEPTABLE POSITION")
        print("   Cache variables are before Cloudinary config")
        print("   This should work, but not ideal")
    elif cache_line > flask_line:
        print("\n❌ WRONG POSITION!")
        print("   Cache variables are AFTER Flask initialization")
        print("   They should be BEFORE the Flask init")
        print(f"   Move lines {cache_line}-{cache_line+2} to line {flask_line-1}")
    else:
        print("\n⚠️  UNUSUAL POSITION")
        print("   Please check the cache variable location manually")

    # Check distance from function
    print("\n" + "-"*70)
    print("Checking for get_cached_model_version function...")
    
    for i, line in enumerate(lines, 1):
        if 'def get_cached_model_version' in line:
            function_line = i
            print(f"✅ Found function at line {function_line}")
            
            if function_line > cache_line:
                distance = function_line - cache_line
                print(f"   Distance: {distance} lines")
                if distance < 100:
                    print("   ✅ Close enough - should work")
                else:
                    print("   ⚠️  Very far - might be an issue")
            else:
                print("   ❌ CRITICAL: Function is BEFORE cache variables!")
                print("   Cache variables must be defined BEFORE the function!")
            break

print("\n" + "="*70)
print("RECOMMENDATION")
print("="*70)

if not found_cache_vars:
    print("Add cache variables after Cloudinary config (around line 120)")
elif cache_line and flask_line and cache_line > flask_line:
    print(f"Move cache variables (lines {cache_line}-{cache_line+2})")
    print(f"To right after Cloudinary config (around line {cloudinary_line + 8})")
else:
    print("Cache variable position looks OK.")
    print("The issue might be elsewhere. Check:")
    print("  1. Are you using 'global' keyword in the function?")
    print("  2. Is the function being called correctly?")
    print("  3. Try adding debug prints in get_cached_model_version()")

print("="*70)