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
CLIENT_ONLY_ROOM_TYPES = {
    "gym", "kids_play_area", "swimming_pool", "studio_room",
    "bedroom", "bedroom_2",
}