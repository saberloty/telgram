import json
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

API_TOKEN = '8177436123:AAG2RuDLbRI6HdgsCTa7_75TJwuQ151ohLA'
ADMIN_ID = 131555118
CHANNEL_ID = -1002798154695

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

users_file = 'users.json'
bot_active = {'status': True}

def load_users():
    try:
        with open(users_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(users_file, 'w') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users = load_users()

def get_main_keyboard():
    keyboard = [
        [KeyboardButton(text='📁 ارسالی‌های شما')],
        [KeyboardButton(text='👤 پروفایل من')],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_admin_keyboard():
    keyboard = [
        [KeyboardButton(text='📁 ارسالی‌های شما')],
        [KeyboardButton(text='👤 پروفایل من')],
        [KeyboardButton(text='👥 لیست کاربران')],
        [KeyboardButton(text='🛑 خاموش کردن ربات' if bot_active['status'] else '✅ روشن کردن ربات')],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name
    if user_id in users:
        text = f"سلام {first_name} عزیز 🖐\nخوش اومدی به ربات ❤️"
        keyboard = get_admin_keyboard() if int(user_id) == ADMIN_ID else get_main_keyboard()
        await message.answer(text, reply_markup=keyboard)
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="✅ شروع عضویت", callback_data="start_register")
        await message.answer(f"سلام {first_name} عزیز 🖐\nبرای استفاده از ربات ابتدا باید عضو بشی.",
                             reply_markup=keyboard.as_markup())

@dp.callback_query(F.data == 'start_register')
async def register_step_1(callback_query):
    user_id = str(callback_query.from_user.id)
    users[user_id] = {'name': '', 'instagram': '', 'phone': '', 'uploads': []}
    await callback_query.message.answer("لطفا نام خود را وارد کنید:", reply_markup=ReplyKeyboardRemove())
    await callback_query.answer()
    dp.fsm[user_id] = 'name'

@dp.message()
async def handle_message(message: Message):
    user_id = str(message.from_user.id)

    if message.text == '🛑 خاموش کردن ربات' and user_id == str(ADMIN_ID):
        bot_active['status'] = False
        await message.answer("ربات غیرفعال شد ❌", reply_markup=get_admin_keyboard())
        return
    if message.text == '✅ روشن کردن ربات' and user_id == str(ADMIN_ID):
        bot_active['status'] = True
        await message.answer("ربات فعال شد ✅", reply_markup=get_admin_keyboard())
        return

    if not bot_active['status'] and user_id != str(ADMIN_ID):
        await message.answer("ربات در حال حاضر غیرفعال است. لطفا بعداً مراجعه کنید.")
        return

    state = dp.fsm.get(user_id)

    if state == 'name':
        users[user_id]['name'] = message.text
        dp.fsm[user_id] = 'instagram'
        await message.answer("لطفا آیدی اینستاگرام خود را وارد کنید:")
    elif state == 'instagram':
        users[user_id]['instagram'] = message.text
        dp.fsm[user_id] = 'phone'
        keyboard = ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="📞 ارسال شماره تماس", request_contact=True)]
        ], resize_keyboard=True)
        await message.answer("لطفا شماره تماس خود را ارسال کنید:", reply_markup=keyboard)
    elif message.contact:
        if user_id in dp.fsm and dp.fsm[user_id] == 'phone':
            users[user_id]['phone'] = message.contact.phone_number
            del dp.fsm[user_id]
            save_users(users)
            await message.answer("ثبت‌نام شما با موفقیت انجام شد ✅", reply_markup=get_main_keyboard())
            await bot.send_message(ADMIN_ID,
                f"<b>ثبت‌نام جدید:</b>\n"
                f"👤 نام: {users[user_id]['name']}\n"
                f"📸 اینستاگرام: {users[user_id]['instagram']}\n"
                f"📞 شماره: {users[user_id]['phone']}\n"
                f"🆔 <a href='tg://user?id={user_id}'>{user_id}</a>")
    elif message.text == '📁 ارسالی‌های شما':
        uploads = users.get(user_id, {}).get('uploads', [])
        if uploads:
            for file_id in uploads:
                await message.answer_document(file_id)
        else:
            await message.answer("شما هنوز فایلی ارسال نکرده‌اید.")
    elif message.text == '👤 پروفایل من':
        profile = users.get(user_id)
        if profile:
            await message.answer(
                f"👤 نام: {profile['name']}\n"
                f"📸 اینستاگرام: {profile['instagram']}\n"
                f"📞 شماره: {profile['phone']}\n"
                f"📁 تعداد فایل‌های ارسالی: {len(profile['uploads'])}")
    elif message.text == '👥 لیست کاربران' and user_id == str(ADMIN_ID):
        for uid, data in users.items():
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❌ حذف", callback_data=f"delete_{uid}")],
                [InlineKeyboardButton(text="📂 مشاهده ارسالی‌ها", callback_data=f"files_{uid}")]
            ])
            await message.answer(
                f"👤 {data['name']}\n📸 {data['instagram']}\n📞 {data['phone']}\n🆔 <a href='tg://user?id={uid}'>{uid}</a>",
                reply_markup=keyboard)

@dp.callback_query()
async def handle_callbacks(callback_query):
    user_id = str(callback_query.from_user.id)
    data = callback_query.data

    if data.startswith("delete_"):
        target_id = data.split("_")[1]
        if target_id in users:
            del users[target_id]
            save_users(users)
            await callback_query.message.edit_text("کاربر حذف شد ❌")
    elif data.startswith("files_"):
        target_id = data.split("_")[1]
        uploads = users.get(target_id, {}).get('uploads', [])
        if uploads:
            for file_id in uploads:
                await bot.send_document(ADMIN_ID, file_id)
        else:
            await callback_query.message.answer("هیچ فایلی برای این کاربر موجود نیست.")
    await callback_query.answer()

@dp.message(F.content_type.in_({'photo', 'video'}))
async def handle_media(message: Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        await message.answer("برای ارسال فایل ابتدا باید ثبت‌نام کنید.")
        return

    file_id = message.photo[-1].file_id if message.photo else message.video.file_id
    users[user_id]['uploads'].append(file_id)
    save_users(users)

    caption = message.caption or "ارسال جدید 🆕"
    user_caption = f"{caption}\n\n👤 <a href='tg://user?id={user_id}'>{message.from_user.username or 'کاربر ناشناس'}</a> | {user_id}"

    await bot.send_message(ADMIN_ID, f"📥 فایل جدید از <a href='tg://user?id={user_id}'>{user_id}</a>")
    await bot.send_chat_action(ADMIN_ID, "upload_document")

    if message.photo:
        await bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=user_caption)
        await bot.send_photo(chat_id=CHANNEL_ID, photo=file_id, caption=user_caption)
    elif message.video:
        await bot.send_video(chat_id=ADMIN_ID, video=file_id, caption=user_caption)
        await bot.send_video(chat_id=CHANNEL_ID, video=file_id, caption=user_caption)

async def main():
    dp.fsm = {}
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
