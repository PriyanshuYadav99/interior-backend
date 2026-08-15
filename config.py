import os
from dotenv import load_dotenv

load_dotenv()

# FAL API Configuration

# Paths to reference room images - CORRECTED PATHS
ROOM_IMAGES = {
    'master_bedroom': 'images/MADHUBANbedroom.webp',
    'bedroom_1': 'images/madhubanbedroom2.webp',
    'living_room': 'images/madhubanlivingroom3.webp',
    'kitchen': 'images/madhubankitchen.webp',
}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOM_IMAGES = {
    'master_bedroom': os.path.join(BASE_DIR, 'images', 'MADHUBANbedroom.webp'),
    'bedroom_1': os.path.join(BASE_DIR, 'images', 'madhubanbedroom2.webp'),
    'living_room': os.path.join(BASE_DIR, 'images', 'madhubanlivingroom3.webp'),
    'kitchen': os.path.join(BASE_DIR, 'images', 'madhubankitchen.webp'),
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
    'camera_angle': 'slightly elevated front view facing the bed directly from foot of bed, eye level approximately 5 feet high, centered perspective showing full room width',
    'room_size': '16 feet x 18 feet (4.88m x 5.49m)',
    'flooring': 'glossy white marble flooring with subtle natural veining, highly polished surface with reflective finish',
    'ceiling': '10 feet height with smooth white finish, recessed lighting zones, clean modern design',
    
    # FIXED POSITIONS (never change)
    'layout': {
        'bed': 'king-size upholstered platform bed positioned center of back wall, directly facing camera, cream/beige fabric upholstered headboard with winged curved design, low-profile wooden base with light wood tone, bed centered perfectly on back wall',
        'left_wall': 'vertical wooden slat wall paneling from floor to ceiling covering entire left wall, natural wood tone with consistent spacing, large potted palm plant in left corner, modern white nightstand with wooden legs and gold accents positioned left of bed',
        'right_wall': 'large built-in floor-to-ceiling illuminated wardrobe system with glass doors (10 feet wide), internal LED strip lighting showing organized clothing and shelves, dark wood frame with backlit interior, extends along most of right wall, grey upholstered accent chair with ottoman positioned in right foreground',
        'back_wall': 'stunning circular backlit feature wall behind bed - large circular wooden panel (approximately 8 feet diameter) with warm LED backlighting creating halo effect, smooth wood finish matching room tones, bed headboard positioned within circle, vertical wooden slat paneling on left portion of back wall transitioning into white panel doors on right portion',
        'front_area': 'grey upholstered bench or ottoman at foot of bed with black and white houndstooth throw blanket casually draped, magazines on floor near ottoman'
    },
    
    'furniture_positions': {
        'nightstands': 'two matching modern nightstands on either side of bed - white drawer units with wooden legs and gold/brass accent handles, floating appearance, under-lighting effect',
        'pendant_lights': 'two modern cylindrical pendant lights with white fabric shades hanging above nightstands, adjustable cable height, warm ambient glow, approximately 30 inches above nightstand surface',
        'bed_styling': 'bed dressed with layered neutral bedding - beige/cream fitted sheet, grey duvet, multiple decorative pillows (2 white euro shams, 2 grey standard pillows, 2-3 patterned accent pillows with geometric black and white designs), brown/tan throw blanket casually placed on bed, bedding appears slightly unmade/lived-in for realistic feel',
        'area_rug': 'large rectangular textured grey area rug under bed and extending into room, extends approximately 3 feet beyond bed on front and sides, low-pile modern weave pattern',
        'accent_chair': 'contemporary grey upholstered swivel accent chair in right foreground with matching upholstered ottoman, rounded organic shape, modern sculptural design',
        'decorative_items': 'small camera on left nightstand, table lamp with white shade on left nightstand, books stacked on right nightstand, potted palm plant in left corner (approximately 5 feet tall)'
    },
    
    'wardrobe_details': {
        'type': 'floor-to-ceiling built-in wardrobe with glass sliding doors',
        'interior': 'illuminated with LED strip lighting on each shelf and hanging rod, warm white light',
        'organization': 'upper shelves with folded clothes and accessories, middle section with hanging clothes on rods (shirts, suits, dresses), lower drawers and shoe storage',
        'finish': 'dark wood frame (walnut or espresso tone) with transparent glass panels, modern handle-less design',
        'position': 'spans 10 feet along right wall, reaches ceiling height, creates feature wall effect when illuminated'
    },
    
    'circular_feature_wall': {
        'design': 'large circular wooden panel mounted on back wall behind bed, approximately 8 feet diameter',
        'lighting': 'warm LED backlighting creating halo glow effect around entire circle perimeter, soft ambient wash',
        'material': 'smooth wood finish matching natural wood tones throughout room, possibly veneer or solid wood',
        'position': 'centered on back wall, bed headboard positioned within lower portion of circle',
        'impact': 'serves as dramatic focal point and statement piece, draws eye to bed area'
    },
    
    'wall_treatments': {
        'left_wall': 'vertical wooden slat paneling, natural wood tone, evenly spaced slats creating linear rhythm, extends full height from floor to ceiling',
        'back_wall_left': 'continuation of vertical wooden slats transitioning from left wall',
        'back_wall_center': 'circular feature panel with backlighting',
        'back_wall_right': 'smooth white panel doors (possibly closet or bathroom access)',
        'right_wall': 'clean white wall with integrated wardrobe system',
        'overall_aesthetic': 'warm wood tones balanced with crisp white surfaces creating modern luxury feel'
    },
    
    'lighting_structure': {
        'natural': 'soft diffused daylight creating gentle ambient illumination, no harsh shadows',
        'feature_lighting': 'warm LED backlighting behind circular feature wall creating dramatic halo effect',
        'wardrobe_lighting': 'internal LED strip lighting in wardrobe illuminating contents with warm white light',
        'pendant_lights': 'two cylindrical pendant lights above nightstands with white fabric diffusers providing task lighting',
        'accent_lighting': 'subtle under-lighting beneath floating nightstands creating floating effect',
        'overall_temperature': 'warm white lighting scheme (2700K-3000K) creating cozy inviting atmosphere'
    },
    
    'color_palette': {
        'primary': 'warm natural wood tones (oak, walnut)',
        'secondary': 'crisp white (walls, ceiling, nightstands)',
        'accent': 'grey tones (chair, rug, bedding)',
        'metallic': 'brushed gold/brass hardware accents',
        'contrast': 'black and white patterns (houndstooth throw, geometric pillows)',
        'overall_mood': 'sophisticated neutral palette with warm undertones, luxury hotel aesthetic'
    },
    
    'material_finishes': {
        'flooring': 'high-gloss white marble with natural grey veining, mirror-like polish',
        'wood_elements': 'matte natural wood finish on slats and circular feature',
        'textiles': 'mixed textures - linen bedding, velvet/chenille upholstery, woven area rug',
        'metals': 'brushed brass/gold on nightstand handles and light fixtures',
        'glass': 'clear glass on wardrobe doors, slight reflective quality'
    },
    
    'styling_details': {
        'bedding': 'layered approach with multiple pillow sizes and textures, slightly tousled for lived-in luxury feel',
        'accessories': 'carefully curated minimal accessories - camera, books, single table lamp, throw blanket',
        'greenery': 'single large potted palm adding organic element and height variation',
        'patterns': 'geometric patterns on accent pillows and throw providing visual interest without overwhelming',
        'overall_vibe': 'modern luxury with warm inviting atmosphere, magazine-worthy yet livable'
    },
    
    'architectural_details': {
        'ceiling_height': '10 feet providing spacious open feel',
        'door_location': 'smooth white panel doors on right portion of back wall (likely bathroom or walk-in closet access)',
        'window_treatment': 'concealed or minimal windows allowing focus on interior lighting design',
        'built_ins': 'extensive built-in wardrobe system demonstrating custom millwork',
        'trim_and_molding': 'minimal or flush detailing maintaining clean modern aesthetic'
    },
    
    'photography_style': {
        'perspective': 'straight-on symmetrical composition, slightly elevated viewpoint',
        'depth_of_field': 'everything in sharp focus from foreground to background',
        'lighting_balance': 'even exposure showing detail in both bright and shadowed areas',
        'color_grading': 'warm natural tones with slight enhancement, professionally color corrected',
        'style': 'architectural photography style, clean and aspirational, suitable for design magazine or portfolio'
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
    'living_room': 'elegant living room with integrated puja area on the front wall',
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