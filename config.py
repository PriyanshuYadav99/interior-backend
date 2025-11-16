import os
from dotenv import load_dotenv

load_dotenv()

# FAL API Configuration
FAL_API_KEY = os.getenv('FAL_API_KEY')

# Paths to reference room images (if you have them)
ROOM_IMAGES = {
    'master_bedroom': 'backend\images\MADHUBANbedroom.webp',
    'bedroom_1': 'backend\images\madhubanbedroom2.webp',
    'bedroom_2': 'backend/images/bedroom_2.png',
    'living_room': 'backend\images\madhubanlivingroom3.webp',
    'kitchen': 'backend\images\madhubankitchen.webp',
    'dining_room': 'backend/images/dining_room.png'
}

# Room base descriptions (Updated based on your floor plan)
# ROOM_DESCRIPTIONS = {
#     'master_bedroom': '15 feet x 12.5 feet empty unfurnished room (4.57m x 3.81m), bare room with no furniture, no bed, no objects, clean empty space with plain walls and floor, 4 feet x 4 feet window on the right wall with natural light, door opening on the bottom wall (entrance viewpoint), view from entrance looking into the room, architectural photography of vacant room ready for interior design',    
#     'bedroom_1': '15 feet x 12 feet (4.57m x 3.66m), empty unfurnished room, 4 feet x 4 feet window on left wall with natural light, door on bottom wall near corner, photographed from entrance doorway looking into the room, bare walls and empty floor space',
#     'bedroom_2': 'comfortable bedroom with bed, modern furniture, pleasant lighting, well-organized layout',
#     'living_room': 'spacious family living room with large seating area, entertainment space, open terrace access, abundant natural light',
#     'kitchen': 'compact modern kitchen with efficient layout, sleek appliances, ample counter space, functional design',
#     'dining_room': 'welcoming dining area with dining table, comfortable seating, family-friendly atmosphere'
# }

# # Room spatial specifications (Converted from meters to feet from your floor plan)
# # Note: 1 meter = 3.28 feet
# ROOM_DIMENSIONS = {
#     'master_bedroom': '''15 feet x 12.5 feet empty unfurnished room (4.57m x 3.81m), 
#     bare room with no furniture, no bed, no objects, 
#     clean empty space with plain walls and floor, 
#     4 feet x 4 feet window on the right wall with natural light, 
#     door opening on the bottom wall (entrance viewpoint), 
#     view from entrance looking into the room, 
#     architectural photography of vacant room ready for interior design''',
    
#     'bedroom_1': '''15 feet x 12 feet (4.57m x 3.66m), 
#     empty unfurnished room, 
#     4 feet x 4 feet window on left wall with natural light, 
#     door on bottom wall near corner, 
#     photographed from entrance doorway looking into the room, 
#     bare walls and empty floor space''',
    
#     'bedroom_2': '''11 feet x 12.5 feet room (3.35m x 3.81m), 
#     full bed 6 feet x 6 feet positioned centrally, 
     
#     door on right wall connecting to passage, 
#     cozy compact room with efficient furniture placement''',
    
#     'living_room': '''23 feet x 14.5 feet spacious family room (7.00m x 4.42m), 
#     large L-shaped or sectional sofa 10-12 feet along main wall, 
#     coffee table in center, TV unit on opposite wall, 
#     open terrace access on top side with sliding doors, 
#     foyer area 5 feet x 5 feet (1.52m x 1.55m) near entrance, 
#     abundant natural light and open layout perfect for family gatherings''',
    
#     'kitchen': '''11 feet x 10 feet efficient kitchen (3.35m x 3.05m), 
#     L-shaped or straight counter layout along two walls, 
#     cooking range, sink, and refrigerator in work triangle, 
#     storage cabinets above and below counters, 
#     window or ventilation for natural light, 
#     door connects to dining area for easy serving''',
    
#     'dining_room': '''9.6 feet x 12 feet dining area (2.93m x 3.66m), 
#     rectangular dining table 5-6 feet x 3 feet centered, 
#     4-6 dining chairs around table, 
#     adjacent to kitchen with easy access, 
#     connects to passage and living areas, 
#     intimate space perfect for family meals'''
# }

# # Additional architectural details from floor plan
# # COMMON_FEATURES = {
# #     'passage': '4 feet wide central passage (1.22m) connecting all rooms with smooth circulation',
# #     'toilets': '3 toilets - one 5x8.2 feet (1.52x2.50m), one 5x7.7 feet (1.52x2.34m), one 6x6 feet (1.83x1.83m)',
# #     'wash_area': 'dedicated wash area 7.5 feet x 2.2 feet (2.28m x 0.67m)',
# #     'store': 'storage room 5 feet x 5 feet (1.52m x 1.52m) near kitchen',
# #     'open_terrace': 'large open terrace accessible from living room for outdoor relaxation'
# # }

