import io
import logging
from typing import Optional

from services.playwright_worker import playwright_worker

logger = logging.getLogger(__name__)

class BetAutomationService:
    """
    Playwright Real Game Automation Service:
    - Real bet placement on live game board (WinGo).
    - 100% Real browser screen capture of the native 'Congratulations' Winning Popup.
    - Captures real game board & My History table if popup auto-closed.
    - ZERO fake canvas/Pillow drawings.
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
        Captures 100% genuine live screenshot directly from the headless browser:
        1. First tries to capture the real on-screen native 'Congratulations' Winning Popup.
        2. If popup closed, captures the real game screen with the updated balance & history table.
        3. Never generates or sends any fake canvas drawings.
        """
        if not self.worker.is_ready:
            logger.info("ℹ️ Browser not yet initialized/ready; re-initializing...")
            try:
                await self.worker.initialize()
            except Exception as e:
                logger.warning(f"Re-init warning: {e}")

        if not self.worker.is_ready:
            logger.warning("⚠️ Real browser is not connected to the game. Skipping screenshot (no fake images will be sent).")
            return None

        # 1. Real Playwright Winning Popup capture
        try:
            real_popup_shot = await self.worker.capture_real_win_popup(
                game_id=game_id,
                issue_number=target_issue,
                choice=choice,
                timeout_seconds=14.0
            )
            if real_popup_shot:
                logger.info(f"📸 100% Real Playwright Winning Popup captured for period {target_issue}!")
                return real_popup_shot
        except Exception as e:
            logger.warning(f"Winning popup capture warning: {e}")

        # 2. Real Playwright Game Board Capture (shows real wallet balance + real My History row)
        try:
            logger.info(f"📸 Capturing real live game board & history table for period {target_issue}...")
            real_board_shot = await self.worker.capture_board_screenshot(game_id=game_id)
            if real_board_shot:
                return real_board_shot
        except Exception as e:
            logger.error(f"Board screenshot error: {e}")

        return None

    async def close(self):
        await self.worker.close()

bet_automation = BetAutomationService()
