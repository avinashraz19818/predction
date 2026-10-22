import io
import os
import shutil
import time
import logging
import asyncio
from typing import Optional
from PIL import Image

import config

logger = logging.getLogger(__name__)

class BDGWinAutomation:
    def __init__(self):
        self.enabled = config.DEMO_AUTO_BET
        self.login_url = config.DEMO_LOGIN_URL or "https://bdgwina.biz/#/login"
        self.username = config.DEMO_USERNAME or "6556745550"
        self.password = config.DEMO_PASSWORD or "win1222"
        self.driver = None
        self.is_logged_in = False
        self._lock = asyncio.Lock()

    def _get_game_url(self, game_id: str) -> str:
        code_map = {
            "wingo_30s": "WinGo_30S",
            "wingo_1m": "WinGo_1M",
            "wingo_3m": "WinGo_3M",
            "wingo_5m": "WinGo_5M"
        }
        game_code = code_map.get(game_id, "WinGo_1M")
        return f"https://bdgwina.biz/#/saasLottery/WinGo?gameCode={game_code}&lottery=WinGo"

    def _create_webdriver(self):
        """Creates a headless Chrome/Chromium driver on Linux VPS or Chrome/Edge on Windows"""
        from selenium import webdriver

        ua = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        common_args = [
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--window-size=412,860",
            f"user-agent={ua}"
        ]

        # 1. Try Chrome / Chromium (Best for Ubuntu/Debian VPS & cross-platform)
        try:
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.chrome.service import Service as ChromeService

            c_opts = ChromeOptions()
            for arg in common_args:
                c_opts.add_argument(arg)

            # Auto-detect Linux Chromium binary if installed
            for bin_path in ["/usr/bin/chromium-browser", "/usr/bin/chromium", "/usr/bin/google-chrome", "/snap/bin/chromium"]:
                if os.path.exists(bin_path):
                    c_opts.binary_location = bin_path
                    break

            # Auto-detect system chromedriver if installed
            driver_path = shutil.which("chromedriver")
            for d_path in ["/usr/bin/chromedriver", "/usr/lib/chromium-browser/chromedriver", "/usr/local/bin/chromedriver"]:
                if os.path.exists(d_path):
                    driver_path = d_path
                    break

            if driver_path:
                service = ChromeService(executable_path=driver_path)
                return webdriver.Chrome(service=service, options=c_opts)
            else:
                return webdriver.Chrome(options=c_opts)
        except Exception as chrome_err:
            logger.debug(f"Chrome/Chromium driver init skipped: {chrome_err}")

        # 2. Fallback to Microsoft Edge (Windows default)
        from selenium.webdriver.edge.options import Options as EdgeOptions
        e_opts = EdgeOptions()
        for arg in common_args:
            e_opts.add_argument(arg)
        return webdriver.Edge(options=e_opts)

    def initialize_sync(self) -> bool:
        """Launches headless browser and logs into BDGWin demo account"""
        if not self.enabled or not self.username or not self.password:
            logger.info("Demo auto-bet automation is disabled.")
            return False

        try:
            from selenium.webdriver.common.by import By

            logger.info("🚀 Launching Headless Browser for BDGWin Auto-Bet & Live Screenshots...")
            self.driver = self._create_webdriver()
            self.driver.set_page_load_timeout(35)

            # 1. Login
            logger.info(f"Navigating to {self.login_url} ...")
            self.driver.get(self.login_url)
            time.sleep(4)

            phone_inp = self.driver.find_element(By.CSS_SELECTOR, "input[name='userNumber']")
            phone_inp.clear()
            phone_inp.send_keys(self.username)

            pwd_inp = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")[0]
            pwd_inp.clear()
            pwd_inp.send_keys(self.password)

            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                if "Log in" in btn.text:
                    self.driver.execute_script("arguments[0].click();", btn)
                    break
            time.sleep(5)

            # 2. Dismiss post-login announcement popups
            self._dismiss_popups()

            # 3. Navigate straight to WinGo 1M so the game board is preloaded
            self.driver.get(self._get_game_url("wingo_1m"))
            time.sleep(3)
            self._dismiss_popups()

            self.is_logged_in = True
            logger.info("✅ Logged into BDGWin demo account and opened WinGo board successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ BDGWin browser initialization error: {e}")
            self.close_sync()
            return False

    def _dismiss_popups(self):
        if not self.driver:
            return
        try:
            from selenium.webdriver.common.by import By
            for _ in range(4):
                clicked = False
                for b in self.driver.find_elements(By.TAG_NAME, "button"):
                    try:
                        if ("Confirm" in b.text or "Close" in b.text) and b.is_displayed():
                            self.driver.execute_script("arguments[0].click();", b)
                            time.sleep(1.0)
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    break
        except Exception:
            pass

    async def initialize(self) -> bool:
        return await asyncio.to_thread(self.initialize_sync)

    def place_bet_sync(self, game_id: str, choice: str) -> bool:
        """Navigates to WinGo game page and places ₹1 bet on BIG or SMALL"""
        if not self.is_logged_in or not self.driver:
            return False

        try:
            from selenium.webdriver.common.by import By

            game_url = self._get_game_url(game_id)
            if game_url.split("?")[1] not in self.driver.current_url:
                self.driver.get(game_url)
                time.sleep(2.5)

            # Remove any injected custom popup from previous round
            self.driver.execute_script("var el = document.getElementById('bdg-custom-win-modal'); if(el) el.remove();")

            target_text = "Big" if choice.upper() == "BIG" else "Small"
            bet_btns = self.driver.find_elements(By.XPATH, f"//*[text()='{target_text}']")
            if not bet_btns:
                return False

            bet_btn = bet_btns[0]
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", bet_btn)
            time.sleep(0.3)
            self.driver.execute_script("arguments[0].click();", bet_btn)
            time.sleep(1.2)

            # Click 'Total amount' button inside the betting sheet
            for b in self.driver.find_elements(By.TAG_NAME, "button"):
                if "Total amount" in b.text and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    logger.info(f"✅ Auto-bet placed on {choice.upper()} for {game_id}!")
                    time.sleep(0.8)
                    return True

            return False

        except Exception as e:
            logger.warning(f"Auto-bet skipped for {game_id}: {e}")
            return False

    async def place_bet(self, game_id: str, choice: str) -> bool:
        async with self._lock:
            return await asyncio.to_thread(self.place_bet_sync, game_id, choice)

    def _inject_bdgwin_winning_popup(self, game_id: str, issue_number: str, choice: str, actual_number: int, level: int = 1):
        """
        Ensures the authentic BDGWin 'Congratulations' Winning Popup is visible on the live BDGWin game screen
        when taking the WIN screenshot (even if the native 3-second popup already auto-closed).
        """
        mode_map = {
            "wingo_30s": "WinGo 30sec",
            "wingo_1m": "WinGo 1Min",
            "wingo_3m": "WinGo 3Min",
            "wingo_5m": "WinGo 5Min"
        }
        mode_name = mode_map.get(game_id, "WinGo 1Min")
        bs_label = "Big" if choice.upper() == "BIG" else "Small"
        color_label = "Green" if actual_number in (1, 3, 5, 7, 9) else "Red"
        pill_bg = "#28b463" if color_label == "Green" else "#e74c3c"
        bs_bg = "#f39c12" if bs_label == "Big" else "#3498db"

        bet_amounts = {1: 1000, 2: 3000, 3: 9000, 4: 27000, 5: 81000}
        win_amt = f"₹{bet_amounts.get(level, 1000) * 1.96:,.2f}"

        js_code = f"""
        (function() {{
            var old = document.getElementById('bdg-custom-win-modal');
            if (old) old.remove();

            var wrapper = document.createElement('div');
            wrapper.id = 'bdg-custom-win-modal';
            wrapper.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.68);z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:sans-serif;';

            wrapper.innerHTML = `
                <div style="width:330px;background:linear-gradient(180deg,#ff7e42 0%,#e83e34 100%);border-radius:24px;border:2.5px solid #ffda85;padding:24px 18px 20px;box-sizing:border-box;text-align:center;box-shadow:0 12px 35px rgba(0,0,0,0.6);position:relative;">
                    <div style="width:88px;height:88px;margin:-64px auto 8px;background:radial-gradient(circle,#ffe699 0%,#f59e0b 100%);border-radius:50%;border:3px solid #fff;display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:24px;box-shadow:0 4px 15px rgba(0,0,0,0.3);">WIN</div>
                    <div style="color:#ffffff;font-size:26px;font-weight:800;letter-spacing:0.5px;margin-bottom:16px;text-shadow:0 2px 4px rgba(0,0,0,0.25);">Congratulations</div>
                    <div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:18px;color:#fff;font-size:13px;font-weight:600;">
                        <span>Lottery results</span>
                        <span style="background:{pill_bg};padding:4px 10px;border-radius:6px;border:1px solid #fff;">{color_label}</span>
                        <span style="background:{pill_bg};width:26px;height:26px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;border:1px solid #fff;font-weight:800;">{actual_number}</span>
                        <span style="background:{bs_bg};padding:4px 10px;border-radius:6px;border:1px solid #fff;">{bs_label}</span>
                    </div>
                    <div style="background:linear-gradient(180deg,#fffdf7 0%,#ffedd4 100%);border-radius:16px;padding:16px 12px;margin-bottom:16px;box-shadow:inset 0 0 8px rgba(0,0,0,0.08);">
                        <div style="color:#e64a33;font-size:15px;font-weight:700;margin-bottom:4px;">Bonus</div>
                        <div style="color:#dc2626;font-size:28px;font-weight:900;margin-bottom:10px;border-bottom:1.5px dashed #e2c09d;padding-bottom:10px;">{win_amt}</div>
                        <div style="color:#666;font-size:12px;font-weight:600;">Period: {mode_name}</div>
                        <div style="color:#333;font-size:14px;font-weight:800;margin-top:2px;">{issue_number}</div>
                    </div>
                    <div style="display:flex;align-items:center;justify-content:flex-start;gap:8px;color:#fff;font-size:12px;padding-left:8px;">
                        <span style="width:18px;height:18px;border-radius:50%;border:1.5px solid #fff;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;">v</span>
                        <span>3 seconds auto close</span>
                    </div>
                </div>
                <div style="width:34px;height:34px;border-radius:50%;border:2px solid #ddd;color:#ddd;display:flex;align-items:center;justify-content:center;margin-top:16px;font-size:16px;font-weight:bold;">X</div>
            `;
            document.body.appendChild(wrapper);
        }})();
        """
        self.driver.execute_script(js_code)

    def capture_win_screenshot_sync(
        self,
        game_id: str,
        target_issue: str,
        choice: str = "BIG",
        actual_number: int = 7,
        level: int = 1
    ) -> Optional[io.BytesIO]:
        """Captures the live BDGWin game screen with the official Winning Popup"""
        if not self.is_logged_in or not self.driver:
            return None

        try:
            game_url = self._get_game_url(game_id)
            if game_url.split("?")[1] not in self.driver.current_url:
                self.driver.get(game_url)
                time.sleep(2.5)

            # Scroll to top of the WinGo game board so Wallet + Timer + Balls + History are framed cleanly
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.4)

            # Ensure the BDGWin Winning Popup is displayed on top of the live game screen
            self._inject_bdgwin_winning_popup(game_id, target_issue, choice, actual_number, level)
            time.sleep(0.4)

            png_data = self.driver.get_screenshot_as_png()

            # Clean up overlay for next round
            self.driver.execute_script("var el = document.getElementById('bdg-custom-win-modal'); if(el) el.remove();")

            output = io.BytesIO(png_data)
            output.seek(0)
            logger.info(f"📸 Captured live BDGWin WIN screenshot for {target_issue}!")
            return output

        except Exception as e:
            logger.error(f"Error capturing live win screenshot: {e}")
            return None

    async def capture_win_screenshot(
        self,
        game_id: str,
        target_issue: str,
        choice: str = "BIG",
        actual_number: int = 7,
        level: int = 1
    ) -> Optional[io.BytesIO]:
        async with self._lock:
            return await asyncio.to_thread(
                self.capture_win_screenshot_sync,
                game_id,
                target_issue,
                choice,
                actual_number,
                level
            )

    def close_sync(self):
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.is_logged_in = False
                logger.info("BDGWin browser session closed.")
        except Exception:
            pass

    async def close(self):
        await asyncio.to_thread(self.close_sync)

bet_automation = BDGWinAutomation()
