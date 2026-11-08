"""
╔══════════════════════════════════════════╗
║     XBOX CHECKER BOT — ENTRY POINT      ║
║          MADE BY - @NUTFRR              ║
╚══════════════════════════════════════════╝
"""
import asyncio
import logging
import os

from aiohttp import web
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from db.database import init_db
from bot.handlers import (
    cmd_start, cmd_help, cmd_status, cmd_redeem,
    cmd_gencode, cmd_revoke, cmd_addpremium, cmd_ban, cmd_unban, cmd_broadcast,
    on_callback, on_message,
    _active,          # shared active-sessions dict
)
from webapp.api_server import create_api_app, set_refs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BOT_TOKEN    = os.environ["BOT_TOKEN"]
WEBHOOK_URL  = os.environ.get("WEBHOOK_URL", "")
WEBHOOK_PORT = int(os.environ.get("PORT", "8080"))
WEBAPP_URL   = os.environ.get("WEBAPP_URL", "")   # same as WEBHOOK_URL usually
ADMIN_ID     = int(os.environ.get("ADMIN_ID", "0"))

_SECRET = BOT_TOKEN.split(":")[1][:20]
WH_PATH = f"/webhook/{_SECRET}"


def build_tg_app():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",        cmd_start))
    app.add_handler(CommandHandler("help",         cmd_help))
    app.add_handler(CommandHandler("status",       cmd_status))
    app.add_handler(CommandHandler("redeem",       cmd_redeem))

    app.add_handler(CommandHandler("gencode",      cmd_gencode))
    app.add_handler(CommandHandler("revoke",       cmd_revoke))
    app.add_handler(CommandHandler("addpremium",   cmd_addpremium))
    app.add_handler(CommandHandler("ban",          cmd_ban))
    app.add_handler(CommandHandler("unban",        cmd_unban))
    app.add_handler(CommandHandler("broadcast",    cmd_broadcast))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(
        filters.Document.TXT | (filters.TEXT & ~filters.COMMAND),
        on_message,
    ))

    return app


async def main():
    init_db()
    logger.info("Database initialised.")

    tg_app = build_tg_app()

    # wire webapp API to the bot instance + shared active dict
    loop = asyncio.get_event_loop()
    set_refs(tg_app.bot, _active, loop)

    # inject WEBAPP_URL into handlers module so it can build Open App buttons
    import bot.handlers as _h
    _h.WEBAPP_URL = WEBAPP_URL or WEBHOOK_URL or ""

    if WEBHOOK_URL:
        # ── production: single aiohttp server handles both webhook + webapp ──
        api_app = create_api_app()

        # mount telegram webhook under the aiohttp app
        async def tg_webhook(request):
            from telegram import Update
            import json
            data = await request.read()
            update = Update.de_json(json.loads(data), tg_app.bot)
            await tg_app.process_update(update)
            return web.Response()

        api_app.router.add_post(WH_PATH, tg_webhook)

        await tg_app.initialize()
        await tg_app.bot.set_webhook(
            url=f"{WEBHOOK_URL.rstrip('/')}{WH_PATH}",
            secret_token=_SECRET,
            drop_pending_updates=True,
        )
        await tg_app.start()

        runner = web.AppRunner(api_app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
        await site.start()
        logger.info("Server running on 0.0.0.0:%d", WEBHOOK_PORT)

        # keep running
        try:
            await asyncio.Event().wait()
        finally:
            await tg_app.stop()
            await tg_app.shutdown()
            await runner.cleanup()
    else:
        # ── local dev: polling + API on a side port ──
        api_app = create_api_app()
        runner = web.AppRunner(api_app)
        await runner.setup()
        api_port = 8081
        site = web.TCPSite(runner, "0.0.0.0", api_port)
        await site.start()
        logger.info("API/webapp running on http://localhost:%d", api_port)
        logger.info("Starting polling (local dev).")

        await tg_app.initialize()
        await tg_app.start()
        await tg_app.updater.start_polling(drop_pending_updates=True)
        try:
            await asyncio.Event().wait()
        finally:
            await tg_app.updater.stop()
            await tg_app.stop()
            await tg_app.shutdown()
            await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
