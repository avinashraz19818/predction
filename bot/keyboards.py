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
            keyboard.append([InlineKeyboardButton(text=text, url=url)])

    if not keyboard:
        return None

    return InlineKeyboardMarkup(keyboard)

def get_admin_main_keyboard(
    operating_mode: str = "24_7",
    browser_ready: bool = False,
    base_bet: int = 10,
    martingale_mult: int = 2,
    max_loss_cards: int = 3,
    auto_clean_loss: bool = True
) -> InlineKeyboardMarkup:
    """Admin Dashboard Main Menu with Mode, Bet Amount, Loss Protection, Sessions & Templates"""
    mode_text = "⚡ Mode: 24/7" if operating_mode == "24_7" else "🕒 Mode: Sessions"
    browser_badge = "🟢 Browser Live" if browser_ready else "⚪ Browser Idle"
    clean_badge = "🧹 Clean Loss: ON" if auto_clean_loss else "🧹 Clean Loss: OFF"

    keyboard = [
        [
            InlineKeyboardButton(mode_text, callback_data="admin_toggle_mode"),
            InlineKeyboardButton("🕒 VIP Sessions", callback_data="admin_sessions")
        ],
        [
            InlineKeyboardButton(f"💰 Base Bet: ₹{base_bet}", callback_data="admin_set_bet"),
            InlineKeyboardButton(f"🛡️ Martingale: {martingale_mult}X", callback_data="admin_toggle_martingale")
        ],
        [
            InlineKeyboardButton(f"🚫 Max Loss Alerts: {max_loss_cards}", callback_data="admin_toggle_max_loss"),
            InlineKeyboardButton(clean_badge, callback_data="admin_toggle_clean_loss")
        ],
        [
            InlineKeyboardButton("📝 Edit ALL Message Templates", callback_data="admin_templates"),
            InlineKeyboardButton(f"🎮 {browser_badge}", callback_data="admin_browser_status")
        ],
        [
            InlineKeyboardButton("📢 Manage Channels", callback_data="admin_channels"),
            InlineKeyboardButton("➕ Add Channel", callback_data="admin_add_channel")
        ],
        [
            InlineKeyboardButton("📊 System Stats", callback_data="admin_stats"),
            InlineKeyboardButton("📣 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("🔄 Refresh Panel", callback_data="admin_refresh")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_bet_amount_keyboard(current_amount: int) -> InlineKeyboardMarkup:
    """Quick select buttons for base bet amount"""
    keyboard = [
        [
            InlineKeyboardButton("₹1", callback_data="set_base_amt:1"),
            InlineKeyboardButton("₹5", callback_data="set_base_amt:5"),
            InlineKeyboardButton("₹10", callback_data="set_base_amt:10")
        ],
        [
            InlineKeyboardButton("₹20", callback_data="set_base_amt:20"),
            InlineKeyboardButton("₹50", callback_data="set_base_amt:50"),
            InlineKeyboardButton("₹100", callback_data="set_base_amt:100")
        ],
        [
            InlineKeyboardButton("✏️ Enter Custom Amount", callback_data="input_custom_bet")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_templates_menu_keyboard() -> InlineKeyboardMarkup:
    """Menu to customize ALL message templates (matching maxie1min format)"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Prediction Card", callback_data="edit_tpl:prediction"),
            InlineKeyboardButton("🏆 Win Card", callback_data="edit_tpl:win")
        ],
        [
            InlineKeyboardButton("⚠️ Loss Card", callback_data="edit_tpl:loss"),
            InlineKeyboardButton("🚨 15m Pre-Alert", callback_data="edit_tpl:pre_session")
        ],
        [
            InlineKeyboardButton("🟢 Session Start", callback_data="edit_tpl:session_start"),
            InlineKeyboardButton("📊 Session Completed", callback_data="edit_tpl:session_summary")
        ],
        [
            InlineKeyboardButton("⏸️ Break Time", callback_data="edit_tpl:break"),
            InlineKeyboardButton("🌅 Good Morning", callback_data="edit_tpl:good_morning")
        ],
        [
            InlineKeyboardButton("🌙 Good Night", callback_data="edit_tpl:good_night")
        ],
        [
            InlineKeyboardButton("🔄 Reset All Templates to Default", callback_data="reset_tpl:all")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_sessions_manage_keyboard(sessions: list) -> InlineKeyboardMarkup:
    """Menu to view, edit timings, and add scheduled VIP sessions"""
    keyboard = []
    for s in sessions:
        s_id = s.get("id")
        s_name = s.get("name", f"Session {s_id}")
        start_t = s.get("start")
        end_t = s.get("end")
        rnds = s.get("max_rounds", 15)
        keyboard.append([
            InlineKeyboardButton(f"🕒 {s_name} [{start_t} - {end_t}] ({rnds} R)", callback_data=f"manage_sess:{s_id}")
        ])

    keyboard.append([
        InlineKeyboardButton("➕ Add New VIP Session", callback_data="admin_add_session"),
        InlineKeyboardButton("🔄 Reset Default Sessions", callback_data="admin_reset_sessions")
    ])
    keyboard.append([
        InlineKeyboardButton("⚙️ Switch to 24/7 Mode", callback_data="set_mode:24_7"),
        InlineKeyboardButton("⚙️ Switch to Session Mode", callback_data="set_mode:scheduled")
    ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_main")
    ])
    return InlineKeyboardMarkup(keyboard)

def get_single_session_keyboard(session_id: int) -> InlineKeyboardMarkup:
    """Controls for a single session"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Edit Timing (Start - End)", callback_data=f"edit_sess_time:{session_id}")
        ],
        [
            InlineKeyboardButton("🏷️ Edit Session Name", callback_data=f"edit_sess_name:{session_id}"),
            InlineKeyboardButton("🎯 Edit Max Rounds", callback_data=f"edit_sess_rnds:{session_id}")
        ],
        [
            InlineKeyboardButton("🗑️ Delete This Session", callback_data=f"del_sess:{session_id}")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Sessions", callback_data="admin_sessions")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_browser_status_keyboard() -> InlineKeyboardMarkup:
    """Menu to inspect browser state and run manual test bet/screenshot"""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Test Bet & Capture Screenshot", callback_data="browser_test_action")
        ],
        [
            InlineKeyboardButton("🔄 Reconnect Browser", callback_data="browser_reconnect")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_main")
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
