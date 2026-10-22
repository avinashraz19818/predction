import os
import re
import json
from typing import List

# Load premium animated emoji IDs from emoji_config.json and convert to Bot API <tg-emoji emoji-id="...">
PREMIUM_EMOJIS = {
    "fire": '<tg-emoji emoji-id="5420315771991497307">🔥</tg-emoji>',
    "crown": '<tg-emoji emoji-id="6266995104687330978">👑</tg-emoji>',
    "sparkles": '<tg-emoji emoji-id="6285088169817805553">✨</tg-emoji>',
    "rocket": '<tg-emoji emoji-id="5188481279963715781">🚀</tg-emoji>',
    "money": '<tg-emoji emoji-id="6267068789146260253">💰</tg-emoji>',
    "chart": '<tg-emoji emoji-id="5431577498364158238">📊</tg-emoji>',
    "target": '<tg-emoji emoji-id="5310278924616356636">🎯</tg-emoji>',
    "trophy": '<tg-emoji emoji-id="5413566144986503832">🏆</tg-emoji>',
    "gift": '<tg-emoji emoji-id="5384578448633129482">🎁</tg-emoji>',
    "lightning": '<tg-emoji emoji-id="6267107057304868214">⚡</tg-emoji>',
    "star": '<tg-emoji emoji-id="5435957248314579621">⭐</tg-emoji>',
    "warning": '<tg-emoji emoji-id="6267039884016358504">⚠️</tg-emoji>',
    "check": '<tg-emoji emoji-id="6267008582294705964">✅</tg-emoji>',
    "cross": '<tg-emoji emoji-id="5343968063970632884">❌</tg-emoji>',
    "clock": '<tg-emoji emoji-id="5386415655253730366">⏰</tg-emoji>',
    "link": '<tg-emoji emoji-id="4958689671950369798">🔗</tg-emoji>',
    "reload": '<tg-emoji emoji-id="5264727218734524899">🔄</tg-emoji>',
    "party": '<tg-emoji emoji-id="5436040291507247633">🎉</tg-emoji>',
    "star2": '<tg-emoji emoji-id="5458799228719472718">🌟</tg-emoji>'
}

def _load_emoji_config():
    try:
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "emoji_config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_map = data.get("premium_emojis", {})
            for key, val in raw_map.items():
                m = re.search(r"<emoji id=(\d+)>(.*?)</emoji>", val)
                if m:
                    eid, fallback = m.group(1), m.group(2)
                    PREMIUM_EMOJIS[key] = f'<tg-emoji emoji-id="{eid}">{fallback}</tg-emoji>'
    except Exception:
        pass

_load_emoji_config()

def em(key: str, default: str = "") -> str:
    return PREMIUM_EMOJIS.get(key, default)

def strip_tg_emoji_tags(html_text: str) -> str:
    """Strips <tg-emoji ...> wrapper keeping inner fallback emoji if needed"""
    return re.sub(r'<tg-emoji[^>]*>(.*?)</tg-emoji>', r'\1', html_text)

