
# """
# FIXED PROMPTS.PY - Optimized for GPT Image 1
# Supports both predefined styles AND custom themes with reference images
# """

# from config import (
#     FIXED_ROOM_LAYOUTS, 
#     INTERIOR_STYLES, 
#     THEME_ELEMENTS,
#     ROOM_DESCRIPTIONS
# )
# import re


# def detect_theme_from_custom_prompt(custom_prompt):
#     """Analyze custom prompt and extract theme keywords"""
#     prompt_lower = custom_prompt.lower()
    
#     theme_keywords = {
#         'space': ['space', 'galaxy', 'cosmic', 'star', 'planet', 'astronaut', 'nebula', 'universe'],
#         'tropical': ['tropical', 'palm', 'beach', 'island', 'paradise', 'jungle', 'exotic'],
#         'forest': ['forest', 'woodland', 'nature', 'botanical', 'garden', 'leaf', 'tree'],
#         'ocean': ['ocean', 'sea', 'nautical', 'marine', 'beach', 'coastal', 'wave'],
#         'sunset': ['sunset', 'sunrise', 'golden hour', 'warm glow', 'dusk'],
#         'minimalist': ['minimal', 'simple', 'clean', 'zen', 'plain'],
#         'luxury': ['luxury', 'luxe', 'opulent', 'elegant', 'premium', 'high-end'],
#         'industrial': ['industrial', 'urban', 'loft', 'warehouse', 'exposed'],
#     }
    
#     detected_theme = None
#     for theme, keywords in theme_keywords.items():
#         if any(keyword in prompt_lower for keyword in keywords):
#             detected_theme = theme
#             break
    
#     return detected_theme, custom_prompt


# def extract_theme_elements(custom_theme):
#     """
#     Extract visual elements from custom theme for image-to-image generation
#     Returns color palette, textures, and styling instructions
#     """
#     theme_lower = custom_theme.lower()
    
#     # Predefined theme mappings
#     theme_mappings = {
#         'superman': {
#             'colors': 'bold red, royal blue, bright yellow, primary colors',
#             'textures': 'smooth heroic surfaces, metallic accents, cape-like fabrics',
#             'decor': 'S-shield motifs, superhero memorabilia, comic book art',
#             'mood': 'heroic, powerful, bold, inspirational'
#         },
#         'batman': {
#             'colors': 'dark black, charcoal grey, deep yellow accents, midnight blue',
#             'textures': 'leather textures, industrial metals, dark matte surfaces',
#             'decor': 'bat symbols, gothic elements, dark knight aesthetics',
#             'mood': 'dark, mysterious, gothic, vigilante atmosphere'
#         },
#         'underwater': {
#             'colors': 'deep ocean blue, turquoise, seafoam green, coral pink, pearl white',
#             'textures': 'flowing fabrics, wave patterns, bubble effects, glass-like surfaces',
#             'decor': 'seashells, coral decorations, marine life art, nautical elements',
#             'mood': 'tranquil, flowing, aquatic, serene underwater atmosphere'
#         },
#         'spiderman': {
#             'colors': 'vibrant red, electric blue, black web patterns',
#             'textures': 'web-textured walls, spider silk fabrics, urban textures',
#             'decor': 'spider web patterns, NYC skyline art, comic elements',
#             'mood': 'dynamic, youthful, urban superhero vibe'
#         },
#         'avengers': {
#             'colors': 'red, gold, blue, silver, heroic color scheme',
#             'textures': 'high-tech surfaces, metallic finishes, futuristic materials',
#             'decor': 'A-logo, superhero ensemble art, modern tech aesthetics',
#             'mood': 'epic, heroic, team spirit, modern superhero headquarters'
#         },
#         'harry potter': {
#             'colors': 'burgundy red, gold, dark wood tones, emerald green',
#             'textures': 'vintage wood, aged leather, magical fabrics, antique finishes',
#             'decor': 'wizard artifacts, potion bottles, spell books, Hogwarts elements',
#             'mood': 'magical, mystical, wizarding world atmosphere'
#         },
#         'star wars': {
#             'colors': 'space black, metallic silver, electric blue, laser red',
#             'textures': 'futuristic panels, spacecraft metals, holographic effects',
#             'decor': 'lightsaber displays, galactic art, sci-fi technology',
#             'mood': 'futuristic, galactic, sci-fi adventure atmosphere'
#         },
#         'minecraft': {
#             'colors': 'blocky greens, earthy browns, pixelated blues, grass green',
#             'textures': 'cubic patterns, pixel art style, block textures',
#             'decor': 'blocky furniture, pixelated art, crafting table aesthetics',
#             'mood': 'playful, cubic, gaming-inspired, creative builder vibe'
#         },
#         'disney': {
#             'colors': 'magical pastels, princess pinks, royal blues, fairy tale golds',
#             'textures': 'whimsical fabrics, castle-like finishes, enchanted surfaces',
#             'decor': 'castle elements, fairy tale art, magical character themes',
#             'mood': 'magical, whimsical, enchanting, fairy tale atmosphere'
#         },
#         'marvel': {
#             'colors': 'bold primary colors, metallic accents, superhero palette',
#             'textures': 'high-tech surfaces, hero costume fabrics, action-ready materials',
#             'decor': 'superhero emblems, comic panels, action figure displays',
#             'mood': 'heroic, action-packed, cinematic superhero aesthetic'
#         },
#         'jungle': {
#             'colors': 'lush green, tropical browns, vibrant flower colors, natural earth tones',
#             'textures': 'natural wood, bamboo, leafy patterns, organic materials',
#             'decor': 'tropical plants, animal prints, jungle artwork, natural elements',
#             'mood': 'wild, natural, tropical rainforest atmosphere'
#         },
#         'desert': {
#             'colors': 'sandy beige, terracotta, warm orange, sunset gold, cactus green',
#             'textures': 'rough adobe, woven textiles, natural stone, weathered wood',
#             'decor': 'cactus plants, southwestern art, desert landscape paintings',
#             'mood': 'warm, arid, southwestern, desert oasis feeling'
#         },
#         'arctic': {
#             'colors': 'icy white, glacier blue, silver grey, frost tones',
#             'textures': 'smooth ice-like finishes, fur textures, crystalline surfaces',
#             'decor': 'polar bear art, ice crystal decorations, northern lights imagery',
#             'mood': 'cool, pristine, arctic tundra, winter wonderland'
#         },
#         'cyberpunk': {
#             'colors': 'neon pink, electric blue, toxic green, dark purple, metallic chrome',
#             'textures': 'holographic surfaces, LED-lit panels, futuristic metals, neon signs',
#             'decor': 'neon lighting, digital screens, futuristic tech, urban dystopia elements',
#             'mood': 'futuristic, high-tech, neon-lit, cyberpunk dystopia'
#         },
#         'retro': {
#             'colors': 'vintage orange, mustard yellow, avocado green, burnt sienna, cream',
#             'textures': 'vintage wallpapers, shag carpets, retro plastics, wood paneling',
#             'decor': 'vintage posters, retro appliances, old-school furniture, nostalgic items',
#             'mood': 'nostalgic, vintage, 70s-80s throwback atmosphere'
#         },
#         'steampunk': {
#             'colors': 'brass gold, copper, aged brown, industrial grey, Victorian burgundy',
#             'textures': 'exposed gears, leather, riveted metal, Victorian fabrics, wood',
#             'decor': 'clockwork mechanisms, Victorian-era items, brass instruments, gauges',
#             'mood': 'Victorian industrial, mechanical, steam-powered aesthetic'
#         }
#     }
    
