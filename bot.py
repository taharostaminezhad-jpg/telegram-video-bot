import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

async def delete_after_10_seconds(bot, chat_id, message_id):
    await asyncio.sleep(10)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except:
        pass

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.message.copy(chat_id=update.effective_chat.id)

    asyncio.create_task(
        delete_after_10_seconds(
            context.bot,
            update.effective_chat.id,
            message.message_id
        )
    )

app = Application.builder().token(TOKEN).build()

app.add_handler(
    MessageHandler(
        filters.VIDEO | filters.Document.VIDEO,
        handle_video
    )
)

app.run_polling()
