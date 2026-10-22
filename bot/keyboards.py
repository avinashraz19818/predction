from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def get_channel_post_keyboard(register_link: str = None) -> InlineKeyboardMarkup:
    """
    High-impact styled channel buttons with Success, Danger/Alert, and VIP themes
    """
    link = register_link or config.DEFAULT_REGISTER_LINK
    
    keyboard = [
        [
            InlineKeyboardButton("🟢 𝗥𝗘𝗚𝗜𝗦𝗧𝗘𝗥 & 𝗣𝗟𝗔𝗬 (𝗦𝗨𝗖𝗖𝗘𝗦𝗦) 🟢", url=link)
        ],
        [
            InlineKeyboardButton("🔴 𝗟𝗜𝗩𝗘 𝗥𝗘𝗦𝗨𝗟𝗧 𝗣𝗥𝗢𝗢𝗙 (𝗗𝗔𝗡𝗚𝗘𝗥) 🔴", url=link),
            InlineKeyboardButton("🎁 𝗖𝗟𝗔𝗜𝗠 ₹𝟱𝟬𝟬 𝗕𝗢𝗡𝗨𝗦 🎁", url=link)
        ],
        [
            InlineKeyboardButton("👑 𝗢𝗙𝗙𝗜𝗖𝗜𝗔𝗟 𝗩𝗜𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 👑", url=link)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Admin Dashboard Main Menu"""
    keyboard = [
        [
            InlineKeyboardButton("📢 Manage Channels", callback_data="admin_channels"),
            InlineKeyboardButton("➕ Add New Channel", callback_data="admin_add_channel")
        ],
        [
            InlineKeyboardButton("📊 System Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("📣 Broadcast Message", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_game_select_keyboard(channel_id: str) -> InlineKeyboardMarkup:
    """Keyboard for selecting WinGo duration when adding/editing channel"""
    keyboard = [
        [
            InlineKeyboardButton("⏱️ WinGo 30s", callback_data=f"setgame:{channel_id}:wingo_30s"),
            InlineKeyboardButton("⏱️ WinGo 1 Min", callback_data=f"setgame:{channel_id}:wingo_1m")
        ],
        [
            InlineKeyboardButton("⏱️ WinGo 3 Min", callback_data=f"setgame:{channel_id}:wingo_3m"),
            InlineKeyboardButton("⏱️ WinGo 5 Min", callback_data=f"setgame:{channel_id}:wingo_5m")
        ],
        [
            InlineKeyboardButton("⬅️ Cancel", callback_data="admin_channels")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_channel_manage_keyboard(channel_id: str, is_active: bool, game_id: str) -> InlineKeyboardMarkup:
    """Individual Channel Settings Menu"""
    toggle_text = "⏸️ Pause Predictions" if is_active else "▶️ Start Predictions"
    toggle_data = f"toggle_ch:{channel_id}"
    
    game_name = config.WINGO_GAMES.get(game_id, {}).get("name", game_id)
    
    keyboard = [
        [
            InlineKeyboardButton(toggle_text, callback_data=toggle_data)
        ],
        [
            InlineKeyboardButton(f"⏱️ Game: {game_name} (Change)", callback_data=f"change_game:{channel_id}")
        ],
        [
            InlineKeyboardButton("🔗 Change Register Link", callback_data=f"edit_link:{channel_id}"),
            InlineKeyboardButton("🔄 Reset Level to 1", callback_data=f"reset_level:{channel_id}")
        ],
        [
            InlineKeyboardButton("🗑️ Remove Channel", callback_data=f"delete_ch:{channel_id}"),
            InlineKeyboardButton("⬅️ Back to Channels", callback_data="admin_channels")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
