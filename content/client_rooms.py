"""
Per-client, per-unit room lists and their reference-image filenames.
A client NOT listed in CLIENT_UNIT_ROOMS is treated as "not unit-aware"
and falls back to the old global ROOM_IMAGES/FIXED_ROOM_LAYOUTS behavior.
"""

CLIENT_UNIT_ROOMS = {
    "the-wow-tower": {
        "studio": [
            {"id": "studio_room",    "name": "Living & Bedroom", "image": "the-wow-tower_living-and-bedroom(studio).webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
        "1BR": [
            {"id": "master_bedroom", "name": "Master Bedroom",   "image": "the-wow-tower_master-bedroom(1BR-2BR).webp"},
            {"id": "living_room",    "name": "Living and Dining", "image": "the-wow-tower_living-room(1BR).webp"},
            {"id": "kitchen",        "name": "Kitchen",          "image": "the-wow-tower_kitchen.webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
        "2BR": [
            {"id": "master_bedroom", "name": "Master Bedroom",   "image": "the-wow-tower_master-bedroom(1BR-2BR).webp"},
            {"id": "bedroom",        "name": "Bedroom",          "image": "the-wow-tower_bedroom.png"},
            {"id": "living_room",    "name": "Living and Dining", "image": "the-wow-tower_living-room(2BR).webp"},
            {"id": "kitchen",        "name": "Kitchen",          "image": "the-wow-tower_kitchen.webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
        "3BR": [
            {"id": "master_bedroom", "name": "Master Bedroom",   "image": "the-wow-tower_master-bedroom(3BR).webp"},
            {"id": "bedroom_1",      "name": "Bedroom 1",        "image": "the-wow-tower_bedroom.png"},
            {"id": "bedroom_2",      "name": "Bedroom 2",        "image": "the-wow-tower_bedroom.png"},
            {"id": "living_room",    "name": "Living and Dining", "image": "the-wow-tower_living-room(3BR).webp"},
            {"id": "kitchen",        "name": "Kitchen",          "image": "the-wow-tower_kitchen.webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
    },
    "nakheel": {
        "Townhouse": [
                    {"id": "townhouse_living_room",    "name": "Living & Bedroom", "image": "nakheel_livingroom(townhouse).jpg"},
                    {"id": "gym",            "name": "Yoga Studio",      "image": "nakheel_yoga-studio.jpg"},
                    {"id": "kids_play_area", "name": "Kids Play Area",   "image": "nakheel_game-room.jpg"},
                    {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "nakheel_infinitypool.jpg"},
                ],

        
        "1BR": [
            {"id": "master_bedroom",    "name": "Master Bedroom",      "image": "nakheel_bedroom.jpg"},
            {"id": "living_room",       "name": "Living Room",         "image": "nakheel_livingroom(1br).jpg"},
            {"id": "dining",            "name": "Dining",              "image": "nakheel_dining.jpg"},
            {"id": "kitchen",           "name": "Kitchen",             "image": "nakheel_kitchen.png"},
            {"id": "gym",               "name": "Yoga Studio",         "image": "nakheel_yoga-studio.jpg"},
            {"id": "swimming_pool",     "name": "Swimming Pool",       "image": "nakheel_infinitypool.jpg"},
            {"id": "kids_play_area",    "name": "Kids Play Area",      "image": "nakheel_game-room.jpg"},
            
        ],
        "2BR": [
                    {"id": "master_bedroom", "name": "Master Bedroom",   "image": "nakheel_bedroom.jpg"},
                    {"id": "bedroom",        "name": "Bedroom",          "image": "nakheel_bedroom.jpg"},
                    {"id": "living_room",    "name": "Living Room",      "image":"nakheel_livingroom(2br-3br).jpg"},
                    {"id": "dining",         "name": "Dining",           "image": "nakheel_dining.jpg"},
                    {"id": "kitchen",        "name": "Kitchen",          "image": "nakheel_kitchen.png"},
                    {"id": "gym",            "name": "Yoga Studio",      "image": "nakheel_yoga-studio.jpg"},
                    {"id": "kids_play_area", "name": "Kids Play Area",   "image": "nakheel_game-room.jpg"},
                    {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "nakheel_infinitypool.jpg"},
                ],
                "3BR": [
                    {"id": "master_bedroom", "name": "Master Bedroom",   "image": "nakheel_bedroom.jpg"},
                    {"id": "bedroom_1",      "name": "Bedroom 1",          "image": "nakheel_bedroom.jpg"},
                    {"id": "bedroom_2",      "name": "Bedroom 2",        "image": "nakheel_bedroom.jpg"},
                    {"id": "living_room",    "name": "Living Room",      "image": "nakheel_livingroom(2br-3br).jpg"},
                    {"id": "dining",         "name": "Dining",           "image": "nakheel_dining.jpg"},
                    {"id": "kitchen",        "name": "Kitchen",          "image": "nakheel_kitchen.png"},
                    {"id": "gym",            "name": "Yoga Studio",      "image": "nakheel_yoga-studio.jpg"},
                    {"id": "kids_play_area", "name": "Kids Play Area",   "image": "nakheel_game-room.jpg"},
                    {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "nakheel_infinitypool.jpg"},
                ],
                "4BR": [
                    {"id": "master_bedroom", "name": "Master Bedroom",   "image": "nakheel_bedroom.jpg"},
                    {"id": "bedroom_1",      "name": "Bedroom 1",        "image": "nakheel_bedroom.jpg"},
                    {"id": "bedroom_2",      "name": "Bedroom 2",        "image": "nakheel_bedroom.jpg"},
                    {"id": "bedroom_3",      "name": "Bedroom 3",        "image": "nakheel_bedroom.jpg"},
                    {"id": "living_room",    "name": "Living Room",      "image": "nakheel_livingroom(4br).jpg"},
                    {"id": "dining",         "name": "Dining",           "image": "nakheel_dining.jpg"},
                    {"id": "kitchen",        "name": "Kitchen",          "image": "nakheel_kitchen.png"},
                    {"id": "gym",            "name": "Yoga Studio",      "image": "nakheel_yoga-studio.jpg"},
                    {"id": "kids_play_area", "name": "Kids Play Area",   "image": "nakheel_game-room.jpg"},
                    {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "nakheel_infinitypool.jpg"},
    ]},
    "spring-field": {
            
                    "3BR": [
                        {"id": "master_bedroom", "name": "Master Bedroom",   "image": "spring-field_master-bedroom.webp"},
                        {"id": "bedroom_1",      "name": "Bedroom 1",        "image": "spring-field_bedroom-1.webp"},
                        {"id": "bedroom_2",      "name": "Bedroom 2",        "image": "spring-field_bedroom-2.webp"},
                        {"id": "living_room",    "name": "Living Room",      "image": "spring-field_living-room.webp"},
                        {"id": "kitchen",        "name": "Kitchen",          "image": "spring-field_kitchen (1).webp"},
                        {"id": "gym",            "name": "Yoga Studio",      "image": "spring-field_yogastudio.jpg"},
                        {"id": "kids_play_area", "name": "Kids Play Area",   "image": "spring-field_gameroom.jpg"},
                        {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "spring-field_infinitypooll.jpg"},
                    ],
                    
        },
}


def get_client_rooms(client_name, flat_type=None):
    client_map = CLIENT_UNIT_ROOMS.get(client_name)
    if client_map is None:
        return None
    return client_map.get(flat_type, [])


def get_client_room_image(client_name, room_type, flat_type=None):
    rooms = get_client_rooms(client_name, flat_type)
    if rooms is None:
        return None
    for room in rooms:
        if room["id"] == room_type:
            return room["image"]
    return None


# Room ids that only exist for unit-aware clients (amenities, combined
# studio layouts, secondary bedrooms) and are intentionally NOT part of
# FIXED_ROOM_LAYOUTS, since FIXED_ROOM_LAYOUTS also doubles as the default
# room list for non-unit-aware clients — adding these there would leak
# "Gym"/"Bedroom 2" into clients that don't have those images.
# validate_inputs() in content/prompts.py checks this set so generation
# isn't blocked for these room types. Note: "bedroom_1" is NOT listed here
# because it already exists as a key in FIXED_ROOM_LAYOUTS.
UNIT_DISPLAY_NAMES = {
    "studio": "Studio", "1BR": "1 Bedroom", "2BR": "2 Bedrooms",
    "3BR": "3 Bedrooms", "4BR": "4 Bedrooms", "Townhouse": "Townhouse",
}

def get_client_units(client_name):
    """[{'id','name'}] for unit-aware clients, else None."""
    client_map = CLIENT_UNIT_ROOMS.get(client_name)
    if client_map is None:
        return None
    return [{'id': k, 'name': k} for k in client_map]

# Auto-built from the config above. Never edit by hand again.
CLIENT_ONLY_ROOM_TYPES = {
    r["id"]
    for units in CLIENT_UNIT_ROOMS.values()
    for rooms in units.values()
    for r in rooms
}