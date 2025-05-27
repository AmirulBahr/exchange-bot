from keep_alive import start_web
import logging
import json
import re
from aiogram import Bot, Dispatcher, executor, types

API_TOKEN = "7222497947:AAEB-_KFbfutXwrW2BsavypFLDiSCu61qKY"
ADMIN_USERNAME = "@rus_tam0"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

with open("rates.json", "r", encoding="utf-8") as f:
    RATES = json.load(f)

user_state = {}

menu_kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
menu_kb.add("Купить USDT", "Продать USDT")
menu_kb.add("Обмен валют", "Перестановка денег")
menu_kb.add("Контакты", "График работы")

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_state.pop(message.from_user.id, None)
    welcome = (
        "Добро пожаловать в официальный Telegram-бот обменного пункта!\n"
        "Мы работаем с валютой и криптовалютой.\n"
        "Гарантируем надёжность, конфиденциальность и индивидуальный подход.\n"
        "Выберите нужный раздел ниже:"
    )
    await message.answer(welcome, reply_markup=menu_kb)

@dp.message_handler(lambda m: m.text == "График работы")
async def handle_hours(message: types.Message):
    await message.answer("""График работы:\nПонедельник–Суббота\nс 10:00 до 20:00""")

@dp.message_handler(lambda m: m.text == "Контакты")
async def handle_contacts(message: types.Message):
    await message.answer("По всем вопросам: @rus_tam0")

@dp.message_handler(lambda m: m.text in ["Купить USDT", "Продать USDT", "Обмен валют", "Перестановка денег"])
async def handle_exchange(message: types.Message):
    user_state[message.from_user.id] = {"step": "direction"}
    await message.answer("Введите направление обмена (например: USD-TRY):")

@dp.message_handler()
async def handle_steps(message: types.Message):
    user_id = message.from_user.id
    state = user_state.get(user_id, {})

    if not state:
        await message.answer("Пожалуйста, начните с выбора действия из меню /start", reply_markup=menu_kb)
        return

    step = state.get("step")

    if step == "direction":
        direction = message.text.upper()
        if direction not in RATES:
            await message.answer("Такое направление не поддерживается. Попробуйте снова.")
            return
        state["direction"] = direction
        state["rate"] = RATES[direction]
        state["step"] = "amount"
        await message.answer(f"Курс {direction}: 1 = {state['rate']}\nВведите сумму:")

    elif step == "amount":
        try:
            amount = float(message.text)
            state["amount"] = amount
            state["total"] = round(amount * state["rate"], 2)
            state["step"] = "name"
            await message.answer("Введите ваше полное имя:")
        except ValueError:
            await message.answer("Введите числовую сумму.")

    elif step == "name":
        state["name"] = message.text.strip()
        state["step"] = "phone"
        await message.answer("Введите номер телефона (пример: +79001234567):")

    elif step == "phone":
        phone = message.text.strip()
        if not re.match(r'^\+?\d{10,15}$', phone):
            await message.answer("Некорректный номер. Введите номер в международном формате.")
            return
        state["phone"] = phone
        state["step"] = "confirm"

        direction = state["direction"]
        amount = state["amount"]
        total = state["total"]
        name = state["name"]
        username = f"@{message.from_user.username}" if message.from_user.username else "Нет username"

        summary = (
            f"Подтвердите заявку:\n"
            f"Имя: {name}\n"
            f"Телефон: {phone}\n"
            f"Username: {username}\n"
            f"Направление: {direction}\n"
            f"Сумма: {amount}\n"
            f"К получению: {total}"
        )

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm"),
            types.InlineKeyboardButton("❌ Отмена", callback_data="cancel")
        )
        await message.answer(summary, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data in ["confirm", "cancel"])
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    state = user_state.pop(user_id, {})

    if callback_query.data == "cancel":
        await bot.send_message(user_id, "Заявка отменена.")
        await bot.answer_callback_query(callback_query.id, "Отмена подтверждена.")
        return

    if not state:
        await bot.answer_callback_query(callback_query.id, "Заявка не найдена.")
        return

    direction = state["direction"]
    amount = state["amount"]
    total = state["total"]
    name = state["name"]
    phone = state["phone"]
    username = f"@{callback_query.from_user.username}" if callback_query.from_user.username else "Нет username"

    text = (
        "НОВАЯ ЗАЯВКА\n"
        f"Имя: {name}\n"
        f"Телефон: {phone}\n"
        f"Username: {username}\n"
        f"Направление: {direction}\n"
        f"Сумма: {amount}\n"
        f"К получению: {total}"
    )

    await bot.send_message(ADMIN_USERNAME, text)
    await bot.send_message(user_id, "Заявка отправлена. Мы свяжемся с вами в ближайшее время.")
    await bot.answer_callback_query(callback_query.id, "Заявка подтверждена.")

if __name__ == "__main__":
    start_web()
    if __name__ == "__main__":
    start_web()
    executor.start_polling(dp, skip_updates=True)
