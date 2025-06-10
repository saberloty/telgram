import json import os from aiogram import Bot, Dispatcher, F, types from aiogram.enums import ParseMode, ContentType from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton from aiogram.filters import CommandStart, Command from aiogram.utils.markdown import hlink from aiogram.fsm.context import FSMContext from aiogram.fsm.state import State, StatesGroup from storage import load_users_data, save_users_data

TOKEN = os.getenv("BOT_TOKEN") ADMIN_ID = 131555118 CHANNEL_ID = -1002798154695

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML) dp = Dispatcher()

users_data = load_users_data()

class RegisterStates(StatesGroup): name = State() instagram = State() phone = State()

@dp.message(CommandStart()) async def start(message: Message, state: FSMContext): user_id = str(message.from_user.id) if user_id in users_data: await message.answer(f"سلام {message.from_user.first_name} عزیز 🌟\nشما قبلاً ثبت‌نام کرده‌اید و می‌توانید عکس یا کلیپ ارسال کنید.", reply_markup=main_keyboard(message.from_user.id)) else: kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="✅ شروع عضویت")]], resize_keyboard=True) await message.answer(f"سلام {message.from_user.first_name} عزیز 🌟\nبرای استفاده از ربات ابتدا باید ثبت‌نام کنید تا بتوانید عکس و کلیپ خود را برای ما ارسال کنید.", reply_markup=kb)

@dp.message(F.text == "✅ شروع عضویت") async def ask_name(message: Message, state: FSMContext): await state.set_state(RegisterStates.name) await message.answer("لطفاً نام کامل خود را وارد کنید:")

@dp.message(RegisterStates.name) async def ask_instagram(message: Message, state: FSMContext): await state.update_data(name=message.text) await state.set_state(RegisterStates.instagram) await message.answer("آیدی پیج اینستاگرام خود را وارد کنید:")

@dp.message(RegisterStates.instagram) async def ask_phone(message: Message, state: FSMContext): await state.update_data(instagram=message.text) contact_button = KeyboardButton(text="📞 ارسال شماره تماس", request_contact=True) kb = ReplyKeyboardMarkup(keyboard=[[contact_button]], resize_keyboard=True, one_time_keyboard=True) await state.set_state(RegisterStates.phone) await message.answer("لطفاً شماره موبایل واقعی خود را از طریق دکمه زیر ارسال کنید:", reply_markup=kb)

@dp.message(RegisterStates.phone, F.contact) async def complete_registration(message: Message, state: FSMContext): user_id = str(message.from_user.id) data = await state.get_data() users_data[user_id] = { "name": data["name"], "instagram": data["instagram"], "phone": message.contact.phone_number, "uploads": [], "vip": False } save_users_data(users_data) await state.clear()

await message.answer("✅ ثبت‌نام با موفقیت انجام شد! اکنون می‌توانید عکس یا کلیپ ارسال کنید.", reply_markup=main_keyboard(message.from_user.id))

caption = f"🆕 کاربر جدید ثبت‌نام کرد:\n👤 نام: {data['name']}\n📸 اینستاگرام: {data['instagram']}\n📞 شماره: {message.contact.phone_number}\n🆔 آیدی: {hlink(user_id, f'tg://user?id={user_id}') }"
await bot.send_message(chat_id=ADMIN_ID, text=caption)

@dp.message(F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO})) async def handle_upload(message: Message): user_id = str(message.from_user.id) if user_id not in users_data: return await message.answer("برای ارسال فایل ابتدا ثبت‌نام کنید.")

users_data[user_id]["uploads"].append(message.photo[-1].file_id if message.photo else message.video.file_id)

# VIP check
if not users_data[user_id].get("vip") and len(users_data[user_id]["uploads"]) >= 5:
    users_data[user_id]["vip"] = True
    await message.answer("🎉 تبریک! شما اکنون کاربر VIP شدید.")

save_users_data(users_data)

caption = f"📥 فایل جدید از {message.from_user.username or '-'}\n🆔 {hlink(user_id, f'tg://user?id={user_id}') }"
await bot.send_photo(chat_id=CHANNEL_ID, photo=message.photo[-1].file_id, caption=caption) if message.photo else await bot.send_video(chat_id=CHANNEL_ID, video=message.video.file_id, caption=caption)

@dp.message(F.text == "📁 ارسالی‌های شما") async def show_user_uploads(message: Message): user_id = str(message.from_user.id) if user_id not in users_data: return await message.answer("برای استفاده از این گزینه ابتدا ثبت‌نام کنید.")

uploads = users_data[user_id].get("uploads", [])
if not uploads:
    return await message.answer("شما هنوز فایلی ارسال نکرده‌اید.")

for file_id in uploads:
    try:
        await bot.send_photo(chat_id=message.chat.id, photo=file_id)
    except:
        await bot.send_video(chat_id=message.chat.id, video=file_id)

@dp.message(F.text == "👤 پروفایل من") async def show_profile(message: Message): user_id = str(message.from_user.id) if user_id not in users_data: return await message.answer("برای استفاده از این گزینه ابتدا ثبت‌نام کنید.")

data = users_data[user_id]
await message.answer(f"👤 نام: {data['name']}\n📸 اینستاگرام: {data['instagram']}\n📞 شماره: {data['phone']}\n📂 تعداد فایل‌های ارسال‌شده: {len(data['uploads'])}\n⭐️ وضعیت: {'VIP' if data['vip'] else 'عادی'}")

@dp.message(Command("users")) async def list_users(message: Message): if message.from_user.id != ADMIN_ID: return

text = "👥 لیست کاربران ثبت‌نام‌کرده:\n"
for uid, info in users_data.items():
    user_link = f"tg://user?id={uid}"
    text += f"\n👤 <a href='{user_link}'>{info['name']}</a> | فایل‌ها: {len(info['uploads'])}"
    text += f"\n🔘 <b>/del_{uid}</b> | <b>/show_{uid}</b>\n"

await message.answer(text)

@dp.message(F.text == "👥 کاربران") async def users_button_handler(message: Message): if message.from_user.id != ADMIN_ID: return await list_users(message)

@dp.message(F.text.startswith("/del_")) async def delete_user(message: Message): if message.from_user.id != ADMIN_ID: return

uid = message.text.split("_", 1)[1]
if uid in users_data:
    users_data.pop(uid)
    save_users_data(users_data)
    await message.answer(f"کاربر {uid} حذف شد.")

@dp.message(F.text.startswith("/show_")) async def show_user_files(message: Message): if message.from_user.id != ADMIN_ID: return

uid = message.text.split("_", 1)[1]
if uid not in users_data:
    return await message.answer("کاربر یافت نشد.")

for file_id in users_data[uid].get("uploads", []):
    try:
        await bot.send_photo(chat_id=ADMIN_ID, photo=file_id)
    except:
        await bot.send_video(chat_id=ADMIN_ID, video=file_id)

def main_keyboard(user_id: int): buttons = [ [KeyboardButton(text="📁 ارسالی‌های شما")], [KeyboardButton(text="👤 پروفایل من")] ] if user_id == ADMIN_ID: buttons.append([KeyboardButton(text="👥 کاربران")]) return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

if name == "main": import asyncio from aiogram import executor

async def run():
    await dp.start_polling(bot)

asyncio.run(run())

