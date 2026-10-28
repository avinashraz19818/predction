import os
import re
import io
import time
import asyncio
import logging
from typing import Optional, Dict, Any, Union
from pyrogram import Client, enums
from pyrogram.errors import (
    FloodWait, SessionPasswordNeeded, PhoneCodeInvalid,
    PasswordHashInvalid, PhoneNumberInvalid, PhoneCodeExpired
)
import config
from database import db_manager

logger = logging.getLogger("WinGoUserbot")

def format_for_pyrogram(text: str) -> str:
    """
    Converts Telegram Bot API HTML custom emoji format:
    <tg-emoji emoji-id="5420315771991497307">🔥</tg-emoji>
    into Pyrogram's native HTML custom emoji format:
    <emoji id=5420315771991497307>🔥</emoji>
    """
    if not text:
        return text
    # Convert <tg-emoji emoji-id="123">🔥</tg-emoji> -> <emoji id=123>🔥</emoji>
    return re.sub(
        r'<tg-emoji\s+emoji-id=["\']?(\d+)["\']?>(.*?)</tg-emoji>',
        r'<emoji id=\1>\2</emoji>',
        text
    )

def append_channel_buttons_html(text: str, channel: Optional[dict]) -> str:
    """
    User accounts cannot directly attach Telegram InlineKeyboardMarkup.
    Instead, this appends channel buttons as elegant, high-impact clickable HTML link rows
    at the bottom of the post, seamlessly supporting animated emojis!
    """
    if not channel:
        return text
    buttons = channel.get("buttons", [])
    if not buttons:
        return text

    btn_lines = []
    for btn in buttons:
        btn_text = btn.get("text", "").strip()
        url = btn.get("url", "").strip()
        if btn_text and url:
            btn_lines.append(f'👉 <a href="{url}"><b>[ {btn_text} ]</b></a>')

    if btn_lines:
        return text + "\n━━━━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(btn_lines)
    return text

