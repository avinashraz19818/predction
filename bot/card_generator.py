import io
import logging
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

def generate_win_result_card(
    game_name: str,
    issue_number: str,
    choice: str,
    actual_number: int,
    level: int,
    streak: int
) -> io.BytesIO:
    """
    Generates a dark-mode neon glowing VIP Result Image Card
    """
    width, height = 800, 480
    bg_color = (15, 17, 26)  # Dark sleek navy
    
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Outer Border Glow
    draw.rectangle([10, 10, width - 10, height - 10], outline=(40, 45, 65), width=3)
    draw.rectangle([16, 16, width - 16, height - 16], outline=(255, 215, 0), width=2)
    
    # Header Banner
    header_text = f"★ VIP {game_name.upper()} OFFICIAL RESULT ★"
    draw.text((width // 2, 45), header_text, fill=(255, 215, 0), anchor="mm")
    
    # Divider
    draw.line([(50, 75), (width - 50, 75)], fill=(70, 75, 100), width=2)
    
    # Issue Number
    draw.text((60, 120), "PERIOD ISSUE:", fill=(160, 170, 190), anchor="lm")
    draw.text((width - 60, 120), str(issue_number), fill=(255, 255, 255), anchor="rm")
    
    # Predicted Choice
    choice_color = (255, 75, 75) if choice == "BIG" else (75, 220, 100)
    draw.text((60, 180), "PREDICTION:", fill=(160, 170, 190), anchor="lm")
    draw.text((width - 60, 180), f"{choice} ({'5-9' if choice == 'BIG' else '0-4'})", fill=choice_color, anchor="rm")
    
    # Actual Number
    draw.text((60, 240), "RESULT NUMBER:", fill=(160, 170, 190), anchor="lm")
    draw.text((width - 60, 240), f"{actual_number} ({choice})", fill=(255, 215, 0), anchor="rm")
    
    # Level Won
    draw.text((60, 300), "STATUS:", fill=(160, 170, 190), anchor="lm")
    draw.text((width - 60, 300), f"WIN AT LEVEL {level}", fill=(75, 220, 100), anchor="rm")
    
    # Divider
    draw.line([(50, 350), (width - 50, 350)], fill=(70, 75, 100), width=2)
    
    # Winning Stamp / Footer Badge
    draw.rectangle([180, 380, width - 180, 440], fill=(20, 90, 45), outline=(75, 220, 100), width=2)
    draw.text((width // 2, 410), f"★ 100% VERIFIED WIN ({streak}x STREAK) ★", fill=(255, 255, 255), anchor="mm")
    
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output
