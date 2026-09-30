import os
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# آیدی عددی صاحب ربات
OWNER_ID = 7223057338


# -----------------------------
# بررسی عضویت در کانال‌ها
# -----------------------------
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


# -----------------------------
# دکمه‌های عضویت
# -----------------------------
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


# -----------------------------
# ارسال فیلم
# -----------------------------
async def send_movie(bot, chat_id, message_id):
    try:
        # ارسال فیلم
        message = await bot.copy_message(
            chat_id=chat_id,
            from_chat_id=STORAGE_CHAT_ID,
            message_id=message_id
        )

        # ارسال پیام هشدار
        warning_message = await bot.send_message(
            chat_id=chat_id,
            text="⚠️ فایل بعد از 10 ثانیه پاک می‌شود."
        )

        # حذف فیلم و پیام هشدار بعد از 10 ثانیه
        asyncio.create_task(
            delete_after_10_seconds(
                bot,
                chat_id,
                message.message_id,
                warning_message.message_id
            )
        )

    except Exception:
        await bot.send_message(
            chat_id=chat_id,
            text="❌ متأسفانه فیلم پیدا نشد."
        )


# -----------------------------
# حذف فیلم و پیام هشدار بعد از 10 ثانیه
# -----------------------------
async def delete_after_10_seconds(
    bot,
    chat_id,
    movie_message_id,
    warning_message_id
):
    await asyncio.sleep(10)

    try:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=movie_message_id
        )
    except Exception:
        pass

    try:
        await bot.delete_message(
            chat_id=chat_id,
            message_id=warning_message_id
        )
    except Exception:
        pass


# -----------------------------
# دستور /start
# -----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "🎬 برای دریافت فیلم، از لینک مخصوص همان فیلم وارد ربات شو."
        )
        return

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


# -----------------------------
# بررسی دکمه «عضو شدم»
# -----------------------------
async def check_membership(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    user_id = query.from_user.id

    # بررسی عضویت
    if not await is_member(context.bot, user_id):
        await query.answer(
            "❌ شما در همه کانال‌ها عضو نشده‌اید.",
            show_alert=True
        )
        return

    # پاسخ به دکمه بعد از تأیید عضویت
    await query.answer()

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


# -----------------------------
# تشخیص فیلم جدید در کانال مخزن
# -----------------------------
async def new_storage_movie(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    message = update.channel_post

    if not message:
        return

    # فقط فیلم یا فایل را قبول کن
    if not message.video and not message.document:
        return

    # گرفتن نام کاربری ربات
    me = await context.bot.get_me()
    bot_username = me.username

    if not bot_username:
        return

    # شماره پست فیلم
    movie_id = message.message_id

    # ساخت لینک مخصوص فیلم
    movie_link = (
        f"https://t.me/{bot_username}?start={movie_id}"
    )

    # ارسال لینک فقط برای صاحب ربات
    try:
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=(
                "🎬 فیلم جدید ثبت شد.\n\n"
                f"📌 شماره پست: {movie_id}\n\n"
                "🔗 لینک دریافت:\n"
                f"{movie_link}"
            )
        )
    except Exception:
        pass


# -----------------------------
# ساخت ربات
# -----------------------------
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


# دریافت پست‌های کانال مخزن
app.add_handler(
    MessageHandler(
        filters.Chat(chat_id=STORAGE_CHAT_ID)
        & filters.UpdateType.CHANNEL_POST
        & (filters.VIDEO | filters.Document.ALL),
        new_storage_movie
    )
)


# اجرای دائمی ربات
app.run_polling()
