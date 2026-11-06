import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ДАННЫЕ О ПРЕПАРАТАХ ==========
# Заполните карточки на основе реальных инструкций. Цены — ориентировочные!
DRUGS = {
    "ketorolac": {
        "name": "Кеторолак (Кетанов)",
        "desc": "От чего: сильная боль (зубная, мышечная, послеоперационная).\n"
                "Дозировка: 10 мг внутрь каждые 4-6 ч, макс 40 мг/сут. Курс не более 5 дней.\n"
                "Цена: ~50-150 руб. (таблетки).\n"
                "Рецепт: Да (по инструкции, но часто продаётся свободно).\n"
                "Противопоказания: язва желудка, почечная недостаточность, беременность, детям до 16 лет."
    },
    "ibuprofen": {
        "name": "Ибупрофен",
        "desc": "От чего: боль слабой/умеренной интенсивности, воспаление, температура.\n"
                "Дозировка: 200-400 мг каждые 4-6 ч, макс 1200 мг/сут (безрецептурно).\n"
                "Цена: ~30-100 руб.\n"
                "Рецепт: Нет.\n"
                "Противопоказания: язва, астма (аспириновая), 3-й триместр беременности, тяжёлая почечная/печёночная недостаточность."
    },
    "paracetamol": {
        "name": "Парацетамол",
        "desc": "От чего: боль слабой интенсивности, температура.\n"
                "Дозировка: 500-1000 мг до 4 раз в сутки, макс 4 г/сут.\n"
                "Цена: ~20-80 руб.\n"
                "Рецепт: Нет.\n"
                "Противопоказания: печёночная недостаточность, алкоголизм, дефицит глюкозо-6-фосфатдегидрогеназы."
    },
    "septolete": {
        "name": "Септолете Тотал",
        "desc": "От чего: боль в горле, воспаление, инфекции полости рта.\n"
                "Дозировка: Таблетки — 1 шт. каждые 3-6 ч (макс 4/сут). Спрей — 1-2 впрыска каждые 2 ч (макс 3-5/сут).\n"
                "Цена: ~300-500 руб.\n"
                "Рецепт: Нет.\n"
                "Противопоказания: дети до 6 лет, индивидуальная непереносимость компонентов."
    },
    # Пример препарата для категории, которая раньше была пустой
    "lisinopril": {
        "name": "Лизиноприл",
        "desc": "От чего: повышенное артериальное давление.\n"
                "Дозировка: Назначается индивидуально врачом (обычно 5-10 мг/сут).\n"
                "Цена: ~50-150 руб.\n"
                "Рецепт: Да (строго по рецепту!).\n"
                "Противопоказания: ангионевротический отек в анамнезе, беременность, стеноз почечных артерий."
    }
}

# ========== КЛАВИАТУРЫ ==========
def main_menu():
    builder = InlineKeyboardBuilder()
    buttons = [
        ("💊 Обезболивающее", "sym_pain"),
        ("🤧 ОРВИ", "sym_orvi"),
        ("🤢 Отравление", "sym_poison"),
        ("💪 Мышечная боль", "sym_muscle"),
        ("😷 Боль в горле", "sym_throat"),
        ("❤️ Давление", "sym_bp"),
    ]
    for text, data in buttons:
        builder.add(InlineKeyboardButton(text=text, callback_data=data))
    builder.adjust(2)
    return builder.as_markup()

def form_menu(symptom):
    forms = {
        "sym_pain": [("Таблетки", "form_pain_tab")],
        "sym_orvi": [("Таблетки", "form_orvi_tab"), ("Сироп", "form_orvi_syr"), ("Спрей", "form_orvi_spray")],
        "sym_poison": [("Таблетки", "form_poison_tab"), ("Раствор", "form_poison_sol")],
        "sym_muscle": [("Таблетки", "form_muscle_tab"), ("Гель/Спрей", "form_muscle_gel")],
        "sym_throat": [("Таблетки", "form_throat_tab"), ("Спрей", "form_throat_spray")],
        "sym_bp": [("Таблетки", "form_bp_tab")],
    }[symptom]
    builder = InlineKeyboardBuilder()
    for text, data in forms:
        builder.add(InlineKeyboardButton(text=text, callback_data=data))
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_main"))
    builder.adjust(1)
    return builder.as_markup()

def drug_menu(form_key):
    mapping = {
        "form_pain_tab": ["ketorolac", "ibuprofen", "paracetamol"],
        "form_orvi_tab": ["paracetamol", "ibuprofen"],
        "form_throat_tab": ["septolete"],
        "form_throat_spray": ["septolete"],
        "form_muscle_tab": ["ibuprofen", "ketorolac"],
        "form_muscle_gel": [], # Здесь пока пусто
        "form_poison_tab": [], # Здесь пока пусто
        "form_bp_tab": ["lisinopril"], # Добавили препарат
        "form_orvi_syr": [], # Здесь пока пусто
        "form_orvi_spray": [], # Здесь пока пусто
        "form_poison_sol": [], # Здесь пока пусто
    }.get(form_key, [])
    
    builder = InlineKeyboardBuilder()
    
    # Если препаратов нет, показываем кнопку-заглушку
    if not mapping:
        builder.add(InlineKeyboardButton(text="❌ В этой категории пока нет препаратов", callback_data="ignore"))
    else:
        for drug_id in mapping:
            if drug_id in DRUGS:
                builder.add(InlineKeyboardButton(text=DRUGS[drug_id]["name"], callback_data=f"drug_{drug_id}"))
                
    builder.add(InlineKeyboardButton(text="🔙 Назад", callback_data="back_main"))
    builder.adjust(1)
    return builder.as_markup()

# ========== ХЕНДЛЕРЫ ==========
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Выберите симптом:", reply_markup=main_menu())

@dp.callback_query(F.data.startswith("sym_"))
async def handle_symptom(callback: CallbackQuery):
    await callback.message.edit_text("Выберите форму выпуска:", reply_markup=form_menu(callback.data))
    await callback.answer()

@dp.callback_query(F.data.startswith("form_"))
async def handle_form(callback: CallbackQuery):
    await callback.message.edit_text("Выберите препарат:", reply_markup=drug_menu(callback.data))
    await callback.answer()

@dp.callback_query(F.data.startswith("drug_"))
async def handle_drug(callback: CallbackQuery):
    drug_id = callback.data.replace("drug_", "")
    drug = DRUGS.get(drug_id)
    if drug:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text="🔙 В начало", callback_data="back_main"))
        await callback.message.edit_text(drug["desc"], reply_markup=builder.as_markup())
    await callback.answer()

@dp.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text("Выберите симптом:", reply_markup=main_menu())
    await callback.answer()

# Обработчик для пустой кнопки (чтобы бот не зависал)
@dp.callback_query(F.data == "ignore")
async def ignore_button(callback: CallbackQuery):
    await callback.answer("Для этого симптома данная форма выпуска не применяется.", show_alert=True)

# ========== ВЕБ-СЕРВЕР ДЛЯ RENDER ==========
async def handle_web(request):
    return web.Response(text="OK")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
