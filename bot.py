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
# ساخت لینک‌های عضویت جدید
# -----------------------------
async def create_invite_links(bot, user_id):
    created_links = []

    try:
        for channel in REQUIRED_CHANNELS:

            invite = await bot.create_chat_invite_link(
                chat_id=channel
            )

            created_links.append({
                "channel": channel,
                "link": invite.invite_link
            })

        return created_links

    except Exception:

        # اگر وسط ساخت لینک خطا خورد،
        # لینک‌هایی که تا اینجا ساخته شده‌اند هم باطل شوند
        for item in created_links:
            try:
                await bot.revoke_chat_invite_link(
                    chat_id=item["channel"],
                    invite_link=item["link"]
                )
            except Exception:
                pass

        return None


# -----------------------------
# باطل کردن تمام لینک‌های قبلی کاربر
# -----------------------------
async def revoke_all_user_invite_links(bot, user_data):

    all_links = user_data.get("invite_links", [])

    for item in all_links:
        try:
            await bot.revoke_chat_invite_link(
                chat_id=item["channel"],
                invite_link=item["link"]
            )
        except Exception:
            pass

    user_data.pop("invite_links", None)


# -----------------------------
# دکمه‌های عضویت
# -----------------------------
def join_keyboard(new_links):

    keyboard = []

    for index, item in enumerate(new_links):

        keyboard.append([
            InlineKeyboardButton(
                f"عضویت در کانال {index + 1} 📢",
                url=item["link"]
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            "عضو شدم ✅",
            callback_data="check_membership"
        )
    ])

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

        # پیام هشدار
        warning_message = await bot.send_message(
            chat_id=chat_id,
            text="⚠️ فایل بعد از 15 ثانیه پاک می‌شود."
        )

        # حذف بعد از 15 ثانیه
        asyncio.create_task(
            delete_after_15_seconds(
                bot,
                chat_id,
                message.message_id,
                warning_message.message_id
            )
        )

        return True

    except Exception:

        await bot.send_message(
            chat_id=chat_id,
            text="❌ متأسفانه فیلم پیدا نشد."
        )

        return False


# -----------------------------
# حذف فیلم و هشدار بعد از 15 ثانیه
# -----------------------------
async def delete_after_15_seconds(
    bot,
    chat_id,
    movie_message_id,
    warning_message_id
):

    await asyncio.sleep(15)

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

    # اگر عضو همه کانال‌هاست
    if await is_member(context.bot, user_id):

        success = await send_movie(
            context.bot,
            update.effective_chat.id,
            movie_id
        )

        # اگر فیلم با موفقیت ارسال شد،
        # تمام لینک‌های عضویت قبلی باطل شوند
        if success:
            await revoke_all_user_invite_links(
                context.bot,
                context.user_data
            )

            context.user_data.pop(
                "pending_movie",
                None
            )

        return

    # -------------------------
    # کاربر عضو نیست
    # -------------------------

    new_links = await create_invite_links(
        context.bot,
        user_id
    )

    if not new_links:

        await update.message.reply_text(
            "❌ خطایی در ساخت لینک عضویت رخ داد."
        )

        return

    # لینک‌های جدید را به لیست قبلی اضافه کن
    # نه اینکه قبلی‌ها را پاک کنیم
    if "invite_links" not in context.user_data:
        context.user_data["invite_links"] = []

    context.user_data["invite_links"].extend(
        new_links
    )

    await update.message.reply_text(
        "⚠️ برای دریافت فیلم، ابتدا در همه کانال‌ها عضو شو:",
        reply_markup=join_keyboard(new_links)
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
    if not await is_member(
        context.bot,
        user_id
    ):

        await query.answer(
            "هنوز توی بعضی از کانالا عضو نشدی رفیق!",
            show_alert=True
        )

        return

    # پاسخ به دکمه
    await query.answer()

    movie_id = context.user_data.get(
        "pending_movie"
    )

    # اگر فیلمی در انتظار نیست
    if not movie_id:

        # با این حال لینک‌های قبلی را باطل کن
        await revoke_all_user_invite_links(
            context.bot,
            context.user_data
        )

        await query.edit_message_text(
            "✅ عضویت تأیید شد.\n"
            "حالا لینک فیلم موردنظرت رو باز کن."
        )

        return

    await query.edit_message_text(
        "✅ عضویت تأیید شد.\n"
        "🎬 در حال ارسال فیلم..."
    )

    # ارسال فیلم
    success = await send_movie(
        context.bot,
        query.message.chat_id,
        movie_id
    )

    # فقط اگر فیلم واقعاً ارسال شد
    # تمام لینک‌های عضویت قبلی باطل شوند
    if success:

        await revoke_all_user_invite_links(
            context.bot,
            context.user_data
        )

        context.user_data.pop(
            "pending_movie",
            None
        )


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

    # فقط فیلم یا فایل
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
    CommandHandler(
        "start",
        start
    )
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
        filters.Chat(
            chat_id=STORAGE_CHAT_ID
        )
        & filters.UpdateType.CHANNEL_POST
        & (
            filters.VIDEO
            | filters.Document.ALL
        ),
        new_storage_movie
    )
)


# اجرای دائمی ربات
app.run_polling()
