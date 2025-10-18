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
    CallbackQuery
)
from configuration.config import API_BASE_URL
import aiohttp
from infrastructure.api_clients.city_client import APIClient
from utils import REGIONS, plot_flights_trend, get_top_10_by_total
from bot_assets.keyboards.inlines import get_main_kb
from typing import Dict


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
    query = inline_query.query.strip().lower()

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
        if query in r["name"].lower()
    ]

    filtered = filtered[:50]

    results = []
    for region in filtered:
        capital_name = region["capital"]["name"] if region.get("capital") else "Нет столицы"
        description = f"Столица: {capital_name}"
        results.append(
            InlineQueryResultArticle(
                id=str(region["id"]),
                title=region["fullname"],
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=f"Вы выбрали регион: {region['name']}\nСтолица: {capital_name}"
                ),
                
            )
        )

    await inline_query.answer(results, cache_time=60, is_personal=True)


@router.chosen_inline_result()
async def on_region_selected(chosen_result: ChosenInlineResult):
    region_id = chosen_result.result_id
    user_id = chosen_result.from_user.id
    client = APIClient()
    region = client.get_region(region_id).get('data')
    statistic_of_region = client.get_statistic_of_region(region_id)
    image_bytes = plot_flights_trend(statistic_of_region['count_flights_by_months'])

    region_text = (
        f"📍 {region.get('fullname')} (ID: {region_id})\n\n"
        "🏆 **Место в рейтинге**: #А как мы его считаем? откуда брать?  \n"
        "📅 **Период**: Январь–Июль 2025  \n"
        f"🛫 Всего полётов: {statistic_of_region.get('total_flights')}  \n\n"

        f"📊 Статистика за {statistic_of_region.get('last_year').get('year')}  \n"
        f"🛫 Полётов за год: {statistic_of_region.get('last_year').get('flight_count')}  \n"
        f"⏱️ Средняя длительность: {statistic_of_region.get('last_year').get('avg_flight_time')}  \n"
        f"{statistic_of_region.get('change_percent')}\n\n"
        "🏢 **Ответственный орган**:  \n"
        "У НАС ТАКОЕ ЕСТЬ???\n\n"
        f"📌 Столица: {region.get('capital').get('name')}  \n"
        f"🗺️ Тип: {region.get('type')}  \n"
        f"👥 Население: {region.get('population')}"
    )
    await chosen_result.bot.send_message(
        chat_id=user_id,
        text=region_text
    )
    await chosen_result.bot.send_photo(
        chat_id=user_id,
        photo=BufferedInputFile(image_bytes.getvalue(), filename="flight_trend.png")
    )

    

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
    
    await callback_query.answer(text)