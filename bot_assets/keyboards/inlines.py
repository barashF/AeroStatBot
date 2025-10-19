from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils import REGIONS


def get_main_kb():
    kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔎 Найти регион", switch_inline_query_current_chat="")],
                [
                    InlineKeyboardButton(text="🌍 Топ-10 регионов", callback_data="show_top_regions"),
                    InlineKeyboardButton(text="📈 Динамика 2025", callback_data="trends_24_all")
                ],
                [
                    InlineKeyboardButton(text="📄 Отчёт по РФ", callback_data="export_rf"),
                    InlineKeyboardButton(text="⚙️ Таблица регионов", callback_data="table_regions")
                ],
            ]
        )
    return kb


def get_region_menu(region_id: int):
    kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Сравнить с другим регионом", callback_data=f"compare_{region_id}")],
                [
                    InlineKeyboardButton(text="🌍 Топ-10 регионов", callback_data="show_top_regions"),
                    InlineKeyboardButton(text="📈 Динамика полётов", callback_data=f"trends_{region_id}_all")
                ],
                [
                    InlineKeyboardButton(text="📄 Экспорт статистики региона", callback_data=f"export_json_{region_id}"),
                    InlineKeyboardButton(text="🛠 Применение БАС", callback_data=f"usebas_{region_id}")
                ],
                [InlineKeyboardButton(text="🛫 Последние полёты в регионе", callback_data=f"last_flights_{region_id}")]
            ]
        )
    return kb


def get_list_regions(region_id: int, columns: int = 2) -> InlineKeyboardMarkup:
    buttons = []
    for region in REGIONS:
        buttons.append(
            InlineKeyboardButton(
                text=region.get('fullname'),
                callback_data=f"voidcompare_{region_id}_{region.get('id')}"
            )
        )
    keyboard = [buttons[i:i + columns] for i in range(0, len(buttons), columns)]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_organizations(region_id: int, type_report: str = 'all'):
    inline_keyboard=[
                [InlineKeyboardButton(text="👤 Физические лица", callback_data=f"trends_{region_id}_fiz"), 
                 InlineKeyboardButton(text="🏢 Юридические лица", callback_data=f"trends_{region_id}_yur")],
                [InlineKeyboardButton(text="📄 Экспорт полетов", callback_data=f"export_trends_{region_id}_{type_report}")],

    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
