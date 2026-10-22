import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

import config
from database import db_manager
from services.lottery_api import lottery_api
from services.bet_automation import bet_automation
from engine.predictor import predictor
from bot.templates import render_prediction_card, render_win_card, render_loss_card
from bot.keyboards import get_channel_post_keyboard
from bot.card_generator import generate_win_result_card

logger = logging.getLogger(__name__)

class WinGoScheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False
        self.tasks = []
        
        # State per game_id: { "last_issue": None, "active_prediction": None, "waiting_result": False }
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
        logger.info("🚀 Starting WinGo Multi-Game Schedulers (30s, 1m, 3m, 5m)...")

        # Initialize demo account automation in background
        if config.DEMO_AUTO_BET:
            asyncio.create_task(bet_automation.initialize())

        for game_id in config.WINGO_GAMES.keys():
            task = asyncio.create_task(self._game_loop(game_id))
            self.tasks.append(task)

    async def stop(self):
        self.running = False
        for task in self.tasks:
            task.cancel()
        await lottery_api.close()
        await bet_automation.close()
        logger.info("🛑 WinGo Schedulers stopped.")

    async def _game_loop(self, game_id: str):
        game_cfg = config.WINGO_GAMES[game_id]
        game_name = game_cfg["name"]
        poll_interval = 5 if game_id == "wingo_30s" else (10 if game_id == "wingo_1m" else 15)

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
                latest_num = latest_item["number"]
                latest_choice = latest_item["big_small"]

                state = self.game_states[game_id]
                active_pred = state["active_prediction"]

                # 2. Check Result of Active Prediction
                if state["waiting_result"] and active_pred:
                    target_issue = str(active_pred["issue"])

                    # Did target_issue finish? Look in recent items
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
                    # Determine next issue
                    next_issue = lottery_api.get_next_issue(latest_issue)

                    if state["last_processed_issue"] != next_issue:
                        # Check if any active channels exist for this game
                        active_channels = db_manager.get_channels_by_game(game_id, only_active=True)
                        if not active_channels:
                            # No channels subscribed to this game, wait
                            await asyncio.sleep(poll_interval)
                            continue

                        # Run AI prediction
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

                        # Place automated demo bet in background
                        if bet_automation.enabled and bet_automation.is_logged_in:
                            asyncio.create_task(bet_automation.place_bet(game_id, pred_data["choice"]))

                        # Send new individual prediction message to each channel
                        await self._broadcast_prediction(game_id, pred_data, active_channels)

                        state["active_prediction"] = pred_data
                        state["waiting_result"] = True
                        state["last_processed_issue"] = next_issue

                        # Save to database
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

        for ch in channels:
            channel_id = ch["channel_id"]
            curr_level = ch.get("current_level", 1)
            reg_link = ch.get("register_link", config.DEFAULT_REGISTER_LINK)
            promo = ch.get("promo_text", config.DEFAULT_PROMO_TEXT)

            text = render_prediction_card(
                game_name=game_name,
                issue_number=pred_data["issue"],
                choice=pred_data["choice"],
                numbers=pred_data["numbers"],
                confidence=pred_data["confidence"],
                level=curr_level,
                pattern_name=pred_data["pattern_name"],
                promo_text=promo
            )

            reply_markup = get_channel_post_keyboard(reg_link)

            try:
                await self.bot.send_message(
                    chat_id=channel_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    disable_web_page_preview=True
                )
                logger.info(f"✅ Signal posted to channel {channel_id}")
            except TelegramError as te:
                logger.error(f"❌ Failed to send prediction to {channel_id}: {te}")
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
        """Sends separate WIN celebration or LOSS recovery notification to channels"""
        channels = db_manager.get_channels_by_game(game_id, only_active=True)
        game_cfg = config.WINGO_GAMES[game_id]
        game_name = game_cfg["name"]

        for ch in channels:
            channel_id = ch["channel_id"]
            reg_link = ch.get("register_link", config.DEFAULT_REGISTER_LINK)

            # Update stats & level in database
            stats, next_level = db_manager.record_channel_result(channel_id, is_win)
            curr_level = ch.get("current_level", 1)
            streak = stats.get("current_streak", 1)

            reply_markup = get_channel_post_keyboard(reg_link)

            try:
                if is_win:
                    win_text = render_win_card(
                        game_name=game_name,
                        issue_number=issue_number,
                        actual_choice=actual_choice,
                        actual_number=actual_number,
                        level=curr_level,
                        streak=streak,
                        hit_lucky_number=hit_lucky_number
                    )

                    # 1. Try real in-game screenshot from demo account
                    screenshot_bytes = None
                    if bet_automation.enabled and bet_automation.is_logged_in:
                        try:
                            screenshot_bytes = await bet_automation.capture_win_screenshot(game_id, issue_number)
                        except Exception as e:
                            logger.error(f"Failed to capture real game screenshot: {e}")

                    # 2. If real screenshot unavailable, fallback to HD card generator
                    if not screenshot_bytes:
                        try:
                            screenshot_bytes = generate_win_result_card(
                                game_name=game_name,
                                issue_number=issue_number,
                                choice=pred_choice,
                                actual_number=actual_number,
                                level=curr_level,
                                streak=streak
                            )
                        except Exception as img_err:
                            logger.warning(f"Failed to generate card image: {img_err}")

                    # 3. Send photo if available, otherwise send text
                    if screenshot_bytes:
                        await self.bot.send_photo(
                            chat_id=channel_id,
                            photo=screenshot_bytes,
                            caption=win_text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup
                        )
                    else:
                        await self.bot.send_message(
                            chat_id=channel_id,
                            text=win_text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=reply_markup,
                            disable_web_page_preview=True
                        )
                else:
                    loss_text = render_loss_card(
                        game_name=game_name,
                        issue_number=issue_number,
                        actual_choice=actual_choice,
                        actual_number=actual_number,
                        curr_level=curr_level,
                        next_level=next_level
                    )
                    await self.bot.send_message(
                        chat_id=channel_id,
                        text=loss_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=reply_markup,
                        disable_web_page_preview=True
                    )

            except TelegramError as te:
                logger.error(f"❌ Failed to send result to channel {channel_id}: {te}")
            except Exception as e:
                logger.error(f"❌ Error broadcasting result to {channel_id}: {e}")
