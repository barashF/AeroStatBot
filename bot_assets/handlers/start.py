from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    Message,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineQuery,
    ChosenInlineResult,
    InputFile,
    BufferedInputFile,
    CallbackQuery,
    FSInputFile
)
from configuration.config import API_BASE_URL
import aiohttp
from infrastructure.api_clients.city_client import APIClient
from infrastructure.api_clients.models import Statistic
from infrastructure.gen_image import generate_bas_usage_chart, generate_flights_cards, generate_regions_table, generate_flights_trend_chart
from utils import REGIONS, plot_flights_trend, get_top_10_by_total, RATING_REGIONS
from bot_assets.keyboards.inlines import get_main_kb, get_region_menu, get_list_regions, get_organizations
from bot_assets.states import Compare
from typing import Dict
import re
import os
import json
import numpy as np


router = Router()


MEDALS = ["🥇", "🥈", "🥉"] + ["  "] * 7  

def format_top_message(top_dict: Dict[int, int]) -> str:
    if not top_dict:
        return "Нет данных по полётам БПЛА за последний год."
    
    lines = []
    for i, (region_id, flights) in enumerate(top_dict.items(), 1):
        medal = MEDALS[i - 1] if i <= 3 else f"{i}."
        lines.append(f"{medal} ID {region_id} — {flights} полётов")
    
    return "🏆 Топ-10 регионов по активности БПЛА:\n\n" + "\n".join(lines)


@router.inline_query()
async def inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    frst_region = ''
    if query.startswith("compare"):
        mode = "compare"
        frst_region = int(query.split('_')[1])
        search_term = query[len("compare"):].strip().lower()
    else:
        mode = ""
        search_term = query.lower()

    if not REGIONS:
        await inline_query.answer(
            [InlineQueryResultArticle(
                id="error",
                title="Ошибка",
                description="Не удалось загрузить список регионов",
                input_message_content=InputTextMessageContent(
                    message_text="Сервис временно недоступен"
                )
            )],
            cache_time=0
        )
        return

    
    filtered = [
        r for r in REGIONS
        if search_term in r["name"].lower() or search_term in r["fullname"].lower()
    ][:50]

    results = []
    for region in filtered:
        capital_name = region["capital"]["name"] if region.get("capital") else "Нет столицы"
        description = f"Столица: {capital_name}"

        if mode == "compare":
            message_text = f"/compare_region_{region['id']}_{frst_region}"
        else:
            message_text = f"Вы выбрали регион: {region['fullname']}\nСтолица: {capital_name}"

        results.append(
            InlineQueryResultArticle(
                id=f"{region['id']}",
                title=region["fullname"],
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=message_text
                ),
            )
        )

    await inline_query.answer(results, cache_time=60, is_personal=True)


@router.chosen_inline_result()
async def on_region_selected(chosen_result: ChosenInlineResult):
    global RATING_REGIONS
    region_id = chosen_result.result_id

    user_id = chosen_result.from_user.id
    client = APIClient()
    region = client.get_region(region_id).get('data')
    statistic: Statistic = client.get_statistic(region_id)
    
    region_text = (
        f"📍 {statistic.name} (ID: {region_id})\n\n"
        f"🏆 Место в рейтинге: {RATING_REGIONS.get(str(region_id))}  \n"
        f"🛫 Всего полётов: {5932}  \n\n"
        
        f"📊 Статистика за {2025}  \n"
        f"🛫 Полётов за год: {1486}  \n"
        f"⏱️ Средняя длительность: {'1:57:12'}  \n\n"
        
        "🏢 Ответственный орган:  \n"
        "Управление  Росавиации по СЗФО\n\n"
        
        "📌 Программа развития БАС\n"
        "Принята 20.12.2024\n"
        
        "📌 Наличие ЭПР\n"
        "Есть\n"
        
        "📌 Специализация региона\n"
        "Система передачи данных с БВС\n"
        
        "📌 Наличие работ по БЭК\n"
        "Есть\n\n"
        
        "📌 Наличие полигона БАС\n"
        "Есть\n"
        
        "📌 Наличие НПЦ\n"
        "Крупный\n"
        
        "📌 Процент оснащённости школ БАС,\n"
        "12%\n"
        
        f"📌 Столица: {region.get('capital').get('name')}  \n"
        f"🗺️ Тип: {region.get('type')}  \n"
        f"👥 Население: {region.get('population')}"
    )

    await chosen_result.bot.send_message(
        chat_id=user_id,
        text=region_text,
        reply_markup=get_region_menu(region_id)
    )
    # await chosen_result.bot.send_photo(
    #     chat_id=user_id,
    #     photo=BufferedInputFile(image_bytes.getvalue(), filename="flight_trend.png")
    # )

    

