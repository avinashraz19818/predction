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

# Real WinGo DOM Selectors from battle-tested smex engine
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
BET_AGREE_SELECTOR = ".agreement div[role='checkbox'], .agreement .van-checkbox, .Betting__Popup-agree"
TOAST_FAIL_SELECTOR = ".van-toast--fail, .van-toast:has-text('insufficient'), .van-toast:has-text('fail'), .van-toast:has-text('parameter')"
WIN_DIALOG_SELECTOR = ".winning:not([style*='display: none']), .winning-body.isWin, .winning-wrap-l1.isWin, .WinningTip__C"

LOGIN_PHONE_SELECTOR = "input[name='userNumber'], input[placeholder*='phone'], input[placeholder*='Phone'], input[type='tel']"
LOGIN_PASS_SELECTOR = "input[type='password']"
LOGIN_SUBMIT_SELECTOR = "button:has-text('Log in'), button:has-text('Login'), .signIn__container-button button, .login-btn, button[type='submit']"

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
    Playwright-based real human-like game player and win-popup screenshot capture engine (smex pattern).
    Flow: Real Login -> Close Popups -> Open Game via Menu -> Place Bet -> Fast Polling -> Real Screenshot.
    """

    def __init__(self):
        self.enabled = config.DEMO_AUTO_BET
        self.login_url = config.DEMO_LOGIN_URL or "https://bdgwina.biz/#/login"
        self.username = config.DEMO_USERNAME or "6556745550"
        self.password = config.DEMO_PASSWORD or "win1222"
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

    def _home_url(self) -> str:
        base = self.login_url.split("#", 1)[0].rstrip("/")
        return f"{base}/#/"

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
        """Launches Playwright persistent browser context and signs in like a real user"""
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

                # Execute Step-by-Step real user navigation from smex
                ok = await self.open_room_step_by_step("wingo_1m")
                if ok:
                    self.is_ready = True
                    logger.info("🎯 Real Browser is logged in and ready on WinGo game board!")
                    return True
                else:
                    logger.warning("⚠️ Room not open yet; will retry on next round.")
                    return False

            except Exception as e:
                logger.error(f"❌ Playwright initialization error: {e}", exc_info=True)
                await self.close()
                return False

    # ------------------------------------------------------------------ #
    #  Real human-like login & popups (smex logic)
    # ------------------------------------------------------------------ #

    async def is_logged_out(self) -> bool:
        """Checks if session expired or user is logged out (smex logic)"""
        if not self.page:
            return True
        try:
            # Check expired toast
            expired_toast = self.page.locator(".van-toast:has-text('expired'), .van-toast:has-text('login')").first
            if await expired_toast.is_visible(timeout=700):
                return True

            curr = self.page.url or ""
            if "#/login" in curr:
                return True

            phone_inp = self.page.locator(LOGIN_PHONE_SELECTOR).first
            if await phone_inp.is_visible(timeout=700):
                return True

            # If board visible, user is logged in
            board = self.page.locator(PERIOD_SELECTOR).first
            if await board.is_visible(timeout=700):
                return False

            # Check guest login button
            guest_btn = self.page.locator(".p8-home__guest-btn--login, button:has-text('Log in')").first
            if await guest_btn.is_visible(timeout=700):
                return True
        except Exception:
            pass
        return False

    async def dismiss_announcements(self):
        """Auto-close password change popups & floating banners (smex logic)"""
        if not self.page:
            return
        try:
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

    async def setup_lottery_token(self):
        """Sets internal localStorage keys so lottery room authenticates instantly (smex logic)"""
        if not self.page:
            return
        try:
            await self.page.evaluate("""() => {
                let urlStr = localStorage.getItem('lotteryLoginUrl');
                if (urlStr) {
                    try {
                        let u = new URL(urlStr);
                        let token = u.searchParams.get("Token");
                        let skin = u.searchParams.get("Skin") || "";
                        let lang = u.searchParams.get("Lang") || "en";

                        localStorage.setItem("ar_token", JSON.stringify({ value: token, expires: -1 }));
                        localStorage.setItem("ar_api", JSON.stringify({ value: "https://h5.ar-lottery06.com", expires: -1 }));
                        localStorage.setItem("ar_api_json", JSON.stringify({ value: "https://draw.ar-lottery06.com", expires: -1 }));
                        localStorage.setItem("ar_lang", JSON.stringify({ value: lang, expires: -1 }));
                        localStorage.setItem("ar_skin", JSON.stringify({ value: skin, expires: -1 }));
                    } catch(e) {}
                }
            }""")
        except Exception:
            pass

    async def ensure_logged_in(self) -> bool:
        """Enters phone and password like a real user and logs in"""
        if not self.page:
            return False

        await self.dismiss_announcements()
        await asyncio.sleep(0.5)

        logged_out = await self.is_logged_out()
        curr = self.page.url or ""

        if not logged_out and "#/login" not in curr:
            return True

        logger.info(f"🔑 Real User Login: Navigating to {self.login_url}...")
        try:
            if "#/login" not in curr:
                await self.page.goto(self.login_url, wait_until="domcontentloaded", timeout=25000)
                await asyncio.sleep(2.5)

            await self.dismiss_announcements()

            phone_field = self.page.locator(LOGIN_PHONE_SELECTOR).first
            await phone_field.wait_for(state="visible", timeout=12000)
            await phone_field.fill(self.username)
            logger.info(f"👉 Entered Mobile Number: {self.username}")
            await asyncio.sleep(0.3)

            pwd_field = self.page.locator(LOGIN_PASS_SELECTOR).first
            await pwd_field.wait_for(state="visible", timeout=6000)
            await pwd_field.fill(self.password)
            logger.info("👉 Entered Password")
            await asyncio.sleep(0.4)

            # Remember me checkbox
            try:
                rem_cb = self.page.locator(".signIn__container-rememberRow .van-checkbox").first
                if await rem_cb.is_visible(timeout=800):
                    await rem_cb.click()
            except Exception:
                pass

            # Click Submit
            submit = self.page.locator(LOGIN_SUBMIT_SELECTOR).first
            await submit.wait_for(state="visible", timeout=6000)
            await submit.click()
            logger.info("👉 Clicked Login Button! Waiting for home page...")
            await asyncio.sleep(4.0)

            # Wait for login loader
            try:
                loader = self.page.locator(".ar-loading-view").first
                await loader.wait_for(state="hidden", timeout=8000)
            except Exception:
                pass

            await self.dismiss_announcements()
            return True
        except Exception as e:
            logger.error(f"❌ Real login error: {e}")
            return False

    async def open_room_step_by_step(self, game_id: str = "wingo_1m") -> bool:
        """
        Executes the exact real human user navigation flow:
        Step 1: Check login & log in with credentials
        Step 2: Home page & dismiss welcome announcement
        Step 3: Click 'Lottery' button or open SaasLottery room
        Step 4: Select 1Min game tab
        Step 5: Confirm WinGo Period is visible on board
        """
        if not self.page:
            return False

        # Step 1: Login
        logger.info("🧭 [1/5] Checking account login status...")
        logged_out = await self.is_logged_out()
        if logged_out:
            logger.info("🧭 [1/5] Not logged in — filling credentials...")
            await self.ensure_logged_in()

        # Step 2: Home Page
        logger.info("🧭 [2/5] Opening Home page...")
        try:
            home = self._home_url()
            await self.page.goto(home, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(2.0)
            await self.dismiss_announcements()
            await self.setup_lottery_token()
        except Exception as e:
            logger.warning(f"Home page warning: {e}")

        # Step 3: Open WinGo Room
        room_url = self._get_game_url(game_id)
        logger.info(f"🧭 [3/5] Opening WinGo Room: {room_url}...")
        try:
            await self.page.goto(room_url, wait_until="domcontentloaded", timeout=25000)
            await asyncio.sleep(3.0)
            await self.dismiss_announcements()

            # If direct URL did not open board, click Lottery button from menu like a human
            board_loc = self.page.locator(PERIOD_SELECTOR).first
            if not await board_loc.is_visible(timeout=3000):
                logger.info("👉 Clicking 'Lottery' icon from home screen...")
                lottery_btn = self.page.locator("text='Lottery', [class*='Lottery']").first
                if await lottery_btn.is_visible(timeout=2000):
                    await lottery_btn.click(force=True)
                    await asyncio.sleep(2.0)
                    await self.page.goto(room_url, wait_until="domcontentloaded", timeout=20000)
                    await asyncio.sleep(2.5)
        except Exception as e:
            logger.warning(f"Room open warning: {e}")

        # Step 4: Ensure WinGo Tab is selected
        logger.info("🧭 [4/5] Selecting WinGo 1Min tab...")
        try:
            tab = self.page.locator(GAME_ITEM_SELECTOR).filter(has_text=re.compile(r"1\s*Min", re.I)).first
            if await tab.is_visible(timeout=1500):
                await tab.click(force=True)
                await asyncio.sleep(1.0)
        except Exception:
            pass

        # Step 5: Check Period
        logger.info("🧭 [5/5] Checking WinGo board...")
        try:
            board_loc = self.page.locator(PERIOD_SELECTOR).first
            if await board_loc.is_visible(timeout=4000):
                period_text = (await board_loc.inner_text()).strip()
                logger.info(f"✅ [5/5] WinGo Board Live & Ready! Current Period: {period_text}")
                return True
        except Exception:
            pass

        logger.info("ℹ️ WinGo board ready.")
        return True

    # ------------------------------------------------------------------ #
    #  Real Bet Placement & Real Win Popup Capture
    # ------------------------------------------------------------------ #

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
                # Dismiss modals before clicking
                await self.dismiss_announcements()

                target_text = "Big" if choice.upper() == "BIG" else "Small"
                target_locator = self.page.locator(
                    f"button:has-text('{target_text}'), div:has-text('{target_text}'):not(:has(div)), .Betting__C-foot-b, .bet-btn-big"
                    if choice.upper() == "BIG"
                    else f"button:has-text('{target_text}'), div:has-text('{target_text}'):not(:has(div)), .Betting__C-foot-s, .bet-btn-small"
                ).first

                clicked = False
                if await target_locator.is_visible(timeout=3000):
                    await target_locator.click(force=True)
                    clicked = True
                else:
                    # Fallback: Click on lucky number ball (e.g. 7 for Big, 2 for Small)
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
                    await self.dismiss_announcements()

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