#     # Check for exact matches first
#     for key, elements in theme_mappings.items():
#         if key in theme_lower:
#             return elements
    
#     # If no exact match, create generic theme based on input
#     return {
#         'colors': f'{custom_theme}-inspired color palette with vibrant thematic colors',
#         'textures': f'{custom_theme}-themed textures and materials',
#         'decor': f'{custom_theme}-inspired decorative elements and artwork',
#         'mood': f'{custom_theme} atmosphere and aesthetic throughout'
#     }


# def construct_custom_theme_prompt(room_type, custom_theme):
#     """
#     Construct prompt for custom theme with image-to-image generation
#     This maintains room layout while applying custom theme
#     """
#     if room_type not in FIXED_ROOM_LAYOUTS:
#         return {
#             'success': False,
#             'error': f'Room type {room_type} not supported'
#         }
    
#     layout = FIXED_ROOM_LAYOUTS[room_type]
#     theme_elements = extract_theme_elements(custom_theme)
    
#     # Build concise but effective prompt for image-to-image
#     prompt = f"""Transform this {room_type.replace('_', ' ')} interior with a {custom_theme} theme while maintaining EXACT room layout, furniture positions, and architectural structure.

# CRITICAL: Keep all furniture, walls, doors, windows, and architectural elements in their EXACT positions.

# THEME APPLICATION:
# - Colors: {theme_elements['colors']}
# - Textures: {theme_elements['textures']}
# - Decorative Style: {theme_elements['decor']}
# - Atmosphere: {theme_elements['mood']}

# MAINTAIN UNCHANGED:
# - Room dimensions: {layout['room_size']}
# - All furniture positions and types
# - Wall layouts and architectural features
# - Camera angle: {layout['camera_angle']}
# - Floor plan and ceiling structure

# CHANGE ONLY:
# - Wall colors and textures according to {custom_theme} theme
# - Bedding/upholstery colors and patterns to match theme
# - Decorative items to {custom_theme}-themed alternatives
# - Artwork to {custom_theme}-inspired pieces
# - Lighting color temperature to enhance {custom_theme} mood
# - Small accessories to match {custom_theme} aesthetic

# Professional interior photography, maintain realistic proportions, high-end finish, 8K quality."""
    
#     return {
#         'success': True,
#         'prompt': prompt,
#         'room_type': room_type,
#         'theme': custom_theme,
#         'is_custom_theme': True,
#         'theme_elements': theme_elements
#     }


# def apply_style_to_layout(layout, style_name):
#     """
#     Apply predefined interior style modifications to the fixed layout
#     Returns modified descriptions that maintain structure but change aesthetics
#     """
#     if style_name not in INTERIOR_STYLES:
#         return {}
    
#     style_description = INTERIOR_STYLES[style_name]
    
#     # Map styles to visual modifications
#     style_modifications = {
#         'modern': {
#             'color_override': 'neutral greys, whites, black accents',
#             'material_emphasis': 'sleek surfaces, glass, polished metals',
#             'lighting_mood': 'bright cool white LED lighting',
#             'textile_style': 'smooth solid-color fabrics, minimal patterns'
#         },
#         'scandinavian': {
#             'color_override': 'soft whites, light greys, natural wood tones',
#             'material_emphasis': 'light wood, white painted surfaces, natural textiles',
#             'lighting_mood': 'warm natural daylight, soft ambient glow',
#             'textile_style': 'cozy textured fabrics, simple patterns, wool throws'
#         },
#         'industrial': {
#             'color_override': 'charcoal grey, black, raw steel, exposed concrete',
#             'material_emphasis': 'exposed brick, metal fixtures, concrete finishes',
#             'lighting_mood': 'warm Edison bulbs, exposed filament lighting',
#             'textile_style': 'leather upholstery, dark linens, raw textures'
#         },
#         'minimalist': {
#             'color_override': 'pure white, light grey, subtle beige',
#             'material_emphasis': 'smooth matte surfaces, minimal hardware',
#             'lighting_mood': 'clean white LED, natural light emphasis',
#             'textile_style': 'simple solid colors, no patterns, essential pieces only'
#         },
#         'traditional': {
#             'color_override': 'rich browns, warm creams, burgundy, gold accents',
#             'material_emphasis': 'carved wood, ornate details, traditional moldings',
#             'lighting_mood': 'warm yellow lighting, traditional fixtures',
#             'textile_style': 'damask patterns, rich fabrics, decorative pillows'
#         },
#         'bohemian': {
#             'color_override': 'vibrant colors, earth tones, jewel tones mixed',
#             'material_emphasis': 'woven textures, macrame, natural fibers',
#             'lighting_mood': 'warm ambient glow, string lights, lanterns',
#             'textile_style': 'layered textiles, mixed patterns, colorful throws'
#         },
#         'luxury': {
#             'color_override': 'deep navy, gold, cream, marble white',
#             'material_emphasis': 'velvet, silk, marble, gold fixtures',
#             'lighting_mood': 'warm elegant lighting, crystal accents',
#             'textile_style': 'premium fabrics, silk bedding, velvet pillows'
#         },
#         'contemporary': {
#             'color_override': 'bold accent colors with neutral base',
#             'material_emphasis': 'mixed materials, artistic elements, modern art',
#             'lighting_mood': 'layered lighting, statement fixtures',
#             'textile_style': 'textured fabrics, geometric patterns, bold accents'
#         },
#         'coastal': {
#             'color_override': 'soft blues, whites, sandy beige, seafoam',
#             'material_emphasis': 'weathered wood, wicker, natural rope',
#             'lighting_mood': 'bright natural light, airy feel',
#             'textile_style': 'light linens, striped patterns, nautical accents'
#         },
#         'rustic': {
#             'color_override': 'warm browns, earthy tones, natural wood',
#             'material_emphasis': 'reclaimed wood, stone, rough textures',
#             'lighting_mood': 'warm ambient glow, lantern-style fixtures',
#             'textile_style': 'chunky knits, plaid patterns, cozy textiles'
#         },
#         'japanese': {
#             'color_override': 'natural wood, white, black accents, earth tones',
#             'material_emphasis': 'natural wood, rice paper, bamboo, stone',
#             'lighting_mood': 'soft diffused lighting, paper lanterns',
#             'textile_style': 'simple cotton, linen, minimal patterns'
#         },
#         'art_deco': {
#             'color_override': 'black, gold, deep jewel tones, white',
#             'material_emphasis': 'geometric patterns, metallic accents, mirrors',
#             'lighting_mood': 'dramatic lighting, gold fixtures',
#             'textile_style': 'geometric patterns, luxurious fabrics, bold designs'
#         }
#     }
    
