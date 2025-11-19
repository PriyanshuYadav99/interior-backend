import os
from dotenv import load_dotenv

load_dotenv()

# FAL API Configuration
FAL_API_KEY = os.getenv('FAL_API_KEY')

# Paths to reference room images
ROOM_IMAGES = {
    'master_bedroom': 'backend/images/MADHUBANbedroom.webp',
    'bedroom_1': 'backend/images/madhubanbedroom2.webp',
    'living_room': 'backend/images/madhubanlivingroom3.webp',
    'kitchen': 'backend/images/madhubankitchen.webp',
}

"""
🎯 FIXED LAYOUT SYSTEM FOR CONSISTENT GENERATION
Only theme, colors, textures, and decorative elements change.
Room structure, furniture positions, and architecture remain IDENTICAL.
"""

# ====================================================================
# 🏗️ FIXED ROOM ARCHITECTURES (NEVER CHANGES)
# ====================================================================

FIXED_ROOM_LAYOUTS = {
    'master_bedroom': {
        'camera_angle': 'front view facing the bed directly from foot of bed',
        'room_size': '14 feet x 17 feet (4.27m x 5.18m)',
        'flooring': 'glossy white marble flooring with subtle natural veining',
        'ceiling': '10 feet height with recessed ceiling detail and cove lighting around perimeter',
        
        # FIXED POSITIONS (never change)
        'layout': {
            'bed': 'king-size upholstered platform bed positioned center of back wall, directly facing camera, bed frame low-profile modern style',
            'left_wall': 'single large floor-to-ceiling window (6 feet wide) with sheer white curtains and grey blackout drapes, window starts 1 foot from corner',
            'right_wall': 'built-in floor-to-ceiling wardrobe with smooth panel doors (8 feet wide), single door positioned on right wall near back corner leading to attached facilities',
            'back_wall': 'textured accent wall behind bed with vertical paneling or fluted design, bed centered against this wall, NO DOORS on back wall',
            'right_corner': 'small seating area with accent chair and side table near wardrobe, compact reading nook'
        },
        
        'furniture_positions': {
            'nightstands': 'two matching floating nightstands on either side of bed, wall-mounted with under-lighting',
            'pendant_lights': 'two modern pendant lights hanging above nightstands, adjustable height, contemporary design',
            'bed_styling': 'bed dressed with layered pillows (3 standard + 2 decorative), folded throw at foot of bed, fitted sheet and duvet',
            'area_rug': 'rectangular textured area rug under bed, extending 2 feet beyond bed on three sides',
            'accent_chair': 'single contemporary accent chair in right corner with small round side table'
        },
        
        'lighting_structure': {
            'natural': 'soft diffused sunlight from left window casting gentle shadows',
            'ambient': 'recessed ceiling lights in cove around perimeter',
            'task': 'pendant lights above nightstands',
            'accent': 'LED strip under floating nightstands'
        }
    },
    
    'bedroom_1': {
        'camera_angle': 'front view from entrance gate (bedroom entry), facing bed directly',
        'room_size': '14 feet x 13 feet (4.27m x 3.96m)',
        'flooring': 'glossy white marble flooring with subtle veining',
        'ceiling': '10 feet height with false ceiling and recessed lighting, modern minimal design',
        
        'layout': {
            'bed': 'queen-size upholstered platform bed centered against back wall, low-profile modern frame, directly in front of camera view',
            'back_wall': 'textured feature wall behind bed with horizontal wood slat panels or subtle geometric pattern, window centered in this wall',
            'window': 'single large window centered on back wall behind bed (5 feet wide), with roller blinds, positioned 3 feet above bed headboard',
            'left_wall': 'full-height built-in wardrobe system with LED-lit shelving and closed cabinet sections, wooden finish with glass display shelves, extends entire wall length',
            'right_wall_door1': 'first door near front (connected to attached toilet/bathroom), modern flush door with concealed hinges',
            'right_wall_door2': 'second door further back (access to small balcony), full-height glass door with wooden frame',
            'right_wall_panel': 'decorative wood slat wall paneling with vertical grooves between the two doors, with ambient backlighting'
        },
        
        'furniture_positions': {
            'nightstands': 'two floating wall-mounted nightstands on either side of bed, dark wood finish with LED under-lighting',
            'pendant_lights': 'two spherical pendant lights with white glass shades, hanging at 30 inches above nightstands',
            'bed_styling': 'bed with upholstered headboard integrated into feature wall, layered pillows (2 standard + 2 decorative), textured throw blanket',
            'area_rug': 'geometric patterned area rug centered under bed, extending 18 inches beyond bed frame on sides and foot'
        },
        
        'lighting_structure': {
            'natural': 'natural light from back wall window, diffused through roller blinds',
            'ambient': 'recessed ceiling spots in false ceiling, evenly distributed',
            'accent': 'LED backlighting behind wood slat panels on right wall, warm white strips under nightstands',
            'task': 'pendant lights above nightstands for reading'
        }
    },
    
    'living_room': {
        'camera_angle': 'front view from left side of room, capturing full width of space',
        'room_size': '11.5 feet x 12.5 feet (3.5m x 3.8m)',
        'flooring': 'glossy white marble flooring with natural veining',
        'ceiling': '10 feet height with simple flat false ceiling, recessed lighting',
        
        'layout': {
    'camera_position': 'camera positioned on left wall, shooting toward right side of room',
    'sofa': 'beige/grey L-shaped sectional sofa positioned against the back wall (concrete textured wall), with chaise extension pointing toward camera/left side',
    'front_wall': 'puja alcove with white arched niche is built into the front wall (same wall where camera is positioned), visible on left side of frame, golden Om symbol above, brass Ganesha idol inside, white cabinet base with closed storage below, alcove is 5 feet wide',
    'back_wall': 'concrete or textured grey accent wall directly opposite to front wall, sofa positioned against this wall, large framed abstract artwork centered above sofa (4 feet wide)',
    'right_wall': 'white/cream painted wall visible on right side of frame, decorative wall clock mounted here (copper/rose gold finish)',
    'right_corner': 'wooden paneled door to bedroom 1 visible in far right corner, tall decorative palm plant in white pot placed near this door'
},
        
        'furniture_positions': {
            'coffee_tables': 'two round nesting coffee tables with marble/stone tops and wooden bases, placed in front of sofa',
            'area_rug': 'geometric patterned area rug (black and white design) placed under coffee tables and in front of sofa, 6 feet x 8 feet',
            'side_table': 'small hexagonal side table with metal frame next to chaise section',
            'sofa_styling': '5-6 throw pillows on sofa (mix of solid and patterned), textured throw blanket draped on chaise',
            'puja_alcove': 'two brass candle holders (diyas) flanking Ganesha idol, small pooja items on cabinet base'
        },
        
        'decorative_elements': {
            'wall_art': 'large abstract or architectural photograph above sofa, black frame, 4 feet x 3 feet',
            'wall_clock': 'decorative wall clock on right side of room (copper/rose gold finish with minimal design)',
            'plants': 'tall palm plant near right door, small potted plant on side table'
        },
        
        'lighting_structure': {
            'ambient': 'recessed ceiling spots, evenly distributed warm white light',
            'accent': 'focused spotlights highlighting puja alcove',
            'natural': 'indirect natural light from adjacent spaces'
        }
    },
    
    'kitchen': {
        'camera_angle': 'front view showing L-shaped kitchen layout',
        'room_size': '10 feet x 20.6 feet (3m x 6.3m)',
        'flooring': 'cream/beige marble flooring with subtle veining',
        'ceiling': '9 feet height with false ceiling, recessed LED panel lights',
        
        'layout': {
            'left_wall': 'tall stainless steel double-door refrigerator in corner, followed by floor-to-ceiling wooden storage cabinets with open shelving sections',
            'left_wall_door': 'utility/store room door on left wall (wooden panel door with modern handle)',
            'front_wall': 'continues the L-shape with grey modular lower cabinets, terrazzo composite countertop, stainless steel sink with modern faucet',
            'front_wall_window': 'medium window with horizontal blinds above sink area, providing natural light to workspace',
            'right_wall': 'grey modular upper cabinets with handleless design, built-in oven at eye level, wooden open shelving with LED strip lighting, black chimney hood above cooktop',
            'countertop': 'L-shaped terrazzo countertop connecting left and front walls, thickness 2 inches, seamless design'
        },
        
        'appliances_positions': {
            'refrigerator': 'double-door stainless steel fridge in left corner, 6 feet tall',
            'built_in_oven': 'eye-level built-in oven on right wall upper section, surrounded by grey cabinets',
            'cooktop': 'gas cooktop on front wall counter with 4 burners, black glass top',
            'chimney': 'black modern chimney hood above cooktop, angular design',
            'sink': 'undermount stainless steel single bowl sink on front wall counter near window'
        },
        
        'storage': {
            'upper_cabinets': 'grey modular cabinets on right and front walls, handleless push-to-open mechanism',
            'lower_cabinets': 'grey modular base cabinets with drawers and closed storage, handleless design',
            'wooden_shelves': 'open wooden shelves on right wall with LED backlighting, displaying cookware and decor',
            'tall_cabinets': 'wooden floor-to-ceiling storage on left wall with combination of closed and open shelving'
        },
        
        'lighting_structure': {
            'natural': 'sunlight from front wall window above sink',
            'ambient': 'recessed LED panel lights in false ceiling, cool white temperature',
            'task': 'under-cabinet LED strips beneath upper cabinets, focused light on countertop workspace',
            'accent': 'LED strip lighting behind open wooden shelves'
        },
        
        'countertop_items': {
            'near_sink': 'dish soap dispenser, small potted plant, cutting board',
            'near_cooktop': 'oil bottles, spice jars, cooking utensils in holder',
            'open_shelves': 'coffee maker, decorative items, cookbooks, small plants'
        }
    }
}

