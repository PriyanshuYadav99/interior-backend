"""
🎯 PROMPT CONSTRUCTION SYSTEM - ULTRA-STRICT LAYOUT VERSION
Maintains FIXED room layouts while applying user-selected themes
"""

from config import (
    FIXED_ROOM_LAYOUTS, 
    INTERIOR_STYLES, 
    THEME_ELEMENTS,
    ROOM_DESCRIPTIONS
)
import re


def detect_theme_from_custom_prompt(custom_prompt):
    """
    Analyze custom prompt and extract theme keywords
    Returns theme category and custom elements
    """
    prompt_lower = custom_prompt.lower()
    
    # Theme detection keywords
    theme_keywords = {
        'space': ['space', 'galaxy', 'cosmic', 'star', 'planet', 'astronaut', 'nebula', 'universe'],
        'tropical': ['tropical', 'palm', 'beach', 'island', 'paradise', 'jungle', 'exotic'],
        'forest': ['forest', 'woodland', 'nature', 'botanical', 'garden', 'leaf', 'tree'],
        'ocean': ['ocean', 'sea', 'nautical', 'marine', 'beach', 'coastal', 'wave'],
        'sunset': ['sunset', 'sunrise', 'golden hour', 'warm glow', 'dusk'],
        'minimalist': ['minimal', 'simple', 'clean', 'zen', 'plain'],
        'luxury': ['luxury', 'luxe', 'opulent', 'elegant', 'premium', 'high-end'],
        'industrial': ['industrial', 'urban', 'loft', 'warehouse', 'exposed'],
        'batman': ['batman', 'gotham', 'dark knight', 'superhero'],
        'marvel': ['marvel', 'avengers', 'superhero', 'iron man', 'spider'],
        'gaming': ['gaming', 'gamer', 'esports', 'xbox', 'playstation']
    }
    
    detected_theme = None
    for theme, keywords in theme_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            detected_theme = theme
            break
    
    return detected_theme, custom_prompt


def deconstruct_theme_to_realistic_elements(custom_prompt):
    """
    LEGACY FUNCTION - kept for backward compatibility with app.py
    Returns theme elements dictionary
    """
    detected_theme, original = detect_theme_from_custom_prompt(custom_prompt)
    
    if detected_theme and detected_theme in THEME_ELEMENTS.get('color_palettes', {}):
        return {
            'colors': THEME_ELEMENTS['color_palettes'][detected_theme],
            'textures': THEME_ELEMENTS['wall_textures'][detected_theme],
            'textiles': THEME_ELEMENTS['textiles'][detected_theme],
            'decor': THEME_ELEMENTS['decor_items'][detected_theme],
            'lighting': THEME_ELEMENTS['lighting_style'][detected_theme],
            'accents': f'{detected_theme} themed decorative elements',
            'theme_name': detected_theme
        }
    
    # If no theme detected, return generic modern style with custom prompt
    return {
        'colors': 'neutral tones with pops of color',
        'textures': 'smooth textured walls',
        'textiles': f'{original} style bedding and soft furnishings',
        'decor': f'{original} inspired decorative items',
        'lighting': 'modern lighting with warm ambiance',
        'accents': f'{original} design elements',
        'theme_name': 'custom'
    }


