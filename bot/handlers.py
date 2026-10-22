import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

import config
from database import db_manager
from bot.keyboards import (
    get_admin_main_keyboard,
    get_game_select_keyboard,
    get_channel_manage_keyboard
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

    text = f"""👑 <b>𝗪𝗜𝗡𝗚𝗢 𝗔𝗜 𝗣𝗥𝗘𝗗𝗜𝗖𝗧𝗜𝗢𝗡 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b> 👑
━━━━━━━━━━━━━━━━━━━━━━━━━
👋 Welcome, <b>{user.first_name}</b>!
⚡ <b>Status:</b> <code>ONLINE & RUNNING</code>
🤖 <b>Engine:</b> WinGo 30s, 1M, 3M, 5M (Multi-Game)
🛡️ <b>Protection:</b> Safe 3-5 Level Martingale
━━━━━━━━━━━━━━━━━━━━━━━━━
Select an option from the menu below:"""

    reply_markup = get_admin_main_keyboard()
    await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not is_admin(user.id):
        await query.edit_message_text("⛔ Unauthorized.")
        return

    data = query.data
    chat_id = query.message.chat_id

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

            buttons.append([
                InlineKeyboardButton(f"{status_icon} {title} ({game_label})", callback_data=f"view_ch:{ch_id}")
            ])

        buttons.append([InlineKeyboardButton("➕ Add Channel", callback_data="admin_add_channel")])
        buttons.append([InlineKeyboardButton("⬅️ Back", callback_data="admin_main")])

        await query.edit_message_text(
            f"📢 <b>Active Channels ({len(channels)})</b>\n\nClick any channel to manage its WinGo game, links, and status:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # 3. View / Manage Specific Channel
    elif data.startswith("view_ch:"):
        ch_id = data.split(":", 1)[1]
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

        text = f"""📢 <b>𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀: {ch.get('title', ch_id)}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>ID:</b> <code>{ch_id}</code>
⚡ <b>Status:</b> {status_text}
⏱️ <b>Game Mode:</b> <b>{game_label}</b>
🛡️ <b>Current Level:</b> <b>Level {ch.get('current_level', 1)}</b>
📊 <b>Win Rate:</b> <b>{win_rate:.1f}%</b> ({wins}W / {losses}L)
🔥 <b>Current Streak:</b> <b>{stats.get('current_streak', 0)}W</b>
🔗 <b>Register Link:</b> <code>{ch.get('register_link', config.DEFAULT_REGISTER_LINK)}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━"""

        reply_markup = get_channel_manage_keyboard(ch_id, is_active, game_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    # 4. Toggle Channel
    elif data.startswith("toggle_ch:"):
        ch_id = data.split(":", 1)[1]
        new_status = db_manager.toggle_channel_active(ch_id)
        status_msg = "STARTED ✅" if new_status else "PAUSED ⏸️"
        await query.answer(f"Predictions {status_msg} for channel!", show_alert=True)
        # Re-render channel view
        ch = db_manager.get_channel(ch_id)
        reply_markup = get_channel_manage_keyboard(ch_id, new_status, ch.get("game_id", "wingo_1m"))
        await query.edit_message_reply_markup(reply_markup=reply_markup)

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
            # New channel being created
            db_manager.add_channel(channel_id=ch_id, game_id=selected_game)
            await query.answer(f"Channel added with {selected_game}!", show_alert=True)

        # Redirect back to channel view
        ch = db_manager.get_channel(ch_id)
        reply_markup = get_channel_manage_keyboard(ch_id, ch.get("is_active", True), selected_game)
        await query.edit_message_text(
            f"✅ Channel <b>{ch_id}</b> configured for <b>{config.WINGO_GAMES.get(selected_game, {}).get('name')}</b>!",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup
        )

    # 7. Reset Level
    elif data.startswith("reset_level:"):
        ch_id = data.split(":", 1)[1]
        db_manager.update_channel(ch_id, {"current_level": 1})
        await query.answer("Current Martingale Level reset to Level 1!", show_alert=True)

    # 8. Delete Channel
    elif data.startswith("delete_ch:"):
        ch_id = data.split(":", 1)[1]
        db_manager.remove_channel(ch_id)
        await query.answer("Channel removed!", show_alert=True)
        # Redirect to channels list
        channels = db_manager.get_all_channels()
        keyboard = [
            [InlineKeyboardButton("➕ Add New Channel", callback_data="admin_add_channel")],
            [InlineKeyboardButton("⬅️ Back to Main", callback_data="admin_main")]
        ]
        await query.edit_message_text("✅ Channel successfully removed.", reply_markup=InlineKeyboardMarkup(keyboard))

    # 9. Add Channel Prompt
    elif data == "admin_add_channel":
        admin_states[user.id] = {"state": "waiting_channel_id"}
        text = """➕ <b>Add New Channel</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
Please send the Channel Username (e.g. <code>@mywingochannel</code>) or numeric ID (e.g. <code>-1001234567890</code>).

⚠️ <i>Make sure this Bot is added as an <b>ADMINISTRATOR</b> with 'Post Messages' permission in that channel!</i>"""
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data="admin_channels")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    # 10. Edit Link Prompt
    elif data.startswith("edit_link:"):
        ch_id = data.split(":", 1)[1]
        admin_states[user.id] = {"state": "waiting_register_link", "channel_id": ch_id}
        text = f"""🔗 <b>Change Register Link for {ch_id}</b>
━━━━━━━━━━━━━━━━━━━━━━━━━
Please send the new Registration URL (starting with <code>https://...</code>):"""
        keyboard = [[InlineKeyboardButton("⬅️ Cancel", callback_data=f"view_ch:{ch_id}")]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

    # 11. System Stats
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

    # 12. Broadcast Prompt
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
        # Ask to choose WinGo duration for this channel
        prompt_text = f"""⏱️ <b>Select Game Duration for channel:</b> <code>{ch_id}</code>
━━━━━━━━━━━━━━━━━━━━━━━━━
Choose which WinGo duration this channel should broadcast signals for:"""
        await update.message.reply_text(
            prompt_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_game_select_keyboard(ch_id)
        )

    # Case 2: New Register Link received
    elif current_state == "waiting_register_link":
        ch_id = state_info.get("channel_id")
        admin_states.pop(user.id, None)
        if text.startswith("http://") or text.startswith("https://"):
            db_manager.update_channel(ch_id, {"register_link": text})
            await update.message.reply_text(
                f"✅ Register link for channel <code>{ch_id}</code> updated to:\n{text}",
                parse_mode=ParseMode.HTML,
                reply_markup=get_admin_main_keyboard()
            )
        else:
            await update.message.reply_text(
                "❌ Invalid URL format. Please start with <code>https://</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=get_admin_main_keyboard()
            )

    # Case 3: Broadcast Text received
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
