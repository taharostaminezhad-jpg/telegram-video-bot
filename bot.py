import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters


TOKEN = os.getenv("BOT_TOKEN")


async def delete_messages_later(bot, chat_id, message_ids):
    await asyncio.sleep(10)

    for message_id in message_ids:
        try:
            await bot.delete_message(
                chat_id=chat_id,
                message_id=message_id
            )
        except Exception:
            pass


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    if not message:
        return

    # اگر فیلم به صورت Video فرستاده شده
    if message.video:
        sent_message = await message.reply_video(
            video=message.video.file_id
        )

    # اگر فیلم به صورت فایل Document فرستاده شده
    elif message.document:
        sent_message = await message.reply_document(
            document=message.document.file_id
        )

    else:
        return

    # حذف پیام کاربر و پیام ربات بعد از ۱۰ ثانیه
    asyncio.create_task(
        delete_messages_later(
            context.bot,
            message.chat_id,
            [message.message_id, sent_message.message_id]
        )
    )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.VIDEO | filters.Document.VIDEO,
            handle_video
        )
    )

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
