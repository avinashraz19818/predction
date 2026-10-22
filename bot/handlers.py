import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
from database import db_manager
from bot.keyboards import (
    get_admin_main_keyboard,
    get_game_select_keyboard,
    get_channel_manage_keyboard,
    get_channel_buttons_keyboard,
    get_button_style_select_keyboard
)

logger = logging.getLogger(__name__)

# In-memory admin state: { user_id: { "state": ..., "data": ... } }
admin_states = {}

def is_admin(user_id: int) -> bool:
    if not config.ADMIN_IDS:
        return True
    return user_id in config.ADMIN_IDS

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("⛔ You are not authorized to access this bot.")
        return

    text = f"""👑 <b>𝗪𝗜𝗡𝗚𝗢 𝗔𝗜 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗢𝗡 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
👋 Welcome, <b>{user.first_name}</b>!
⚡ <b>Status:</b> <code>ONLINE & RUNNING</code>
🤖 <b>Engine:</b> WinGo 30s, 1M, 3M, 5M (Multi-Game)
🛡️ <b>Protection:</b> Safe 3-5 Level Martingale
━━━━━━━━━━━━━━━━━━━━━━━━━
Select an option from the menu below:"""

    reply_markup = get_admin_main_keyboard()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def _render_channel_view(query, ch_id: str):
    ch = db_manager.get_channel(ch_id)
    if not ch:
        await query.edit_message_text("❌ Channel not found.", reply_markup=get_admin_main_keyboard())
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

    # 1. Main Menu Refresh
    if data in ["admin_main", "admin_refresh"]:
        admin_states.pop(user.id, None)
        text = f"""👑 <b>𝗪𝗜𝗡𝗚𝗢 𝗔𝗜 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
👋 Welcome, <b>{user.first_name}</b>!
⚡ <b>Status:</b> <code>ONLINE & RUNNING</code>
🤖 <b>Engine:</b> WinGo 30s, 1M, 3M, 5M (Multi-Game)
━━━━━━━━━━━━━━━━━━━━━━━━━
Select an option:"""
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=get_admin_main_keyboard())

    # 2. Channel List
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

    # 3. View / Manage Specific Channel
    elif data.startswith("view_ch:"):
        admin_states.pop(user.id, None)
        ch_id = data.split(":", 1)[1]
        await _render_channel_view(query, ch_id)

    # 4. Toggle Channel
    elif data.startswith("toggle_ch:"):
        ch_id = data.split(":", 1)[1]
        new_status = db_manager.toggle_channel_active(ch_id)
        status_msg = "STARTED ✅" if new_status else "PAUSED ⏸️"
        await query.answer(f"Predictions {status_msg} for channel!", show_alert=True)
        await _render_channel_view(query, ch_id)

    # 5. Change Game Duration
    elif data.startswith("change_game:"):
        ch_id = data.split(":", 1)[1]
        text = f"⏱️ <b>Select New WinGo Duration for channel {ch_id}:</b>"
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=get_game_select_keyboard(ch_id))

    # 6. Set Game Duration Callback
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
            # New channel being created (with 0 buttons by default!)
            db_manager.add_channel(channel_id=ch_id, game_id=selected_game)
            await query.answer(f"Channel added with {selected_game}!", show_alert=True)

        await _render_channel_view(query, ch_id)

    # 7. Manage Channel Buttons Menu
    elif data.startswith("manage_btns:"):
        admin_states.pop(user.id, None)
        ch_id = data.split(":", 1)[1]
        ch = db_manager.get_channel(ch_id)
        if not ch:
            await query.edit_message_text("❌ Channel not found.", reply_markup=get_admin_main_keyboard())
            return

        buttons = ch.get("buttons", [])
        if not buttons:
            desc = "⚪ <b>Currently NO buttons are set for this channel.</b>\nMessages will be posted without any buttons until you add one below."
        else:
            lines = []
            for idx, b in enumerate(buttons):
                st = (b.get("style") or "default").upper()
                lines.append(f"<b>{idx+1}. {b.get('text')}</b>\n   🔗 <code>{b.get('url')}</code>\n   🎨 Style: <code>{st}</code>")
            desc = "\n\n".join(lines)

        text = f"""🔘 <b>𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗕𝘂𝘁𝘁𝗼𝗻𝘀 𝗠𝗮𝗻𝗮𝗴𝗲𝗿 ({ch_id})</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
{desc}
━━━━━━━━━━━━━━━━━━━━━━━━━
💡 <i>Supports Telegram's Native Colored Buttons (🟢 Success Green, 🔴 Danger Red, 🔵 Primary Blue) & Animated Emoji Icons!</i>"""

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_channel_buttons_keyboard(ch_id, buttons),
            disable_web_page_preview=True
        )

    # 8. Add Button Step 1: Ask for Button Text
    elif data.startswith("add_btn:"):
        ch_id = data.split(":", 1)[1]
        admin_states[user.id] = {
            "state": "waiting_btn_text",
            "channel_id": ch_id
        }
        text = f"""➕ <b>Add New Button for {ch_id} (Step 1/3)</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
Please send the <b>Button Text / Label</b> you want to display on the button:
<i>Example:</i> <code>🔥 REGISTER & WIN ₹500 🔥</code>"""
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data=f"manage_btns:{ch_id}")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    # 9. Add Button Step 3: Select Button Color Style
    elif data.startswith("btnstyle:"):
        parts = data.split(":")
        ch_id = parts[1]
        style_choice = parts[2]
        emoji_id = parts[3] if len(parts) > 3 and parts[3] != "none" else None

        state_info = admin_states.pop(user.id, None)
        if not state_info or "btn_text" not in state_info or "btn_url" not in state_info:
            await query.answer("⚠️ Session expired. Please add button again.", show_alert=True)
            await _render_channel_view(query, ch_id)
            return

        actual_style = style_choice if style_choice in ("success", "danger", "primary") else None
        buttons = db_manager.add_channel_button(
            channel_id=ch_id,
            text=state_info["btn_text"],
            url=state_info["btn_url"],
            style=actual_style,
            icon_custom_emoji_id=emoji_id
        )
        await query.answer("✅ Colored Button Added Successfully!", show_alert=True)

        text = f"""✅ <b>Button Added to {ch_id}!</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ <b>Text:</b> {state_info['btn_text']}
🔗 <b>URL:</b> <code>{state_info['btn_url']}</code>
🎨 <b>Color Style:</b> <code>{(actual_style or 'default').upper()}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
Total Active Buttons on this channel: <b>{len(buttons)}</b>"""
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_channel_buttons_keyboard(ch_id, buttons),
            disable_web_page_preview=True
        )

    # 10. Delete Single Button
    elif data.startswith("del_btn:"):
        parts = data.split(":")
        ch_id = parts[1]
        idx = int(parts[2])
        buttons = db_manager.remove_channel_button(ch_id, idx)
        await query.answer("🗑️ Button removed!", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=get_channel_buttons_keyboard(ch_id, buttons))

    # 11. Clear All Buttons
    elif data.startswith("clear_btns:"):
        ch_id = data.split(":", 1)[1]
        db_manager.clear_channel_buttons(ch_id)
        await query.answer("🗑️ All buttons cleared! Messages will now have NO buttons.", show_alert=True)
        await _render_channel_view(query, ch_id)

    # 12. Reset Level
    elif data.startswith("reset_level:"):
        ch_id = data.split(":", 1)[1]
        db_manager.update_channel(ch_id, {"current_level": 1})
        await query.answer("Current Martingale Level reset to Level 1!", show_alert=True)
        await _render_channel_view(query, ch_id)

    # 13. Delete Channel
    elif data.startswith("delete_ch:"):
        ch_id = data.split(":", 1)[1]
        db_manager.remove_channel(ch_id)
        await query.answer("Channel removed!", show_alert=True)
        keyboard = [
            [InlineKeyboardButton("➕ Add New Channel", callback_data="admin_add_channel")],
            [InlineKeyboardButton("⬅️ Back to Main", callback_data="admin_main")]
        ]
        await query.edit_message_text("✅ Channel successfully removed.", reply_markup=InlineKeyboardMarkup(keyboard))

    # 14. Add Channel Prompt
    elif data == "admin_add_channel":
        admin_states[user.id] = {"state": "waiting_channel_id"}
        text = """➕ <b>Add New Channel</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
Please send the Channel Username (e.g. <code>@mywingochannel</code>) or numeric ID (e.g. <code>-1001234567890</code>).

⚠️ <i>Make sure this Bot is added as an <b>ADMINISTRATOR</b> with 'Post Messages' permission in that channel!</i>"""
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data="admin_channels")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    # 15. System Stats
    elif data == "admin_stats":
        channels = db_manager.get_all_channels()
        active_count = len([c for c in channels if c.get("is_active", True)])
        
        total_w = sum(c.get("stats", {}).get("wins", 0) for c in channels)
        total_l = sum(c.get("stats", {}).get("losses", 0) for c in channels)
        total_all = total_w + total_l
        avg_rate = (total_w / total_all * 100) if total_all > 0 else 0.0

        text = f"""📊 <b>𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗧𝗔𝗧𝗜𝗦𝗧𝗜𝗖𝗦</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
📢 <b>Total Channels:</b> <code>{len(channels)}</code> (Active: <code>{active_count}</code>)
🏆 <b>Total Wins Recorded:</b> <code>{total_w}</code>
❌ <b>Total Losses Recorded:</b> <code>{total_l}</code>
📈 <b>Overall Win Rate:</b> <b>{avg_rate:.1f}%</b>
━━━━━━━━━━━━━━━━━━━━━━━━━"""
        keyboard = [[InlineKeyboardButton("⬅️ Back", callback_data="admin_main")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    # 16. Broadcast Prompt
    elif data == "admin_broadcast":
        admin_states[user.id] = {"state": "waiting_broadcast_text"}
        text = """📣 <b>Broadcast to All Channels</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
Please send the message text you want to broadcast to all connected channels:"""
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data="admin_main")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    state_info = admin_states.get(user.id)
    if not state_info:
        return

    current_state = state_info.get("state")
    text = update.message.text.strip() if update.message.text else ""

    # Case 1: Channel ID received
    if current_state == "waiting_channel_id":
        admin_states.pop(user.id, None)
        ch_id = text
        prompt_text = f"""⏱️ <b>Select Game Duration for channel:</b> <code>{ch_id}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
Choose which WinGo duration this channel should broadcast signals for:"""
        await update.message.reply_text(
            prompt_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_game_select_keyboard(ch_id)
        )

    # Case 2: Button Text received (Step 1 -> Step 2)
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

    # Case 3: Button URL received (Step 2 -> Step 3: Select Color Style)
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
            reply_markup=get_admin_main_keyboard()
        )