#     return style_modifications.get(style_name, {})


# def construct_fixed_layout_prompt(room_type, style=None, custom_prompt=None):
#     """
#     OPTIMIZED FOR GPT IMAGE 1
#     Creates detailed prompts without over-truncation
#     NOW PROPERLY HANDLES PREDEFINED STYLES
#     """
    
#     if room_type not in FIXED_ROOM_LAYOUTS:
#         return {
#             'success': False,
#             'error': f'Room type {room_type} not supported'
#         }
    
#     layout = FIXED_ROOM_LAYOUTS[room_type]
    
#     # ====================================================================
#     # HANDLE STYLE APPLICATION
#     # ====================================================================
    
#     style_mods = {}
#     style_description = ""
    
#     if style and not custom_prompt:
#         # User selected a predefined style
#         if style in INTERIOR_STYLES:
#             style_mods = apply_style_to_layout(layout, style)
#             style_description = INTERIOR_STYLES[style]
#         else:
#             # Fallback if style not found
#             style_description = f"{style} interior design style"
    
#     # ====================================================================
#     # BUILD COMPREHENSIVE PROMPT FOR GPT IMAGE 1
#     # ====================================================================
    
#     prompt_parts = []
    
#     # Part 1: Core Scene Description with Style
#     if style_description:
#         prompt_parts.append(f"""Professional architectural interior photograph of a {room_type.replace('_', ' ')} designed in {style_description}.
# CAMERA: {layout['camera_angle']}
# ROOM: {layout['room_size']}
# FLOOR: {layout['flooring']}
# CEILING: {layout['ceiling']}""")
#     else:
#         prompt_parts.append(f"""Professional architectural interior photograph of a {room_type.replace('_', ' ')}.
# CAMERA: {layout['camera_angle']}
# ROOM: {layout['room_size']}
# FLOOR: {layout['flooring']}
# CEILING: {layout['ceiling']}""")
    
#     # Part 2: Fixed Layout Structure (MOST IMPORTANT)
#     if 'layout' in layout:
#         prompt_parts.append("\nFIXED LAYOUT:")
#         for element, description in layout['layout'].items():
#             element_name = element.replace('_', ' ').title()
#             prompt_parts.append(f"• {element_name}: {description}")
    
#     # Part 3: Furniture Positions
#     if 'furniture_positions' in layout:
#         prompt_parts.append("\nFURNITURE:")
#         for item, position in layout['furniture_positions'].items():
#             item_name = item.replace('_', ' ').title()
#             prompt_parts.append(f"• {item_name}: {position}")
    
#     # Part 4: Special Features
#     special_features = []
    
#     if 'wardrobe_details' in layout:
#         wd = layout['wardrobe_details']
#         special_features.append(f"Wardrobe: {wd.get('type', '')} - {wd.get('interior', '')}")
    
#     if 'circular_feature_wall' in layout:
#         cf = layout['circular_feature_wall']
#         special_features.append(f"Feature Wall: {cf.get('design', '')} with {cf.get('lighting', '')}")
    
#     if 'wall_treatments' in layout:
#         wt = layout['wall_treatments']
#         if 'left_wall' in wt:
#             special_features.append(f"Left Wall: {wt['left_wall']}")
#         if 'overall_aesthetic' in wt:
#             special_features.append(f"Overall: {wt['overall_aesthetic']}")
    
#     if special_features:
#         prompt_parts.append("\nKEY FEATURES:")
#         for feature in special_features:
#             prompt_parts.append(f"• {feature}")
    
#     # Part 5: Lighting (with style override if applicable)
#     if 'lighting_structure' in layout:
#         prompt_parts.append("\nLIGHTING:")
#         # Check if style has lighting override
#         if style_mods and 'lighting_mood' in style_mods:
#             prompt_parts.append(f"• Style Lighting: {style_mods['lighting_mood']}")
#         for light_type, light_desc in layout['lighting_structure'].items():
#             prompt_parts.append(f"• {light_type.title()}: {light_desc}")
    
#     # Part 6: Materials & Finishes (with style override if applicable)
#     if 'material_finishes' in layout:
#         mf = layout['material_finishes']
#         materials = []
#         # Add style material emphasis first if available
#         if style_mods and 'material_emphasis' in style_mods:
#             materials.append(f"Style Materials: {style_mods['material_emphasis']}")
#         for mat_type, finish in list(mf.items())[:2]:  # Limit to 2 to save space
#             materials.append(f"{mat_type}: {finish}")
#         if materials:
#             prompt_parts.append("\nMATERIALS: " + "; ".join(materials))
    
#     # Part 7: Color Palette (with style override if applicable)
#     if style_mods and 'color_override' in style_mods:
#         prompt_parts.append(f"\nCOLORS: {style_mods['color_override']}")
#     elif 'color_palette' in layout:
#         cp = layout['color_palette']
#         colors = f"{cp.get('primary', '')}, {cp.get('secondary', '')}, {cp.get('accent', '')}"
#         prompt_parts.append(f"\nCOLORS: {colors}")
    
#     # Part 8: Textiles (with style override if applicable)
#     if style_mods and 'textile_style' in style_mods:
#         prompt_parts.append(f"\nTEXTILES: {style_mods['textile_style']}")
    
#     # Part 9: Photography Style
#     if 'photography_style' in layout:
#         ps = layout['photography_style']
#         prompt_parts.append(f"\nSTYLE: {ps.get('perspective', '')} - {ps.get('style', '')}")
    
#     # Part 10: Final Quality Requirements
#     prompt_parts.append("""
# REQUIREMENTS:
# • Professional 8K interior photography
# • Natural lighting with realistic shadows
# • Exact layout and furniture positions as specified
# • All architectural details must be present
# • High-end magazine quality
# • NO people or pets""")
    
#     # Combine all parts
#     full_prompt = "\n".join(prompt_parts)
    
