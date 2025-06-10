import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hlink
from flask import Flask
import json
import os

# تنظیمات
BOT_TOKEN = "8177436123:AAG2RuDLbRI6HdgsCTa7_75TJwuQ151ohLA"
ADMIN_ID = 131555118
CHANNEL_ID = -1002798154695
DATA_FILE = "users.json"

# راه‌اندازی بات
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# بارگذاری اطلاعات کاربران
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        users = json.load(f)
else:
    users = {}

# دکمه‌های اصلی
def main_menu():
    buttons = [
        [types.KeyboardButton(text="📁 ارسالی‌های شما")],
        [types.KeyboardButton(text="👤 پروفایل من")]
    ]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ذخیره اطلاعات کاربران
def save_users():
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# شروع ربات
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in users:
        await message.answer(f"سلام {message.from_user.first_name} عزیز 🌟\nشما قبلاً ثبت‌نام کرده‌اید.", reply_markup=main_menu())
    else:
        btn = types.InlineKeyboardButton(text="✅ شروع عضویت", callback_data="start_register")
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[btn]])
        await message.answer(f"سلام {message.from_user.first_name} 👋\nبرای استفاده از ربات باید ثبت‌نام کنید.", reply_markup=kb)

@dp.callback_query(F.data == "start_register")
async def register_start(callback: types.CallbackQuery):
    await callback.message.answer("لطفاً نام خود را وارد کنید:")
    await callback.answer()
    dp.fsm_data[callback.from_user.id] = {"step": "name"}

@dp.message()
async def handle_messages(message: types.Message):
    user_id = str(message.from_user.id)

    if user_id in dp.fsm_data:
        step_data = dp.fsm_data[user_id]

        if step_data["step"] == "name":
            step_data["name"] = message.text
            step_data["step"] = "instagram"
            await message.answer("آیدی اینستاگرام خود را وارد کنید (بدون @):")

        elif step_data["step"] == "instagram":
            step_data["instagram"] = message.text
            step_data["step"] = "phone"
            kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            kb.add(KeyboardButton(text="ارسال شماره ☎️", request_contact=True))
            await message.answer("لطفاً شماره تماس خود را با دکمه زیر ارسال کنید:", reply_markup=kb)

    elif user_id in users:
        if message.text == "📁 ارسالی‌های شما":
            uploads = users[user_id].get("uploads", [])
            if uploads:
                for item in uploads:
                    await message.answer_media_group(media=[item])
            else:
                await message.answer("شما تاکنون فایلی ارسال نکرده‌اید.")
        elif message.text == "👤 پروفایل من":
            info = users[user_id]
            text = (
                f"<b>👤 نام:</b> {info['name']}\n"
                f"<b>📸 اینستاگرام:</b> @{info['instagram']}\n"
                f"<b>☎️ شماره:</b> {info['phone']}\n"
                f"<b>📂 تعداد فایل‌های ارسالی:</b> {len(info.get('uploads', []))}"
            )
            await message.answer(text)
    else:
        await message.answer("برای استفاده از ربات، ابتدا ثبت‌نام کنید.")

@dp.message(F.contact)
async def get_contact(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id in dp.fsm_data and dp.fsm_data[user_id]["step"] == "phone":
        contact = message.contact
        if contact.user_id != message.from_user.id:
            await message.answer("لطفاً شماره خودتان را با دکمه ارسال کنید، نه تایپ شده!")
            return

        # ثبت کاربر
        dp.fsm_data[user_id]["phone"] = contact.phone_number
        users[user_id] = {
            "name": dp.fsm_data[user_id]["name"],
            "instagram": dp.fsm_data[user_id]["instagram"],
            "phone": dp.fsm_data[user_id]["phone"],
            "uploads": []
        }
        save_users()
        del dp.fsm_data[user_id]
        await message.answer("✅ ثبت‌نام شما با موفقیت انجام شد.", reply_markup=main_menu())

        # اطلاع به ادمین
        link = f"tg://user?id={user_id}"
        await bot.send_message(
            ADMIN_ID,
            f"🎉 <b>ثبت‌نام جدید:</b>\n"
            f"👤 نام: {users[user_id]['name']}\n"
            f"📸 اینستاگرام: @{users[user_id]['instagram']}\n"
            f"☎️ شماره: {users[user_id]['phone']}\n"
            f"🆔 <a href='{link}'>{user_id}</a>"
        )

@dp.message(F.content_type.in_({"photo", "video"}))
async def save_uploads(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("شما هنوز ثبت‌نام نکرده‌اید.")
        return

    file = message.photo[-1].file_id if message.photo else message.video.file_id
    media_type = "photo" if message.photo else "video"
    caption = f"📤 فایل از <a href='tg://user?id={user_id}'>@{message.from_user.username or 'بدون_نام'}</a> | ID: {user_id}"

    if media_type == "photo":
        await bot.send_photo(CHANNEL_ID, file, caption=caption)
    else:
        await bot.send_video(CHANNEL_ID, file, caption=caption)

    users[user_id].setdefault("uploads", []).append(types.InputMediaPhoto(media=file) if media_type == "photo" else types.InputMediaVideo(media=file))
    save_users()
    await message.answer("✅ فایل شما دریافت شد.")

# اجرای Flask برای Railway
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is alive!", 200

# اجرای همزمان Flask و Aiogram
async def main():
    import threading
    threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=8080)).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
