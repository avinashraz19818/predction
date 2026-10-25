import io
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
from database import db_manager
from services.bet_automation import bet_automation
from bot.keyboards import (
    get_admin_main_keyboard,
    get_game_select_keyboard,
    get_channel_manage_keyboard,
    get_channel_buttons_keyboard,
    get_button_style_select_keyboard,
    get_sessions_manage_keyboard,
    get_browser_status_keyboard
)

logger = logging.getLogger(__name__)

# In-memory admin state: { user_id: { "state": ..., "data": ... } }
admin_states = {}

def is_admin(user_id: int) -> bool:
    if not config.ADMIN_IDS:
        return True
    return user_id in config.ADMIN_IDS

def _get_admin_panel_text(user_first_name: str) -> str:
    cfg = db_manager.get_system_settings()
    mode = cfg.get("mode", "24_7")
    mode_str = "⚡ 24/7 Continuous (Non-Stop)" if mode == "24_7" else "🕒 Scheduled VIP Sessions (IST)"
    browser_ready = bet_automation.is_logged_in
    browser_status = "🟢 Logged In & Ready (Playwright)" if browser_ready else "⚪ Idle / Connecting..."

    return f"""👑 <b>𝗪𝗜𝗡𝗚𝗢 𝗔𝗜 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
👋 Welcome, <b>{user_first_name}</b>!
⚡ <b>Operating Mode:</b> <code>{mode_str}</code>
🎮 <b>Automation Status:</b> <code>{browser_status}</code>
🤖 <b>Engine:</b> WinGo 30s, 1M, 3M, 5M (Multi-Game)
🛡️ <b>Strategy:</b> 3-5 Level Martingale
━━━━━━━━━━━━━━━━━━━━━━━━━
Select an option from the menu below:"""

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ You are not authorized to access this bot.")
        return

    cfg = db_manager.get_system_settings()
    mode = cfg.get("mode", "24_7")
    text = _get_admin_panel_text(user.first_name)
    reply_markup = get_admin_main_keyboard(operating_mode=mode, browser_ready=bet_automation.is_logged_in)
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def _render_channel_view(query, ch_id: str):
    ch = db_manager.get_channel(ch_id)
    if not ch:
        cfg = db_manager.get_system_settings()
        await query.edit_message_text(
            "❌ Channel not found.",
            reply_markup=get_admin_main_keyboard(cfg.get("mode", "24_7"), bet_automation.is_logged_in)
        )
        return

    game_id = ch.get("game_id", "wingo_1m")
    game_label = config.WINGO_GAMES.get(game_id, {}).get("display_name", game_id)
    is_active = ch.get("is_active", True)
    status_text = "🟢 Active" if is_active else "⏸️ Paused"
    stats = ch.get("stats", {})
    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0.0
    buttons = ch.get("buttons", [])
    btn_summary = f"<code>{len(buttons)} Button(s) Set</code>" if buttons else "<code>None (No Buttons Shown)</code>"

    text = f"""📢 <b>𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀: {ch.get('title', ch_id)}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>ID:</b> <code>{ch_id}</code>
⚡ <b>Status:</b> {status_text}
⏱️ <b>Game Mode:</b> <b>{game_label}</b>
🛡️ <b>Current Level:</b> <b>Level {ch.get('current_level', 1)}</b>
📊 <b>Win Rate:</b> <b>{win_rate:.1f}%</b> ({wins}W / {losses}L)
🔥 <b>Current Streak:</b> <b>{stats.get('current_streak', 0)}W</b>
🔘 <b>Channel Buttons:</b> {btn_summary}
━━━━━━━━━━━━━━━━━━━━━━━━━"""

    reply_markup = get_channel_manage_keyboard(ch_id, is_active, game_id, len(buttons))
    await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not is_admin(user.id):
        await query.edit_message_text("⛔ Unauthorized.")
        return

    data = query.data
    cfg = db_manager.get_system_settings()

    # 1. Main Menu Refresh / Home
    if data in ["admin_main", "admin_refresh"]:
        admin_states.pop(user.id, None)
        mode = cfg.get("mode", "24_7")
        text = _get_admin_panel_text(user.first_name)
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_main_keyboard(operating_mode=mode, browser_ready=bet_automation.is_logged_in)
        )

    # 2. Toggle Operating Mode (24/7 vs Scheduled)
    elif data == "admin_toggle_mode":
        curr_mode = cfg.get("mode", "24_7")
        new_mode = "scheduled" if curr_mode == "24_7" else "24_7"
        db_manager.set_operating_mode(new_mode)
        mode_str = "Scheduled VIP Sessions" if new_mode == "scheduled" else "24/7 Continuous Mode"
        await query.answer(f"Switched to {mode_str}!", show_alert=True)
        text = _get_admin_panel_text(user.first_name)
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_main_keyboard(operating_mode=new_mode, browser_ready=bet_automation.is_logged_in)
        )

    elif data.startswith("set_mode:"):
        target_mode = data.split(":")[1]
        db_manager.set_operating_mode(target_mode)
        mode_str = "Scheduled VIP Sessions" if target_mode == "scheduled" else "24/7 Continuous Mode"
        await query.answer(f"Operating Mode set to: {mode_str}!", show_alert=True)
        text = _get_admin_panel_text(user.first_name)
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_main_keyboard(operating_mode=target_mode, browser_ready=bet_automation.is_logged_in)
        )

    # 3. View Scheduled Sessions
    elif data == "admin_sessions":
        sessions = db_manager.get_sessions()
        curr_mode = cfg.get("mode", "24_7")
        mode_label = "⚡ 24/7 Continuous" if curr_mode == "24_7" else "🕒 Scheduled VIP Sessions Active"

        lines = [
            "🕒 <b>𝗗𝗔𝗜𝗟𝗬 𝗩𝗜𝗣 𝗦𝗘𝗦𝗦𝗜𝗢𝗡 𝗧𝗜𝗠𝗜𝗡𝗚𝗦 (𝗜𝗦𝗧)</b> 🕒",
            "━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"⚡ <b>Current Mode:</b> <code>{mode_label}</code>",
            f"🔔 <b>Pre-Session Alert:</b> <code>15 Minutes Before Start</code>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
        for s in sessions:
            lines.append(f"• <b>{s.get('name', 'Session')}:</b> <code>{s.get('start')} – {s.get('end')} IST</code> (Target: {s.get('max_rounds', 15)} rounds)")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("<i>Pre-Session alerts, Live Kickoff, and Session Summary cards are sent automatically in Scheduled Mode!</i>")

        text = "\n".join(lines)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=get_sessions_manage_keyboard(sessions))

    # 4. Browser Automation Status & Test
    elif data == "admin_browser_status":
        ready = bet_automation.is_logged_in
        status_label = "🟢 Logged In & Ready (Playwright)" if ready else "⚪ Disconnected / Initializing"
        demo_user = config.DEMO_USERNAME or "N/A"
        demo_url = config.DEMO_LOGIN_URL or "N/A"

        text = f"""🎮 <b>𝗣𝗟𝗔𝗬𝗪𝗥𝗜𝗚𝗛𝗧 𝗔𝗨𝗧𝗢𝗠𝗔𝗧𝗜𝗢𝗡 𝗦𝗧𝗔𝗧𝗨𝗦</b> 🎮
━━━━━━━━━━━━━━━━━━━━━━━━━
⚡ <b>Status:</b> <code>{status_label}</code>
👤 <b>Account:</b> <code>{demo_user}</code>
🌐 <b>Game Platform:</b> <code>{demo_url}</code>
🎯 <b>Auto-Bet Mode:</b> <code>{'ENABLED' if config.DEMO_AUTO_BET else 'DISABLED'}</code>
📸 <b>Real Win Popup:</b> <code>Active Fast Detector (80ms)</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
Click below to test live bet placement and capture a screenshot:"""
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=get_browser_status_keyboard())

    # 5. Browser Test Bet & Screenshot
    elif data == "browser_test_action":
        await query.answer("Capturing live game board screenshot...", show_alert=False)
        loading_msg = await query.message.reply_text("⏳ Communicating with Playwright browser on live game screen...")

        try:
            shot_stream = await bet_automation.capture_win_screenshot(
                game_id="wingo_1m",
                target_issue="TEST-PERIOD",
                choice="BIG",
                actual_number=7,
                level=1,
                streak=5
            )
            if shot_stream:
                raw = shot_stream.getvalue()
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=io.BytesIO(raw),
                    caption="📸 <b>Verified Live Screen Capture!</b>\nReal winning popup & board capture is functioning 100% properly.",
                    parse_mode=ParseMode.HTML
                )
                await loading_msg.delete()
            else:
                await loading_msg.edit_text("⚠️ Could not capture screenshot. Check browser logs.")
        except Exception as e:
            await loading_msg.edit_text(f"❌ Error during test: {e}")

    # 6. Reconnect Browser
    elif data == "browser_reconnect":
        await query.answer("Reconnecting Playwright browser...", show_alert=True)
        try:
            await bet_automation.initialize()
            await query.answer("Browser reconnected successfully!", show_alert=True)
        except Exception as e:
            await query.answer(f"Reconnect failed: {e}", show_alert=True)
        text = _get_admin_panel_text(user.first_name)
        mode = cfg.get("mode", "24_7")
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_main_keyboard(operating_mode=mode, browser_ready=bet_automation.is_logged_in)
        )

    # 7. Channel List
    elif data == "admin_channels":
        admin_states.pop(user.id, None)
        channels = db_manager.get_all_channels()
        if not channels:
            keyboard = [
                [InlineKeyboardButton("➕ Add New Channel", callback_data="admin_add_channel")],
                [InlineKeyboardButton("⬅️ Back", callback_data="admin_main")]
            ]
            await query.edit_message_text(
                "📢 <b>No channels added yet!</b>\n\nClick below to add your first channel.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return

        buttons = []
        for ch in channels:
            ch_id = ch["channel_id"]
            title = ch.get("title", ch_id)
            game_id = ch.get("game_id", "wingo_1m")
            game_info = config.WINGO_GAMES.get(game_id, {})
            game_label = game_info.get("name", game_id)
            status_icon = "🟢" if ch.get("is_active", True) else "🔴"
            btn_cnt = len(ch.get("buttons", []))

            buttons.append([
                InlineKeyboardButton(f"{status_icon} {title} ({game_label} | {btn_cnt} Btns)", callback_data=f"view_ch:{ch_id}")
            ])

        buttons.append([InlineKeyboardButton("➕ Add Channel", callback_data="admin_add_channel")])
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_main")])

        await query.edit_message_text(
            f"📢 <b>Active Channels ({len(channels)})</b>\n\nClick any channel to manage its WinGo game, colored buttons, and status:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # 8. View / Manage Specific Channel
    elif data.startswith("view_ch:"):
        admin_states.pop(user.id, None)
        ch_id = data.split(":", 1)[1]
        await _render_channel_view(query, ch_id)

    # 9. Toggle Channel
    elif data.startswith("toggle_ch:"):
        ch_id = data.split(":", 1)[1]
        new_status = db_manager.toggle_channel_active(ch_id)
        status_msg = "STARTED ✅" if new_status else "PAUSED ⏸️"
        await query.answer(f"Predictions {status_msg} for channel!", show_alert=True)
        await _render_channel_view(query, ch_id)

    # 10. Change Game Duration
    elif data.startswith("change_game:"):
        ch_id = data.split(":", 1)[1]
        text = f"⏱️ <b>Select New WinGo Duration for channel {ch_id}:</b>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=get_game_select_keyboard(ch_id))

    # 11. Set Game Duration Callback
    elif data.startswith("setgame:"):
        parts = data.split(":")
        ch_id = parts[1]
        selected_game = parts[2]

        ch = db_manager.get_channel(ch_id)
        if ch:
            db_manager.update_channel(ch_id, {"game_id": selected_game})
            game_name = config.WINGO_GAMES.get(selected_game, {}).get("name", selected_game)
            await query.answer(f"Game updated to {game_name}!", show_alert=True)
        else:
            db_manager.add_channel(channel_id=ch_id, game_id=selected_game)
            await query.answer(f"Channel added with {selected_game}!", show_alert=True)

        await _render_channel_view(query, ch_id)

    # 12. Manage Channel Buttons Menu
    elif data.startswith("manage_btns:"):
        admin_states.pop(user.id, None)
        ch_id = data.split(":", 1)[1]
        ch = db_manager.get_channel(ch_id)
        if not ch:
            await query.answer("Channel not found", show_alert=True)
            return

        buttons = ch.get("buttons", [])
        text = f"""🔘 <b>𝗠𝗮𝗻𝗮𝗴𝗲 𝗜𝗻𝗹𝗶𝗻𝗲 𝗕𝘂𝘁𝘁𝗼𝗻𝘀 𝗳𝗼𝗿 {ch.get('title', ch_id)}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
Active Buttons: <b>{len(buttons)}</b>
<i>These buttons appear below every signal & win notification posted in this channel.</i>
━━━━━━━━━━━━━━━━━━━━━━━━━"""
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=get_channel_buttons_keyboard(ch_id, buttons))

    # 13. Add Button (Initiate Step 1: Text)
    elif data.startswith("add_btn:"):
        ch_id = data.split(":", 1)[1]
        admin_states[user.id] = {"state": "waiting_btn_text", "channel_id": ch_id}
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data=f"manage_btns:{ch_id}")]]
        await query.edit_message_text(
            f"➕ <b>Add Button for {ch_id} (Step 1/3)</b>\n\nPlease send the <b>Button Text</b> (e.g., <code>🔥 Register VIP Account</code>):",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 14. Select Button Style & Save
    elif data.startswith("btnstyle:"):
        parts = data.split(":")
        ch_id = parts[1]
        chosen_style = parts[2]
        emoji_id = parts[3] if len(parts) > 3 and parts[3] != "none" else None

        state_info = admin_states.pop(user.id, None)
        if not state_info or state_info.get("channel_id") != ch_id:
            await query.answer("Session expired. Please try again.", show_alert=True)
            await _render_channel_view(query, ch_id)
            return

        btn_text = state_info.get("btn_text")
        btn_url = state_info.get("btn_url")
        style_val = chosen_style if chosen_style in ("success", "danger", "primary") else None

        db_manager.add_channel_button(
            channel_id=ch_id,
            text=btn_text,
            url=btn_url,
            style=style_val,
            icon_custom_emoji_id=emoji_id
        )

        await query.answer("✅ Button added successfully!", show_alert=True)
        ch = db_manager.get_channel(ch_id)
        buttons = ch.get("buttons", [])
        await query.edit_message_text(
            f"✅ <b>Button added! Total: {len(buttons)} button(s).</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_channel_buttons_keyboard(ch_id, buttons)
        )

    # 15. Delete Single Button
    elif data.startswith("del_btn:"):
        parts = data.split(":")
        ch_id = parts[1]
        btn_idx = int(parts[2])
        db_manager.remove_channel_button(ch_id, btn_idx)
        await query.answer("Button removed!", show_alert=True)
        ch = db_manager.get_channel(ch_id)
        buttons = ch.get("buttons", [])
        await query.edit_message_text(
            f"🗑️ <b>Button removed. Total: {len(buttons)} remaining.</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_channel_buttons_keyboard(ch_id, buttons)
        )

    # 16. Clear All Buttons
    elif data.startswith("clear_btns:"):
        ch_id = data.split(":", 1)[1]
        db_manager.clear_channel_buttons(ch_id)
        await query.answer("All buttons cleared! Posts will have 0 buttons.", show_alert=True)
        await query.edit_message_text(
            "🗑️ <b>All buttons removed. Posts in this channel will now be sent with NO buttons.</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_channel_buttons_keyboard(ch_id, [])
        )

    # 17. Reset Level to 1
    elif data.startswith("reset_level:"):
        ch_id = data.split(":", 1)[1]
        db_manager.update_channel(ch_id, {"current_level": 1})
        await query.answer("Martingale level reset to Level 1!", show_alert=True)
        await _render_channel_view(query, ch_id)

    # 18. Delete Channel
    elif data.startswith("delete_ch:"):
        ch_id = data.split(":", 1)[1]
        db_manager.remove_channel(ch_id)
        await query.answer("Channel removed!", show_alert=True)
        keyboard = [
            [InlineKeyboardButton("📢 Channel List", callback_data="admin_channels")],
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="admin_main")]
        ]
        await query.edit_message_text(
            f"🗑️ <b>Channel {ch_id} has been removed.</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # 19. Add Channel Form
    elif data == "admin_add_channel":
        admin_states[user.id] = {"state": "waiting_channel_id"}
        text = """➕ <b>𝗔𝗱𝗱 𝗡𝗲𝘄 𝗧𝗲𝗹𝗲𝗴𝗿𝗮𝗺 𝗖𝗵𝗮𝗻𝗻𝗲𝗹</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
1. Make sure this bot is added as an <b>Administrator</b> in your channel with <b>Post Messages</b> permission.
2. Send your Channel Username or ID below:
   • Example Username: <code>@MyWinGoVIP</code>
   • Example Channel ID: <code>-1001234567890</code>

Send your Channel ID or Username now:"""
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data="admin_channels")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    # 20. Overall System Stats
    elif data == "admin_stats":
        channels = db_manager.get_all_channels()
        total_ch = len(channels)
        active_ch = len([c for c in channels if c.get("is_active", True)])

        tot_preds = sum(c.get("stats", {}).get("total_predictions", 0) for c in channels)
        tot_wins = sum(c.get("stats", {}).get("wins", 0) for c in channels)
        tot_losses = sum(c.get("stats", {}).get("losses", 0) for c in channels)
        overall_wr = (tot_wins / tot_preds * 100) if tot_preds > 0 else 0.0

        text = f"""📊 <b>𝗪𝗜𝗡𝗚𝗢 𝗔𝗜 𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦</b> 📊
━━━━━━━━━━━━━━━━━━━━━━━━━
📢 <b>Channels:</b> <code>{active_ch} Active / {total_ch} Total</code>
🎯 <b>Total Predictions Sent:</b> <code>{tot_preds}</code>
✅ <b>Total Wins:</b> <code>{tot_wins}</code>
❌ <b>Total Losses:</b> <code>{tot_losses}</code>
🏆 <b>Overall Win Rate:</b> <b>{overall_wr:.1f}%</b>
━━━━━━━━━━━━━━━━━━━━━━━━━"""
        keyboard = [[InlineKeyboardButton("⬅️ Back to Admin", callback_data="admin_main")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    # 21. Broadcast
    elif data == "admin_broadcast":
        admin_states[user.id] = {"state": "waiting_broadcast_text"}
        text = "📣 <b>Broadcast Message to All Channels</b>\n\nSend the message text you want to broadcast (HTML supported):"
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data="admin_main")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    text = update.message.text.strip()
    state_info = admin_states.get(user.id)
    if not state_info:
        return

    current_state = state_info.get("state")
    cfg = db_manager.get_system_settings()

    # Case 1: Channel ID received
    if current_state == "waiting_channel_id":
        admin_states.pop(user.id, None)
        ch_id = text
        prompt_text = f"""⏱️ <b>Select WinGo Duration for {ch_id}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
Choose which WinGo duration this channel should broadcast signals for:"""
        await update.message.reply_text(
            prompt_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_game_select_keyboard(ch_id)
        )

    # Case 2: Button Text received
    elif current_state == "waiting_btn_text":
        ch_id = state_info.get("channel_id")
        if not text:
            await update.message.reply_text("❌ Button text cannot be empty. Please send valid text:")
            return

        admin_states[user.id] = {
            "state": "waiting_btn_url",
            "channel_id": ch_id,
            "btn_text": text
        }
        prompt = f"""🔗 <b>Add Button for {ch_id} (Step 2/3)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ <b>Button Text:</b> <code>{text}</code>

Now send the <b>Button URL / Link</b> (must start with <code>https://</code> or <code>http://</code> or <code>tg://</code>):"""
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data=f"manage_btns:{ch_id}")]]
        await update.message.reply_text(
            prompt,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # Case 3: Button URL received
    elif current_state == "waiting_btn_url":
        ch_id = state_info.get("channel_id")
        btn_text = state_info.get("btn_text")

        if not (text.startswith("http://") or text.startswith("https://") or text.startswith("tg://")):
            await update.message.reply_text(
                "❌ Invalid URL! Please send a valid link starting with <code>https://</code>:",
                parse_mode=ParseMode.HTML
            )
            return

        admin_states[user.id] = {
            "state": "waiting_btn_style",
            "channel_id": ch_id,
            "btn_text": btn_text,
            "btn_url": text
        }
        prompt = f"""🎨 <b>Select Button Color Style (Step 3/3)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ <b>Text:</b> {btn_text}
🔗 <b>URL:</b> <code>{text}</code>

Choose the Telegram Native Colored Button Style below:"""
        await update.message.reply_text(
            prompt,
            parse_mode=ParseMode.HTML,
            reply_markup=get_button_style_select_keyboard(ch_id),
            disable_web_page_preview=True
        )

    # Case 4: Broadcast Text received
    elif current_state == "waiting_broadcast_text":
        admin_states.pop(user.id, None)
        channels = db_manager.get_all_channels()
        sent_count = 0

        for ch in channels:
            ch_id = ch["channel_id"]
            try:
                await context.bot.send_message(
                    chat_id=ch_id,
                    text=text,
                    parse_mode=ParseMode.HTML
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Error broadcasting to {ch_id}: {e}")

        await update.message.reply_text(
            f"📣 <b>Broadcast Complete!</b>\nSent successfully to <b>{sent_count}/{len(channels)}</b> channels.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_main_keyboard(cfg.get("mode", "24_7"), bet_automation.is_logged_in)
        )
