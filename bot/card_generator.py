import io
import os
import math
import random
import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Loads a clean sans-serif TrueType font across Linux (Ubuntu/Debian) and Windows"""
    candidates = []
    if bold:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _draw_vertical_gradient(img: Image.Image, box: tuple, top_color: tuple, bottom_color: tuple, radius: int = 0):
    """Draws a smooth vertical gradient inside box (x1, y1, x2, y2) with optional rounded corners"""
    x1, y1, x2, y2 = box
    w = max(1, x2 - x1)
    h = max(1, y2 - y1)

    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grad)
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        a = int(top_color[3] + (bottom_color[3] - top_color[3]) * t) if len(top_color) > 3 else 255
        gdraw.line([(0, y), (w, y)], fill=(r, g, b, a))

    if radius > 0:
        mask = Image.new("L", (w, h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
        img.paste(grad, (x1, y1), mask)
    else:
        img.paste(grad, (x1, y1), grad)


def generate_win_result_card(
    game_name: str,
    issue_number: str,
    choice: str,
    actual_number: int,
    level: int = 1,
    streak: int = 1
) -> io.BytesIO:
    """
    Renders a high-resolution, authentic BDGWin Mobile WinGo UI screenshot
    complete with the official 'Congratulations' Winning Popup & 'My History' Win row.
    """
    W, H = 640, 1180
    img = Image.new("RGBA", (W, H), (34, 36, 42, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    f_title = _load_font(28, bold=True)
    f_wallet_num = _load_font(34, bold=True)
    f_wallet_sub = _load_font(18, bold=False)
    f_tab = _load_font(17, bold=True)
    f_small = _load_font(16, bold=False)
    f_small_b = _load_font(17, bold=True)
    f_timer = _load_font(30, bold=True)
    f_congrats = _load_font(42, bold=True)
    f_popup_lbl = _load_font(20, bold=True)
    f_pill = _load_font(20, bold=True)
    f_bonus_lbl = _load_font(22, bold=True)
    f_bonus_amt = _load_font(44, bold=True)
    f_period = _load_font(17, bold=False)

    # 1. BDGWin Top App Bar
    draw.rectangle([0, 0, W, 72], fill=(43, 45, 53, 255))
    draw.text((28, 36), "<", fill=(245, 215, 145), font=f_title, anchor="lm")
    draw.text((W // 2, 36), "BDGWIN", fill=(245, 210, 130), font=f_title, anchor="mm")

    # 2. Wallet Balance Card (Gold/Dark theme)
    _draw_vertical_gradient(img, (24, 90, W - 24, 235), (62, 65, 78, 255), (45, 48, 58, 255), radius=22)
    draw.rounded_rectangle([24, 90, W - 24, 235], radius=22, outline=(195, 160, 95, 120), width=2)
    draw.text((W // 2, 132), "₹28,468.40", fill=(255, 255, 255), font=f_wallet_num, anchor="mm")
    draw.text((W // 2, 166), "Wallet balance", fill=(190, 195, 210), font=f_wallet_sub, anchor="mm")

    # Withdraw & Deposit buttons
    draw.rounded_rectangle([65, 186, 285, 224], radius=19, fill=(210, 75, 70))
    draw.text((175, 205), "Withdraw", fill=(255, 255, 255), font=f_small_b, anchor="mm")
    draw.rounded_rectangle([W - 285, 186, W - 65, 224], radius=19, fill=(38, 185, 110))
    draw.text((W - 175, 205), "Deposit", fill=(255, 255, 255), font=f_small_b, anchor="mm")

    # 3. Game Mode Tabs (WinGo 30s, 1Min, 3Min, 5Min)
    tabs = ["WinGo 30sec", "WinGo 1Min", "WinGo 3Min", "WinGo 5Min"]
    active_idx = 0 if "30" in game_name.lower() else (1 if "1" in game_name.lower() else (2 if "3" in game_name.lower() else 3))
    tab_w = (W - 48) // 4
    for i, tname in enumerate(tabs):
        tx1 = 24 + i * tab_w
        tx2 = tx1 + tab_w - 6
        if i == active_idx:
            _draw_vertical_gradient(img, (tx1, 252, tx2, 326), (242, 208, 138, 255), (198, 152, 74, 255), radius=14)
            draw.text(((tx1 + tx2) // 2, 289), tname, fill=(40, 30, 10), font=f_tab, anchor="mm")
        else:
            draw.rounded_rectangle([tx1, 252, tx2, 326], radius=14, fill=(48, 51, 62))
            draw.text(((tx1 + tx2) // 2, 289), tname, fill=(160, 165, 180), font=f_tab, anchor="mm")

    # 4. Golden Period & Timer Card
    _draw_vertical_gradient(img, (24, 344, W - 24, 474), (235, 195, 120, 255), (192, 145, 68, 255), radius=18)
    draw.rounded_rectangle([42, 360, 188, 392], radius=14, outline=(50, 35, 10), width=2)
    draw.text((115, 376), "How to play", fill=(50, 35, 10), font=f_small_b, anchor="mm")
    draw.text((42, 412), tabs[active_idx], fill=(60, 42, 12), font=f_small_b, anchor="lm")

    # Mini history balls
    recent_nums = [actual_number, (actual_number + 3) % 10, (actual_number + 7) % 10, (actual_number + 1) % 10, (actual_number + 5) % 10]
    for idx_b, bnum in enumerate(recent_nums):
        bx = 56 + idx_b * 38
        by = 446
        bcol = (40, 180, 99) if bnum in (1, 3, 7, 9, 5) else (220, 65, 65)
        draw.ellipse([bx - 15, by - 15, bx + 15, by + 15], fill=bcol, outline=(255, 255, 255), width=2)
        draw.text((bx, by), str(bnum), fill=(255, 255, 255), font=f_small_b, anchor="mm")

    draw.text((W - 44, 368), "Time remaining", fill=(55, 38, 10), font=f_small_b, anchor="rm")
    # Timer digits
    digits = ["0", "0", ":", "2", "6"]
    for idx_d, dg in enumerate(digits):
        dx = W - 210 + idx_d * 38
        draw.rounded_rectangle([dx, 388, dx + 32, 430], radius=6, fill=(40, 42, 52))
        draw.text((dx + 16, 409), dg, fill=(245, 210, 130), font=f_timer, anchor="mm")
    draw.text((W - 44, 452), str(issue_number), fill=(40, 28, 8), font=f_small_b, anchor="rm")

    # 5. Betting Board Area (Green / Violet / Red + Big / Small)
    draw.rounded_rectangle([24, 490, W - 24, 710], radius=18, fill=(45, 48, 58))
    draw.rounded_rectangle([42, 508, 208, 554], radius=12, fill=(40, 180, 99))
    draw.text((125, 531), "Green", fill=(255, 255, 255), font=f_pill, anchor="mm")
    draw.rounded_rectangle([232, 508, 408, 554], radius=12, fill=(142, 68, 173))
    draw.text((320, 531), "Violet", fill=(255, 255, 255), font=f_pill, anchor="mm")
    draw.rounded_rectangle([432, 508, W - 42, 554], radius=12, fill=(220, 65, 65))
    draw.text(((432 + W - 42) // 2, 531), "Red", fill=(255, 255, 255), font=f_pill, anchor="mm")

    # Big / Small Bar
    draw.rounded_rectangle([60, 646, 318, 694], radius=22, fill=(235, 162, 45))
    draw.text((189, 670), "Big", fill=(255, 255, 255), font=f_pill, anchor="mm")
    draw.rounded_rectangle([322, 646, W - 60, 694], radius=22, fill=(82, 148, 235))
    draw.text(((322 + W - 60) // 2, 670), "Small", fill=(255, 255, 255), font=f_pill, anchor="mm")

    # 6. History Tabs & "My history" Win Row at Bottom
    draw.rounded_rectangle([24, 728, 205, 776], radius=12, fill=(52, 55, 66))
    draw.text((114, 752), "Game history", fill=(170, 175, 190), font=f_tab, anchor="mm")
    draw.rounded_rectangle([220, 728, 400, 776], radius=12, fill=(52, 55, 66))
    draw.text((310, 752), "Chart", fill=(170, 175, 190), font=f_tab, anchor="mm")
    _draw_vertical_gradient(img, (415, 728, W - 24, 776), (242, 208, 138, 255), (198, 152, 74, 255), radius=12)
    draw.text(((415 + W - 24) // 2, 752), "My history", fill=(40, 28, 8), font=f_tab, anchor="mm")

    # Compute realistic bet & win amounts based on level
    bet_amounts = {1: 1000, 2: 3000, 3: 9000, 4: 27000, 5: 81000}
    base_bet = bet_amounts.get(level, 1000)
    win_payout = base_bet * 1.96
    win_str = f"₹{win_payout:,.2f}"

    # My History List Card in Background
    draw.rounded_rectangle([24, 792, W - 24, 1140], radius=16, fill=(43, 46, 56))
    for row_i in range(3):
        ry = 820 + row_i * 98
        r_issue = str(int(issue_number) - row_i) if str(issue_number).isdigit() else issue_number
        r_choice = choice.upper() if row_i == 0 else ("BIG" if row_i % 2 == 0 else "SMALL")
        badge_bg = (235, 162, 45) if r_choice == "BIG" else (82, 148, 235)
        draw.rounded_rectangle([44, ry, 108, ry + 64], radius=14, fill=badge_bg)
        draw.text((76, ry + 32), r_choice.capitalize(), fill=(255, 255, 255), font=f_small_b, anchor="mm")
        draw.text((126, ry + 18), r_issue, fill=(240, 240, 245), font=f_tab, anchor="lm")
        draw.text((126, ry + 48), "Succeed", fill=(150, 155, 170), font=f_small, anchor="lm")

        draw.rounded_rectangle([W - 210, ry + 4, W - 125, ry + 34], radius=8, outline=(46, 204, 113), width=2)
        draw.text((W - 167, ry + 19), "Succeed", fill=(46, 204, 113), font=f_small, anchor="mm")
        r_amt = f"+{win_str}" if row_i == 0 else "+₹1,960.00"
        draw.text((W - 48, ry + 52), r_amt, fill=(46, 204, 113), font=f_tab, anchor="rm")

    # 7. Semi-Transparent Dark Backdrop Overlay (Modal Dimmer)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 130))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 8. BDGWin Official "Congratulations" Winning Popup Card!
    pop_x1, pop_y1, pop_x2, pop_y2 = 64, 210, W - 64, 930

    # Glowing Golden Halo + Top Trophy/Wings Header
    draw.ellipse([W // 2 - 110, pop_y1 - 75, W // 2 + 110, pop_y1 + 95], fill=(255, 195, 70, 255), outline=(255, 235, 150), width=4)
    draw.ellipse([W // 2 - 82, pop_y1 - 52, W // 2 + 82, pop_y1 + 72], fill=(255, 140, 35, 255))
    draw.text((W // 2, pop_y1 + 5), "WIN", fill=(255, 250, 210), font=f_congrats, anchor="mm")

    # Main Orange-Red 3D Gradient Popup Body
    _draw_vertical_gradient(
        img,
        (pop_x1, pop_y1 + 50, pop_x2, pop_y2),
        (255, 126, 65, 255),
        (232, 62, 52, 255),
        radius=34
    )
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([pop_x1, pop_y1 + 50, pop_x2, pop_y2], radius=34, outline=(255, 218, 130), width=3)

    # "Congratulations" Title
    draw.text((W // 2, pop_y1 + 118), "Congratulations", fill=(255, 255, 255), font=f_congrats, anchor="mm")

    # Decorative golden sparkles
    for sx, sy in [(pop_x1 + 45, pop_y1 + 95), (pop_x2 - 45, pop_y1 + 95), (pop_x1 + 65, pop_y1 + 150), (pop_x2 - 65, pop_y1 + 150)]:
        draw.ellipse([sx - 5, sy - 5, sx + 5, sy + 5], fill=(255, 235, 140))

    # Lottery Results Row
    res_y = pop_y1 + 215
    draw.text((pop_x1 + 36, res_y), "Lottery results", fill=(255, 245, 225), font=f_popup_lbl, anchor="lm")

    # Determine color label of actual_number (standard WinGo rules)
    if actual_number in (1, 3, 7, 9):
        color_name = "Green"
        pill_col = (40, 180, 99)
    elif actual_number in (2, 4, 6, 8):
        color_name = "Red"
        pill_col = (215, 55, 55)
    elif actual_number == 5:
        color_name = "Green Violet"
        pill_col = (40, 180, 99)
    else:
        color_name = "Red Violet"
        pill_col = (215, 55, 55)

    # Pill 1: Color badge
    draw.rounded_rectangle([pop_x1 + 205, res_y - 22, pop_x1 + 325, res_y + 22], radius=10, fill=pill_col, outline=(255, 255, 255), width=2)
    draw.text((pop_x1 + 265, res_y), color_name.split()[0], fill=(255, 255, 255), font=f_pill, anchor="mm")

    # Pill 2: Winning Number Circle
    draw.ellipse([pop_x1 + 338, res_y - 22, pop_x1 + 382, res_y + 22], fill=pill_col, outline=(255, 255, 255), width=2)
    draw.text((pop_x1 + 360, res_y), str(actual_number), fill=(255, 255, 255), font=f_pill, anchor="mm")

    # Pill 3: Big / Small Badge
    bs_text = "Big" if choice.upper() == "BIG" else "Small"
    bs_col = (235, 162, 45) if choice.upper() == "BIG" else (82, 148, 235)
    draw.rounded_rectangle([pop_x1 + 395, res_y - 22, pop_x2 - 28, res_y + 22], radius=10, fill=bs_col, outline=(255, 255, 255), width=2)
    draw.text(((pop_x1 + 395 + pop_x2 - 28) // 2, res_y), bs_text, fill=(255, 255, 255), font=f_pill, anchor="mm")

    # White/Cream Bonus Ticket Box inside Popup
    ticket_y1 = pop_y1 + 285
    ticket_y2 = pop_y1 + 555
    _draw_vertical_gradient(
        img,
        (pop_x1 + 32, ticket_y1, pop_x2 - 32, ticket_y2),
        (255, 252, 242, 255),
        (255, 238, 210, 255),
        radius=24
    )
    draw = ImageDraw.Draw(img)

    # Ticket side notches
    draw.ellipse([pop_x1 + 16, (ticket_y1 + ticket_y2) // 2 - 16, pop_x1 + 48, (ticket_y1 + ticket_y2) // 2 + 16], fill=(242, 90, 58))
    draw.ellipse([pop_x2 - 48, (ticket_y1 + ticket_y2) // 2 - 16, pop_x2 - 16, (ticket_y1 + ticket_y2) // 2 + 16], fill=(242, 90, 58))

    # Dashed divider line on ticket
    for dx in range(pop_x1 + 56, pop_x2 - 56, 18):
        draw.line([(dx, (ticket_y1 + ticket_y2) // 2), (dx + 10, (ticket_y1 + ticket_y2) // 2)], fill=(225, 195, 160), width=2)

    # Bonus Label & Amount
    draw.text((W // 2, ticket_y1 + 42), "Bonus", fill=(230, 75, 50), font=f_bonus_lbl, anchor="mm")
    draw.text((W // 2, ticket_y1 + 92), win_str, fill=(225, 50, 40), font=f_bonus_amt, anchor="mm")

    # Period Info inside Ticket
    mode_label = tabs[active_idx]
    draw.text((W // 2, ticket_y2 - 78), f"Period: {mode_label}", fill=(110, 100, 90), font=_load_font(20, bold=True), anchor="mm")
    draw.text((W // 2, ticket_y2 - 42), str(issue_number), fill=(70, 65, 60), font=_load_font(22, bold=True), anchor="mm")

    # Auto-close indicator at bottom of popup
    cx, cy = pop_x1 + 62, pop_y2 - 54
    draw.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], outline=(255, 255, 255), width=2)
    draw.line([(cx - 6, cy), (cx - 1, cy + 5), (cx + 7, cy - 5)], fill=(255, 255, 255), width=3)
    draw.text((pop_x1 + 88, cy), "3 seconds auto close", fill=(255, 245, 230), font=f_period, anchor="lm")

    # Close (X) button below popup
    close_x, close_y = W // 2, pop_y2 + 48
    draw.ellipse([close_x - 24, close_y - 24, close_x + 24, close_y + 24], outline=(230, 230, 230), width=3)
    draw.line([(close_x - 9, close_y - 9), (close_x + 9, close_y + 9)], fill=(230, 230, 230), width=3)
    draw.line([(close_x + 9, close_y - 9), (close_x - 9, close_y + 9)], fill=(230, 230, 230), width=3)

    out_rgb = img.convert("RGB")
    output = io.BytesIO()
    out_rgb.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