# ====================================================================
# 🎨 THEME TRANSLATION SYSTEM
# Translates user themes into specific visual elements
# ====================================================================

THEME_ELEMENTS = {
    # Color schemes for different themes
    'color_palettes': {
        'space': 'deep midnight blue, cosmic purple, silver, black with galaxy gradient accents',
        'tropical': 'vibrant turquoise, coral pink, lime green, sandy beige, ocean blue',
        'forest': 'deep forest green, earthy brown, moss green, warm wood tones, natural beige',
        'ocean': 'navy blue, seafoam green, white, sand beige, aqua blue',
        'sunset': 'burnt orange, warm pink, golden yellow, deep purple, terracotta',
        'minimalist': 'pure white, light grey, charcoal, natural wood, soft beige',
        'luxury': 'deep navy, gold, cream, marble white, burgundy',
        'industrial': 'charcoal grey, black, raw steel, exposed concrete, warm Edison bulb glow'
    },
    
    # Wall treatments for themes
    'wall_textures': {
        'space': 'deep blue wall with subtle galaxy nebula pattern, starfield gradient',
        'tropical': 'walls with palm leaf pattern wallpaper or tropical botanical prints',
        'forest': 'textured wood panels or forest green paint with botanical wall art',
        'ocean': 'soft blue gradient walls or wave-pattern textured panels',
        'sunset': 'warm ombre walls from orange to pink with abstract sunset artwork',
        'minimalist': 'clean matte white or light grey smooth walls',
        'luxury': 'velvet textured wallpaper or leather-look panels with gold trim',
        'industrial': 'exposed concrete finish or dark grey industrial paint'
    },
    
    # Textile and soft furnishings
    'textiles': {
        'space': 'bedding with galaxy prints, metallic silver pillows, dark blue velvet throw',
        'tropical': 'bright floral prints, palm leaf patterns, rattan textures, tropical themed pillows',
        'forest': 'earth-tone linens, botanical print pillows, natural fiber textures',
        'ocean': 'blue and white striped patterns, nautical themed accents, linen textures',
        'sunset': 'warm gradient bedding, terracotta pillows, woven textures',
        'minimalist': 'solid neutral bedding, simple geometric pillows, natural cotton',
        'luxury': 'silk or velvet bedding, gold embroidered pillows, plush materials',
        'industrial': 'dark grey linens, leather accents, raw cotton textures'
    },
    
    # Decorative accents
    'decor_items': {
        'space': 'moon phase wall art, LED star lights, planetary models, rocket ship figurines',
        'tropical': 'palm leaf artwork, tropical flowers in vases, bamboo accents, seashells',
        'forest': 'botanical prints, wooden branch sculptures, potted ferns, nature photography',
        'ocean': 'seashell collections, driftwood art, marine life prints, coral decorations',
        'sunset': 'abstract sunset paintings, warm metallic accents, desert-inspired decor',
        'minimalist': 'single statement art piece, minimal vase with single stem, simple clock',
        'luxury': 'crystal vases, gold-framed mirrors, elegant sculptures, designer books',
        'industrial': 'vintage metal signs, Edison bulb fixtures, exposed gear decorations'
    },
    
    # Lighting modifications
    'lighting_style': {
        'space': 'LED strip lights with purple/blue glow, fiber optic star ceiling',
        'tropical': 'warm yellow lighting, rattan pendant shades, natural bamboo fixtures',
        'forest': 'warm wood pendant lights, Edison bulbs, natural light emphasis',
        'ocean': 'cool white light, wave-patterned light fixtures, blue accent lighting',
        'sunset': 'warm amber lighting, gradient LED strips, golden hour simulation',
        'minimalist': 'simple white LED, clean geometric fixtures, natural daylight temperature',
        'luxury': 'crystal chandeliers, gold fixtures, warm elegant lighting',
        'industrial': 'exposed Edison bulbs, metal cage fixtures, warm vintage glow'
    }
}