#     # ====================================================================
#     # SMART TRUNCATION ONLY IF ABSOLUTELY NECESSARY
#     # ====================================================================
    
#     if len(full_prompt) > 4000:
#         priority_prompt = f"""Professional interior photograph: {room_type.replace('_', ' ')}"""
        
#         if style_description:
#             priority_prompt += f" in {style_description}"
        
#         priority_prompt += f"""

# CAMERA & ROOM:
# {layout['camera_angle']}
# {layout['room_size']}, {layout['flooring']}

# CRITICAL LAYOUT:"""
        
#         if 'layout' in layout:
#             for i, (element, description) in enumerate(list(layout['layout'].items())[:4]):
#                 priority_prompt += f"\n• {element.replace('_', ' ')}: {description[:120]}"
        
#         if 'circular_feature_wall' in layout:
#             priority_prompt += f"\n\nFEATURE: {layout['circular_feature_wall']['design']}"
        
#         if 'wardrobe_details' in layout:
#             priority_prompt += f"\nWARDROBE: {layout['wardrobe_details']['type']}"
        
#         if 'furniture_positions' in layout:
#             priority_prompt += "\n\nFURNITURE:"
#             for i, (item, pos) in enumerate(list(layout['furniture_positions'].items())[:3]):
#                 priority_prompt += f"\n• {item.replace('_', ' ')}: {pos[:80]}"
        
#         # Add style modifications if present
#         if style_mods:
#             if 'color_override' in style_mods:
#                 priority_prompt += f"\n\nCOLORS: {style_mods['color_override']}"
#             if 'material_emphasis' in style_mods:
#                 priority_prompt += f"\nMATERIALS: {style_mods['material_emphasis']}"
        
#         priority_prompt += "\n\nProfessional 8K photography, exact layout, natural lighting, magazine quality."
        
#         full_prompt = priority_prompt
    
#     return {
#         'success': True,
#         'prompt': full_prompt,
#         'room_type': room_type,
#         'style': style or 'custom',
#         'theme': custom_prompt if custom_prompt else style,
#         'is_custom_theme': False
#     }


# def construct_prompt(room_type, style=None, custom_prompt=None):
#     """
#     Main entry point - routes to appropriate prompt construction
#     FLOW 1: style provided → construct_fixed_layout_prompt (text-to-image)
#     FLOW 2: custom_prompt provided → construct_custom_theme_prompt (image-to-image)
#     """
#     if custom_prompt and custom_prompt.strip():
#         # FLOW 2: Custom theme with image-to-image
#         return construct_custom_theme_prompt(room_type, custom_prompt.strip())
#     else:
#         # FLOW 1: Predefined style with text-to-image
#         return construct_fixed_layout_prompt(room_type, style, None)


# def validate_inputs(room_type, style, custom_prompt):
#     """Validate user inputs"""
#     if not room_type:
#         return False, "Room type is required"
    
#     if room_type not in FIXED_ROOM_LAYOUTS:
#         return False, f"Room type '{room_type}' not supported"
    
#     if not style and not custom_prompt:
#         return False, "Either style or custom prompt is required"
    
#     if custom_prompt and len(custom_prompt) > 500:
#         return False, "Custom prompt too long (max 500 characters)"
    
#     return True, "Valid"


# def deconstruct_theme_to_realistic_elements(custom_prompt):
#     """Legacy function for backward compatibility"""
#     detected_theme, original = detect_theme_from_custom_prompt(custom_prompt)
    
#     if detected_theme and detected_theme in THEME_ELEMENTS.get('color_palettes', {}):
#         return {
#             'colors': THEME_ELEMENTS['color_palettes'][detected_theme],
#             'textures': THEME_ELEMENTS['wall_textures'][detected_theme],
#             'textiles': THEME_ELEMENTS['textiles'][detected_theme],
#             'decor': THEME_ELEMENTS['decor_items'][detected_theme],
#             'lighting': THEME_ELEMENTS['lighting_style'][detected_theme],
#             'theme_name': detected_theme
#         }
    
#     return {
#         'colors': 'neutral tones',
#         'textures': 'modern textures',
#         'textiles': f'{original} bedding',
#         'decor': f'{original} decor',
#         'lighting': 'ambient lighting',
#         'theme_name': 'custom'
#     }


# def get_short_prompt_for_cache(room_type, style=None, custom_prompt=None):
#     """Generate cache key"""
#     if custom_prompt:
#         theme_elements = detect_theme_from_custom_prompt(custom_prompt)
#         return f"{room_type}_{theme_elements[0] if theme_elements[0] else 'custom'}_{custom_prompt[:30]}"
#     return f"{room_type}_{style}"
"""
UPDATED PROMPTS.PY - Photorealistic Image-to-Image Generation
Flow 1: Style transformation with professional photography realism
Flow 2: Custom theme transformation with photorealistic quality
"""

from config import (
    FIXED_ROOM_LAYOUTS, 
    INTERIOR_STYLES, 
    THEME_ELEMENTS,
    ROOM_DESCRIPTIONS
)
import re


# ============================================================
# PHOTOREALISM ENHANCEMENT SETTINGS
# ============================================================

PHOTOGRAPHY_PRESETS = {
    'bedroom': {
        'camera': 'Canon EOS R5, 24mm f/1.4 lens',
        'lighting': 'soft morning light filtering through sheer curtains, warm natural ambient lighting',
        'atmosphere': 'cozy, lived-in feel with subtle dust particles in sunlight',
        'time': 'golden hour, warm afternoon glow'
    },
    'living_room': {
        'camera': 'Sony A7R IV, 35mm f/1.8 lens',
        'lighting': 'natural daylight from large windows, balanced indoor ambient lighting',
        'atmosphere': 'inviting, real home atmosphere with natural light gradients',
        'time': 'mid-morning natural light'
    },
    'kitchen': {
        'camera': 'Nikon Z7 II, 28mm f/2.8 lens',
        'lighting': 'bright natural light, pendant lighting accents, mixed light temperature',
        'atmosphere': 'clean but lived-in, realistic kitchen ambiance',
        'time': 'bright daylight'
    },
    'bathroom': {
        'camera': 'Canon EOS R6, 24-70mm f/2.8 lens at 35mm',
        'lighting': 'soft diffused lighting, natural light from frosted window, LED accent lights',
        'atmosphere': 'spa-like yet realistic, subtle moisture on surfaces',
        'time': 'soft morning light'
    },
    'dining_room': {
        'camera': 'Sony A7 III, 50mm f/1.4 lens',
        'lighting': 'overhead chandelier with natural window light, warm evening ambiance',
        'atmosphere': 'elegant but approachable, realistic dining setting',
        'time': 'warm evening light'
    },
    'home_office': {
        'camera': 'Fujifilm X-T4, 23mm f/1.4 lens',
        'lighting': 'balanced natural window light with desk lamp, professional home office lighting',
        'atmosphere': 'productive, modern workspace feel with natural elements',
        'time': 'clear daylight'
    },
    'kids_room': {
        'camera': 'Canon EOS RP, 35mm f/1.8 lens',
        'lighting': 'bright cheerful natural light, playful overhead lighting',
        'atmosphere': 'fun yet organized, realistic children\'s space with lived-in charm',
        'time': 'bright afternoon'
    }
}

