from typing import Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config

def get_channel_post_keyboard(channel: dict = None, include_custom_emoji: bool = True, include_style: bool = True) -> Optional[InlineKeyboardMarkup]:
    """
    Builds inline keyboard for channel posts ONLY from buttons explicitly configured by the admin.
    If no buttons are configured for the channel, returns None (no buttons attached).
    Supports Telegram Bot API native colored button styles: 'success' (green), 'danger' (red), 'primary' (blue).
    """
    if not channel:
        return None

    buttons_cfg = channel.get("buttons", [])
    if not buttons_cfg:
        return None

    keyboard = []
    for btn in buttons_cfg:
        text = btn.get("text", "").strip()
        url = btn.get("url", "").strip()
        if not text or not url:
            continue

        style = btn.get("style") if include_style else None
        if style not in ("success", "danger", "primary"):
            style = None

        emoji_id = btn.get("icon_custom_emoji_id") if include_custom_emoji else None

        try:
            button_kwargs = {"text": text, "url": url}
            if style:
                button_kwargs["style"] = style
            if emoji_id:
                button_kwargs["icon_custom_emoji_id"] = str(emoji_id)
            keyboard.append([InlineKeyboardButton(**button_kwargs)])
        except TypeError:
            # Fallback if older PTB version is installed
            keyboard.append([InlineKeyboardButton(text=text, url=url)])

    if not keyboard:
        return None

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

def get_channel_manage_keyboard(channel_id: str, is_active: bool, game_id: str, buttons_count: int = 0) -> InlineKeyboardMarkup:
    """Individual Channel Settings Menu"""
    toggle_text = "⏸️ Pause Predictions" if is_active else "▶️ Start Predictions"
    toggle_data = f"toggle_ch:{channel_id}"
    
    game_name = config.WINGO_GAMES.get(game_id, {}).get("name", game_id)
    btn_label = f"🔘 Manage Buttons ({buttons_count} Active)" if buttons_count > 0 else "🔘 Add / Set Channel Buttons (None)"
    
    keyboard = [
        [
            InlineKeyboardButton(toggle_text, callback_data=toggle_data)
        ],
        [
            InlineKeyboardButton(f"⏱️ Game: {game_name} (Change)", callback_data=f"change_game:{channel_id}")
        ],
        [
            InlineKeyboardButton(btn_label, callback_data=f"manage_btns:{channel_id}")
        ],
        [
            InlineKeyboardButton("🔄 Reset Level to 1", callback_data=f"reset_level:{channel_id}"),
            InlineKeyboardButton("🗑️ Remove Channel", callback_data=f"delete_ch:{channel_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Channels", callback_data="admin_channels")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_channel_buttons_keyboard(channel_id: str, buttons: list) -> InlineKeyboardMarkup:
    """Menu to view, add, or delete custom styled buttons for a channel"""
    keyboard = []
    style_badges = {
        "success": "🟢 Green",
        "danger": "🔴 Red",
        "primary": "🔵 Blue",
        None: "⚪ Default"
    }

    for idx, btn in enumerate(buttons):
        b_text = btn.get("text", "Button")
        b_style = style_badges.get(btn.get("style"), "⚪ Default")
        keyboard.append([
            InlineKeyboardButton(f"{idx+1}. {b_text} [{b_style}]", url=btn.get("url", "https://t.me")),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"del_btn:{channel_id}:{idx}")
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Add New Button", callback_data=f"add_btn:{channel_id}")
    ])
    if buttons:
        keyboard.append([
            InlineKeyboardButton("🗑️ Remove All Buttons (No Buttons)", callback_data=f"clear_btns:{channel_id}")
        ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Back to Channel Settings", callback_data=f"view_ch:{channel_id}")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_button_style_select_keyboard(channel_id: str) -> InlineKeyboardMarkup:
    """Menu to choose Telegram's native colored button style + premium emoji icon"""
    keyboard = [
        [
            InlineKeyboardButton("🟢 Green (Success Style)", callback_data=f"btnstyle:{channel_id}:success:5420315771991497307")
        ],
        [
            InlineKeyboardButton("🔴 Red (Danger Style)", callback_data=f"btnstyle:{channel_id}:danger:5188481279963715781")
        ],
        [
            InlineKeyboardButton("🔵 Blue (Primary Style)", callback_data=f"btnstyle:{channel_id}:primary:6266995104687330978")
        ],
        [
            InlineKeyboardButton("⚪ Default (Standard Style)", callback_data=f"btnstyle:{channel_id}:default:none")
        ],
        [
            InlineKeyboardButton("⬅️ Cancel", callback_data=f"manage_btns:{channel_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
