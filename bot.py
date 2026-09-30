import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

# کانال‌های اجباری
REQUIRED_CHANNELS = [
    "@restiko_zapas",
    "@Restiko4",
]


async def is_member(bot, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)

            if member.status not in ["member", "administrator", "creator"]:
                return False

        except Exception:
            return False

    return True


def join_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                "عضویت در کانال اول 📢",
                url="https://t.me/restiko_zapas"
            )
        ],
        [
            InlineKeyboardButton(
                "عضویت در کانال دوم 📢",
                url="https://t.me/Restiko4"
            )
        ],
        [
            InlineKeyboardButton(
                "عضو شدم ✅",
                callback_data="check_membership"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def delete_after_10_seconds(bot, chat_id, message_id):
    await asyncio.sleep(10)

    try:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=message_id
        )
    except Exception:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if await is_member(context.bot, user_id):
        await update.message.reply_text(
            "✅ عضویت شما تأیید شد.\n"
            "حالا فایل یا فیلم موردنظرت رو بفرست."
        )
    else:
        await update.message.reply_text(
            "⚠️ برای استفاده از ربات، ابتدا در هر دو کانال زیر عضو شو:",
            reply_markup=join_keyboard()
        )


async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if await is_member(context.bot, user_id):
        await query.edit_message_text(
            "✅ عضویت شما تأیید شد.\n"
            "حالا فایل یا فیلم موردنظرت رو بفرست."
        )
    else:
        await query.answer(
            "❌ هنوز در هر دو کانال عضو نشدی.",
            show_alert=True
        )


async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_member(context.bot, user_id):
        await update.message.reply_text(
            "⚠️ ابتدا باید در هر دو کانال عضو شوی:",
            reply_markup=join_keyboard()
        )
        return

    message = await update.message.copy(
        chat_id=update.effective_chat.id
    )

    asyncio.create_task(
        delete_after_10_seconds(
            context.bot,
            update.effective_chat.id,
            message.message_id
        )
    )


app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(
    CallbackQueryHandler(
        check_membership,
        pattern="^check_membership$"
    )
)

app.add_handler(
    MessageHandler(
        filters.VIDEO | filters.Document.ALL,
        handle_video
    )
)

app.run_polling()