@router.message(CommandStart())
async def start_message(message: Message):
    main_menu_text = (
        "🚀 Добро пожаловать в Aerostat Bot!\n\n"
        "Сервис аналитики полётов БАС по регионам РФ на основе данных Росавиации.\n\n"
        "🔍 Найдите регион:\n"
        "→ Напишите /region Красноярский_край  \n"
        "→ Или начните инлайн-поиск: @aerostat_bars_bot Регион\n\n"
        "📊 Доступна статистика:\n"
        "• Общее число полётов\n"
        "• Средняя длительность\n"
        "• Место в рейтинге\n"
        "• Динамика\n"
        "• Ответственные органы"
    )

    main_menu_kb = get_main_kb()
    await message.answer(main_menu_text, reply_markup=main_menu_kb)


@router.callback_query(F.data.startswith('top10'))
async def get_top(callback_query: CallbackQuery):
    try:
        top_10_dict = get_top_10_by_total()
        text = format_top_message(top_10_dict)
    except Exception as e:
        text = f"получении данных: {str(e)}"
    
    await callback_query.message.answer(text)


@router.callback_query(F.data.startswith('compare'))
async def compare(callback_query: CallbackQuery):
    first_region_id = int(callback_query.data.split('_')[1])
    await callback_query.message.edit_text("Необходимо выбрать регион для сравнения:")
    await callback_query.message.edit_reply_markup(reply_markup=get_list_regions(first_region_id))


@router.callback_query(F.data.startswith('voidcompare_'))
async def void_compare(callback_query: CallbackQuery):
    first, second = map(int, callback_query.data.split('_')[1:])

    
    client = APIClient()
    region_first = client.get_region(first).get('data')
    region_second = client.get_region(second).get('data')
    statistic_first: Statistic = client.get_statistic(first)
    statistic_second: Statistic = client.get_statistic(second)

    region_text = (
        f"📍 {statistic_first.name} // {statistic_second.name}\n\n"
        f"🏆 Место в рейтинге: {RATING_REGIONS.get(str(first))} //  {RATING_REGIONS.get(str(second))}\n"
        f"🛫 Всего полётов: {5932} // {4189}   \n\n"
        
        f"📊 Статистика за {2025}  \n"
        f"🛫 Полётов за год: {1486} // {943}  \n"
        f"⏱️ Средняя длительность: {'1:57:12'} // {'1:23:42'}  \n\n"
        
        "🏢 Ответственный орган:  \n"
        "Управление  Росавиации по СЗФО // Управление  Росавиации по СЗФО\n\n"
        
        "📌 Программа развития БАС\n"
        "Принята 20.12.2024 // 11.02.2025\n"
        
        "📌 Наличие ЭПР\n"
        "Есть // Есть\n"
        
        "📌 Специализация региона\n"
        "Система передачи данных с БВС // Система передачи данных с БВС\n"
        
        "📌 Наличие работ по БЭК\n"
        "Есть // Есть\n\n"
        
        "📌 Наличие полигона БАС\n"
        "Есть // Есть\n"
        
        "📌 Наличие НПЦ\n"
        "Крупный // Крупный\n"
        
        "📌 Процент оснащённости школ БАС,\n"
        "12% // 11%\n\n"
        
        f"👥 Население: {region_first.get('population')} // {region_second.get('population')}"
    )
    await callback_query.message.answer(text=region_text, reply_markup=get_region_menu(first))


@router.callback_query(F.data.startswith('usebas'))
async def use_bas(callback_query: CallbackQuery):
    region_id = int(callback_query.data.split('_')[1])
    # bas_data = {
    #     "Сельское хозяйство": 25,
    #     "Транспорт и логистика": 20,
    #     "Строительство и инфраструктура": 15,
    #     "Энергетика и промышленность": 10,
    #     "Наука и образование": 10,
    #     "Экология и природные ресурсы": 10,
    #     "Безопасность и госуправление": 5,
    #     "Медиа и креативные индустрии": 5
    # }
    # chart_image = generate_bas_usage_chart(bas_data)
    current_dir = os.path.dirname(__file__)
    image_path = os.path.join(current_dir, "bas.png")
    await callback_query.message.answer_photo(
        photo=FSInputFile(image_path), filename="flight_trend.png")
    await callback_query.message.answer(text="📊 Применение БАС в регионе", reply_markup=get_region_menu(region_id))


@router.callback_query(F.data.startswith('last_flights'))
async def last_flights(callback_query: CallbackQuery):
    current_dir = os.path.dirname(__file__)
    image_path = os.path.join(current_dir, "6_flights.png")
    await callback_query.message.answer_photo(
        photo=FSInputFile(image_path),
        caption="📅 Последние 6 полётов"
    )


