import io
import logging
from typing import Optional

from services.playwright_worker import playwright_worker
from bot.card_generator import generate_win_result_card

logger = logging.getLogger(__name__)

class BetAutomationService:
    """
    Seamless interface that coordinates:
    1. Real Playwright automated bet placement & real win-popup screenshot capture.
    2. Instant high-resolution fallback rendering via card_generator if browser is offline.
    """

    def __init__(self):
        self.worker = playwright_worker

    @property
    def enabled(self) -> bool:
        return self.worker.enabled

    @property
    def is_logged_in(self) -> bool:
        return self.worker.is_ready

    async def initialize(self) -> bool:
        return await self.worker.initialize()

    async def place_bet(self, game_id: str, choice: str, issue_number: str = "") -> bool:
        res = await self.worker.place_bet(game_id, choice, issue_number)
        return res.get("ok", False)

    async def capture_win_screenshot(
        self,
        game_id: str,
        target_issue: str,
        choice: str = "BIG",
        actual_number: int = 7,
        level: int = 1,
        streak: int = 1
    ) -> Optional[io.BytesIO]:
        """
        Attempts real live Playwright screen capture of the native game winning popup.
        If browser is not ready or popup didn't fire, seamlessly falls back to authentic
        BDGWin canvas generator.
        """
        # 1. Try real Playwright popup capture
        if self.worker.is_ready:
            try:
                real_shot = await self.worker.capture_real_win_popup(
                    game_id=game_id,
                    issue_number=target_issue,
                    choice=choice,
                    timeout_seconds=12.0
                )
                if real_shot:
                    logger.info(f"📸 Real Playwright Winning Popup captured for issue {target_issue}!")
                    return real_shot
            except Exception as e:
                logger.warning(f"Real popup capture skipped: {e}")

        # 2. Seamless Fallback Generator
        try:
            logger.info(f"🎨 Generating authentic BDGWin Win Card for issue {target_issue}...")
            return generate_win_result_card(
                game_name="WinGo 1M" if "1m" in game_id else "WinGo",
                issue_number=target_issue,
                choice=choice,
                actual_number=actual_number,
                level=level,
                streak=streak
            )
        except Exception as gen_err:
            logger.error(f"Fallback generation error: {gen_err}")
            return None

    async def close(self):
        await self.worker.close()

bet_automation = BetAutomationService()
