import logging
import asyncio
import json
import os
import sys
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from keep_alive import keep_alive

API_TOKEN = 'توکن ربات خودت'
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

def user_keyboard(is_admin=False):
    buttons = [
        [KeyboardButton(text="📁 ارسالی‌های شما")],
        [KeyboardButton(text="👤 پروفایل من")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="📋 لیست کاربران")])
        buttons.append([KeyboardButton(text="🛑 خاموش کردن ربات")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    name = message.from_user.first_name

    if user_id in users and users[user_id].get("completed"):
        kb = user_keyboard(is_admin=(message.from_user.id == ADMIN_ID))
        await message.answer("شما قبلاً ثبت‌نام کرده‌اید. اکنون می‌توانید عکس یا کلیپ ارسال کنید.", reply_markup=kb)
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer("سلام ادمین عزیز. شما به پنل مدیریتی دسترسی دارید.", reply_markup=user_keyboard(is_admin=True))
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ شروع عضویت", callback_data="start_register")]
    ])
    await message.answer(
        f"سلام {name} عزیز 👋
برای استفاده از ربات ابتدا باید ثبت‌نام کنید تا بتوانید عکس و کلیپ خود را برای ما ارسال کنید.",
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
    users[user_id]["is_vip"] = False
    users[user_id].pop("step", None)
    save_users(users)

    await message.answer("✅ ثبت‌نام شما با موفقیت انجام شد. اکنون می‌توانید عکس یا کلیپ بفرستید.", reply_markup=user_keyboard())
    await bot.send_message(ADMIN_ID, f"""
📝 <b>ثبت‌نام جدید:</b>
👤 نام: {users[user_id]['name']}
📸 اینستاگرام: {users[user_id]['instagram']}
📞 شماره: {users[user_id]['phone']}
🆔 آیدی عددی: <a href="tg://user?id={user_id}">{user_id}</a>
🔗 یوزرنیم: @{users[user_id]["username"]}
""")
    await state.clear()

@dp.message(F.text == "🛑 خاموش کردن ربات")
async def shutdown_bot(message: Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("ربات در حال خاموش شدن است...")
        await bot.session.close()
        await dp.storage.close()
        sys.exit()

async def main():
    await bot.send_message(ADMIN_ID, "✅ ربات شما با موفقیت دیپلوی و راه‌اندازی شد.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
