import asyncio
import json
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile, KeyboardButton, ReplyKeyboardMarkup
from aiogram.enums import ParseMode, ContentType
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# مشخصات اصلی ربات
BOT_TOKEN = "8177436123:AAG2RuDLbRI6HdgsCTa7_75TJwuQ151ohLA"
ADMIN_ID = 131555118
CHANNEL_ID = -1002798154695

# ساخت بات و دیسپچر
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# فایل دیتابیس
USERS_FILE = "users.json"

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

users = load_users()

# دکمه‌های دائمی برای کاربران ثبت‌نام‌شده
def get_user_keyboard():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📁 ارسالی‌های شما")],
            [KeyboardButton(text="👤 پروفایل من")]
        ],
        resize_keyboard=True
    )
    return kb

# استیت‌های ثبت‌نام
class RegisterState(StatesGroup):
    name = State()
    instagram = State()
    phone = State()

# شروع بات
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name

    if user_id in users:
        await message.answer(f"سلام {first_name} عزیز 🌟\nشما قبلاً ثبت‌نام کرده‌اید.", reply_markup=get_user_keyboard())
    else:
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ شروع عضویت", callback_data="start_register")
        await message.answer(f"سلام {first_name} عزیز 🌟\nبرای استفاده از ربات ابتدا ثبت‌نام کنید.", reply_markup=kb.as_markup())

# کلیک روی شروع عضویت
@dp.callback_query(F.data == "start_register")
async def start_register(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("لطفاً نام خود را وارد کنید:")
    await state.set_state(RegisterState.name)

# دریافت نام
@dp.message(RegisterState.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("لطفاً آیدی اینستاگرام خود را وارد کنید:")
    await state.set_state(RegisterState.instagram)

# دریافت آیدی اینستاگرام
@dp.message(RegisterState.instagram)
async def get_instagram(message: Message, state: FSMContext):
    await state.update_data(instagram=message.text)

    contact_btn = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 ارسال شماره", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("لطفاً شماره تماس خود را با دکمه زیر ارسال کنید:", reply_markup=contact_btn)
    await state.set_state(RegisterState.phone)

# دریافت شماره تماس
@dp.message(RegisterState.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    phone = message.contact.phone_number
    user_id = str(message.from_user.id)
    username = message.from_user.username or "بدون یوزرنیم"

    users[user_id] = {
        "name": data["name"],
        "instagram": data["instagram"],
        "phone": phone,
        "username": username,
        "uploads": []
    }
    save_users(users)
    await state.clear()

    await message.answer("✅ ثبت‌نام با موفقیت انجام شد.", reply_markup=get_user_keyboard())

    # اطلاع به ادمین
    mention = f"<a href='tg://user?id={user_id}'>{user_id}</a>"
    await bot.send_message(ADMIN_ID, f"🔔 ثبت‌نام جدید:\n👤 نام: {data['name']}\n📸 اینستاگرام: {data['instagram']}\n📞 شماره: {phone}\n🆔 یوزرنیم: @{username}\n🧾 آیدی عددی: {mention}")

# جلوگیری از ارسال دستی شماره
@dp.message(RegisterState.phone)
async def reject_manual_phone(message: Message):
    await message.answer("لطفاً شماره را فقط از طریق دکمه ارسال شماره بفرستید.")

# هندل ارسال فایل (فقط کاربران ثبت‌نام‌شده)
@dp.message(F.content_type.in_({"photo", "video"}))
async def handle_media(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("⚠️ برای استفاده از ربات ابتدا ثبت‌نام کنید.")
        return

    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    file_type = "photo" if message.photo else "video"

    users[user_id]["uploads"].append({
        "type": file_type,
        "file_id": file_id
    })
    save_users(users)

    # ارسال به کانال
    caption = f"ارسال از: @{users[user_id]['username']} | <a href='tg://user?id={user_id}'>{user_id}</a>"
    if file_type == "photo":
        await bot.send_photo(CHANNEL_ID, file_id, caption=caption)
    else:
        await bot.send_video(CHANNEL_ID, file_id, caption=caption)

    await message.answer("✅ فایل با موفقیت ذخیره و ارسال شد.")

# دکمه 📁 ارسالی‌های شما
@dp.message(F.text == "📁 ارسالی‌های شما")
async def show_user_uploads(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("⚠️ شما هنوز ثبت‌نام نکرده‌اید.")
        return

    uploads = users[user_id].get("uploads", [])
    if not uploads:
        await message.answer("شما هنوز فایلی ارسال نکرده‌اید.")
        return

    await message.answer(f"شما {len(uploads)} فایل ارسال کرده‌اید:")
    for item in uploads:
        if item["type"] == "photo":
            await message.answer_photo(item["file_id"])
        else:
            await message.answer_video(item["file_id"])

# دکمه 👤 پروفایل من
@dp.message(F.text == "👤 پروفایل من")
async def show_profile(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("⚠️ شما هنوز ثبت‌نام نکرده‌اید.")
        return

    data = users[user_id]
    await message.answer(
        f"👤 <b>نام:</b> {data['name']}\n"
        f"📸 <b>اینستاگرام:</b> {data['instagram']}\n"
        f"📞 <b>شماره:</b> {data['phone']}\n"
        f"🆔 <b>یوزرنیم:</b> @{data['username']}\n"
        f"📂 <b>تعداد فایل‌های ارسال‌شده:</b> {len(data['uploads'])}"
    )

# لیست کاربران برای ادمین
@dp.message(F.text == "/users")
async def list_users(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not users:
        await message.answer("هیچ کاربری ثبت‌نام نکرده است.")
        return

    for uid, info in users.items():
        kb = InlineKeyboardBuilder()
        kb.button(text="📁 مشاهده ارسالی‌ها", callback_data=f"files_{uid}")
        kb.button(text="❌ حذف", callback_data=f"delete_{uid}")
        mention = f"<a href='tg://user?id={uid}'>{uid}</a>"
        await message.answer(
            f"👤 {info['name']} | @{info['username']} | {mention}",
            reply_markup=kb.as_markup()
        )

# حذف کاربر یا نمایش فایل‌ها برای ادمین
@dp.callback_query(F.data.startswith("delete_") | F.data.startswith("files_"))
async def admin_actions(callback: CallbackQuery):
    action, uid = callback.data.split("_")
    if str(callback.from_user.id) != str(ADMIN_ID):
        return

    if uid not in users:
        await callback.message.answer("کاربر یافت نشد.")
        return

    if action == "delete":
        del users[uid]
        save_users(users)
        await callback.message.answer("✅ کاربر حذف شد.")
    elif action == "files":
        uploads = users[uid].get("uploads", [])
        if not uploads:
            await callback.message.answer("این کاربر فایلی ارسال نکرده است.")
        else:
            for item in uploads:
                if item["type"] == "photo":
                    await callback.message.answer_photo(item["file_id"])
                else:
                    await callback.message.answer_video(item["file_id"])

# تابع اصلی اجرای بات
async def main():
    await dp.start_polling(bot)

# اجرای بات
if __name__ == "__main__":
    asyncio.run(main())
