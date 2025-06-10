import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, Contact
from aiogram.filters import CommandStart
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "8177436123:AAG2RuDLbRI6HdgsCTa7_75TJwuQ151ohLA"
ADMIN_ID = 131555118
CHANNEL_ID = -1002798154695
USERS_FILE = "users.json"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

users = {}

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def load_users():
    global users
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

load_users()

start_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ شروع عضویت", callback_data="start_register")]
])

user_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📁 ارسالی‌های شما")],
    [KeyboardButton(text="👤 پروفایل من")]
], resize_keyboard=True)

contact_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="ارسال شماره تماس ☎️", request_contact=True)]
], resize_keyboard=True, one_time_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    first_name = message.from_user.first_name
    await message.answer(f"سلام {first_name} عزیز 🌟\nبرای استفاده از ربات باید ثبت‌نام کنی.", reply_markup=start_kb)

@dp.callback_query(F.data == "start_register")
async def start_register(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    if user_id in users:
        await callback.message.answer("شما قبلاً ثبت‌نام کرده‌اید ✅", reply_markup=user_kb)
    else:
        users[user_id] = {"step": "name"}
        await callback.message.answer("لطفاً نام خود را وارد کنید 📝")
    await callback.answer()

@dp.message(F.text & ~F.contact)
async def handle_text(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("برای استفاده از ربات، ابتدا ثبت‌نام کنید.", reply_markup=start_kb)
        return

    user = users[user_id]
    step = user.get("step")

    if step == "name":
        user["name"] = message.text
        user["step"] = "instagram"
        await message.answer("آیدی اینستاگرام خود را وارد کنید 📸")
    elif step == "instagram":
        user["instagram"] = message.text
        user["step"] = "phone"
        await message.answer("لطفاً شماره تماس خود را با دکمه زیر ارسال کنید ☎️", reply_markup=contact_kb)
    else:
        await message.answer("شما ثبت‌نام را قبلاً انجام داده‌اید ✅", reply_markup=user_kb)

    save_users()

@dp.message(F.contact)
async def handle_contact(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("ابتدا ثبت‌نام را انجام دهید.", reply_markup=start_kb)
        return

    contact: Contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer("لطفاً فقط با دکمه ارسال، شماره خود را ارسال کنید.")
        return

    users[user_id]["phone"] = contact.phone_number
    users[user_id]["username"] = message.from_user.username or "بدون_نام‌کاربری"
    users[user_id]["step"] = "done"
    users[user_id]["uploads"] = []

    save_users()

    await message.answer("✅ ثبت‌نام با موفقیت انجام شد. حالا می‌تونی عکس یا ویدیو ارسال کنی.", reply_markup=user_kb)

    info = users[user_id]
    await bot.send_message(
        ADMIN_ID,
        f"🆕 ثبت‌نام جدید:\n\n"
        f"👤 نام: {info.get('name')}\n"
        f"📸 اینستاگرام: {info.get('instagram')}\n"
        f"☎️ شماره: {info.get('phone')}\n"
        f"🔗 <a href='tg://user?id={user_id}'>مشاهده پروفایل</a>\n"
        f"🔢 ID: {user_id}\n"
        f"📛 username: @{info.get('username')}"
    )

@dp.message(F.photo | F.video)
async def handle_media(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users or users[user_id].get("step") != "done":
        await message.answer("برای ارسال فایل، ابتدا ثبت‌نام کنید.", reply_markup=start_kb)
        return

    users[user_id]["uploads"].append(message.message_id)
    save_users()

    file_caption = f"📤 فایل از: @{message.from_user.username or 'ندارد'}\n🆔 <a href='tg://user?id={user_id}'>{user_id}</a>"

    if message.photo:
        await bot.copy_message(CHANNEL_ID, message.chat.id, message.message_id, caption=file_caption)
    elif message.video:
        await bot.copy_message(CHANNEL_ID, message.chat.id, message.message_id, caption=file_caption)

    await message.answer("فایل شما با موفقیت ارسال شد ✅")

@dp.message(F.text == "📁 ارسالی‌های شما")
async def my_uploads(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users or users[user_id].get("step") != "done":
        await message.answer("ابتدا ثبت‌نام کنید.", reply_markup=start_kb)
        return

    uploads = users[user_id].get("uploads", [])
    if not uploads:
        await message.answer("شما هنوز فایلی ارسال نکرده‌اید.")
        return

    await message.answer("📁 فایل‌های ارسالی شما:")
    for msg_id in uploads:
        await bot.copy_message(message.chat.id, message.chat.id, msg_id)

@dp.message(F.text == "👤 پروفایل من")
async def profile(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("ابتدا ثبت‌نام کنید.")
        return

    info = users[user_id]
    await message.answer(
        f"👤 <b>نام:</b> {info.get('name', 'ندارد')}\n"
        f"📸 <b>اینستاگرام:</b> {info.get('instagram', 'ندارد')}\n"
        f"☎️ <b>شماره:</b> {info.get('phone', 'ندارد')}\n"
        f"📁 <b>تعداد فایل‌های ارسالی:</b> {len(info.get('uploads', []))}"
    )

@dp.message(F.text == "/admin")  # فقط برای مدیر
async def list_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = "📋 لیست کاربران:\n\n"
    for user_id, info in users.items():
        name = info.get("name", "نام‌وارد‌نشده")
        username = info.get("username", "بدون‌نام‌کاربری")
        text += f"👤 {name} | @{username} | <a href='tg://user?id={user_id}'>نمایش</a>\n"

    await message.answer(text)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
