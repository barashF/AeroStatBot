from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_kb():
    kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔎 Найти регион", switch_inline_query_current_chat="")],
                [
                    InlineKeyboardButton(text="🌍 Топ-10 регионов", callback_data="top10"),
                    InlineKeyboardButton(text="📈 Динамика 2025", callback_data="trend_2025")
                ],
                [
                    InlineKeyboardButton(text="📄 Отчёт по РФ", callback_data="report_rf"),
                    InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")
                ],
            ]
        )
    return kb