import os
import re
import json
from typing import List, Optional

# Load premium animated emoji IDs from emoji_config.json and convert to Bot API <tg-emoji emoji-id="...">
DEFAULT_PREDICTION_TEMPLATE = """{crown} <b>𝗩𝗜𝗣 {game_name} 𝗦𝗜𝗚𝗡𝗔𝗟</b> {crown}
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue}</code>
{chart} <b>𝗣𝗿𝗲𝗱𝗶𝗰𝘁𝗶𝗼𝗻:</b> <b>{prediction}</b>
{fire} <b>𝗖𝗼𝗻𝗳𝗶𝗱𝗲𝗻𝗰𝗲:</b> <code>[{progress}] {confidence}%</code>
🛡️ <b>𝗦𝗮𝗳𝗲 𝗟𝗲𝘃𝗲𝗹:</b> <b>𝗟𝗲𝘃𝗲𝗹 {level} (Safe Martingale)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{lightning} <i>Pattern: {pattern}</i>
{money} <i>{promo}</i>"""

DEFAULT_WIN_TEMPLATE = """{party} <b>𝗪𝗜𝗡 𝗖𝗢𝗡𝗙𝗜𝗥𝗠𝗘𝗗! 𝗣𝗔𝗦𝗦𝗘𝗗</b> {fire}
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue}</code>
{check} <b>𝗥𝗲𝘀𝘂𝗹𝘁:</b> <b>{result} (Number: {number})</b>
{trophy} <b>𝗦𝘁𝗮𝘁𝘂𝘀:</b> <b>𝗪𝗜𝗡 𝗔𝗧 𝗟𝗘𝗩𝗘𝗟 {level}!</b>
{fire} <b>𝗪𝗶𝗻 𝗦𝘁𝗿𝗲𝗮𝗸:</b> <b>{streak}x 𝗖𝗼𝗻𝘀𝗲𝗰𝘂𝘁𝗶𝘃𝗲 𝗪𝗶𝗻𝘀</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{rocket} <i>Next round signal starting in a few seconds! Keep profits safe!</i>"""

DEFAULT_LOSS_TEMPLATE = """{warning} <b>𝗟𝗘𝗩𝗘𝗟 {curr_level} 𝗠𝗜𝗦𝗦𝗘𝗗!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue}</code> (Result: {number} - {result})
{reload} <b>𝗡𝗲𝘅𝘁 𝗔𝗰𝘁𝗶𝗼𝗻:</b> <b>𝗠𝗼𝘃𝗲 𝘁𝗼 𝗟𝗲𝘃𝗲𝗹 {next_level}</b>
{lightning} <i>Follow Martingale to recover all investment with profit!</i>
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <i>Next prediction incoming immediately...</i>"""

DEFAULT_PRE_SESSION_TEMPLATE = """{warning} <b>𝗩𝗜𝗣 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 𝗔𝗟𝗘𝗥𝗧</b> {warning}
━━━━━━━━━━━━━━━━━━━━━━━━━
{clock} <b>𝗦𝗲𝘀𝘀𝗶𝗼𝗻:</b> <b>{session_name}</b>
{target} <b>𝗦𝘁𝗮𝗿𝘁 𝗧𝗶𝗺𝗲:</b> <code>{start_time} IST</code> <b>(In 15 Minutes!)</b>
🎮 <b>𝗚𝗮𝗺𝗲 𝗠𝗼𝗱𝗲:</b> <code>{game_name}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ <b>𝗙𝘂𝗻𝗱 𝗠𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝘁 𝗥𝘂𝗹𝗲:</b>
{fire} <i>{promo}</i>
{money} <i>Recharge your wallet beforehand to avoid missing profitable rounds!</i>
━━━━━━━━━━━━━━━━━━━━━━━━━
{lightning} <i>Live signals will begin automatically right on time. Get ready!</i>"""

DEFAULT_SESSION_START_TEMPLATE = """{reload} <b>𝐍𝐄𝐖 𝐒𝐄𝐒𝐒𝐈𝐎𝐍 𝐒𝐓𝐀𝐑𝐓𝐄𝐃</b> {reload}
━━━━━━━━━━━━━━━━━━━━━━━━━
{crown} <b>𝐁𝐃𝐆 𝐖𝐈𝐍 𝐖𝐈𝐍𝐆𝐎 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋</b> {crown}
   ——————————————
        {sparkles} <b>{game_name}</b> {sparkles}
    —————————————
      {check} <b>𝐒𝐄𝐒𝐒𝐈𝐎𝐍:</b> <code>{session_name}</code>
    —————————————
{clock} <b>Timing:</b> <code>Until {end_time} IST</code>
{target} <b>Target Rounds:</b> <code>{max_rounds} Signals</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
{rocket} <i>Session Started! Ultra-accurate predictions incoming...</i>"""