def translate_custom_prompt_to_decorative_only(custom_prompt, room_type):
    """
    🔥 NEW FUNCTION: Convert user's custom prompt into DECORATIVE-ONLY instructions
    This prevents the prompt from affecting layout
    """
    detected_theme, original = detect_theme_from_custom_prompt(custom_prompt)
    
    # Theme-specific decorative translations
    decorative_instructions = {
        'batman': {
            'wall_decor': 'Batman logo wall art, Gotham city skyline wall decals on back wall behind bed',
            'colors': 'dark grey walls, black and yellow accent colors',
            'textiles': 'black bedding with subtle Batman emblem on throw pillows',
            'accessories': 'small Batman figurines on nightstands, black and yellow decorative items',
            'lighting': 'warm ambient lighting with yellow/gold accent glow'
        },
        'space': {
            'wall_decor': 'galaxy nebula wall art, moon phase prints',
            'colors': 'deep navy blue walls with purple accents',
            'textiles': 'dark blue bedding with starfield pattern on pillows',
            'accessories': 'small planet models, LED star lights on nightstands',
            'lighting': 'blue/purple LED accent lighting'
        },
        'tropical': {
            'wall_decor': 'large palm leaf prints, tropical botanical art',
            'colors': 'white walls with turquoise and coral accents',
            'textiles': 'bright tropical print bedding, palm leaf throw pillows',
            'accessories': 'small potted tropical plants, bamboo decor items',
            'lighting': 'warm natural lighting'
        },
        'gaming': {
            'wall_decor': 'gaming posters, LED strip lights along edges',
            'colors': 'dark grey walls with RGB accent colors',
            'textiles': 'gaming-themed bedding, controller-print pillows',
            'accessories': 'small gaming figurines, LED lights on nightstands',
            'lighting': 'RGB LED strips, colorful ambient lighting'
        },
        'marvel': {
            'wall_decor': 'Marvel superhero posters, Avengers logo wall art',
            'colors': 'red, blue, and gold accent colors on neutral walls',
            'textiles': 'superhero-themed bedding, Marvel character throw pillows',
            'accessories': 'small superhero figurines, comic book displays',
            'lighting': 'dynamic colored LED accent lighting'
        },
        'ocean': {
            'wall_decor': 'ocean wave photography, nautical artwork',
            'colors': 'blue and white color scheme with sandy beige accents',
            'textiles': 'blue ocean-themed bedding, wave-pattern pillows',
            'accessories': 'seashells, coral decorations, small marine items',
            'lighting': 'cool blue-tinted ambient lighting'
        }
    }
    
    # If we have a specific theme translation, use it
    if detected_theme and detected_theme in decorative_instructions:
        return decorative_instructions[detected_theme]
    
    # Otherwise, create generic decorative instructions from the prompt
    return {
        'wall_decor': f'{original} themed wall art and prints',
        'colors': f'{original} inspired color palette for walls and accents',
        'textiles': f'{original} themed bedding patterns and throw pillows',
        'accessories': f'{original} inspired small decorative items',
        'lighting': f'{original} appropriate lighting atmosphere'
    }


def construct_fixed_layout_prompt(room_type, style=None, custom_prompt=None):
    """
    🎯 MAIN PROMPT CONSTRUCTOR - ULTRA-STRICT VERSION
    Creates ultra-detailed prompt with IMMUTABLE layout + variable decorations
    """
    
    # Get fixed layout for this room
    if room_type not in FIXED_ROOM_LAYOUTS:
        return {
            'success': False,
            'error': f'Room type {room_type} not supported'
        }
    
    layout = FIXED_ROOM_LAYOUTS[room_type]
    
    # ====================================================================
    # PART 0: ULTRA-CRITICAL LAYOUT LOCK
    # ====================================================================
    
    layout_lock = f"""⚠️⚠️⚠️ ARCHITECTURAL RENDERING - FIXED STRUCTURE ⚠️⚠️⚠️

THIS IS NOT A CREATIVE GENERATION. THIS IS AN ARCHITECTURAL VISUALIZATION.
YOU MUST RENDER THE EXACT ROOM LAYOUT SPECIFIED BELOW.

🔒 ABSOLUTE REQUIREMENTS:
1. Room dimensions: {layout['room_size']} - EXACT, DO NOT CHANGE
2. Camera angle: {layout['camera_angle']} - EXACT, DO NOT CHANGE
3. Flooring: {layout['flooring']} - EXACT, DO NOT CHANGE
4. All furniture positions listed below are LOCKED and CANNOT BE MOVED

🎨 WHAT YOU MAY CUSTOMIZE:
- Wall paint colors and decorative wall art
- Bedding colors and pillow patterns
- Small decorative accessories (books, plants, figurines on existing surfaces)
- Lighting color temperature (not fixture positions)

❌ WHAT YOU ABSOLUTELY CANNOT DO:
- Move any furniture from its specified position
- Add or remove doors, windows, or walls
- Change the camera angle or room dimensions
- Rearrange the furniture layout
- Add large furniture pieces not listed below

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

    # ====================================================================
    # PART 1: IMMUTABLE ARCHITECTURE
    # ====================================================================
    
    fixed_structure = f"""

