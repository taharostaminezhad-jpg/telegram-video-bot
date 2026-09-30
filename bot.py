import os
import asyncio

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

# کانال‌های اجباری
REQUIRED_CHANNELS = [
    "@restiko_zapas",
    "@Restiko4",
]

# کانال مخزن
STORAGE_CHAT_ID = -1003691964343


async def is_member(bot, user_id):
    for channel in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)

            if member.status not in [
                "member",
                "administrator",
                "creator"
            ]:
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


async def send_movie(bot, chat_id, message_id):
    try:
        message = await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=STORAGE_CHAT_ID,
            message_id=message_id
        )

        asyncio.create_task(
            delete_after_10_seconds(
                bot,
                chat_id,
                message.message_id
            )
        )

    except Exception:
        await bot.send_message(
            chat_id=chat_id,
            text="❌ متأسفانه فیلم پیدا نشد."
        )


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

    # اگر لینک فیلم نباشد
    if not context.args:
        await update.message.reply_text(
            "🎬 برای دریافت فیلم، از لینک مخصوص همان فیلم وارد ربات شو."
        )
        return

    # شماره پست فیلم در کانال مخزن
    movie_id = context.args[0]

    try:
        movie_id = int(movie_id)
    except ValueError:
        await update.message.reply_text(
            "❌ لینک فیلم نامعتبر است."
        )
        return

    # ذخیره فیلم درخواستی
    context.user_data["pending_movie"] = movie_id

    # بررسی عضویت
    if not await is_member(context.bot, user_id):
        await update.message.reply_text(
            "⚠️ برای دریافت فیلم، ابتدا در هر دو کانال عضو شو:",
            reply_markup=join_keyboard()
        )
        return

    # ارسال فیلم
    await send_movie(
        context.bot,
        update.effective_chat.id,
        movie_id
    )


async def check_membership(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # بررسی دوباره عضویت
    if not await is_member(context.bot, user_id):
        await query.answer(
            "❌ هنوز در هر دو کانال عضو نیستی.",
            show_alert=True
        )
        return

    movie_id = context.user_data.get("pending_movie")

    if not movie_id:
        await query.edit_message_text(
            "✅ عضویت تأیید شد.\n"
            "حالا لینک فیلم موردنظرت رو باز کن."
        )
        return

    await query.edit_message_text(
        "✅ عضویت تأیید شد.\n"
        "🎬 در حال ارسال فیلم..."
    )

    await send_movie(
        context.bot,
        query.message.chat_id,
        movie_id
    )

    context.user_data.pop("pending_movie", None)


# این تابع وقتی فیلم جدیدی در کانال مخزن گذاشته شود اجرا می‌شود
async def new_storage_movie(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.channel_post

    if not message:
        return

    if not message.video and not message.document:
        return

    me = await context.bot.get_me()
    bot_username = me.username

    if not bot_username:
        return

    movie_id = message.message_id

    movie_link = f"https://t.me/{bot_username}?start={movie_id}"

    await context.bot.send_message(
        chat_id=STORAGE_CHAT_ID,
        text=(
            "🎬 فیلم جدید ثبت شد.\n\n"
            "🔗 لینک دریافت:\n"
            f"{movie_link}"
        )
    )
app = Application.builder().token(TOKEN).build()

# دستور /start
app.add_handler(
    CommandHandler("start", start)
)

# دکمه «عضو شدم»
app.add_handler(
    CallbackQueryHandler(
        check_membership,
        pattern="^check_membership$"
    )
)

# تشخیص فیلم‌های جدید در کانال مخزن
app.add_handler(
    MessageHandler(
        filters.Chat(chat_id=STORAGE_CHAT_ID)
        & filters.UpdateType.CHANNEL_POST
        & (filters.VIDEO | filters.Document.ALL),
        new_storage_movie
    )
)

app.run_polling()
