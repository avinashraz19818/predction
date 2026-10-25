import io
import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

import config
from database import db_manager
from services.lottery_api import lottery_api
from services.bet_automation import bet_automation
from engine.predictor import predictor
from bot.templates import (
    render_prediction_card,
    render_win_card,
    render_loss_card,
    render_pre_session_alert_card,
    render_session_start_card,
    render_session_summary_card,
    strip_tg_emoji_tags
)
from bot.keyboards import get_channel_post_keyboard

logger = logging.getLogger(__name__)


class WinGoScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False
        self.tasks = []
        self.tz = pytz.timezone(getattr(config, "TIMEZONE", "Asia/Kolkata"))

        # Session tracking state
        self.active_session = None  # None or dict of active session details
        self.pre_alerts_sent_today = set()  # set of session_ids
        self.completed_sessions_today = set()  # set of session_ids
        self.last_day_checked = None

        # State per game_id
        self.game_states = {
            game_id: {
                "last_processed_issue": None,
                "active_prediction": None,
                "waiting_result": False
            }
            for game_id in config.WINGO_GAMES.keys()
        }

    async def start(self):
        self.running = True
        logger.info("🚀 Starting WinGo Multi-Game Schedulers with Session Controller...")

        # Initialize Playwright real game automation in background
        if config.DEMO_AUTO_BET:
            asyncio.create_task(bet_automation.initialize())

        # Start game prediction loops
        for game_id in config.WINGO_GAMES.keys():
            task = asyncio.create_task(self._game_loop(game_id))
            self.tasks.append(task)

        # Start Session Controller loop
        session_task = asyncio.create_task(self._session_controller_loop())
        self.tasks.append(session_task)

    async def stop(self):
        self.running = False
        for task in self.tasks:
            task.cancel()
        await lottery_api.close()
        await bet_automation.close()
        logger.info("🛑 WinGo Schedulers stopped.")

    # ================= MESSAGE SENDING HELPERS =================

    async def _safe_send_message(self, channel: dict, text: str):
        """Sends message with custom colored buttons & premium emojis, with fallback"""
        channel_id = channel["channel_id"]
        reply_markup = get_channel_post_keyboard(channel, include_custom_emoji=True, include_style=True)

        try:
            await self.bot.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup,
                disable_web_page_preview=True
            )
            return True
        except TelegramError as te:
            err_str = str(te).lower()
            if "custom_emoji" in err_str or "button" in err_str or "style" in err_str:
                try:
                    fallback_markup = get_channel_post_keyboard(channel, include_custom_emoji=False, include_style=True)
                    await self.bot.send_message(
                        chat_id=channel_id,
                        text=text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=fallback_markup,
                        disable_web_page_preview=True
                    )
                    return True
                except TelegramError:
                    fallback_markup2 = get_channel_post_keyboard(channel, include_custom_emoji=False, include_style=False)
                    await self.bot.send_message(
                        chat_id=channel_id,
                        text=strip_tg_emoji_tags(text),
                        parse_mode=ParseMode.HTML,
                        reply_markup=fallback_markup2,
                        disable_web_page_preview=True
                    )
                    return True
            logger.error(f"❌ Failed to send message to {channel_id}: {te}")
            return False

    async def _safe_send_photo(self, channel: dict, photo_bytes: bytes, caption: str):
        """Sends photo with custom colored buttons & premium emojis, with fallback"""
        channel_id = channel["channel_id"]
        reply_markup = get_channel_post_keyboard(channel, include_custom_emoji=True, include_style=True)

        try:
            await self.bot.send_photo(
                chat_id=channel_id,
                photo=io.BytesIO(photo_bytes),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
            return True
        except TelegramError as te:
            err_str = str(te).lower()
            if "custom_emoji" in err_str or "button" in err_str or "style" in err_str:
                try:
                    fallback_markup = get_channel_post_keyboard(channel, include_custom_emoji=False, include_style=True)
                    await self.bot.send_photo(
                        chat_id=channel_id,
                        photo=io.BytesIO(photo_bytes),
                        caption=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=fallback_markup
                    )
                    return True
                except TelegramError:
                    fallback_markup2 = get_channel_post_keyboard(channel, include_custom_emoji=False, include_style=False)
                    await self.bot.send_photo(
                        chat_id=channel_id,
                        photo=io.BytesIO(photo_bytes),
                        caption=strip_tg_emoji_tags(caption),
                        parse_mode=ParseMode.HTML,
                        reply_markup=fallback_markup2
                    )
                    return True
            logger.error(f"❌ Failed to send photo to {channel_id}: {te}")
            return False

    # ================= SESSION SCHEDULER CONTROLLER =================

    def _now_ist(self) -> datetime:
        return datetime.now(self.tz)

    def is_signal_allowed(self) -> bool:
        """Determines if signals should be posted right now based on mode"""
        cfg = db_manager.get_system_settings()
        mode = cfg.get("mode", "24_7")
        if mode == "24_7":
            return True
        # In Scheduled mode, only allowed if a session is actively running
        return self.active_session is not None

    async def _session_controller_loop(self):
        """Monitors IST clock and manages pre-alerts, session starts, and wrap-up cards"""
        logger.info("🕒 Session Controller Loop active (Timezone: IST)...")

        while self.running:
            try:
                now = self._now_ist()
                today_str = now.strftime("%Y-%m-%d")

                # Daily reset of session tracking
                if self.last_day_checked != today_str:
                    self.pre_alerts_sent_today.clear()
                    self.completed_sessions_today.clear()
                    self.last_day_checked = today_str

                cfg = db_manager.get_system_settings()
                mode = cfg.get("mode", "24_7")

                if mode == "scheduled":
                    sessions = cfg.get("sessions", getattr(config, "DEFAULT_SESSIONS", []))
                    current_hm = now.strftime("%H:%M")
                    pre_alert_mins = int(cfg.get("pre_alert_minutes", 15))

                    for s in sessions:
                        s_id = s["id"]
                        s_name = s.get("name", f"Session {s_id}")
                        start_str = s["start"]
                        end_str = s["end"]
                        max_rounds = s.get("max_rounds", 15)

                        # Parse times
                        s_start_dt = now.replace(
                            hour=int(start_str.split(":")[0]),
                            minute=int(start_str.split(":")[1]),
                            second=0,
                            microsecond=0
                        )
                        s_end_dt = now.replace(
                            hour=int(end_str.split(":")[0]),
                            minute=int(end_str.split(":")[1]),
                            second=0,
                            microsecond=0
                        )
                        pre_alert_dt = s_start_dt - timedelta(minutes=pre_alert_mins)

                        # 1. Check Pre-Session Alert (T - 15 mins)
                        if pre_alert_dt <= now < s_start_dt:
                            if s_id not in self.pre_alerts_sent_today:
                                await self._broadcast_pre_session_alert(s_name, start_str)
                                self.pre_alerts_sent_today.add(s_id)

                        # 2. Check Session Start
                        if s_start_dt <= now < s_end_dt and s_id not in self.completed_sessions_today:
                            if not self.active_session or self.active_session.get("id") != s_id:
                                self.active_session = {
                                    "id": s_id,
                                    "name": s_name,
                                    "start": start_str,
                                    "end": end_str,
                                    "max_rounds": max_rounds,
                                    "rounds": 0,
                                    "wins": 0,
                                    "losses": 0,
                                    "current_streak": 0,
                                    "max_streak": 0,
                                    "max_level_used": 1,
                                    "profit": 0.0
                                }
                                await self._broadcast_session_start(s_name, end_str, max_rounds)

                        # 3. Check Session End Condition
                        if self.active_session and self.active_session.get("id") == s_id:
                            time_up = (now >= s_end_dt)
                            rounds_done = (self.active_session["rounds"] >= max_rounds)

                            if time_up or rounds_done:
                                await self._conclude_session(self.active_session, sessions)
                                self.completed_sessions_today.add(s_id)
                                self.active_session = None

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session controller: {e}", exc_info=True)

            await asyncio.sleep(10)

    async def _broadcast_pre_session_alert(self, session_name: str, start_time: str):
        """Sends 15-minute advance notice to all active channels"""
        channels = db_manager.get_all_channels()
        active_channels = [c for c in channels if c.get("is_active", True)]
        if not active_channels:
            return

        logger.info(f"🚨 Broadcasting Pre-Session Alert for {session_name} starting at {start_time} IST...")
        for ch in active_channels:
            promo = ch.get("promo_text", config.DEFAULT_PROMO_TEXT)
            text = render_pre_session_alert_card(
                session_name=session_name,
                start_time=start_time,
                game_name="WinGo 1 Minute VIP",
                promo_text=promo
            )
            await self._safe_send_message(ch, text)

    async def _broadcast_session_start(self, session_name: str, end_time: str, max_rounds: int):
        """Sends live kickoff announcement to all channels"""
        channels = db_manager.get_all_channels()
        active_channels = [c for c in channels if c.get("is_active", True)]
        if not active_channels:
            return

        logger.info(f"🟢 Broadcasting VIP Session Live Alert: {session_name}!")
        for ch in active_channels:
            text = render_session_start_card(
                session_name=session_name,
                end_time=end_time,
                max_rounds=max_rounds,
                game_name="WinGo 1 Minute"
            )
            await self._safe_send_message(ch, text)

    async def _conclude_session(self, session_data: dict, all_sessions: list):
        """Sends end-of-session summary card with accuracy and profit metrics"""
        channels = db_manager.get_all_channels()
        active_channels = [c for c in channels if c.get("is_active", True)]
        if not active_channels:
            return

        # Find next session
        next_text = "Tomorrow at 11:00 AM IST"
        curr_id = session_data["id"]
        for s in all_sessions:
            if s["id"] > curr_id:
                next_text = f"Today at {s['start']} IST ({s.get('name', 'Next Session')})"
                break

        total_rounds = session_data["rounds"]
        wins = session_data["wins"]
        losses = session_data["losses"]
        max_streak = session_data["max_streak"]
        max_lvl = session_data["max_level_used"]
        profit = session_data["profit"]

        logger.info(f"🏆 Concluding {session_data['name']}: {wins}/{total_rounds} Wins | Profit: ₹{profit}")

        text = render_session_summary_card(
            session_name=session_data["name"],
            total_rounds=total_rounds,
            wins=wins,
            losses=losses,
            max_streak=max_streak,
            max_level_used=max_lvl,
            profit_inr=profit,
            next_session_text=next_text
        )

        for ch in active_channels:
            await self._safe_send_message(ch, text)

    # ================= MAIN GAME LOOP =================

    async def _game_loop(self, game_id: str):
        game_cfg = config.WINGO_GAMES[game_id]
        game_name = game_cfg["name"]
        poll_interval = 4 if game_id == "wingo_30s" else (8 if game_id == "wingo_1m" else 15)

        logger.info(f"[{game_name}] Loop active (Polling every {poll_interval}s)")

        while self.running:
            try:
                # 1. Fetch live history
                history = await lottery_api.fetch_history(game_id)
                if not history or len(history) < 2:
                    await asyncio.sleep(poll_interval)
                    continue

                latest_item = history[0]
                latest_issue = str(latest_item["issueNumber"])

                state = self.game_states[game_id]
                active_pred = state["active_prediction"]

                # 2. Check Result of Active Prediction
                if state["waiting_result"] and active_pred:
                    target_issue = str(active_pred["issue"])

                    matched_item = None
                    for item in history[:5]:
                        if str(item["issueNumber"]) == target_issue:
                            matched_item = item
                            break

                    if matched_item:
                        actual_num = matched_item["number"]
                        actual_choice = matched_item["big_small"]
                        is_win = (active_pred["choice"] == actual_choice)
                        hit_lucky = (actual_num in active_pred["numbers"])

                        logger.info(f"[{game_name}] Result for {target_issue}: {actual_choice} ({actual_num}) | Pred: {active_pred['choice']} -> {'WIN ✅' if is_win else 'LOSS ❌'}")

                        # Update session stats if session is active
                        if self.active_session:
                            self.active_session["rounds"] += 1
                            if is_win:
                                self.active_session["wins"] += 1
                                self.active_session["current_streak"] += 1
                                if self.active_session["current_streak"] > self.active_session["max_streak"]:
                                    self.active_session["max_streak"] = self.active_session["current_streak"]
                                self.active_session["profit"] += 350.0  # Normalized estimated VIP win profit
                            else:
                                self.active_session["losses"] += 1
                                self.active_session["current_streak"] = 0

                        # Broadcast result to channels
                        await self._broadcast_result(
                            game_id=game_id,
                            issue_number=target_issue,
                            pred_choice=active_pred["choice"],
                            actual_choice=actual_choice,
                            actual_number=actual_num,
                            is_win=is_win,
                            hit_lucky_number=hit_lucky
                        )

                        state["waiting_result"] = False
                        state["active_prediction"] = None

                # 3. Generate and Send Next Prediction
                if not state["waiting_result"]:
                    # Guard: Check if signals are allowed by Operating Mode (24/7 or Session)
                    if not self.is_signal_allowed():
                        await asyncio.sleep(poll_interval)
                        continue

                    next_issue = lottery_api.get_next_issue(latest_issue)

                    if state["last_processed_issue"] != next_issue:
                        active_channels = db_manager.get_channels_by_game(game_id, only_active=True)
                        if not active_channels:
                            await asyncio.sleep(poll_interval)
                            continue

                        pred_result = predictor.analyze(history)
                        pred_data = {
                            "issue": next_issue,
                            "choice": pred_result["choice"],
                            "numbers": pred_result["numbers"],
                            "confidence": pred_result["confidence"],
                            "pattern_name": pred_result["pattern_name"],
                            "created_at": datetime.utcnow().isoformat()
                        }

                        logger.info(f"[{game_name}] New Signal for {next_issue}: {pred_data['choice']} Numbers: {pred_data['numbers']} ({pred_data['confidence']}%)")

                        current_martingale_level = max([ch.get("current_level", 1) for ch in active_channels], default=1)

                        # Place real bet in Playwright headless browser
                        if bet_automation.enabled and bet_automation.is_logged_in:
                            asyncio.create_task(bet_automation.place_bet(game_id, pred_data["choice"], next_issue, level=current_martingale_level))

                        # Send individual prediction message to channels
                        await self._broadcast_prediction(game_id, pred_data, active_channels)

                        state["active_prediction"] = pred_data
                        state["waiting_result"] = True
                        state["last_processed_issue"] = next_issue

                        db_manager.save_prediction(game_id, next_issue, pred_data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{game_name}] Loop error: {e}", exc_info=True)

            await asyncio.sleep(poll_interval)

    async def _broadcast_prediction(self, game_id: str, pred_data: dict, channels: list):
        """Sends a brand new individual prediction message to all subscribed channels"""
        game_cfg = config.WINGO_GAMES[game_id]
        game_name = game_cfg["name"]
        custom_tpl = db_manager.get_message_template("prediction")

        for ch in channels:
            channel_id = ch["channel_id"]
            curr_level = ch.get("current_level", 1)
            promo = ch.get("promo_text", config.DEFAULT_PROMO_TEXT)

            text = render_prediction_card(
                game_name=game_name,
                issue_number=pred_data["issue"],
                choice=pred_data["choice"],
                numbers=pred_data["numbers"],
                confidence=pred_data["confidence"],
                level=curr_level,
                pattern_name=pred_data["pattern_name"],
                promo_text=promo,
                custom_template=custom_tpl
            )

            try:
                ok = await self._safe_send_message(ch, text)
                if ok:
                    logger.info(f"✅ Signal posted to channel {channel_id}")
            except Exception as e:
                logger.error(f"❌ Unexpected error sending to {channel_id}: {e}")

    async def _broadcast_result(
        self,
        game_id: str,
        issue_number: str,
        pred_choice: str,
        actual_choice: str,
        actual_number: int,
        is_win: bool,
        hit_lucky_number: bool
    ):
        """
        Sends separate WIN celebration (with real Playwright winning screenshot) or LOSS notification
        """
        channels = db_manager.get_channels_by_game(game_id, only_active=True)
        game_cfg = config.WINGO_GAMES[game_id]
        game_name = game_cfg["name"]
        custom_win_tpl = db_manager.get_message_template("win")
        custom_loss_tpl = db_manager.get_message_template("loss")

        for ch in channels:
            channel_id = ch["channel_id"]
            curr_level = ch.get("current_level", 1)

            # Update stats & level in database
            stats, next_level = db_manager.record_channel_result(channel_id, is_win)
            streak = stats.get("current_streak", 1)

            if self.active_session:
                if curr_level > self.active_session["max_level_used"]:
                    self.active_session["max_level_used"] = curr_level

            try:
                if is_win:
                    win_text = render_win_card(
                        game_name=game_name,
                        issue_number=issue_number,
                        actual_choice=actual_choice,
                        actual_number=actual_number,
                        level=curr_level,
                        streak=streak,
                        hit_lucky_number=hit_lucky_number,
                        custom_template=custom_win_tpl
                    )

                    # Real Playwright screenshot of the actual Congratulations popup
                    screenshot_stream = await bet_automation.capture_win_screenshot(
                        game_id=game_id,
                        target_issue=issue_number,
                        choice=actual_choice,
                        actual_number=actual_number,
                        level=curr_level,
                        streak=streak
                    )

                    if screenshot_stream:
                        raw_bytes = screenshot_stream.getvalue()
                        await self._safe_send_photo(ch, raw_bytes, win_text)
                    else:
                        await self._safe_send_message(ch, win_text)
                else:
                    loss_text = render_loss_card(
                        game_name=game_name,
                        issue_number=issue_number,
                        actual_choice=actual_choice,
                        actual_number=actual_number,
                        curr_level=curr_level,
                        next_level=next_level,
                        custom_template=custom_loss_tpl
                    )
                    await self._safe_send_message(ch, loss_text)

            except Exception as e:
                logger.error(f"❌ Error broadcasting result to {channel_id}: {e}")