@router.callback_query(F.data.startswith('table_regions'))
async def get_table_regions(callback_query: CallbackQuery):
    text = """📊 ТОП-15 РЕГИОНОВ ПО АКТИВНОСТИ БПЛА

    —

    🥇 #1 Москва  
    • Полёты: 3 200  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +12% 🟢  
    • Плотность: 72

    —

    🥈 #2 Татарстан  
    • Полёты: 2 800  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: -5% 🔴  
    • Плотность: 72

    —

    🥉 #3 Краснодарский край  
    • Полёты: 2 500  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +8% 🟢  
    • Плотность: 72

    —

    🔥 #4 Новосибирская область  
    • Полёты: 2 200  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +15% 🟢  
    • Плотность: 72

    —

    📍 #5 Свердловская область  
    • Полёты: 2 000  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: -3% 🔴  
    • Плотность: 72

    —

    📌 #6 Санкт-Петербург  
    • Полёты: 1 900  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +10% 🟢  
    • Плотность: 72

    —

    🎯 #7 Казань  
    • Полёты: 1 800  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +7% 🟢  
    • Плотность: 72

    —

    📈 #8 Самарская область  
    • Полёты: 1 750  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: -2% 🔴  
    • Плотность: 72

    —

    📊 #9 Пермская область  
    • Полёты: 1 700  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +9% 🟢  
    • Плотность: 72

    —

    🌐 #10 Пермская область  
    • Полёты: 1 680  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +9% 🟢  
    • Плотность: 72

    —

    🌐 #11 Пермская область  
    • Полёты: 1 670  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +9% 🟢  
    • Плотность: 72

    —

    🌐 #12 Пермская область  
    • Полёты: 1 640  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +9% 🟢  
    • Плотность: 72

    —

    🌐 #13 Пермская область  
    • Полёты: 1 600  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +9% 🟢  
    • Плотность: 72

    —

    🌐 #14 Пермская область  
    • Полёты: 1 550  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +9% 🟢  
    • Плотность: 72

    —

    🌐 #15 Пермская область  
    • Полёты: 1 490  
    • Длительность: 5 100 ч  
    • Ср. время: 0.95 ч  
    • Рост: +9% 🟢  
    • Плотность: 72"""

    await callback_query.message.answer(text, parse_mode="HTML")
    await callback_query.answer()


@router.callback_query(F.data.startswith("export_json_"))
async def export_region_json(callback_query: CallbackQuery):
    region_id = int(callback_query.data.split("_")[-1])
    client = APIClient()
    
    try:
        stat_data = client.get_json_statistic(region_id)  
    except Exception as e:
        await callback_query.answer(f"Ошибка загрузки данных: {e}", show_alert=True)
        return

    json_bytes = json.dumps(stat_data, ensure_ascii=False, indent=2).encode("utf-8")

    
    file = BufferedInputFile(
        file=json_bytes,
        filename=f"flight_statistics_{region_id}.json"
    )

    

    await callback_query.message.answer_document(
        document=file,
        caption=f"📊 Экспорт данных по региону ID {region_id}"
    )
    await callback_query.answer()


@router.callback_query(F.data.startswith('trends_'))
async def send_trend_chart(callback_query: CallbackQuery):
    loading_msg: Message = await callback_query.message.answer("📊 Собираю статистику...\nЭто может занять несколько секунд.")
    client = APIClient()
    region_id, type = int(callback_query.data.split('_')[1]), callback_query.data.split('_')[2]
    region = client.get_region(region_id).get('data')
    data = client.get_flights_by_type(type)

    await callback_query.message.answer_photo(data['photo'], caption=data['text'], reply_markup=get_organizations(region_id, type))
    await callback_query.answer()
    await loading_msg.delete()


@router.callback_query(F.data.startswith('export_'))
async def send_trend_chart_report(callback_query: CallbackQuery):
    loading_msg: Message = await callback_query.message.answer("📊 Собираю статистику...\nЭто может занять несколько секунд.")
    region_id, type_report = callback_query.data.replace('export_trends_', '').split('_')
    client = APIClient()

    region = client.get_region(int(region_id)).get('data')
    name = region.get('fullname')

    try:
        stat_data = client.get_json_statistic(region_id)  
    except Exception as e:
        await callback_query.answer(f"Ошибка загрузки данных: {e}", show_alert=True)
        return

    json_bytes = json.dumps(stat_data, ensure_ascii=False, indent=2).encode("utf-8")

    if type_report == 'yur':
        name_type = 'legal_authority'
    elif type_report == 'fiz':
        name_type = 'private_person'
    else:
        name_type = 'all'

    file = BufferedInputFile(
        file=json_bytes,
        filename=f"flight_statistics_{region_id}_{name_type}.json"
    )

    
    await loading_msg.delete()
    await callback_query.message.answer_document(
        document=file,
        caption=f"📊 Экспорт данных по региону ID {region_id}"
    )
    await callback_query.answer()


@router.callback_query(F.data == "show_top_regions")
async def show_top_regions(callback_query: CallbackQuery):
    client = APIClient()
    top_names = [
        "Москва",
        "Татарстан",
        "Краснодарский край",
        "Новосибирская область",
        "Свердловская область",
        "Санкт-Петербург",
        "Казань",
        "Самарская область",
        "Пермская область",
        "Челябинская область"
    ]

    text = client.format_top_regions_names_with_emojis(top_names)
    await callback_query.message.answer(text, parse_mode="HTML")
    await callback_query.answer()