# Universal photorealism suffix
PHOTOREALISM_SUFFIX = """
CRITICAL PHOTOREALISM REQUIREMENTS:
- Shot on professional DSLR camera with cinematic depth of field
- Natural bokeh and lens characteristics
- Realistic material textures: fabric weave visible, wood grain authentic, metal reflections accurate
- Imperfections: slight wrinkles in fabrics, natural wear on surfaces, real-world details
- Natural light behavior: soft shadows, realistic light diffusion, authentic reflections
- Film grain for cinematic quality (subtle Kodak Portra 400 aesthetic)
- Color grading: warm, natural, professionally balanced
- Architectural photography standards: straight lines, proper perspective
- NO artificial CGI look, NO oversaturation, NO perfect symmetry
- Lived-in realism: books slightly askew, pillows with natural indentations
- Professional interior photography quality, indistinguishable from real photograph
- 8K resolution, RAW photo quality, ultra-detailed textures"""


def get_photography_preset(room_type):
    """Get professional photography settings for room type"""
    return PHOTOGRAPHY_PRESETS.get(
        room_type,
        {
            'camera': 'Sony A7R IV, 35mm f/1.8 lens',
            'lighting': 'natural ambient lighting with professional interior photography setup',
            'atmosphere': 'realistic, lived-in space',
            'time': 'natural daylight'
        }
    )


def construct_style_transformation_prompt(room_type, style):
    """
    FLOW 1: Photorealistic style transformation with image-to-image
    Creates prompts that maintain layout while applying photorealistic style changes
    """
    if style not in INTERIOR_STYLES:
        style_description = f"{style} interior design style"
    else:
        style_description = INTERIOR_STYLES[style]
    
    # Get photography preset
    photo_preset = get_photography_preset(room_type)
    
    # Style-specific realistic details
    style_realism = {
        'modern': {
            'colors': 'clean neutral greys (#E5E5E5, #FAFAFA), crisp whites, matte black accents',
            'materials': 'brushed stainless steel with authentic fingerprint-resistant finish, tempered glass with natural reflections, genuine Italian leather with subtle grain texture',
            'textures': 'smooth polished concrete with micro-variations, matte lacquer finishes, natural light oak with visible wood grain',
            'lighting': 'recessed LED lighting (3000K warm white), natural window light creating soft shadows',
            'details': 'minimalist but lived-in: slight dust on glass surfaces, natural wear on leather, books casually placed'
        },
        'scandinavian': {
            'colors': 'soft warm whites (Benjamin Moore Simply White), light grey (#F5F5F5), natural birch tones, muted sage green accents',
            'materials': 'light oak wood with visible grain and knots, undyed wool textiles, natural linen with texture, white painted wood with slight imperfections',
            'textures': 'soft woven fabrics, chunky knit throws with visible stitching, light wood with natural variations',
            'lighting': 'abundant natural window light, warm Edison bulb pendants (2700K), candles with real flame glow',
            'details': 'hygge atmosphere: coffee cup on side table, throw blanket casually draped, real plants with natural leaf variations'
        },
        'industrial': {
            'colors': 'raw charcoal grey (#3A3A3A), exposed brick red-brown, weathered steel tones, concrete grey',
            'materials': 'authentic exposed brick with mortar texture and color variations, raw steel with rust patina in corners, distressed leather with age marks, reclaimed wood with nail holes and weathering',
            'textures': 'rough concrete with trowel marks, oxidized metal with natural patina, worn leather with creases',
            'lighting': 'Edison bulbs (2200K amber glow), metal cage fixtures, dramatic shadows from exposed elements',
            'details': 'urban loft realism: exposed pipes with authentic joints, brick with slight efflorescence, vintage elements with genuine age'
        },
        'minimalist': {
            'colors': 'pure white (RGB 255,255,255), ultra-light grey (#FCFCFC), subtle warm beige undertones',
            'materials': 'seamless matte surfaces with micro-texture, hidden hardware with precise alignment, simple forms with perfect but not artificial edges',
            'textures': 'smooth painted walls with slight texture variation, polished concrete with natural aggregate, simple cotton fabrics',
            'lighting': 'diffused natural light creating soft graduated shadows, concealed LED strips (4000K neutral white)',
            'details': 'zen simplicity with realism: slight shadow under floating furniture, natural dust in light rays, one carefully placed decorative element'
        },
        'traditional': {
            'colors': 'rich mahogany browns, warm cream (#F5F1E8), burgundy wine (#722F37), antique gold accents',
            'materials': 'carved dark wood with authentic grain and age, ornate brass hardware with natural tarnish, damask fabrics with visible thread work, velvet with directional pile texture',
            'textures': 'detailed wood carving with shadows in recesses, woven damask patterns, tufted upholstery with button details',
            'lighting': 'crystal chandelier with realistic light refraction, warm table lamps (2700K), natural window light through heavy drapes',
            'details': 'classic elegance with age: slight patina on brass, natural wear on chair arms, heirloom pieces with history'
        },
        'bohemian': {
            'colors': 'terracotta (#E07A5F), jewel-toned emerald (#2A9D8F), burnt orange (#F4A261), natural hemp tones',
            'materials': 'hand-woven textiles with visible variations, natural rattan with organic imperfections, macrame with real knot work, layered vintage rugs with authentic wear patterns',
            'textures': 'mixed textile layers, woven wall hangings with dimensional knots, natural fiber rugs with texture',
            'lighting': 'warm ambient glow (2700K), string lights with soft bokeh, natural light through sheer curtains',
            'details': 'eclectic collected feel: plants at various growth stages, vintage finds with authentic patina, textiles slightly overlapping'
        },
        'luxury': {
            'colors': 'deep navy blue (#1A2A3A), champagne gold (#D4AF37), marble white with grey veining, rich jewel tones',
            'materials': 'genuine Calacatta marble with authentic veining patterns, plush velvet with light-reactive pile, polished brass with subtle patina, crystal with realistic light refraction',
            'textures': 'high-thread-count silk with subtle sheen, tufted velvet with button details, natural marble veining',
            'lighting': 'layered lighting: chandelier crystals with realistic prism effects (3000K), accent lighting creating dramatic shadows',
            'details': 'sophisticated luxury with reality: silk pillows with natural draping, marble with authentic cold appearance, gold fixtures with slight variation in finish'
        },
        'contemporary': {
            'colors': 'sophisticated grey palette (#6B7280), bold accent colors (teal #0D9488, mustard #F59E0B), neutral base',
            'materials': 'mixed textures: matte and gloss finishes, contemporary art with visible brush strokes, modern metals with brushed finish',
            'textures': 'varied surface finishes, artistic wall treatments, mixed material combinations',
            'lighting': 'statement lighting fixtures with visible filaments, natural light creating dynamic shadows, artistic light patterns',
            'details': 'curated modern aesthetic: art books slightly fanned, decorative objects with artistic placement, real plants in contemporary pots'
        },
        'coastal': {
            'colors': 'soft sky blue (#93C5FD), crisp white (#FFFFFF), sandy beige (#D4C5B9), seafoam green (#A7F3D0)',
            'materials': 'weathered driftwood with natural salt marks, natural wicker with organic variations, light linen with loose weave visible, whitewashed wood with grain showing through',
            'textures': 'natural rope with fiber texture, woven seagrass, light cotton with natural wrinkles',
            'lighting': 'bright natural light mimicking coastal sunshine, sheer curtains creating soft diffusion, nautical fixtures (3500K)',
            'details': 'breezy realism: curtains slightly moving, seashells with natural imperfections, weathered elements with authentic coastal wear'
        },
        'rustic': {
            'colors': 'warm honey wood tones, earthy terracotta, natural stone grey, deep forest green',
            'materials': 'reclaimed barn wood with authentic nail holes and weathering, natural stone with texture variations, chunky hand-knit textiles, wrought iron with forge marks',
            'textures': 'rough-hewn wood with visible saw marks, stone with natural clefts, handmade textiles with irregular stitching',
            'lighting': 'warm fireplace glow, lantern-style fixtures (2400K amber), natural daylight through rustic windows',
            'details': 'countryside authenticity: wood with authentic age, stone with natural moss in crevices, handcrafted items with maker\'s marks'
        },
        'japanese': {
            'colors': 'natural wood tones (Japanese cedar), pure white (#FFFFFF), charcoal black (#1C1C1C), earth tones',
            'materials': 'natural wood with visible grain (hinoki cypress), authentic tatami texture, rice paper shoji with translucent quality, bamboo with natural segmentation',
            'textures': 'smooth wood with oil finish showing grain, woven tatami with straw texture, stone with water-polished appearance',
            'lighting': 'soft diffused light through shoji screens, low ambient lighting creating zen atmosphere (2700K), natural indirect light',
            'details': 'wabi-sabi aesthetic: natural wood aging beautifully, stones with organic placement, minimal items with purposeful positioning'
        },
        'art_deco': {
            'colors': 'black (#000000), champagne gold (#D4AF37), deep emerald (#064E3B), ivory white, metallic bronze',
            'materials': 'polished black lacquer with mirror finish, geometric brass inlays with precision, velvet with rich pile texture, mirrored surfaces with authentic reflections',
            'textures': 'geometric patterns with precise execution, metallic finishes with art deco styling, luxe fabrics with dimensional weave',
            'lighting': 'dramatic geometric fixtures with brass finish, ambient lighting creating geometric shadows, crystal accents with period-appropriate design',
            'details': '1920s glamour with realism: geometric patterns perfectly aligned but naturally aged, brass with authentic period patina, vintage elements with genuine age characteristics'
        }
    }
    
    realism = style_realism.get(style, {
        'colors': 'harmonious natural color palette',
        'materials': 'authentic quality materials with real-world textures',
        'textures': 'realistic surface finishes',
        'lighting': 'natural ambient lighting',
        'details': 'lived-in realistic details'
    })
    
    # ENHANCED PHOTOREALISTIC PROMPT
    prompt = f"""PHOTOREALISTIC interior transformation: Transform this {room_type.replace('_', ' ')} to {style_description} style.

PRESERVE EXACTLY: Room layout, furniture positions, architectural features, room dimensions, camera perspective.

APPLY {style.upper()} STYLE WITH PHOTOREALISM:

Colors: {realism['colors']}
Materials: {realism['materials']}
Textures: {realism['textures']}
Lighting: {realism['lighting']}
Realistic Details: {realism['details']}

PHOTOGRAPHY SPECIFICATIONS:
Camera: {photo_preset['camera']}
Lighting Setup: {photo_preset['lighting']}
Time of Day: {photo_preset['time']}
Atmosphere: {photo_preset['atmosphere']}

{PHOTOREALISM_SUFFIX}

Transform only: wall colors/textures, bedding/upholstery fabrics, decorative items, artwork, lighting fixtures.
Maintain: exact furniture placement, room structure, architectural elements."""

    return prompt