# ====================================================================
# 🎯 PREDEFINED INTERIOR STYLES (For non-custom selections)
# ====================================================================

INTERIOR_STYLES = {
    'modern': 'modern minimalist design with clean lines, neutral colors, sleek furniture, contemporary lighting',
    'scandinavian': 'scandinavian style with light wood, white walls, cozy textiles, natural light, hygge aesthetic',
    'industrial': 'industrial loft style with metal accents, exposed materials, leather furniture, Edison bulbs',
    'minimalist': 'minimalist design with essential furniture, simple forms, neutral palette, zen atmosphere',
    'traditional': 'traditional classic design with elegant wooden furniture, rich fabrics, ornate details, warm colors',
    'contemporary': 'contemporary style with modern furniture, mixed materials, bold accents, artistic elements',
    'luxury': 'luxury interior with premium furniture, velvet upholstery, gold accents, crystal lighting, marble surfaces',
    'coastal': 'coastal beach style with light blue and white, wicker furniture, nautical decor, natural textures',
    'rustic': 'rustic countryside style with reclaimed wood, stone accents, earthy tones, cozy atmosphere',
    'japanese': 'japanese zen style with low furniture, natural materials, minimal decor, peaceful ambiance',
    'bohemian': 'bohemian eclectic style with colorful textiles, layered rugs, plants, global-inspired decor',
    'art_deco': 'art deco style with geometric patterns, luxurious materials, bold colors, metallic accents'
}

# Room base descriptions (simplified, main details in FIXED_ROOM_LAYOUTS)
ROOM_DESCRIPTIONS = {
    'master_bedroom': 'luxurious master bedroom',
    'bedroom_1': 'comfortable modern bedroom',
    'living_room': 'elegant living room with integrated puja area',
    'kitchen': 'contemporary L-shaped kitchen',
}

# Image generation parameters
IMAGE_CONFIG = {
    'width': 1024,
    'height': 768,
    'num_images': 2,
    'guidance_scale': 7.5,
    'num_inference_steps': 50,
    'prompt_strength': 0.75
}