# # Predefined interior design styles
# INTERIOR_STYLES = {
#     'modern': 'modern minimalist interior design with clean lines, neutral color palette, contemporary furniture, sleek finishes',
#     'scandinavian': 'scandinavian interior design with light wood tones, white walls, cozy textiles, natural light, hygge aesthetic',
#     'industrial': 'industrial loft interior design with exposed brick walls, metal fixtures, concrete elements, raw materials',
#     'minimalist': 'minimalist interior design with simple forms, uncluttered space, functional furniture, zen-like atmosphere',
#     'traditional': 'traditional classic interior design with elegant furniture, rich colors, ornate details, timeless appeal',
#     'bohemian': 'bohemian eclectic interior design with colorful textiles, artistic elements, plants, global-inspired decor',
#     'contemporary': 'contemporary interior design with current trends, mixed materials, bold accents, comfortable sophistication',
#     'coastal': 'coastal beach-inspired interior with light blues, whites, natural textures, airy feel, relaxed atmosphere'
# }

# # Image generation parameters
# IMAGE_CONFIG = {
#     'width': 1024,
#     'height': 768,
#     'num_images': 2,
#     'guidance_scale': 7.5,
#     'num_inference_steps': 50,
#     'prompt_strength': 0.75  # How much to transform the input image (0.5-0.9)
# }

# # Window specifications for accurate prompting
# # WINDOW_DETAILS = {
# #     'master_bedroom': 'large 4x4 feet window on right wall with curtains or blinds, natural daylight',
# #     'bedroom_1': 'large 4x4 feet window on left wall with window treatment, good ventilation',
# #     'bedroom_2': 'large 4x4 feet window on left wall with natural light streaming in'
# # }

# # Furniture placement guidelines based on floor plan
# # FURNITURE_PLACEMENT = {
# #     'master_bedroom': {
# #         'bed': 'centered against left wall, headboard on wall',
# #         'nightstands': 'on both sides of bed',
# #         'dresser': 'opposite to bed or on wall near window',
# #         'seating': 'small chair or bench near window if space permits'
# #     },
# #     'bedroom_1': {
# #         'bed': 'against right wall to maximize floor space',
# #         'wardrobe': 'on left wall near door',
# #         'study_desk': 'near window for natural light',
# #         'nightstand': 'beside bed'
# #     },
# #     'bedroom_2': {
# #         'bed': 'centered against back wall',
# #         'wardrobe': 'compact wardrobe on available wall',
# #         'desk': 'small desk or shelf unit if space allows',
# #         'efficient_storage': 'under-bed storage for space optimization'
# #     },
# #     'living_room': {
# #         'main_seating': 'L-shaped or sectional sofa facing entertainment wall',
# #         'tv_unit': 'on main wall with storage',
# #         'coffee_table': 'centered in seating area',
# #         'accent_chairs': 'near terrace door or as additional seating',
# #         'console': 'in foyer area near entrance',
# #         'decor': 'plants near terrace, artwork on walls'
# #     },
# #     'kitchen': {
# #         'layout': 'L-shaped counter with cooking range on one side',
# #         'sink': 'under window or on main counter',
# #         'refrigerator': 'in corner for easy access',
# #         'cabinets': 'upper and lower cabinets for storage',
# #         'microwave': 'on counter or built-in'
# #     },
# #     'dining_room': {
# #         'table': 'rectangular table centered in room',
# #         'chairs': '4-6 chairs around table',
# #         'sideboard': 'optional sideboard against wall for serving',
# #         'lighting': 'pendant light centered above table'
# #     }
# # }

# # Door positions for spatial accuracy
# # DOOR_POSITIONS = {
# #     'master_bedroom': 'door on bottom wall connecting to 1.22m wide passage',
# #     'bedroom_1': 'door on bottom wall near toilet, opens to passage',
# #     'bedroom_2': 'door on right wall connecting to central passage',
# #     'living_room': 'main entrance from foyer area, access to open terrace',
# #     'kitchen': 'door connecting to dining area and passage',
# #     'dining_room': 'open connection to passage and kitchen'
# # }
"""
Final Ready-to-Use Config for Interior Design AI
Based on your actual floor plan with correct camera positions
"""

# Room base descriptions (for furnished rooms)
ROOM_DESCRIPTIONS = {
    'master_bedroom': 'luxurious master bedroom with elegant design',
    'bedroom_1': 'comfortable bedroom with modern amenities',
    'living_room': 'combined living room and puja area with traditional elements',
    'kitchen': 'modern kitchen with functional layout',
    'dining_room': 'welcoming dining area with beautiful setup',
}

