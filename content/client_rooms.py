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
                    {"id": "master_bedroom",    "name": "Master Bedroom",      "image": "nakheel_masterbedroom(townhouse).png"},
                    {"id": "bedroom_1",         "name": "Bedroom 1",        "image": "nakheel_bedroom1.jpg"},
                    {"id": "bedroom_2",         "name": "Bedroom 2",        "image": "nakheel_bedroom2.png"},
                    {"id": "bedroom_3",         "name": "Bedroom 3",        "image": "nakheel_bedroom3.png"},
                    {"id": "living_room",       "name": "Living Room",         "image": "nakheel_livingroom(townhouse).jpg"},
                    {"id": "kitchen",           "name": "Kitchen",             "image": "nakheel_kitchen(townhouse).png"},
                    
                ],

        
        "1BR": [
            {"id": "master_bedroom",    "name": "Master Bedroom",      "image": "nakheel_masterbedroom(1br-3br).png"},
            {"id": "living_room",       "name": "Living Room",         "image": "nakheel_livingroom(1br).jpg"},
            {"id": "kitchen",           "name": "Kitchen",             "image": "nakheel_kitchen(1br-3br).png"},
            
        ],
        "2BR": [
                    {"id": "master_bedroom", "name": "Master Bedroom",   "image": "nakheel_masterbedroom(2br).png"},
                    {"id": "bedroom",        "name": "Bedroom",          "image": "nakheel_bedroom1.jpg"},
                    {"id": "living_room",    "name": "Living Room",      "image":"nakheel_livingroom(2br).jpg"},
                    {"id": "kitchen",        "name": "Kitchen",          "image": "nakheel_kitchen(2br-4br).png"},
                    
                ],
                "3BR": [
                    {"id": "master_bedroom", "name": "Master Bedroom",   "image": "nakheel_masterbedroom(1br-3br).png"},
                    {"id": "bedroom_1",      "name": "Bedroom 1",        "image": "nakheel_bedroom1.jpg"},
                    {"id": "bedroom_2",      "name": "Bedroom 2",        "image": "nakheel_bedroom2.png"},
                    {"id": "living_room",    "name": "Living Room",      "image": "nakheel_livingroom(3br).png"},
                    {"id": "kitchen",        "name": "Kitchen",          "image": "nakheel_kitchen(1br-3br).png"},
                    
                ],
                "4BR": [
                    {"id": "master_bedroom", "name": "Master Bedroom",   "image": "nakheel_masterbedroom(4br).png"},
                    {"id": "bedroom_1",      "name": "Bedroom 1",        "image": "nakheel_bedroom1.jpg"},
                    {"id": "bedroom_2",      "name": "Bedroom 2",        "image": "nakheel_bedroom2.png"},
                    {"id": "bedroom_3",      "name": "Bedroom 3",        "image": "nakheel_bedroom3.png"},
                    {"id": "living_room",    "name": "Living Room",      "image": "nakheel_livingroom(4br).jpg"},
                    {"id": "kitchen",        "name": "Kitchen",          "image": "nakheel_kitchen(2br-4br).png"},
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
         "fam": {
        "1br": [
            {"id": "master_bedroom", "name": "Master Bedroom", "image": "fam_master-bedroom(1br).png"},
            {"id": "living_room",    "name": "Living Room",    "image": "fam_Living-room(1br).png"},
            {"id": "kitchen",        "name": "Kitchen",        "image": "fam_kitchen(1br-2br).png"},
        ],
        "2br": [
            {"id": "master_bedroom", "name": "Master Bedroom", "image": "fam_master-bedroom(2br).png"},
            {"id": "bedroom",        "name": "Bedroom",        "image": "fam_bedroom(1br-2br).jpg"},
            {"id": "living_room",    "name": "Living Room",    "image": "fam_Living-room(2br).png"},
            {"id": "kitchen",        "name": "Kitchen",        "image": "fam_kitchen(1br-2br).png"},
        ],
        "3br": [
            {"id": "master_bedroom", "name": "Master Bedroom", "image": "fam_master-bedroom(3br).png"},
            {"id": "bedroom_1",      "name": "Bedroom 1",      "image": "fam_bedroom1(3br).png"},
            {"id": "bedroom_2",      "name": "Bedroom 2",      "image": "fam_bedroom2(3br).png"},
            {"id": "living_room",    "name": "Living Room",    "image": "fam_Living-room(3br).png"},
            {"id": "kitchen",        "name": "Kitchen",        "image": "fam_kitchen(3br).png"},
        ],
    },  
    "home-and-rentals": {
                
                        "Single-Family(TWO-STORY)": [
                            {"id": "master_bedroom", "name": "Master Bedroom",   "image": "home-and-rentals_master-bedroom.jpeg"},
                            {"id": "bedroom_1",      "name": "Bedroom 1",        "image": "home-and-rentals_bedroom-1.jpeg"},
                            {"id": "bedroom_2",      "name": "Bedroom 2",        "image": "home-and-rentals_bedroom-2.jpeg"},
                            {"id": "bedroom_3",      "name": "Bedroom 3",        "image": "home-and-rentals_bedroom-3.jpeg"},
                            {"id": "living_room",    "name": "Living Room",      "image": "home-and-rentals_living-room.jpeg"},
                            {"id": "kitchen",        "name": "Kitchen",          "image": "home-and-rentals_kitchen.jpeg"},
                            {"id": "bathroom",       "name": "Bathroom",         "image": "home-and-rentals_bathroom.jpeg"},
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


CLIENT_ONLY_ROOM_TYPES = {
    r["id"]
    for units in CLIENT_UNIT_ROOMS.values()
    for rooms in units.values()
    for r in rooms
}