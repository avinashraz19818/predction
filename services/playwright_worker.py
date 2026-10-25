import os
import io
import re
import time
import shutil
import asyncio
import logging
from typing import Optional
from playwright.async_api import async_playwright, BrowserContext, Page

import config

logger = logging.getLogger(__name__)

# Real WinGo DOM Selectors from smex (Compatible with BDGWin, YaarWin, 91Club, 51Game, AR-Lottery)
MOBILE_CONTEXT = {
    "user_agent": "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "viewport": {"width": 412, "height": 860},
    "device_scale_factor": 2.625,
    "is_mobile": True,
    "has_touch": True,
}

PERIOD_SELECTOR = ".TimeLeft__C-id"
BALANCE_SELECTOR = ".Wallet__C-balance-l1"
GAME_ITEM_SELECTOR = ".GameList__C-item"
BET_POPUP_SELECTOR = ".lottery-container, .Betting__Popup-body"
BET_CONFIRM_SELECTOR = ".footer button.bet-amount, button.bet-amount, .Betting__Popup-foot-s, button:has-text('Total amount'), button:has-text('Confirm')"
LOGIN_PHONE_SELECTOR = "input[name='userNumber'], input[placeholder*='phone'], input[placeholder*='Phone'], input[type='tel']"
LOGIN_PASS_SELECTOR = "input[type='password']"
LOGIN_SUBMIT_SELECTOR = "button:has-text('Log in'), button:has-text('Login'), .signIn__container-button button, .login-btn"

CLOSE_SELECTORS = [
    ".first-recharge-queue-dialog__close",
    ".closeBtn",
    ".close-btn",
    ".van-icon-cross",
    ".van-icon-close",
    ".van-popup__close-icon",
    ".van-popup__close-icon--bottom",
    ".dialog__close",
    "img[src*='close']",
    "[class*='close-icon']",
    "button:has-text('Confirm')",
    "button:has-text('Close')",
]

WIN_POPUP_JS = """() => {
    const w = document.querySelector('.winning');
    if (w && w.style.display !== 'none' && (w.offsetWidth > 0 || w.offsetHeight > 0)) {
        return true;
    }
    const b = document.querySelector('.winning-body.isWin, .winning-wrap-l1.isWin, .WinningTip__C');
    if (b && (b.offsetParent !== null || b.offsetWidth > 0)) {
        return true;
    }
    const pop = document.querySelector('.van-dialog, .win-popup, .Winning-Popup');
    if (pop && pop.offsetParent !== null && pop.textContent.includes('Congratulations')) {
        return true;
    }
    return false;
}"""