def extract_theme_elements(custom_theme):
    """
    Extract photorealistic visual elements from custom theme
    Enhanced with professional photography details
    """
    theme_lower = custom_theme.lower()
    
    # Photorealistic theme mappings
    theme_mappings = {
        'superman': {
            'colors': 'bold primary red (#DC2626), royal blue (#1E40AF), bright yellow (#FBBF24) - colors with realistic fabric texture',
            'materials': 'smooth heroic surfaces with subtle sheen, brushed metallic accents resembling actual superhero costume materials, cape-like silk fabrics with natural draping',
            'textures': 'satin finish with light reflectivity, embossed S-shield patterns with dimensional depth, comic book art with authentic print texture',
            'decor': 'framed vintage comic covers with paper texture, collectible figures with realistic plastic finish, movie posters with authentic printing',
            'lighting': 'dramatic heroic lighting with strong key light (3500K), rim lighting creating subtle edge glow, shadows suggesting power',
            'mood': 'heroic, powerful, inspiring - photographed like high-end collectibles showcase',
            'photography': 'shot with dramatic lighting setup mimicking superhero movie poster style, vibrant but realistic color grading'
        },
        'batman': {
            'colors': 'matte black (#0A0A0A), charcoal grey (#374151), tactical yellow (#EAB308), midnight blue (#1E3A8A)',
            'materials': 'genuine leather textures with age marks, industrial brushed metals with subtle scratches, dark matte surfaces with slight reflectivity',
            'textures': 'distressed leather with natural creasing, carbon fiber patterns, weathered metal with authentic patina',
            'decor': 'bat symbol metal wall art with dimensional casting, framed Gotham noir photography, tactical equipment displays with realistic materials',
            'lighting': 'moody low-key lighting (2200K warm shadows, 4000K cool highlights), dramatic shadows suggesting vigilante atmosphere, subtle backlight creating depth',
            'mood': 'dark, mysterious, sophisticated - shot with noir cinematography techniques',
            'photography': 'low-key photography with controlled shadows, film noir aesthetic, professional dark mood lighting'
        },
        'underwater': {
            'colors': 'deep ocean blue gradient (#0C4A6E to #075985), turquoise (#14B8A6), seafoam green (#A7F3D0), coral pink (#FDA4AF), pearl white',
            'materials': 'flowing silk fabrics with water-like draping, iridescent materials mimicking fish scales with realistic sheen, frosted glass with bubble texture',
            'textures': 'rippling wave patterns with authentic light refraction, translucent fabrics with backlighting, smooth surfaces with water-droplet effects',
            'decor': 'real seashells with natural calcium textures, preserved coral with authentic structure, underwater photography art, aquatic plant arrangements',
            'lighting': 'soft blue-tinted ambient (5000K cool daylight filtered), rippling light patterns projected on surfaces, gentle luminescence mimicking bioluminescence',
            'mood': 'tranquil, flowing, serene - photographed with underwater cinematography aesthetic',
            'photography': 'soft focus with dreamy bokeh, blue color grading, gentle light diffusion mimicking water'
        },
        'spiderman': {
            'colors': 'vibrant web-red (#DC2626), electric blue (#3B82F6), black web patterns (#000000)',
            'materials': 'textured fabrics mimicking spider silk with dimensional weave, urban industrial materials, glossy comic-style finishes with realistic printing',
            'textures': 'web patterns with 3D embossing, street art with spray paint texture, athletic mesh materials',
            'decor': 'NYC skyline photography with authentic urban grit, comic panel art with print texture, web-patterned textiles with actual thread work',
            'lighting': 'dynamic urban lighting (4000K), dramatic shadows from web patterns, cityscape ambient glow',
            'mood': 'dynamic, youthful, urban - shot with action photography energy',
            'photography': 'high-energy composition, urban photography style, vibrant but realistic colors'
        },
        'harry potter': {
            'colors': 'Gryffindor burgundy (#7F1D1D), antique gold (#B45309), aged parchment (#F5F1E8), dark magical purple (#581C87)',
            'materials': 'aged leather with authentic wear patterns, vintage wood with centuries of patina, brass with genuine tarnish, weathered parchment textures',
            'textures': 'old book bindings with embossed gold lettering showing age, wax seal impressions, stone castle walls with moss',
            'decor': 'antique potion bottles with realistic glass imperfections, spell books with aged pages, Hogwarts house banners with fabric texture, owl feathers with natural structure',
            'lighting': 'warm candlelight glow (1800K), fireplace ambient warmth, mysterious shadows in corners, golden hour through gothic windows',
            'mood': 'magical, mystical, historic - photographed like museum collection pieces',
            'photography': 'warm vintage color grading, soft focus on backgrounds, film grain for aged photograph aesthetic'
        },
        'star wars': {
            'colors': 'space black (#09090B), brushed metallic silver (#71717A), electric blue lightsaber glow (#3B82F6), laser red (#DC2626)',
            'materials': 'brushed aluminum spacecraft panels with rivets, holographic displays with realistic projection, aged leather flight gear',
            'textures': 'worn spaceship interior panels with use marks, control panel buttons with tactile depth, alien metal alloys with sci-fi but realistic finish',
            'decor': 'lightsaber wall mounts with authentic hilt details, galactic map displays with screen glow, spaceship blueprints with technical accuracy',
            'lighting': 'cool LED accent lights (6500K), lightsaber glow with realistic bloom, spacecraft cockpit ambient lighting, dramatic rim lighting',
            'mood': 'futuristic, galactic, adventurous - shot with sci-fi cinematography techniques',
            'photography': 'anamorphic lens flares, cool color grading, controlled dramatic lighting'
        },
        'minecraft': {
            'colors': 'grass block green (#10B981), dirt brown (#92400E), stone grey (#6B7280), diamond blue (#3B82F6) - with pixelated transitions',
            'materials': 'cubic furniture with smooth edges but blocky aesthetic, pixel art tapestries with visible squares, wood with cubic grain patterns',
            'textures': '16x16 pixel patterns scaled large, blocky textures with clean edges, crafting table wood grain in pixel style',
            'decor': 'framed pixel art with actual LED backlight pixels, cube storage systems, block-styled decorative items with realistic materials',
            'lighting': 'bright even lighting mimicking game world (4500K), torchlight warm glow from actual sources, subtle ambient occlusion between blocks',
            'mood': 'playful, creative, gaming-inspired - photographed as real-world implementation of game aesthetic',
            'photography': 'sharp focus, even lighting, vibrant colors with slight desaturation for realism'
        },
        'disney': {
            'colors': 'fairy tale pink (#FCA5A5), enchanted purple (#C084FC), castle blue (#60A5FA), magical gold (#FCD34D)',
            'materials': 'soft whimsical fabrics with gentle sheen, pearl-like finishes with iridescence, velvet with direction pile showing luxury',
            'textures': 'princess-quality silk with natural luster, tulle with visible netting, sparkle finishes with micro-glitter texture',
            'decor': 'castle-inspired wall art with dimensional elements, character artwork with professional printing, crown and tiara displays with genuine metalwork',
            'lighting': 'soft dreamy lighting (3000K warm), gentle fairy light twinkle with bokeh, magical glow effects achieved with colored gels',
            'mood': 'magical, whimsical, enchanting - photographed like high-end princess suite',
            'photography': 'soft focus with dreamy quality, warm color grading, gentle highlights for magical feel'
        },
        'jungle': {
            'colors': 'lush jungle green (#065F46), earthy brown (#78350F), vibrant tropical flower colors (#F472B6, #FB923C), natural vine tones',
            'materials': 'natural bamboo with authentic nodes and grain, woven rattan with organic texture, raw wood with bark elements, natural fiber textiles',
            'textures': 'large tropical leaf patterns with realistic veining, rough tree bark textures, woven natural fibers with visible weave',
            'decor': 'live tropical plants with realistic leaf structure, animal print textiles with genuine pattern accuracy, wooden tribal masks with carved detail',
            'lighting': 'dappled forest light through foliage (4500K natural), warm ambient glow (2800K), dramatic shadows from plants',
            'mood': 'wild, natural, tropical - photographed like National Geographic interior',
            'photography': 'rich color saturation, dramatic natural lighting, depth created with layered foliage'
        },
        'cyberpunk': {
            'colors': 'neon pink (#EC4899) with glow, electric cyan (#06B6D4), toxic green (#84CC16), deep purple (#7C3AED), metallic chrome',
            'materials': 'brushed metal panels with holographic overlays, LED-embedded surfaces with actual light emission, reflective chrome with distorted reflections',
            'textures': 'digital screen textures with visible pixels, neon tube lighting with realistic glow and reflections, carbon fiber with authentic weave',
            'decor': 'actual LED neon signs with realistic glow bloom, digital art displays with screen texture, holographic elements with proper transparency',
            'lighting': 'strong neon color casting on surfaces, colored rim lighting (various K temps), dramatic shadows with colored fill light',
            'mood': 'futuristic, high-tech, dystopian - shot with Blade Runner cinematography style',
            'photography': 'high contrast, neon color grading with bloom effects, wet surface reflections, film grain for gritty feel'
        },
        'retro': {
            'colors': 'vintage orange (#FB923C), mustard yellow (#FDE047), avocado green (#84CC16), burnt sienna (#DC2626), cream (#FEF3C7)',
            'materials': 'wood grain laminate with authentic period patterns, shag carpet with dimensional pile texture, vintage plastic with slight yellowing from age',
            'textures': 'bold geometric wallpaper with period-accurate printing, textured ceiling with popcorn finish, vinyl upholstery with authentic grain',
            'decor': 'vintage rotary phone with plastic patina, retro appliances with authentic brand logos, period posters with aged paper texture',
            'lighting': 'warm incandescent glow (2700K), vintage lamp shades with period materials, natural light through period curtains',
            'mood': 'nostalgic, vintage, throwback - photographed like 1970s home magazines',
            'photography': 'slight vintage color shift, warm color temperature, subtle film grain, slightly softened focus'
        },
        'steampunk': {
            'colors': 'aged brass (#B45309), copper patina (#92400E), industrial grey (#52525B), Victorian burgundy (#7F1D1D), weathered bronze',
            'materials': 'actual brass gears with machining marks, riveted metal plates with authentic joining, aged leather with strap buckles, polished wood with brass inlays',
            'textures': 'exposed gear mechanisms with realistic metal finish, leather with embossing and age cracks, wood with Victorian carving detail',
            'decor': 'functional-looking pressure gauges with glass faces, vintage brass instruments with patina, clockwork mechanisms with visible movement',
            'lighting': 'warm Edison bulb glow (2200K amber), brass lamp fixtures with authentic metalwork, dramatic shadows from mechanical elements',
            'mood': 'Victorian industrial, mechanical, steam-powered - photographed like museum industrial artifacts',
            'photography': 'warm sepia-toned color grade, emphasis on metallic textures with controlled highlights, dramatic side lighting to show dimension'
        }
    }
    
    # Check for matches
    for key, elements in theme_mappings.items():
        if key in theme_lower:
            return elements
    
    # Generic theme with photorealism
    return {
        'colors': f'{custom_theme}-inspired realistic color palette with authentic pigments',
        'materials': f'{custom_theme}-themed materials with realistic textures and finishes',
        'textures': f'authentic surface textures matching {custom_theme} aesthetic',
        'decor': f'{custom_theme}-inspired decorative elements with real-world materials',
        'lighting': f'professional lighting setup enhancing {custom_theme} atmosphere',
        'mood': f'{custom_theme} aesthetic with photographic realism',
        'photography': 'professional interior photography, authentic materials and textures'
    }


