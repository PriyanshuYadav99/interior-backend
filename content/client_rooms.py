"""
Per-client, per-unit room lists and their reference-image filenames.
A client NOT listed in CLIENT_UNIT_ROOMS is treated as "not unit-aware"
and falls back to the old global ROOM_IMAGES/FIXED_ROOM_LAYOUTS behavior.
"""

CLIENT_UNIT_ROOMS = {
    "the-wow-tower": {
        "studio": [
            {"id": "studio_room",    "name": "Living & Bedroom", "image": "the-wow-tower_living-and-bedroom(studio).webp"},
            {"id": "kitchen",        "name": "Kitchen",          "image": "the-wow-tower_kitchen.webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
        "1BR": [
            {"id": "master_bedroom", "name": "Master Bedroom",   "image": "the-wow-tower_master-bedroom(1BR-2BR).webp"},
            {"id": "living_room",    "name": "Living Room",      "image": "the-wow-tower_living-room(1BR).webp"},
            {"id": "kitchen",        "name": "Kitchen",          "image": "the-wow-tower_kitchen.webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
        "2BR": [
            {"id": "master_bedroom", "name": "Master Bedroom",   "image": "the-wow-tower_master-bedroom(1BR-2BR).webp"},
            {"id": "bedroom",        "name": "Bedroom",          "image": "the-wow-tower_bedroom.png"},
            {"id": "living_room",    "name": "Living Room",      "image": "the-wow-tower_living-room(2BR).webp"},
            {"id": "kitchen",        "name": "Kitchen",          "image": "the-wow-tower_kitchen.webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
        "3BR": [
            {"id": "master_bedroom", "name": "Master Bedroom",   "image": "the-wow-tower_master-bedroom(3BR).webp"},
            {"id": "bedroom",        "name": "Bedroom",          "image": "the-wow-tower_bedroom.png"},
            {"id": "living_room",    "name": "Living Room",      "image": "the-wow-tower_living-room(3BR).webp"},
            {"id": "kitchen",        "name": "Kitchen",          "image": "the-wow-tower_kitchen.webp"},
            {"id": "gym",            "name": "Gym",              "image": "the-wow-tower_gym.webp"},
            {"id": "kids_play_area", "name": "Kids Play Area",   "image": "the-wow-tower_kids-play-area.webp"},
            {"id": "swimming_pool",  "name": "Swimming Pool",    "image": "the-wow-tower_swimming-pool.webp"},
        ],
    },
}


def get_client_rooms(client_name, flat_type=None):
    """Rooms for client+unit, or None if this client isn't unit-aware
    (caller should fall back to the global room list)."""
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