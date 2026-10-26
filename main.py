import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

import config
from bot.handlers import start_handler, callback_handler, message_handler
from bot.scheduler import WinGoScheduler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("WinGoBot")

scheduler_instance = None

async def post_init(application: Application):
    """Called after application is initialized, starts background scheduler"""
    global scheduler_instance
    scheduler_instance = WinGoScheduler(application.bot)
    await scheduler_instance.start()
    logger.info("✅ WinGo Multi-Game Scheduler started successfully!")

async def post_shutdown(application: Application):
    """Called during graceful shutdown"""
    global scheduler_instance
    if scheduler_instance:
        await scheduler_instance.stop()
    logger.info("🛑 Bot shutdown complete.")

def main():
    if not config.BOT_TOKEN:
        logger.critical("❌ BOT_TOKEN is missing! Please configure it in .env file.")
        return

    logger.info("🚀 Starting Modern WinGo VIP Prediction Bot...")
    logger.info(f"👑 Admins configured: {config.ADMIN_IDS}")
    logger.info("⚡ Games: WinGo 30s, 1M, 3M, 5M (Multi-Channel)")
    logger.info("🎨 UI: Separate Messages, Styled High-Impact Buttons, AI Prediction")

    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Register handlers
    app.add_handler(CommandHandler(["start", "admin"], start_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler((filters.TEXT | filters.Document.ALL) & ~filters.COMMAND, message_handler))

    # Run Telegram Bot polling
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