DEFAULT_SESSION_SUMMARY_TEMPLATE = """{trophy} <b>𝐒𝐄𝐒𝐒𝐈𝐎𝐍 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃</b> {trophy}
━━━━━━━━━━━━━━━━━━━━━━━━━
{crown} <b>{session_name}</b> {crown}
━━━━━━━━━━━━━━━━━━━━━━━━━
{chart} <b>Total Predictions:</b> <code>{total_rounds}</code>
{check} <b>Wins:</b> <code>{wins}</code>
{cross} <b>Losses:</b> <code>{losses}</code>
🎯 <b>Win Rate:</b> <b>{win_rate}%</b>
{fire} <b>Best Streak:</b> <b>{max_streak}x Consecutive</b>
🛡️ <b>Max Level Used:</b> <b>Level {max_level_used}</b>
{money} <b>Estimated Profit:</b> <b>+₹{profit}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{clock} <b>Next Session:</b> <code>{next_session}</code>
🌟 <i>Congratulations to all VIP members who played this session!</i>"""

DEFAULT_BREAK_TEMPLATE = """{break_icon} <b>𝐁𝐑𝐄𝐀𝐊 𝐓𝐈𝐌𝐄</b> {break_icon}
━━━━━━━━━━━━━━━━━━━━━━━━━
🌀 <b>{duration_mins} Minutes Break</b>
{clock} <b>Next Session:</b> <code>{next_session}</code>

{sleep} <i>Taking a short break...</i>
{reload} <i>Back with even smarter predictions!</i>

Don't miss this opportunity!
{target} <i>Next session starts soon...</i>"""

DEFAULT_GOOD_MORNING_TEMPLATE = """{sun} <b>𝐆𝐎𝐎𝐃 𝐌𝐎𝐑𝐍𝐈𝐍𝐆 𝐖𝐈𝐍𝐍𝐄𝐑𝐒!</b> {sun}
━━━━━━━━━━━━━━━━━━━━━━━━━
{sparkles} <i>A new day of winning begins!</i>
{lightning} <i>VIP Predictions starting today!</i>
{money} <i>Let's make today profitable!</i>

{coffee} <i>Have your coffee ready...</i>
{rocket} <i>Ultra-smart WinGo signals starting soon!</i>"""