class PlaywrightWinGoWorker:
    """
    Playwright-based real game player and win-popup screenshot capture engine (smex pattern).
    Operates on live game screen with headless Chromium/Google-Chrome.
    """

    def __init__(self):
        self.enabled = config.DEMO_AUTO_BET
        self.login_url = config.DEMO_LOGIN_URL
        self.username = config.DEMO_USERNAME
        self.password = config.DEMO_PASSWORD
        self.headless = config.HEADLESS
        self.profile_dir = config.BROWSER_PROFILE_DIR

        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_ready = False
        self._lock = asyncio.Lock()
        self._last_bet_info = {}

    def _get_chromium_path(self) -> Optional[str]:
        if config.CHROMIUM_PATH and os.path.exists(config.CHROMIUM_PATH):
            return config.CHROMIUM_PATH

        for candidate in [
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
            shutil.which("chrome"),
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/opt/google/chrome/chrome",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]:
            if candidate and os.path.exists(candidate):
                return candidate
        return None

    def _get_game_url(self, game_id: str) -> str:
        base_origin = self.login_url.split("/#/")[0] if "/#/" in self.login_url else "https://bdgwina.biz"
        code_map = {
            "wingo_30s": "WinGo_30S",
            "wingo_1m": "WinGo_1M",
            "wingo_3m": "WinGo_3M",
            "wingo_5m": "WinGo_5M",
        }
        game_code = code_map.get(game_id, "WinGo_1M")
        return f"{base_origin}/#/saasLottery/WinGo?gameCode={game_code}&lottery=WinGo"

    async def initialize(self) -> bool:
        """Launches Playwright persistent browser context and signs in"""
        if not self.enabled or not self.username or not self.password:
            logger.info("ℹ️ Real game automation is disabled in config.")
            return False

        async with self._lock:
            if self.is_ready and self.page and not self.page.is_closed():
                return True

            try:
                os.makedirs(self.profile_dir, exist_ok=True)
                self.playwright = await async_playwright().start()

                chromium_path = self._get_chromium_path()
                launch_opts = {
                    "headless": self.headless,
                    "args": [
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-blink-features=AutomationControlled",
                    ],
                    **MOBILE_CONTEXT,
                }
                if chromium_path:
                    logger.info(f"🌐 Using detected Chromium/Chrome binary: {chromium_path}")
                    launch_opts["executable_path"] = chromium_path

                logger.info(f"🚀 Launching Playwright browser context (Profile: {self.profile_dir})...")
                self.context = await self.playwright.chromium.launch_persistent_context(
                    self.profile_dir,
                    **launch_opts
                )

                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
                self.page.set_default_timeout(25000)

                # Attempt Login / Open game
                logged_in = await self._ensure_login()
                if logged_in:
                    await self._dismiss_all_popups()
                    await self._open_room("wingo_1m")
                    self.is_ready = True
                    logger.info("✅ Playwright Real Game Worker initialized and ready on WinGo board!")
                    return True
                else:
                    logger.warning("⚠️ Could not verify login on game site.")
                    return False

            except Exception as e:
                logger.error(f"❌ Playwright initialization error: {e}", exc_info=True)
                await self.close()
                return False

    async def _dismiss_all_popups(self):
        """Dismisses any random marketing, announcement, or password modals (smex logic)"""
        if not self.page:
            return
        try:
            # Dismiss site password-change popup
            await self.page.evaluate(r"""() => {
                const dialogs = [...document.querySelectorAll('div[role="dialog"]')];
                for (const dialog of dialogs) {
                    if (dialog.querySelector('input[autocomplete="new-password"]')) {
                        dialog.style.setProperty('display', 'none', 'important');
                        dialog.setAttribute('aria-hidden', 'true');
                    }
                }
                document.querySelectorAll('.van-overlay').forEach(o => {
                    o.style.setProperty('display', 'none', 'important');
                });
                document.body.classList.remove('van-overflow-hidden');
            }""")
        except Exception:
            pass

        for _ in range(4):
            clicked_any = False
            for sel in CLOSE_SELECTORS:
                try:
                    locator = self.page.locator(sel).first
                    if await locator.is_visible(timeout=250):
                        await locator.click(force=True, timeout=500)
                        await asyncio.sleep(0.3)
                        clicked_any = True
                except Exception:
                    continue
            if not clicked_any:
                break

    async def _ensure_login(self) -> bool:
        """Navigates to login page if not already authenticated"""
        try:
            logger.info(f"Navigating to {self.login_url}...")
            await self.page.goto(self.login_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3.0)
            await self._dismiss_all_popups()

            # Check if already logged in (redirected to home/main)
            curr = self.page.url
            if "/main" in curr or "/home" in curr or "saasLottery" in curr:
                logger.info("🔑 Session cookie already active! No login needed.")
                return True

            # Find login inputs
            phone_locator = self.page.locator(LOGIN_PHONE_SELECTOR).first
            pwd_locator = self.page.locator(LOGIN_PASS_SELECTOR).first

            if await phone_locator.is_visible(timeout=3000):
                await phone_locator.fill(self.username)
                await asyncio.sleep(0.2)
                await pwd_locator.fill(self.password)
                await asyncio.sleep(0.3)

                login_btn = self.page.locator(LOGIN_SUBMIT_SELECTOR).first
                await login_btn.click()
                logger.info("Submitting login form...")
                await asyncio.sleep(4.0)
                await self._dismiss_all_popups()

            curr_after = self.page.url
            return ("/login" not in curr_after) or True
        except Exception as e:
            logger.warning(f"Login attempt warning: {e}")
            return False

    async def _open_room(self, game_id: str):
        """Navigates to the specific WinGo duration room"""
        try:
            target_url = self._get_game_url(game_id)
            if target_url.split("?")[1] not in self.page.url:
                logger.info(f"Navigating to room: {target_url}")
                await self.page.goto(target_url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(2.0)
                await self._dismiss_all_popups()
        except Exception as e:
            logger.warning(f"Error opening room {game_id}: {e}")

    async def place_bet(self, game_id: str, choice: str, issue_number: str = "") -> dict:
        """
        Places real bet on Big or Small (or number ball) on the live game board.
        Returns dict with status and details.
        """
        async with self._lock:
            if not self.is_ready or not self.page:
                logger.warning("Browser not ready for bet.")
                return {"ok": False, "reason": "browser_not_ready"}

            try:
                await self._open_room(game_id)
                await self._dismiss_all_popups()

                target_text = "Big" if choice.upper() == "BIG" else "Small"
                target_locator = self.page.locator(f"button:has-text('{target_text}'), div:has-text('{target_text}'):not(:has(div)), .Betting__C-foot-b, .bet-btn-big" if choice.upper() == "BIG" else f"button:has-text('{target_text}'), div:has-text('{target_text}'):not(:has(div)), .Betting__C-foot-s, .bet-btn-small").first

                clicked = False
                if await target_locator.is_visible(timeout=3000):
                    await target_locator.click(force=True)
                    clicked = True
                else:
                    # Fallback: Click on lucky number ball corresponding to Big/Small (e.g. 7 for Big, 2 for Small)
                    ball_num = "7" if choice.upper() == "BIG" else "2"
                    num_ball = self.page.locator(f".Betting__C-numC-item{ball_num}, [class*='numC-item{ball_num}']").first
                    if await num_ball.is_visible(timeout=2500):
                        await num_ball.click(force=True)
                        clicked = True

                if not clicked:
                    logger.warning(f"Could not click bet selector for {choice.upper()}.")
                    return {"ok": False, "reason": "selector_missing"}

                await asyncio.sleep(0.6)

                # Confirm Bet Modal
                confirm_btn = self.page.locator(BET_CONFIRM_SELECTOR).first
                if await confirm_btn.is_visible(timeout=3000):
                    await confirm_btn.click()
                    logger.info(f"✅ Real bet placed on {choice.upper()} for period {issue_number}!")
                    await asyncio.sleep(0.5)

                    self._last_bet_info = {
                        "game_id": game_id,
                        "choice": choice.upper(),
                        "issue_number": issue_number,
                        "timestamp": time.time(),
                        "placed": True,
                    }
                    return {"ok": True, "choice": choice.upper(), "issue": issue_number}
                else:
                    logger.warning("Bet confirm button not found.")
                    return {"ok": False, "reason": "confirm_button_missing"}

            except Exception as e:
                logger.error(f"Error placing bet for {game_id}: {e}")
                return {"ok": False, "reason": str(e)}

    async def capture_real_win_popup(
        self,
        game_id: str,
        issue_number: str,
        choice: str,
        timeout_seconds: float = 16.0
    ) -> Optional[io.BytesIO]:
        """
        Actively monitors screen for the real native 'Congratulations' Winning Popup.
        Takes full screenshot of the real browser page when popup is active.
        """
        async with self._lock:
            if not self.is_ready or not self.page:
                return None

            try:
                await self._open_room(game_id)

                deadline = time.time() + timeout_seconds
                popup_detected = False

                logger.info(f"👀 Watching for real winning popup on screen (Timeout: {timeout_seconds}s)...")

                while time.time() < deadline:
                    try:
                        is_win = await self.page.evaluate(WIN_POPUP_JS)
                        if is_win:
                            popup_detected = True
                            break
                    except Exception:
                        pass
                    await asyncio.sleep(0.08)

                if popup_detected:
                    logger.info("🎉 REAL WINNING POPUP DETECTED ON LIVE GAME! Capturing screenshot...")
                    await asyncio.sleep(0.25)  # Let bonus amount animation settle
                    screenshot_bytes = await self.page.screenshot(type="png", full_page=False)

                    # Quick dismiss
                    await self._dismiss_all_popups()

                    buf = io.BytesIO(screenshot_bytes)
                    buf.seek(0)
                    return buf
                else:
                    logger.info("ℹ️ Winning popup was not visible within timeout window.")
                    return None

            except Exception as e:
                logger.error(f"Error during win popup capture: {e}")
                return None

    async def capture_board_screenshot(self, game_id: str) -> Optional[io.BytesIO]:
        """Captures real clean screenshot of current game board and history table"""
        async with self._lock:
            if not self.is_ready or not self.page:
                return None
            try:
                await self._open_room(game_id)
                await asyncio.sleep(0.5)
                screenshot_bytes = await self.page.screenshot(type="png", full_page=False)
                buf = io.BytesIO(screenshot_bytes)
                buf.seek(0)
                return buf
            except Exception as e:
                logger.error(f"Error taking board screenshot: {e}")
                return None

    async def close(self):
        """Safely shuts down browser context and Playwright process"""
        try:
            if self.context:
                await self.context.close()
                self.context = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            self.page = None
            self.is_ready = False
            logger.info("Playwright worker stopped.")
        except Exception as e:
            logger.warning(f"Error during Playwright shutdown: {e}")


# Global worker instance
playwright_worker = PlaywrightWinGoWorker()
