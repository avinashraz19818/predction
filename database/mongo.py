import logging
from datetime import datetime
from pymongo import MongoClient
import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        self._memory_channels = {}
        self._memory_settings = {}
        self.connect()

    def connect(self):
        try:
            self.client = MongoClient(
                config.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            self.db = self.client[config.MONGO_DB_NAME]
            # Test connection
            self.client.admin.command('ping')
            self.connected = True
            logger.info("✅ MongoDB connected successfully!")
            self._ensure_indexes()
        except Exception as e:
            self.connected = False
            logger.warning(f"⚠️ MongoDB connection failed: {e}. Using in-memory fallback storage.")

    def _ensure_indexes(self):
        if not self.connected:
            return
        try:
            self.db.channels.create_index("channel_id", unique=True)
            self.db.predictions.create_index([("game_id", 1), ("issue_number", 1)])
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    # ================= CHANNEL MANAGEMENT =================

    def add_channel(self, channel_id, title="", game_id="wingo_1m", register_link=None, promo_text=None):
        channel_id = str(channel_id).strip()
        existing = self.get_channel(channel_id)
        existing_buttons = existing.get("buttons", []) if existing else []

        data = {
            "channel_id": channel_id,
            "title": title or (existing.get("title") if existing else f"Channel {channel_id}"),
            "game_id": game_id,
            "is_active": True,
            "register_link": register_link or (existing.get("register_link") if existing else config.DEFAULT_REGISTER_LINK),
            "promo_text": promo_text or (existing.get("promo_text") if existing else config.DEFAULT_PROMO_TEXT),
            "buttons": existing_buttons,  # Empty by default! Only buttons added by admin will appear
            "current_level": existing.get("current_level", 1) if existing else 1,
            "max_level": 5,
            "stats": existing.get("stats", {
                "total_predictions": 0,
                "wins": 0,
                "losses": 0,
                "current_streak": 0,
                "best_streak": 0
            }) if existing else {
                "total_predictions": 0,
                "wins": 0,
                "losses": 0,
                "current_streak": 0,
                "best_streak": 0
            },
            "created_at": existing.get("created_at", datetime.utcnow()) if existing else datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        self._memory_channels[channel_id] = data

        if self.connected:
            try:
                self.db.channels.update_one(
                    {"channel_id": channel_id},
                    {"$set": data},
                    upsert=True
                )
                logger.info(f"✅ Channel {channel_id} saved to MongoDB (Game: {game_id})")
            except Exception as e:
                logger.error(f"Error saving channel to Mongo: {e}")
        return data

    def get_channel(self, channel_id):
        channel_id = str(channel_id).strip()
        if self.connected:
            try:
                doc = self.db.channels.find_one({"channel_id": channel_id})
                if doc:
                    doc.pop("_id", None)
                    if "buttons" not in doc:
                        doc["buttons"] = []
                    return doc
            except Exception as e:
                logger.error(f"Error getting channel from Mongo: {e}")
        return self._memory_channels.get(channel_id)

    def get_all_channels(self):
        if self.connected:
            try:
                cursor = self.db.channels.find()
                channels = []
                for c in cursor:
                    c.pop("_id", None)
                    if "buttons" not in c:
                        c["buttons"] = []
                    channels.append(c)
                # Keep memory synced
                for c in channels:
                    self._memory_channels[c["channel_id"]] = c
                return channels
            except Exception as e:
                logger.error(f"Error fetching all channels: {e}")
        return list(self._memory_channels.values())

    def get_channels_by_game(self, game_id, only_active=True):
        channels = self.get_all_channels()
        filtered = [c for c in channels if c.get("game_id") == game_id]
        if only_active:
            filtered = [c for c in filtered if c.get("is_active", True)]
        return filtered

    def update_channel(self, channel_id, updates: dict):
        channel_id = str(channel_id).strip()
        updates["updated_at"] = datetime.utcnow()

        if channel_id in self._memory_channels:
            self._memory_channels[channel_id].update(updates)

        if self.connected:
            try:
                self.db.channels.update_one(
                    {"channel_id": channel_id},
                    {"$set": updates}
                )
                logger.info(f"✅ Channel {channel_id} updated: {list(updates.keys())}")
            except Exception as e:
                logger.error(f"Error updating channel: {e}")

    # ================= CHANNEL BUTTON MANAGEMENT =================

    def add_channel_button(self, channel_id: str, text: str, url: str, style: str = None, icon_custom_emoji_id: str = None):
        """Adds a custom inline button with optional Telegram native color style (success/danger/primary)"""
        ch = self.get_channel(channel_id)
        if not ch:
            return []
        buttons = ch.get("buttons", [])
        btn_obj = {
            "text": text.strip(),
            "url": url.strip(),
            "style": style if style in ("success", "danger", "primary") else None,
            "icon_custom_emoji_id": icon_custom_emoji_id
        }
        buttons.append(btn_obj)
        self.update_channel(channel_id, {"buttons": buttons})
        return buttons

    def remove_channel_button(self, channel_id: str, index: int):
        """Removes a button by index from the channel's buttons list"""
        ch = self.get_channel(channel_id)
        if not ch:
            return []
        buttons = ch.get("buttons", [])
        if 0 <= index < len(buttons):
            buttons.pop(index)
            self.update_channel(channel_id, {"buttons": buttons})
        return buttons

    def clear_channel_buttons(self, channel_id: str):
        """Removes all buttons from a channel so messages are sent with zero buttons"""
        self.update_channel(channel_id, {"buttons": []})
        return []

    def remove_channel(self, channel_id):
        channel_id = str(channel_id).strip()
        self._memory_channels.pop(channel_id, None)
        if self.connected:
            try:
                self.db.channels.delete_one({"channel_id": channel_id})
                logger.info(f"✅ Channel {channel_id} deleted from DB")
                return True
            except Exception as e:
                logger.error(f"Error removing channel: {e}")
        return True

    def toggle_channel_active(self, channel_id):
        ch = self.get_channel(channel_id)
        if not ch:
            return False
        new_status = not ch.get("is_active", True)
        self.update_channel(channel_id, {"is_active": new_status})
        return new_status

    def record_channel_result(self, channel_id, is_win: bool):
        ch = self.get_channel(channel_id)
        if not ch:
            return {}, 1

        stats = ch.get("stats", {
            "total_predictions": 0,
            "wins": 0,
            "losses": 0,
            "current_streak": 0,
            "best_streak": 0
        })

        curr_level = ch.get("current_level", 1)
        max_level = ch.get("max_level", 5)

        stats["total_predictions"] += 1
        if is_win:
            stats["wins"] += 1
            stats["current_streak"] = stats.get("current_streak", 0) + 1
            if stats["current_streak"] > stats.get("best_streak", 0):
                stats["best_streak"] = stats["current_streak"]
            next_level = 1  # Reset to Level 1 on WIN
        else:
            stats["losses"] += 1
            stats["current_streak"] = 0
            next_level = curr_level + 1 if curr_level < max_level else 1

        self.update_channel(channel_id, {
            "stats": stats,
            "current_level": next_level
        })
        return stats, next_level

    # ================= PREDICTION HISTORY =================

    def save_prediction(self, game_id, issue_number, prediction_data):
        doc = {
            "game_id": game_id,
            "issue_number": str(issue_number),
            "data": prediction_data,
            "created_at": datetime.utcnow()
        }
        if self.connected:
            try:
                self.db.predictions.update_one(
                    {"game_id": game_id, "issue_number": str(issue_number)},
                    {"$set": doc},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error saving prediction doc: {e}")

db_manager = DatabaseManager()