def _update_env_file(key: str, value: Optional[str]):
    """Safely updates or removes a key in .env file on disk"""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        env_path = ".env"
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f.read().splitlines():
                    if "=" in line and line.split("=", 1)[0].strip() == key:
                        continue
                    lines.append(line)
        if value:
            lines.append(f"{key}={value}")
        with open(env_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        if value:
            os.environ[key] = str(value)
        else:
            os.environ.pop(key, None)
    except Exception as e:
        logger.warning(f"Could not update .env file: {e}")

class UserbotManager:
    """
    Manages Telegram Userbot session for broadcasting predictions & results
    with 100% animated custom emojis into channels.
    """
    def __init__(self):
        self.client: Optional[Client] = None
        self.me: Optional[Dict[str, Any]] = None
        self.active_logins: Dict[int, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def is_active(self) -> bool:
        return bool(self.client and getattr(self.client, "is_connected", False) and self.me)

    def get_status(self) -> Dict[str, Any]:
        return {
            "active": self.is_active(),
            "me": self.me
        }

    async def start(self, session_str: Optional[str] = None) -> bool:
        """Starts live userbot client with session string"""
        async with self._lock:
            if not session_str:
                session_str = db_manager.get_userbot_session()

            if not session_str:
                logger.info("ℹ️ No Userbot session found. Standard bot delivery active.")
                return False

            # Stop existing if running
            await self._stop_internal()

            try:
                logger.info("🚀 Starting Telegram Userbot client for animated emoji delivery...")
                client = Client(
                    "userbot_live",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=session_str.strip(),
                    in_memory=True
                )
                await client.start()
                me = await client.get_me()
                self.client = client
                self.me = {
                    "id": me.id,
                    "first_name": me.first_name,
                    "last_name": me.last_name or "",
                    "username": me.username or "",
                    "is_premium": getattr(me, "is_premium", False),
                    "phone_number": getattr(me, "phone_number", "")
                }
                logger.info(
                    f"✅ Userbot Active: {self.me['first_name']} (@{self.me['username'] or 'No username'}), "
                    f"ID: {self.me['id']}, Premium: {self.me['is_premium']}"
                )

                # Prime peer cache so channel IDs are immediately resolvable
                asyncio.create_task(self._prime_dialogs())
                return True
            except Exception as e:
                logger.error(f"❌ Failed to start Userbot client: {e}")
                self.client = None
                self.me = None
                return False

    async def _prime_dialogs(self):
        """Loads recent dialogs in background to populate Pyrogram peer cache"""
        if not self.client:
            return
        try:
            count = 0
            async for _ in self.client.get_dialogs(limit=50):
                count += 1
            logger.info(f"📁 Userbot primed {count} dialogs in peer cache.")
        except Exception as e:
            logger.debug(f"Priming dialogs notice: {e}")

    async def stop(self):
        """Stops live userbot client"""
        async with self._lock:
            await self._stop_internal()

    async def _stop_internal(self):
        if self.client:
            try:
                if getattr(self.client, "is_connected", False):
                    await self.client.stop()
            except Exception as e:
                logger.warning(f"Error stopping userbot client: {e}")
            finally:
                self.client = None
                self.me = None

    async def logout(self) -> bool:
        """Logs out userbot, clearing session from Mongo & .env"""
        await self.stop()
        db_manager.set_userbot_session(None)
        _update_env_file("USERBOT_SESSION", "")
        logger.info("🚪 Userbot session logged out successfully.")
        return True

    # ================= INTERACTIVE ADMIN LOGIN FLOW =================

    async def send_login_code(self, admin_id: int, phone: str) -> Dict[str, Any]:
        """Step 1: Connects in-memory client and sends login code via Telegram"""
        # Cleanup any existing pending login for this admin
        await self.cancel_login(admin_id)

        digits = re.sub(r"\D", "", phone.strip())
        if len(digits) < 10 or len(digits) > 15:
            return {"ok": False, "error": "Invalid phone number format. Please include country code, e.g. +919876543210"}

        norm_phone = "+" + digits
        tmp = Client(
            f"login_{admin_id}",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            in_memory=True
        )

        try:
            await tmp.connect()
        except Exception as e:
            return {"ok": False, "error": f"Failed to connect to Telegram servers: {e}"}

        try:
            sent = await tmp.send_code(norm_phone)
            self.active_logins[admin_id] = {
                "tmp": tmp,
                "phone": norm_phone,
                "phone_code_hash": sent.phone_code_hash,
                "step": "otp",
                "ts": time.time()
            }
            return {"ok": True, "phone": norm_phone}
        except FloodWait as e:
            await self._safe_disconnect(tmp)
            wait_sec = getattr(e, "value", None) or getattr(e, "x", 60)
            return {"ok": False, "error": f"Telegram rate limit: Please wait {wait_sec} seconds before trying again."}
        except PhoneNumberInvalid:
            await self._safe_disconnect(tmp)
            return {"ok": False, "error": "This phone number is not registered on Telegram. Check the number and country code."}
        except Exception as e:
            await self._safe_disconnect(tmp)
            return {"ok": False, "error": f"Error sending OTP: {e}"}

    async def sign_in_otp(self, admin_id: int, raw_otp: str) -> Dict[str, Any]:
        """Step 2: Submits OTP code for verification"""
        st = self.active_logins.get(admin_id)
        if not st:
            return {"ok": False, "error": "No active login session. Type /login to start again."}

        otp = re.sub(r"\D", "", raw_otp.strip())
        if len(otp) < 4:
            return {"ok": False, "error": "OTP code is too short. Please send all digits received in Telegram."}

        tmp = st["tmp"]
        try:
            await tmp.sign_in(st["phone"], st["phone_code_hash"], otp)
        except SessionPasswordNeeded:
            st["step"] = "password"
            st["ts"] = time.time()
            return {"ok": True, "needs_password": True}
        except PhoneCodeInvalid:
            return {"ok": False, "error": "Incorrect OTP code. Please enter the valid code received from Telegram."}
        except PhoneCodeExpired:
            await self.cancel_login(admin_id)
            return {"ok": False, "error": "OTP has expired. Please type /login to request a new code."}
        except FloodWait as e:
            wait_sec = getattr(e, "value", None) or getattr(e, "x", 60)
            return {"ok": False, "error": f"Telegram rate limit: Please wait {wait_sec} seconds."}
        except Exception as e:
            await self.cancel_login(admin_id)
            return {"ok": False, "error": f"Login failed: {e}"}

        # If we got here, login succeeded without 2FA
        return await self._finish_login(admin_id, st)

    async def check_password(self, admin_id: int, password: str) -> Dict[str, Any]:
        """Step 3: Submits 2-Step Verification password if required"""
        st = self.active_logins.get(admin_id)
        if not st:
            return {"ok": False, "error": "No active login session. Type /login to start again."}

        pwd = password.strip()
        tmp = st["tmp"]
        try:
            await tmp.check_password(pwd)
        except PasswordHashInvalid:
            return {"ok": False, "error": "Incorrect 2-Step Verification password. Please try again."}
        except FloodWait as e:
            wait_sec = getattr(e, "value", None) or getattr(e, "x", 60)
            return {"ok": False, "error": f"Telegram rate limit: Please wait {wait_sec} seconds."}
        except Exception as e:
            await self.cancel_login(admin_id)
            return {"ok": False, "error": f"2FA verification failed: {e}"}

        return await self._finish_login(admin_id, st)

    async def _finish_login(self, admin_id: int, st: Dict[str, Any]) -> Dict[str, Any]:
        """Exports session string, saves to MongoDB & .env, and starts live userbot"""
        tmp = st["tmp"]
        try:
            session_str = await tmp.export_session_string()
            me = await tmp.get_me()
            me_info = {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name or "",
                "username": me.username or "",
                "is_premium": getattr(me, "is_premium", False)
            }
        except Exception as e:
            await self.cancel_login(admin_id)
            return {"ok": False, "error": f"Failed to export session string: {e}"}

        await self._safe_disconnect(tmp)
        self.active_logins.pop(admin_id, None)

        # Save session string persistently
        db_manager.set_userbot_session(session_str)
        _update_env_file("USERBOT_SESSION", session_str)

        # Start live client immediately
        started = await self.start(session_str)
        return {
            "ok": True,
            "needs_password": False,
            "started": started,
            "me": me_info
        }

    async def cancel_login(self, admin_id: int):
        """Cleans up ongoing login attempt"""
        st = self.active_logins.pop(admin_id, None)
        if st and "tmp" in st:
            await self._safe_disconnect(st["tmp"])

    async def _safe_disconnect(self, client: Client):
        try:
            if getattr(client, "is_connected", False):
                await client.disconnect()
        except Exception:
            pass

    # ================= MESSAGE & MEDIA DELIVERY =================

    async def _resolve_peer(self, chat_id: Union[int, str]):
        if isinstance(chat_id, str):
            chat_id = chat_id.strip()
            if chat_id.startswith("-100") or chat_id.startswith("-") or chat_id.isdigit():
                try:
                    chat_id = int(chat_id)
                except ValueError:
                    pass
        return chat_id

    async def send_channel_message(
        self,
        chat_id: Union[int, str],
        text: str,
        channel: Optional[dict] = None
    ) -> Any:
        """
        Sends formatted text message with animated custom emojis to channel.
        Raises exception on failure to allow caller to fall back to standard bot.
        """
        if not self.is_active():
            raise RuntimeError("Userbot is not active")

        peer = await self._resolve_peer(chat_id)
        text_with_btns = append_channel_buttons_html(text, channel)
        pyr_text = format_for_pyrogram(text_with_btns)

        return await self.client.send_message(
            chat_id=peer,
            text=pyr_text,
            parse_mode=enums.ParseMode.HTML,
            disable_web_page_preview=True
        )

    async def send_channel_photo(
        self,
        chat_id: Union[int, str],
        photo_bytes: bytes,
        caption: str,
        channel: Optional[dict] = None
    ) -> Any:
        """
        Sends photo screenshot with animated custom emojis in caption to channel.
        Raises exception on failure to allow caller to fall back to standard bot.
        """
        if not self.is_active():
            raise RuntimeError("Userbot is not active")

        peer = await self._resolve_peer(chat_id)
        caption_with_btns = append_channel_buttons_html(caption, channel)
        pyr_caption = format_for_pyrogram(caption_with_btns)

        bio = io.BytesIO(photo_bytes)
        bio.name = "screenshot.png"

        return await self.client.send_photo(
            chat_id=peer,
            photo=bio,
            caption=pyr_caption,
            parse_mode=enums.ParseMode.HTML
        )

    async def send_channel_sticker(
        self,
        chat_id: Union[int, str],
        sticker: str
    ) -> Any:
        """Sends sticker to channel via Userbot"""
        if not self.is_active():
            raise RuntimeError("Userbot is not active")
        peer = await self._resolve_peer(chat_id)
        return await self.client.send_sticker(chat_id=peer, sticker=sticker)

    async def send_channel_document(
        self,
        chat_id: Union[int, str],
        document: str,
        caption: Optional[str] = None
    ) -> Any:
        """Sends document file to channel via Userbot"""
        if not self.is_active():
            raise RuntimeError("Userbot is not active")
        peer = await self._resolve_peer(chat_id)
        pyr_caption = format_for_pyrogram(caption) if caption else None
        return await self.client.send_document(
            chat_id=peer,
            document=document,
            caption=pyr_caption,
            parse_mode=enums.ParseMode.HTML if pyr_caption else None
        )

# Global singleton instance
userbot_manager = UserbotManager()
