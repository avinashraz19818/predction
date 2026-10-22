from typing import List

def make_progress_bar(percent: int, length: int = 8) -> str:
    """Generates a stylish progress bar like [████████░░]"""
    filled_len = int(round(length * percent / 100))
    bar = '█' * filled_len + '░' * (length - filled_len)
    return bar

def render_prediction_card(
    game_name: str,
    issue_number: str,
    choice: str,
    numbers: List[int],
    confidence: int,
    level: int,
    pattern_name: str = "Trend Momentum",
    promo_text: str = ""
) -> str:
    """
    Renders the modern Cyberpunk / VIP Gold Prediction Signal Card
    """
    progress = make_progress_bar(confidence, 8)
    numbers_str = ", ".join(map(str, numbers))
    
    choice_badge = "🟥 BIGGG (5-9)" if choice == "BIG" else "🟩 SMALL (0-4)"
    
    msg = f"""👑 <b>𝗩𝗜𝗣 {game_name.upper()} 𝗦𝗜𝗚𝗡𝗔𝗟</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code>
📊 <b>𝗣𝗿𝗲𝗱𝗶𝗰𝘁𝗶𝗼𝗻:</b> <b>{choice_badge}</b>
🎲 <b>𝗟𝘂𝗰𝗸𝘆 𝗡𝘂𝗺𝗯𝗲𝗿𝘀:</b> <b>[ {numbers_str} ]</b>
🔥 <b>𝗖𝗼𝗻𝗳𝗶𝗱𝗲𝗻𝗰𝗲:</b> <b>[{progress}] {confidence}%</b>
🛡️ <b>𝗦𝗮𝗳𝗲 𝗟𝗲𝘃𝗲𝗹:</b> <b>𝗟𝗲𝘃𝗲𝗹 {level} (Safe Martingale)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ <i>Pattern: {pattern_name}</i>
💰 <i>{promo_text}</i>"""
    return msg

def render_win_card(
    game_name: str,
    issue_number: str,
    actual_choice: str,
    actual_number: int,
    level: int,
    streak: int,
    hit_lucky_number: bool = False
) -> str:
    """
    Celebration WIN Card posted as an individual message immediately after winning!
    """
    lucky_badge = f"\n💎 <b>𝗕𝗢𝗡𝗨𝗦: Lucky Number {actual_number} Direct HIT! 🎯</b>" if hit_lucky_number else ""
    fire_streak = "🔥" * min(5, max(1, streak))
    
    msg = f"""🎉 <b>𝗪𝗜𝗡 𝗖𝗢𝗡𝗙𝗜𝗥𝗠𝗘𝗗! 𝗣𝗔𝗦𝗦𝗘𝗗 {fire_streak}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code>
✅ <b>𝗥𝗲𝘀𝘂𝗹𝘁:</b> <b>{actual_choice} (Number: {actual_number})</b>
🏆 <b>𝗦𝘁𝗮𝘁𝘂𝘀:</b> <b>𝗪𝗜𝗡 𝗔𝗧 𝗟𝗘𝗩𝗘𝗟 {level}!</b>
🔥 <b>𝗪𝗶𝗻 𝗦𝘁𝗿𝗲𝗮𝗸:</b> <b>{streak}x 𝗖𝗼𝗻𝘀𝗲𝗰𝘂𝘁𝗶𝘃𝗲 𝗪𝗶𝗻𝘀</b>{lucky_badge}
━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 <i>Next round signal starting in a few seconds! Keep profits safe!</i>"""
    return msg

def render_loss_card(
    game_name: str,
    issue_number: str,
    actual_choice: str,
    actual_number: int,
    curr_level: int,
    next_level: int
) -> str:
    """
    Level increment card for Martingale recovery
    """
    msg = f"""⚠️ <b>𝗟𝗘𝗩𝗘𝗟 {curr_level} 𝗠𝗜𝗦𝗦𝗘𝗗!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code> (Result: {actual_number} - {actual_choice})
🛡️ <b>𝗡𝗲𝘅𝘁 𝗔𝗰𝘁𝗶𝗼𝗻:</b> <b>𝗠𝗼𝘃𝗲 𝘁𝗼 𝗟𝗲𝘃𝗲𝗹 {next_level}</b>
⚡ <i>Follow 3x Martingale to recover all investment with profit!</i>
━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <i>Next prediction incoming immediately...</i>"""
    return msg