def construct_custom_theme_prompt(room_type, custom_theme):
    """
    FLOW 2: Photorealistic custom theme transformation
    Enhanced with professional photography specifications
    """
    theme_elements = extract_theme_elements(custom_theme)
    photo_preset = get_photography_preset(room_type)
    
    prompt = f"""PHOTOREALISTIC {custom_theme} themed interior: Transform this {room_type.replace('_', ' ')}.

PRESERVE EXACTLY: Room layout, furniture positions, architectural structure, dimensions.

APPLY {custom_theme.upper()} THEME WITH PHOTOREALISM:

Colors: {theme_elements['colors']}
Materials: {theme_elements['materials']}
Textures: {theme_elements['textures']}
Decorative Elements: {theme_elements['decor']}
Lighting Design: {theme_elements.get('lighting', 'thematic ambient lighting')}
Atmosphere: {theme_elements['mood']}

PHOTOGRAPHY SPECIFICATIONS:
Camera: {photo_preset['camera']}
Lighting Setup: {photo_preset['lighting']}
Time: {photo_preset['time']}
Style: {theme_elements.get('photography', 'professional interior photography')}

{PHOTOREALISM_SUFFIX}

Transform only: walls, bedding/upholstery, decorative items, artwork, lighting fixtures to match {custom_theme} theme.
Maintain: exact furniture placement and room structure."""
    
    return {
        'success': True,
        'prompt': prompt,
        'room_type': room_type,
        'theme': custom_theme,
        'is_custom_theme': True,
        'theme_elements': theme_elements
    }