DEFAULT_GOOD_NIGHT_TEMPLATE = """{moon} <b>𝐆𝐎𝐎𝐃 𝐍𝐈𝐆𝐇𝐓 𝐖𝐈𝐍𝐍𝐄𝐑𝐒!</b> {moon}
━━━━━━━━━━━━━━━━━━━━━━━━━
{sleep} <i>VIP Prediction sessions concluded for today!</i>
{chart} <b>Today's Record:</b> <code>{wins} Wins / {losses} Losses ({win_rate}% Win Rate)</code>

{moon} <i>Sweet dreams winners!</i>
{reload} <i>See you tomorrow for more massive wins!</i>"""

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
    "star2": '<tg-emoji emoji-id="5458799228719472718">🌟</tg-emoji>',
    "moon": '<tg-emoji emoji-id="5208554136039073738">🌙</tg-emoji>',
    "sun": '<tg-emoji emoji-id="5413883478645169306>🌅</tg-emoji>',
    "coffee": '<tg-emoji emoji-id="5451959871257713464>☕</tg-emoji>',
    "sleep": '<tg-emoji emoji-id="5359543311897998264>💤</tg-emoji>',
    "break_icon": '<tg-emoji emoji-id="5359543311897998264">⏸️</tg-emoji>'
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
    promo_text: str = "",
    custom_template: Optional[str] = None
) -> str:
    """
    Renders prediction signal card.
    Lucky numbers removed per user request: only shows choice (BIG 5-9 or SMALL 0-4).
    Supports custom template from admin panel.
    """
    progress = make_progress_bar(confidence, 10)
    
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

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{game_name}": game_name,
            "{issue}": str(issue_number),
            "{prediction}": choice_badge,
            "{choice}": choice,
            "{confidence}": str(confidence),
            "{progress}": progress,
            "{level}": str(level),
            "{pattern}": pattern_name,
            "{promo}": promo_clean,
            "{crown}": crown,
            "{target}": target,
            "{chart}": chart,
            "{fire}": fire,
            "{sparkles}": sparkles,
            "{money}": money,
            "{lightning}": lightning
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    # Default clean template without redundant lucky numbers row
    msg = f"""{crown} <b>𝗩𝗜𝗣 {game_name.upper()} 𝗦𝗜𝗚𝗡𝗔𝗟</b> {crown}
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code>
{chart} <b>𝗣𝗿𝗲𝗱𝗶𝗰𝘁𝗶𝗼𝗻:</b> <b>{choice_badge}</b>
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
    hit_lucky_number: bool = False,
    custom_template: Optional[str] = None
) -> str:
    """
    Celebration WIN Card with Telegram Premium Animated Emojis.
    Supports admin custom template.
    """
    party = em("party", "🎉")
    fire = em("fire", "🔥")
    target = em("target", "🎯")
    check = em("check", "✅")
    trophy = em("trophy", "🏆")
    sparkles = em("sparkles", "✨")
    rocket = em("rocket", "🚀")

    fire_streak = fire * min(5, max(1, streak))

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{game_name}": game_name,
            "{issue}": str(issue_number),
            "{result}": actual_choice,
            "{number}": str(actual_number),
            "{level}": str(level),
            "{streak}": str(streak),
            "{fire}": fire,
            "{trophy}": trophy,
            "{check}": check,
            "{party}": party,
            "{rocket}": rocket
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    msg = f"""{party} <b>𝗪𝗜𝗡 𝗖𝗢𝗡𝗙𝗜𝗥𝗠𝗘𝗗! 𝗣𝗔𝗦𝗦𝗘𝗗</b> {fire_streak}
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code>
{check} <b>𝗥𝗲𝘀𝘂𝗹𝘁:</b> <b>{actual_choice} (Number: {actual_number})</b>
{trophy} <b>𝗦𝘁𝗮𝘁𝘂𝘀:</b> <b>𝗪𝗜𝗡 𝗔𝗧 𝗟𝗘𝗩𝗘𝗟 {level}!</b>
{fire} <b>𝗪𝗶𝗻 𝗦𝘁𝗿𝗲𝗮𝗸:</b> <b>{streak}x 𝗖𝗼𝗻𝘀𝗲𝗰𝘂𝘁𝗶𝘃𝗲 𝗪𝗶𝗻𝘀</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{rocket} <i>Next round signal starting in a few seconds! Keep profits safe!</i>"""
    return msg

def render_loss_card(
    game_name: str,
    issue_number: str,
    actual_choice: str,
    actual_number: int,
    curr_level: int,
    next_level: int,
    custom_template: Optional[str] = None
) -> str:
    """
    Level increment card for Martingale recovery with Premium Animated Emojis.
    Supports admin custom template.
    """
    warning = em("warning", "⚠️")
    target = em("target", "🎯")
    reload_em = em("reload", "🔄")
    lightning = em("lightning", "⚡")

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{game_name}": game_name,
            "{issue}": str(issue_number),
            "{result}": actual_choice,
            "{number}": str(actual_number),
            "{curr_level}": str(curr_level),
            "{next_level}": str(next_level),
            "{warning}": warning,
            "{target}": target,
            "{reload}": reload_em,
            "{lightning}": lightning
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    msg = f"""{warning} <b>𝗟𝗘𝗩𝗘𝗟 {curr_level} 𝗠𝗜𝗦𝗦𝗘𝗗!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <b>𝗣𝗲𝗿𝗶𝗼𝗱:</b> <code>{issue_number}</code> (Result: {actual_number} - {actual_choice})
{reload_em} <b>𝗡𝗲𝘅𝘁 𝗔𝗰𝘁𝗶𝗼𝗻:</b> <b>𝗠𝗼𝘃𝗲 𝘁𝗼 𝗟𝗲𝘃𝗲𝗹 {next_level}</b>
{lightning} <i>Follow Martingale to recover all investment with profit!</i>
━━━━━━━━━━━━━━━━━━━━━━━━━
{target} <i>Next prediction incoming immediately...</i>"""
    return msg

def render_pre_session_alert_card(
    session_name: str,
    start_time: str,
    game_name: str = "WinGo 1 Minute",
    promo_text: str = "",
    custom_template: Optional[str] = None
) -> str:
    warning = em("warning", "🚨")
    clock = em("clock", "⏰")
    target = em("target", "🎯")
    money = em("money", "💰")
    fire = em("fire", "🔥")
    lightning = em("lightning", "⚡")

    promo_clean = promo_text or "Maintain 5 to 6 Levels Balance for 100% Guaranteed Profit!"

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{session_name}": session_name,
            "{start_time}": start_time,
            "{game_name}": game_name,
            "{promo}": promo_clean,
            "{warning}": warning,
            "{clock}": clock,
            "{target}": target,
            "{money}": money,
            "{fire}": fire,
            "{lightning}": lightning
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    msg = f"""{warning} <b>𝗩𝗜𝗣 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 𝗔𝗟𝗘𝗥𝗧</b> {warning}
━━━━━━━━━━━━━━━━━━━━━━━━━
{clock} <b>𝗦𝗲𝘀𝘀𝗶𝗼𝗻:</b> <b>{session_name}</b>
{target} <b>𝗦𝘁𝗮𝗿𝘁 𝗧𝗶𝗺𝗲:</b> <code>{start_time} IST</code> <b>(In 15 Minutes!)</b>
🎮 <b>𝗚𝗮𝗺𝗲 𝗠𝗼𝗱𝗲:</b> <code>{game_name}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️ <b>𝗙𝘂𝗻𝗱 𝗠𝗮𝗻𝗮𝗴𝗲𝗺𝗲𝗻𝘁 𝗥𝘂𝗹𝗲:</b>
{fire} <i>{promo_clean}</i>
{money} <i>Recharge your wallet beforehand to avoid missing profitable rounds!</i>
━━━━━━━━━━━━━━━━━━━━━━━━━
{lightning} <i>Live signals will begin automatically right on time. Get ready!</i>"""
    return msg

def render_session_start_card(
    session_name: str,
    end_time: str,
    max_rounds: int = 15,
    game_name: str = "WinGo 1 Minute",
    custom_template: Optional[str] = None
) -> str:
    crown = em("crown", "👑")
    rocket = em("rocket", "🚀")
    clock = em("clock", "⏰")
    target = em("target", "🎯")
    fire = em("fire", "🔥")

    reload_em = em("reload", "🔄")
    sparkles = em("sparkles", "✨")
    check = em("check", "✅")

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{session_name}": session_name,
            "{end_time}": end_time,
            "{max_rounds}": str(max_rounds),
            "{game_name}": game_name,
            "{crown}": crown,
            "{rocket}": rocket,
            "{clock}": clock,
            "{target}": target,
            "{fire}": fire,
            "{reload}": reload_em,
            "{sparkles}": sparkles,
            "{check}": check
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    msg = f"""{reload_em} <b>𝐍𝐄𝐖 𝐒𝐄𝐒𝐒𝐈𝐎𝐍 𝐒𝐓𝐀𝐑𝐓𝐄𝐃</b> {reload_em}
━━━━━━━━━━━━━━━━━━━━━━━━━
{crown} <b>𝐁𝐃𝐆 𝐖𝐈𝐍 𝐖𝐈𝐍𝐆𝐎 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋</b> {crown}
   ——————————————
        {sparkles} <b>{game_name.upper()}</b> {sparkles}
    —————————————
      {check} <b>𝐒𝐄𝐒𝐒𝐈𝐎𝐍:</b> <code>{session_name}</code>
    —————————————
{clock} <b>Timing:</b> <code>Until {end_time} IST</code>
{target} <b>Target Rounds:</b> <code>{max_rounds} Signals</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
{rocket} <i>Session Started! Ultra-accurate predictions incoming...</i>"""
    return msg

def render_session_summary_card(
    session_name: str,
    total_rounds: int,
    wins: int,
    losses: int,
    max_streak: int,
    max_level_used: int,
    profit_inr: float,
    next_session_text: str = "Tomorrow at 11:00 AM",
    custom_template: Optional[str] = None
) -> str:
    trophy = em("trophy", "🏆")
    party = em("party", "🎉")
    chart = em("chart", "📊")
    check = em("check", "✅")
    cross = em("cross", "❌")
    fire = em("fire", "🔥")
    money = em("money", "💰")
    clock = em("clock", "⏰")

    crown = em("crown", "👑")

    win_rate = (wins / total_rounds * 100) if total_rounds > 0 else 0.0

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{session_name}": session_name,
            "{total_rounds}": str(total_rounds),
            "{wins}": str(wins),
            "{losses}": str(losses),
            "{win_rate}": f"{win_rate:.1f}",
            "{max_streak}": str(max_streak),
            "{max_level_used}": str(max_level_used),
            "{profit}": f"{profit_inr:,.2f}",
            "{next_session}": next_session_text,
            "{trophy}": trophy,
            "{crown}": crown,
            "{party}": party,
            "{chart}": chart,
            "{check}": check,
            "{cross}": cross,
            "{fire}": fire,
            "{money}": money,
            "{clock}": clock
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    msg = f"""{trophy} <b>𝐒𝐄𝐒𝐒𝐈𝐎𝐍 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃</b> {trophy}
━━━━━━━━━━━━━━━━━━━━━━━━━
{crown} <b>{session_name}</b> {crown}
━━━━━━━━━━━━━━━━━━━━━━━━━
{chart} <b>Total Predictions:</b> <code>{total_rounds}</code>
{check} <b>Wins:</b> <code>{wins}</code>
{cross} <b>Losses:</b> <code>{losses}</code>
🎯 <b>Win Rate:</b> <b>{win_rate:.1f}%</b>
{fire} <b>Best Streak:</b> <b>{max_streak}x Consecutive</b>
🛡️ <b>Max Level Used:</b> <b>Level {max_level_used}</b>
{money} <b>Estimated Profit:</b> <b>+₹{profit_inr:,.2f}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{clock} <b>Next Session:</b> <code>{next_session_text}</code>
🌟 <i>Congratulations to all VIP members who played this session!</i>"""
    return msg

def render_break_card(
    next_session_text: str,
    duration_mins: int = 15,
    custom_template: Optional[str] = None
) -> str:
    break_icon = em("break_icon", "⏸️")
    clock = em("clock", "⏰")
    sleep = em("sleep", "💤")
    reload_em = em("reload", "🔄")
    target = em("target", "🎯")

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{break_icon}": break_icon,
            "{duration_mins}": str(duration_mins),
            "{next_session}": next_session_text,
            "{clock}": clock,
            "{sleep}": sleep,
            "{reload}": reload_em,
            "{target}": target
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    return f"""{break_icon} <b>𝐁𝐑𝐄𝐀𝐊 𝐓𝐈𝐌𝐄</b> {break_icon}
━━━━━━━━━━━━━━━━━━━━━━━━━
🌀 <b>{duration_mins} Minutes Break</b>
{clock} <b>Next Session:</b> <code>{next_session_text}</code>

