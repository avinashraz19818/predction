import io
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
        self.username = config.DEMO_USERNAME
        self.password = config.DEMO_PASSWORD
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

    def initialize_sync(self) -> bool:
        """Launches headless Edge and logs into BDGWin"""
        if not self.enabled or not self.username or not self.password:
            logger.info("Demo auto-bet automation is disabled in .env")
            return False

        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
            from selenium.webdriver.common.by import By

            logger.info("🚀 Launching Headless Edge for BDGWin Auto-Bet & Screenshots...")
            options = Options()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--window-size=412,915")  # Mobile viewport
            options.add_argument("user-agent=Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36")

            self.driver = webdriver.Edge(options=options)
            self.driver.set_page_load_timeout(30)

            # 1. Login
            logger.info(f"Navigating to {self.login_url} ...")
            self.driver.get(self.login_url)
            time.sleep(3)

            phone_inp = self.driver.find_element(By.CSS_SELECTOR, "input[name='userNumber']")
            phone_inp.clear()
            phone_inp.send_keys(self.username)

            pwd_inp = self.driver.find_elements(By.CSS_SELECTOR, "input[type='password']")[0]
            pwd_inp.clear()
            pwd_inp.send_keys(self.password)

            for btn in self.driver.find_elements(By.TAG_NAME, "button"):
                if "Log in" in btn.text:
                    btn.click()
                    break
            time.sleep(4)

            # 2. Close announcement popups
            for _ in range(3):
                clicked = False
                for b in self.driver.find_elements(By.TAG_NAME, "button"):
                    if "Confirm" in b.text and b.is_displayed():
                        b.click()
                        time.sleep(1.5)
                        clicked = True
                        break
                if not clicked:
                    break

            self.is_logged_in = True
            logger.info("✅ Logged into BDGWin demo account successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ BDGWin login error: {e}", exc_info=True)
            self.close_sync()
            return False

    async def initialize(self) -> bool:
        return await asyncio.to_thread(self.initialize_sync)

    def place_bet_sync(self, game_id: str, choice: str) -> bool:
        """Navigates to game page and places ₹1 bet on BIG or SMALL"""
        if not self.is_logged_in or not self.driver:
            return False

        try:
            from selenium.webdriver.common.by import By

            game_url = self._get_game_url(game_id)
            if game_url not in self.driver.current_url:
                self.driver.get(game_url)
                time.sleep(3)

            # Look for Big or Small button
            target_text = "Big" if choice.upper() == "BIG" else "Small"
            bet_btn = self.driver.find_element(By.XPATH, f"//*[text()='{target_text}']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", bet_btn)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", bet_btn)
            time.sleep(1.5)

            # Confirm bet by clicking 'Total amount ₹1.00' button
            for b in self.driver.find_elements(By.TAG_NAME, "button"):
                if "Total amount" in b.text:
                    b.click()
                    logger.info(f"✅ Auto-bet ₹1 placed on {choice.upper()} for {game_id}!")
                    time.sleep(1)
                    return True

            logger.warning(f"Could not find Total amount button for bet on {choice}")
            return False

        except Exception as e:
            logger.error(f"Error placing bet on {choice}: {e}")
            return False

    async def place_bet(self, game_id: str, choice: str) -> bool:
        async with self._lock:
            return await asyncio.to_thread(self.place_bet_sync, game_id, choice)

    def capture_win_screenshot_sync(self, game_id: str, target_issue: str) -> Optional[io.BytesIO]:
        """Navigates to My History tab and captures the official WIN record"""
        if not self.is_logged_in or not self.driver:
            return None

        try:
            from selenium.webdriver.common.by import By

            game_url = self._get_game_url(game_id)
            if game_url not in self.driver.current_url:
                self.driver.get(game_url)
                time.sleep(3)

            # Scroll down and click My History tab
            my_hist = self.driver.find_element(By.XPATH, "//*[text()='My history']")
            self.driver.execute_script("arguments[0].scrollIntoView(true);", my_hist)
            time.sleep(0.5)
            self.driver.execute_script("arguments[0].click();", my_hist)
            time.sleep(2)

            # Grab full screenshot PNG
            png_data = self.driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(png_data))

            # Crop neatly to the result area (centered around the My History winning card)
            # Mobile viewport is 412 x 915. The card is roughly from y=480 to y=820
            width, height = img.size
            crop_box = (10, int(height * 0.50), width - 10, int(height * 0.92))
            cropped_img = img.crop(crop_box)

            output = io.BytesIO()
            cropped_img.save(output, format="PNG")
            output.seek(0)
            logger.info(f"📸 Captured real BDGWin WIN record screenshot for {target_issue}!")
            return output

        except Exception as e:
            logger.error(f"Error capturing win screenshot: {e}")
            return None

    async def capture_win_screenshot(self, game_id: str, target_issue: str) -> Optional[io.BytesIO]:
        async with self._lock:
            return await asyncio.to_thread(self.capture_win_screenshot_sync, game_id, target_issue)

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