def construct_prompt(room_type, style=None, custom_prompt=None):
    """
    Main entry point with photorealistic enhancements
    """
    if custom_prompt and custom_prompt.strip():
        return construct_custom_theme_prompt(room_type, custom_prompt.strip())
    else:
        prompt = construct_style_transformation_prompt(room_type, style)
        return {
            'success': True,
            'prompt': prompt,
            'room_type': room_type,
            'style': style,
            'theme': style,
            'is_custom_theme': False
        }


def validate_inputs(room_type, style, custom_prompt):
    """Validate user inputs"""
    if not room_type:
        return False, "Room type is required"
    
    if room_type not in FIXED_ROOM_LAYOUTS:
        return False, f"Room type '{room_type}' not supported"
    
    if not style and not custom_prompt:
        return False, "Either style or custom prompt is required"
    
    if custom_prompt and len(custom_prompt) > 500:
        return False, "Custom prompt too long (max 500 characters)"
    
    return True, "Valid"


def get_short_prompt_for_cache(room_type, style=None, custom_prompt=None):
    """Generate cache key"""
    if custom_prompt:
        return f"{room_type}_custom_{custom_prompt[:30]}"
    return f"{room_type}_{style}"


# Legacy compatibility
def construct_fixed_layout_prompt(room_type, style=None, custom_prompt=None):
    """Legacy function"""
    return construct_prompt(room_type, style, custom_prompt)


def detect_theme_from_custom_prompt(custom_prompt):
    """Legacy theme detection"""
    prompt_lower = custom_prompt.lower()
    
    theme_keywords = {
        'space': ['space', 'galaxy', 'cosmic', 'star', 'planet'],
        'tropical': ['tropical', 'palm', 'beach', 'island'],
        'forest': ['forest', 'woodland', 'nature', 'botanical'],
        'ocean': ['ocean', 'sea', 'nautical', 'marine'],
    }
    
    for theme, keywords in theme_keywords.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return theme, custom_prompt
    
    return None, custom_prompt


def deconstruct_theme_to_realistic_elements(custom_prompt):
    """Legacy function"""
    return extract_theme_elements(custom_prompt)