{sleep} <i>Taking a short break...</i>
{reload_em} <i>Back with even smarter predictions!</i>

Don't miss this opportunity!
{target} <i>Next session starts soon...</i>"""

def render_good_morning_card(custom_template: Optional[str] = None) -> str:
    sun = em("sun", "🌅")
    sparkles = em("sparkles", "✨")
    lightning = em("lightning", "⚡")
    money = em("money", "💰")
    coffee = em("coffee", "☕")
    rocket = em("rocket", "🚀")

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{sun}": sun,
            "{sparkles}": sparkles,
            "{lightning}": lightning,
            "{money}": money,
            "{coffee}": coffee,
            "{rocket}": rocket
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    return f"""{sun} <b>𝐆𝐎𝐎𝐃 𝐌𝐎𝐑𝐍𝐈𝐍𝐆 𝐖𝐈𝐍𝐍𝐄𝐑𝐒!</b> {sun}
━━━━━━━━━━━━━━━━━━━━━━━━━
{sparkles} <i>A new day of winning begins!</i>
{lightning} <i>VIP Predictions starting today!</i>
{money} <i>Let's make today profitable!</i>

{coffee} <i>Have your coffee ready...</i>
{rocket} <i>Ultra-smart WinGo signals starting soon!</i>"""

def render_good_night_card(
    wins: int = 0,
    losses: int = 0,
    custom_template: Optional[str] = None
) -> str:
    moon = em("moon", "🌙")
    sleep = em("sleep", "💤")
    chart = em("chart", "📊")
    reload_em = em("reload", "🔄")

    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0.0

    if custom_template and custom_template.strip():
        txt = custom_template
        replacements = {
            "{moon}": moon,
            "{sleep}": sleep,
            "{chart}": chart,
            "{reload}": reload_em,
            "{wins}": str(wins),
            "{losses}": str(losses),
            "{win_rate}": f"{win_rate:.1f}"
        }
        for k, v in replacements.items():
            txt = txt.replace(k, v)
        return txt

    return f"""{moon} <b>𝐆𝐎𝐎𝐃 𝐍𝐈𝐆𝐇𝐓 𝐖𝐈𝐍𝐍𝐄𝐑𝐒!</b> {moon}
━━━━━━━━━━━━━━━━━━━━━━━━━
{sleep} <i>VIP Prediction sessions concluded for today!</i>
{chart} <b>Today's Record:</b> <code>{wins} Wins / {losses} Losses ({win_rate:.1f}% Win Rate)</code>

{moon} <i>Sweet dreams winners!</i>
{reload_em} <i>See you tomorrow for more massive wins!</i>"""