FIXED ARCHITECTURAL BLUEPRINT (RENDER EXACTLY AS SPECIFIED):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAMERA SPECIFICATIONS:
• Position: {layout['camera_angle']}
• Equipment: Canon EOS R5, 24mm wide-angle, f/8 aperture
• Quality: Professional architectural photography

ROOM DIMENSIONS (LOCKED):
• Size: {layout['room_size']}
• Floor: {layout['flooring']}
• Ceiling: {layout['ceiling']}"""
    
    # Add wall specifications with MAXIMUM emphasis
    if 'layout' in layout:
        fixed_structure += "\n\n🏗️ WALL CONFIGURATION (EXACT - DO NOT MODIFY):"
        for element, description in layout['layout'].items():
            element_name = element.replace('_', ' ').upper()
            fixed_structure += f"\n\n{element_name}:"
            fixed_structure += f"\n{description}"
            
            # Special emphasis for back wall (no door issue)
            if 'back_wall' in element:
                fixed_structure += "\n⚠️ CRITICAL: This wall is SOLID with NO doors, NO windows, ONLY the bed and decorative elements"
    
    # Add furniture with position coordinates if possible
    if 'furniture_positions' in layout:
        fixed_structure += "\n\n🪑 FURNITURE LAYOUT (POSITIONS ARE LOCKED - DO NOT MOVE):"
        for item, position in layout['furniture_positions'].items():
            item_name = item.replace('_', ' ').upper()
            fixed_structure += f"\n\n{item_name}:"
            fixed_structure += f"\n{position}"
            fixed_structure += "\n⚠️ This item's position CANNOT be changed"
    
    # ====================================================================
    # PART 2: DECORATIVE THEME APPLICATION
    # ====================================================================
    
    theme_styling = ""
    
    if custom_prompt:
        # 🔥 NEW: Translate custom prompt to decorative instructions only
        decorative_guide = translate_custom_prompt_to_decorative_only(custom_prompt, room_type)
        
        theme_styling = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 DECORATIVE THEME APPLICATION: "{custom_prompt}"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ CRITICAL REMINDER: The layout above is FIXED. Apply this theme through:

1️⃣ WALL COLORS & DECORATION:
{decorative_guide['colors']}
Wall art placement: {decorative_guide['wall_decor']}
⚠️ Apply to existing walls only - do not add/remove walls

2️⃣ TEXTILES (bedding, pillows, throws):
{decorative_guide['textiles']}
⚠️ Change patterns/colors only - bed position stays the same

3️⃣ SMALL ACCESSORIES:
{decorative_guide['accessories']}
⚠️ Place on existing surfaces (nightstands, floor near corners) only

4️⃣ LIGHTING ATMOSPHERE:
{decorative_guide['lighting']}
⚠️ Adjust color/warmth only - existing fixtures stay in place:"""
        
        # Add lighting structure
        if 'lighting_structure' in layout:
            for light_type, light_desc in layout['lighting_structure'].items():
                theme_styling += f"\n   • {light_type}: {light_desc}"
        
        theme_styling += f"""

🚫 FORBIDDEN ACTIONS FOR THIS THEME:
- Do NOT rearrange furniture to match the theme
- Do NOT add large theme-specific furniture
- Do NOT change the room structure or dimensions
- Do NOT move the bed or other major furniture
- Theme should be visible through: wall art, colors, small decor, textiles ONLY"""
    
    elif style and style in INTERIOR_STYLES:
        # Predefined style
        style_desc = INTERIOR_STYLES[style]
        
        theme_styling = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 DESIGN STYLE: {style.replace('_', ' ').title()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Style Description: {style_desc}

⚠️ Apply this style through colors, materials, and decorative accents only.
The architectural layout and furniture positions above are LOCKED.

LIGHTING (adjust atmosphere within existing fixtures):"""
        
        if 'lighting_structure' in layout:
            for light_type, light_desc in layout['lighting_structure'].items():
                theme_styling += f"\n• {light_type}: {light_desc}"
    
    # ====================================================================
    # PART 3: FINAL ENFORCEMENT
    # ====================================================================
    
    final_enforcement = """

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 RENDERING REQUIREMENTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

QUALITY:
• 8K photorealistic architectural photography
• Professional HDR lighting, accurate materials
• Sharp focus, proper shadows and reflections
• Magazine-quality output

✅ MUST RENDER:
• ALL architectural elements exactly as specified in blueprint
• ALL furniture in EXACT positions described
• Decorative theme through colors, textiles, wall art, small accessories only
• Proper room proportions and camera angle as specified

❌ MUST NOT RENDER:
• Any layout changes or furniture rearrangement
• People, pets, or living beings
• Additional structural elements (doors, windows, walls) not specified
• Fantasy or cartoon elements

⚠️⚠️⚠️ FINAL CRITICAL REMINDER ⚠️⚠️⚠️
This is an ARCHITECTURAL RENDERING with FIXED LAYOUT.
Only decorative elements (colors, art, small accessories) vary.
The room structure and furniture positions are IMMUTABLE."""
    
    # ====================================================================
    # COMBINE ALL PARTS
    # ====================================================================
    
    full_prompt = layout_lock + fixed_structure + theme_styling + final_enforcement
    
    # Aggressive truncation if needed - keep layout lock and structure
    if len(full_prompt) > 3900:
        # Keep the most critical parts
        full_prompt = (layout_lock + fixed_structure + 
                      f"\n\n🎨 THEME: {custom_prompt if custom_prompt else style}\n" +
                      "Apply through wall colors, textiles, small decorative items ONLY. " +
                      "Layout LOCKED." + final_enforcement)
    
    return {
        'success': True,
        'prompt': full_prompt,
        'room_type': room_type,
        'style': style or 'custom',
        'theme': custom_prompt if custom_prompt else style
    }


def construct_prompt(room_type, style=None, custom_prompt=None):
    """
    Wrapper function for backward compatibility
    Calls the new fixed layout system
    """
    return construct_fixed_layout_prompt(room_type, style, custom_prompt)


def validate_inputs(room_type, style, custom_prompt):
    """
    Validate user inputs before generation
    """
    if not room_type:
        return False, "Room type is required"
    
    if room_type not in FIXED_ROOM_LAYOUTS:
        return False, f"Room type '{room_type}' is not supported. Available: {', '.join(FIXED_ROOM_LAYOUTS.keys())}"
    
    if not style and not custom_prompt:
        return False, "Either style or custom prompt is required"
    
    if custom_prompt and len(custom_prompt) > 500:
        return False, "Custom prompt too long (max 500 characters)"
    
    return True, "Valid"


def get_short_prompt_for_cache(room_type, style=None, custom_prompt=None):
    """
    Generate a shorter version for caching purposes
    """
    if custom_prompt:
        theme_elements = detect_theme_from_custom_prompt(custom_prompt)
        return f"{room_type}_{theme_elements[0] if theme_elements[0] else 'custom'}_{custom_prompt[:30]}"
    else:
        return f"{room_type}_{style}"