# Room spatial specifications based on YOUR floor plan with camera viewpoint
ROOM_DIMENSIONS = {
    'master_bedroom': '''14 feet x 17 feet (4.27m x 5.18m) master bedroom,
    photographed from the front of the bed (bed is directly in front of camera),
    window on LEFT wall with soft natural sunlight streaming in,
    bed positioned in front of camera view,
    wardrobe on RIGHT wall,
    door opening on the wall behind camera position,
    spacious rectangular elegant layout''',
    
    'bedroom_1': '''14 feet x 13 feet (4.27m x 3.96m) bedroom,
    photographed from entrance gate (connected to living room),
    bed directly in front of camera,
    window on BACK wall behind the bed with natural light,
    wardrobe on LEFT wall,
    door to attached toilet on RIGHT wall,
    door to small balcony also on RIGHT wall,
    well-proportioned comfortable rectangular room''',
    
    'living_room': '''11.5x12.5 ft rectangular living room, front view. Left side: flat white arched puja alcove built INTO left wall, golden Om, Ganesha idol, white base cabinet. Center: beige L-sofa with chaise, round marble tables, patterned rug. Right side: wooden door on right wall, palm plant. Back: concrete accent wall with large artwork above sofa. Glossy white marble floor.''',
    
    'kitchen': '''10x20.6 ft modern L-shaped kitchen. Left: tall fridge, built-in oven, wooden storage. Center: wooden utility door. Right: grey modular cabinets, terrazzo countertop, steel sink, black chimney. Back: window with blinds, wooden open shelving. Cream marble floor, recessed ceiling lights, contemporary design.''',
    
    'dining_room': '''comfortable dining space,
    family-friendly dining setup,
    adjacent to kitchen for convenience,
    welcoming atmosphere''',
}

# Predefined interior design styles (with furniture and decor)
INTERIOR_STYLES = {
    'modern': 'modern minimalist design with clean lines, neutral colors, sleek furniture, contemporary lighting, glass and metal accents, uncluttered space, polished flooring',
    
    'scandinavian': 'scandinavian style with light wood furniture, white walls, cozy textiles, natural light, hygge aesthetic, minimalist decor, plants, bright airy feel',
    
    'industrial': 'industrial loft style with metal accents, exposed brick or concrete walls, leather furniture, Edison bulbs, urban warehouse aesthetic, raw materials',
    
    'minimalist': 'minimalist design with essential furniture only, simple forms, neutral palette, clean surfaces, zen atmosphere, functional pieces, uncluttered space',
    
    'traditional': 'traditional classic design with elegant wooden furniture, rich fabrics, ornate details, warm colors, timeless decor, vintage elements, crown molding',
    
    'contemporary': 'contemporary style with modern furniture, mixed materials, bold accent colors, artistic elements, sophisticated look, sleek finishes, current trends',
    
    'luxury': 'luxury interior with premium furniture, velvet upholstery, gold accents, crystal chandeliers, marble surfaces, opulent decor, high-end finishes, elegant details',
    
    'coastal': 'coastal beach style with light blue and white colors, wicker furniture, nautical decor, natural textures, airy feel, relaxed atmosphere, seaside elements',
    
    'rustic': 'rustic countryside style with reclaimed wood furniture, stone accents, earthy tones, vintage pieces, cozy atmosphere, natural materials, cabin-like warmth',
    
    'japanese': 'japanese zen style with low furniture, natural materials, shoji screens, minimal decor, tatami elements, peaceful ambiance, bamboo accents, zen-inspired',
    
    'bohemian': 'bohemian eclectic style with colorful textiles, layered rugs, plants, macrame, global-inspired decor, artistic vibe, mix of patterns, vibrant atmosphere',
    
    'art_deco': 'art deco style with geometric patterns, luxurious materials, bold colors, metallic accents, glamorous furniture, 1920s elegance, sophisticated glamour',
}

# Image generation parameters
IMAGE_CONFIG = {
    'width': 1024,
    'height': 768,
    'num_images': 2,
    'guidance_scale': 7.5,
    'num_inference_steps': 50,
    'prompt_strength': 0.75  # How much to transform the input image (0.5-0.9)
}

# Additional room details for reference
ROOM_NOTES = {
    'ground_floor': {
        'master_bedroom': 'Ground floor, 14\'x17\', window on left, wardrobe right, bed in front, door at back',
        'bedroom_1': 'Ground floor, 14\'x13\', bed in front, window at back, wardrobe left, toilet door right, balcony access right',
        'living_puja': 'Combined space 11\'6"x12\'6" + 5\'x5\' puja corner, photographed from master bedroom door, staircase on left',
        'toilets': 'Two toilets on ground floor - 6\'4"x8\'3" and 6\'x8\'6"',
        'wet_area': 'Utility space adjacent to toilets',
        'dress_area': '6\'x8\'6" dressing/storage area'
    },
    'upper_floor': {
        'bedroom_2': '14\'x17\'9" with attached facilities',
        'bedroom_3': '14\'x13\' with 6\'9"x4\'9" balcony',
        'toilet': '6\'4"x8\'3" attached bathroom'
    }
}

# Camera position summary (for your reference)
CAMERA_POSITIONS = {
    'master_bedroom': 'From front of bed (bed in front, window left, wardrobe right)',
    'bedroom_1': 'From entrance gate (bed in front, window back, wardrobe left, doors right)',
    'living_room': 'From master bedroom entry door (puja corner integrated, staircase left)',
}