def make_progress_bar(percent: int, length: int = 10) -> str:
    """Generates a sleek uniform-width progress bar"""
    filled_len = int(round(length * percent / 100))
    filled_len = max(1, min(length, filled_len))
    bar = '▰' * filled_len + '▱' * (length - filled_len)
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
    Renders the modern VIP Gold Prediction Signal Card with Telegram Premium Animated Emojis
    """
    progress = make_progress_bar(confidence, 10)
    numbers_str = ", ".join(map(str, numbers))
    
    crown = em("crown", "👑")
    target = em("target", "🎯")
    chart = em("chart", "📊")
    sparkles = em("sparkles", "✨")
    fire = em("fire", "🔥")
    star = em("star", "⭐")
    lightning = em("lightning", "⚡")
    money = em("money", "💰")

    choice_badge = f"🟥 𝗕𝗜𝗚𝗚𝗚 (5-9) {fire}" if choice == "BIG" else f"🟩 𝗦𝗠𝗔𝗟𝗟 (0-4) {sparkles}"
    
    promo_clean = promo_text.replace("🔥", fire) if promo_text else f"{fire} Maintain 3-5 Level Fund for 100% Daily Profit!"

    msg = f"""{crown} <b>𝗩𝗜𝗣 {game_name.upper()} 𝗦𝗜𝗚𝗡𝗔𝗟</b> {crown}
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code>
{chart} <b>𝗣𝗿𝗲𝗱𝗶𝗰𝘁𝗶𝗼𝗻:</b> <b>{choice_badge}</b>
{star} <b>𝗟𝘂𝗰𝗸𝘆 𝗡𝘂𝗺𝗯𝗲𝗿𝘀:</b> <code>[ {numbers_str} ]</code>
{fire} <b>𝗖𝗼𝗻𝗳𝗶𝗱𝗲𝗻𝗰𝗲:</b> <code>[{progress}] {confidence}%</code>
🛡️ <b>𝗦𝗮𝗳𝗲 𝗟𝗲𝘃𝗲𝗹:</b> <b>𝗟𝗲𝘃𝗲𝗹 {level} (Safe Martingale)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{lightning} <i>Pattern: {pattern_name}</i>
{money} <i>{promo_clean}</i>"""
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
    Celebration WIN Card with Telegram Premium Animated Emojis
    """
    party = em("party", "🎉")
    fire = em("fire", "🔥")
    target = em("target", "🎯")
    check = em("check", "✅")
    trophy = em("trophy", "🏆")
    sparkles = em("sparkles", "✨")
    rocket = em("rocket", "🚀")

    lucky_badge = f"\n{sparkles} <b>𝗕𝗢𝗡𝗨𝗦: Lucky Number {actual_number} Direct HIT! {target}</b>" if hit_lucky_number else ""
    fire_streak = fire * min(5, max(1, streak))
    
    msg = f"""{party} <b>𝗪𝗜𝗡 𝗖𝗢𝗡𝗙𝗜𝗥𝗠𝗘𝗗! 𝗣𝗔𝗦𝗦𝗘𝗗</b> {fire_streak}
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code>
{check} <b>𝗥𝗲𝘀𝘂𝗹𝘁:</b> <b>{actual_choice} (Number: {actual_number})</b>
{trophy} <b>𝗦𝘁𝗮𝘁𝘂𝘀:</b> <b>𝗪𝗜𝗡 𝗔𝗧 𝗟𝗘𝗩𝗘𝗟 {level}!</b>
{fire} <b>𝗪𝗶𝗻 𝗦𝘁𝗿𝗲𝗮𝗸:</b> <b>{streak}x 𝗖𝗼𝗻𝘀𝗲𝗰𝘂𝘁𝗶𝘃𝗲 𝗪𝗶𝗻𝘀</b>{lucky_badge}
━━━━━━━━━━━━━━━━━━━━━━━━━
{rocket} <i>Next round signal starting in a few seconds! Keep profits safe!</i>"""
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
    Level increment card for Martingale recovery with Premium Animated Emojis
    """
    warning = em("warning", "⚠️")
    target = em("target", "🎯")
    reload_em = em("reload", "🔄")
    lightning = em("lightning", "⚡")

    msg = f"""{warning} <b>𝗟𝗘𝗩𝗘𝗟 {curr_level} 𝗠𝗜𝗦𝗦𝗘𝗗!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code> (Result: {actual_number} - {actual_choice})
{reload_em} <b>𝗡𝗲𝘅𝘁 𝗔𝗰𝘁𝗶𝗼𝗻:</b> <b>𝗠𝗼𝘃𝗲 𝘁𝗼 𝗟𝗲𝘃𝗲𝗹 {next_level}</b>
{lightning} <i>Follow 3x Martingale to recover all investment with profit!</i>
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <i>Next prediction incoming immediately...</i>"""
    return msg
