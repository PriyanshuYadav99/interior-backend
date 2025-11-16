from config import ROOM_DESCRIPTIONS, INTERIOR_STYLES, ROOM_DIMENSIONS

# def construct_ai_prompt(room_type, style=None, custom_prompt=None):
#     """
#     Construct detailed prompt for AI image generation with spatial information
    
#     Args:
#         room_type (str): Type of room (e.g., 'master_bedroom')
#         style (str): Predefined style (e.g., 'modern')
#         custom_prompt (str): Custom user-provided description
    
#     Returns:
#         dict: Contains 'prompt' and 'negative_prompt'
#     """
    
#     # Get base room description
#     room_desc = ROOM_DESCRIPTIONS.get(room_type, 'interior room')
    
#     # Get room dimensions
#     dimensions = ROOM_DIMENSIONS.get(room_type, '')
    
#     # Build main prompt
#     if custom_prompt and custom_prompt.strip():
#         # User provided custom styling
#         main_prompt = f"Professional interior design photograph of a {room_desc}"
#         if dimensions:
#             main_prompt += f", {dimensions}"
#         main_prompt += f", {custom_prompt}"
#     elif style and style in INTERIOR_STYLES:
#         # Use predefined style
#         style_desc = INTERIOR_STYLES[style]
#         main_prompt = f"Professional interior design photograph of a {room_desc}"
#         if dimensions:
#             main_prompt += f", {dimensions}"
#         main_prompt += f", {style_desc}"
#     else:
#         # Default modern style
#         main_prompt = f"Professional interior design photograph of a {room_desc}"
#         if dimensions:
#             main_prompt += f", {dimensions}"
#         main_prompt += ", modern minimalist design"
    
#     # Add quality enhancers
#     prompt = f"{main_prompt}, high resolution, detailed, professional photography, architectural digest, interior design magazine, 8k, sharp focus, well lit"
    
#     # Negative prompt to avoid unwanted elements
#     negative_prompt = "blurry, low quality, distorted, ugly, bad anatomy, deformed, amateur, dark, underexposed, overexposed, watermark, text, signature, people, humans"
    
#     return {
#         'prompt': prompt,
#         'negative_prompt': negative_prompt
#     }

# # Alias for backward compatibility
# construct_prompt = construct_ai_prompt

# def validate_inputs(room_type, style, custom_prompt):
#     """Validate user inputs"""
    
#     if not room_type or room_type not in ROOM_DESCRIPTIONS:
#         return False, "Invalid room type selected"
    
#     if not style and not custom_prompt:
#         return False, "Please select a style or provide custom prompt"
    
#     if custom_prompt and len(custom_prompt) > 500:
#         return False, "Custom prompt is too long (max 500 characters)"
    
#     return True, "Valid"
from config import ROOM_DESCRIPTIONS, INTERIOR_STYLES, ROOM_DIMENSIONS

def construct_ai_prompt(room_type, style=None, custom_prompt=None):
    """
    Construct detailed prompt for AI image generation with spatial information
    
    Args:
        room_type (str): Type of room (e.g., 'master_bedroom')
        style (str): Predefined style (e.g., 'modern')
        custom_prompt (str): Custom user-provided description
    
    Returns:
        dict: Contains 'prompt' and 'negative_prompt'
    """
    
    # Get base room description
    room_desc = ROOM_DESCRIPTIONS.get(room_type, 'interior room')
    
    # Get room dimensions
    dimensions = ROOM_DIMENSIONS.get(room_type, '')
    
    # Build main prompt
    if custom_prompt and custom_prompt.strip():
        # CUSTOM PROMPT - Use simple room name to avoid conflicting descriptions
        simple_room = room_type.replace('_', ' ')  # e.g., "master_bedroom" -> "master bedroom"
        
        main_prompt = f"{custom_prompt}, {simple_room}"
        
        # Extract only the size from dimensions (first part before comma)
        if dimensions:
            size_only = dimensions.split(',')[0].strip()
            main_prompt += f", {size_only}"
        
        # Minimal quality enhancers + reinforce custom theme at end
        prompt = f"{main_prompt}, high quality, detailed, 8k, {custom_prompt} style"
        
        # DEBUG: Print the actual prompt being sent
        print(f"\n{'='*60}")
        print(f"DEBUG - CUSTOM PROMPT DETECTED")
        print(f"User input: {custom_prompt}")
        print(f"Room type: {room_type}")
        print(f"Final prompt: {prompt}")
        print(f"{'='*60}\n")
        
    elif style and style in INTERIOR_STYLES:
        # Use predefined style - full professional treatment with detailed description
        style_desc = INTERIOR_STYLES[style]
        main_prompt = f"Professional interior design photograph of a {room_desc}"
        if dimensions:
            main_prompt += f", {dimensions}"
        main_prompt += f", {style_desc}"
        prompt = f"{main_prompt}, high resolution, detailed, professional photography, architectural digest, interior design magazine, 8k, sharp focus, well lit"
        
        print(f"\n{'='*60}")
        print(f"DEBUG - PREDEFINED STYLE")
        print(f"Style: {style}")
        print(f"Final prompt: {prompt}")
        print(f"{'='*60}\n")
        
    else:
        # Default modern style
        main_prompt = f"Professional interior design photograph of a {room_desc}"
        if dimensions:
            main_prompt += f", {dimensions}"
        main_prompt += ", modern minimalist design"
        prompt = f"{main_prompt}, high resolution, detailed, professional photography, 8k, sharp focus, well lit"
        
        print(f"\n{'='*60}")
        print(f"DEBUG - DEFAULT STYLE")
        print(f"Final prompt: {prompt}")
        print(f"{'='*60}\n")
    
    # Negative prompt to avoid unwanted elements
    negative_prompt = "blurry, low quality, distorted, ugly, bad anatomy, deformed, amateur, dark, underexposed, overexposed, watermark, text, signature, people, humans"
    
    return {
        'prompt': prompt,
        'negative_prompt': negative_prompt
    }

# Alias for backward compatibility
construct_prompt = construct_ai_prompt

def validate_inputs(room_type, style, custom_prompt):
    """Validate user inputs"""
    
    if not room_type or room_type not in ROOM_DESCRIPTIONS:
        return False, "Invalid room type selected"
    
    if not style and not custom_prompt:
        return False, "Please select a style or provide custom prompt"
    
    if custom_prompt and len(custom_prompt) > 500:
        return False, "Custom prompt is too long (max 500 characters)"
    
    return True, "Valid"
