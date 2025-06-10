import logging
import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from keep_alive import keep_alive

API_TOKEN = '8177436123:AAG2RuDLbRI6HdgsCTa7_75TJwuQ151ohLA'
ADMIN_ID = 131555118
CHANNEL_ID = -1002798154695
USERS_FILE = "users.json"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class RegisterState(StatesGroup):
    waiting_for_name = State()
    waiting_for_instagram = State()
    waiting_for_phone = State()

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = load_users()

def user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 ارسالی‌های شما")],
            [KeyboardButton(text="👤 پروفایل من")]
        ],
        resize_keyboard=True
    )

@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    name = message.from_user.first_name
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ شروع عضویت", callback_data="start_register")]
    ])
    await message.answer(
        f"سلام {name} عزیز 👋\nبرای استفاده از ربات ابتدا باید ثبت‌نام کنید تا بتوانید عکس و کلیپ خود را برای ما ارسال کنید.",
        reply_markup=kb
    )

@dp.callback_query(F.data == "start_register")
async def begin_register(callback: types.CallbackQuery, state: FSMContext):
    user_id = str(callback.from_user.id)
    if user_id in users and users[user_id].get("completed"):
        await callback.message.answer("شما قبلاً ثبت‌نام کرده‌اید.", reply_markup=user_keyboard())
        return
    users[user_id] = {"step": "ask_name"}
    save_users(users)
    await callback.message.answer("لطفاً نام خود را وارد کنید:")
    await state.set_state(RegisterState.waiting_for_name)

@dp.message(RegisterState.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users[user_id]["name"] = message.text
    users[user_id]["step"] = "ask_instagram"
    save_users(users)
    await message.answer("لطفاً آیدی اینستاگرام خود را وارد کنید:")
    await state.set_state(RegisterState.waiting_for_instagram)

@dp.message(RegisterState.waiting_for_instagram)
async def get_instagram(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    users[user_id]["instagram"] = message.text
    users[user_id]["step"] = "ask_phone"
    save_users(users)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 ارسال شماره من", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("فقط از طریق دکمه زیر شماره خود را ارسال کنید:", reply_markup=kb)
    await state.set_state(RegisterState.waiting_for_phone)

@dp.message(RegisterState.waiting_for_phone, F.contact)
async def get_real_phone(message: Message, state: FSMContext):
    if message.contact.user_id != message.from_user.id:
        await message.answer("⚠️ فقط شماره خودتان را ارسال کنید.")
        return
    user_id = str(message.from_user.id)
    users[user_id]["phone"] = message.contact.phone_number
    users[user_id]["completed"] = True
    users[user_id]["username"] = message.from_user.username or "ندارد"
    users[user_id]["uploads"] = []
    users[user_id].pop("step", None)
    save_users(users)

    await message.answer("✅ ثبت‌نام شما با موفقیت انجام شد اکنون میتوانید عکس یا کلیپ بفرستید.", reply_markup=user_keyboard())
    await bot.send_message(ADMIN_ID, f"""
📝 <b>ثبت‌نام جدید:</b>
👤 نام: {users[user_id]['name']}
📸 اینستاگرام: {users[user_id]['instagram']}
📞 شماره: {users[user_id]['phone']}
🆔 آیدی عددی: <a href="tg://user?id={user_id}">{user_id}</a>
🔗 یوزرنیم: @{users[user_id]["username"]}
""")
    await state.clear()

@dp.message(RegisterState.waiting_for_phone)
async def reject_typed_phone(message: Message):
    await message.answer("❌ لطفاً فقط با دکمه '📱 ارسال شماره من' شماره‌تان را بفرستید.")

@dp.message(F.photo | F.video)
async def handle_media(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users or not users[user_id].get("completed"):
        await message.answer("ابتدا ثبت‌نام را کامل کنید.")
        return

    file_info = {"type": "photo" if message.photo else "video", "file_id": None}
    caption = f"📤 ارسال جدید\n👤 @{message.from_user.username or 'ندارد'}\n🆔 <a href='tg://user?id={user_id}'>{user_id}</a>"

    if message.photo:
        file_info["file_id"] = message.photo[-1].file_id
        await bot.send_photo(chat_id=CHANNEL_ID, photo=file_info["file_id"], caption=caption)
        await bot.send_photo(chat_id=ADMIN_ID, photo=file_info["file_id"], caption=caption)
    else:
        file_info["file_id"] = message.video.file_id
        await bot.send_video(chat_id=CHANNEL_ID, video=file_info["file_id"], caption=caption)
        await bot.send_video(chat_id=ADMIN_ID, video=file_info["file_id"], caption=caption)

    users[user_id].setdefault("uploads", []).append(file_info)
    save_users(users)
    await message.answer("✅ فایل شما دریافت شد.")

@dp.message(F.text == "📁 ارسالی‌های شما")
async def your_uploads(message: Message):
    user_id = str(message.from_user.id)
    uploads = users.get(user_id, {}).get("uploads", [])
    if not uploads:
        await message.answer("شما هنوز فایلی ارسال نکرده‌اید.")
        return
    for item in uploads:
        if item["type"] == "photo":
            await message.answer_photo(photo=item["file_id"])
        else:
            await message.answer_video(video=item["file_id"])

@dp.message(F.text == "👤 پروفایل من")
async def show_profile(message: Message):
    user_id = str(message.from_user.id)
    data = users.get(user_id)
    if not data:
        await message.answer("شما هنوز ثبت‌نام نکرده‌اید.")
        return
    await message.answer(f"""
👤 نام: {data['name']}
📸 اینستاگرام: {data['instagram']}
📞 شماره: {data['phone']}
🔗 یوزرنیم: @{data['username']}
🆔 آیدی عددی: <a href="tg://user?id={user_id}">{user_id}</a>
📂 تعداد فایل‌های ارسالی: {len(data.get('uploads', []))}
""")

@dp.message(F.text == "/users")
async def list_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    for uid, data in users.items():
        if data.get("completed"):
            info = f"""
👤 نام: {data['name']}
📸 اینستاگرام: {data['instagram']}
📞 شماره: {data['phone']}
🆔 آیدی عددی: <a href="tg://user?id={uid}">{uid}</a>
🔗 یوزرنیم: @{data.get('username', 'ندارد')}
"""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🗑 حذف", callback_data=f"delete_{uid}"),
                    InlineKeyboardButton(text="📁 ارسالی‌ها", callback_data=f"view_{uid}")
                ]
            ])
            await message.answer(info, reply_markup=keyboard)

@dp.callback_query(F.data.startswith("delete_"))
async def handle_delete_user(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    user_id = callback.data.replace("delete_", "")
    if user_id in users:
        users.pop(user_id)
        save_users(users)
        await callback.message.edit_text("❌ کاربر حذف شد.")
        await callback.answer("حذف شد.")

@dp.callback_query(F.data.startswith("view_"))
async def handle_view_uploads(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    user_id = callback.data.replace("view_", "")
    uploads = users.get(user_id, {}).get("uploads", [])
    if not uploads:
        await callback.message.answer("کاربر فایلی ارسال نکرده است.")
        return
    for item in uploads:
        if item["type"] == "photo":
            await bot.send_photo(chat_id=ADMIN_ID, photo=item["file_id"])
        else:
            await bot.send_video(chat_id=ADMIN_ID, video=item["file_id"])
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())