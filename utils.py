import aiohttp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from typing import List
from configuration.config import API_BASE_URL
from infrastructure.api_clients.city_client import APIClient


REGIONS = []
STATISTICS = []
TOP = []

async def fetch_regions():
    global REGIONS
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/region") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    REGIONS[:] = data.get("data", [])
                    print(f"Загружено {len(REGIONS)} регионов")
                else:
                    print("Ошибка загрузки регионов:", resp.status)
    except Exception as e:
        print("Исключение при загрузке регионов:", e)




def plot_flights_trend(flight_counts: List[int], labels: List[str] = None) -> BytesIO:

    """
    Создаёт график динамики количества полётов.

    :param flight_counts: Список чисел — количество полётов (например, [120, 150, 90])
    :param labels: Список меток для оси X (например, ['2022', '2023', '2024']). 
                   Если не задан — генерируются как 1, 2, 3...
    :return: BytesIO — изображение в формате PNG, готовое к отправке в Telegram
    """
    if not flight_counts:
        raise ValueError("Список flight_counts не должен быть пустым")

    n = len(flight_counts)
    if labels is None:
        labels = [str(i + 1) for i in range(n)]
    elif len(labels) != n:
        raise ValueError("Длина labels должна совпадать с длиной flight_counts")

    plt.figure(figsize=(8, 4))
    plt.plot(labels, flight_counts, marker='o', linestyle='-', linewidth=2, markersize=6, color='#1f77b4')
    plt.title('Динамика количества полётов', fontsize=14)
    plt.xlabel('Период', fontsize=12)
    plt.ylabel('Количество полётов', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    # Сохраняем в буфер
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close()  # освобождаем память
    buf.seek(0)
    return buf


def find_top_regions():
    global TOP
    top_regions = []
    for region in STATISTICS:
        d = {}
        by_year = region.get('by_year')
        region_id = region.get('id')
        d['id'] = region_id
        d['total'] = region.get('total_flights')
        for year in by_year:
            d[year.get('year')] = year.get('flight_count')
            top_regions.append(d)
    TOP [:] = top_regions


def get_statistics_of_regions():
    global STATISTICS
    api_client = APIClient()
    
    for region in REGIONS:
        region_id = region.get('id')
        statistic = api_client.get_statistic_of_region(region_id)
        STATISTICS.append(statistic)
    find_top_regions()


def get_top_10_by_total() -> dict:
    valid_regions = [
        r for r in TOP
        if r.get('id') is not None and isinstance(r.get('total'), int) and r['total'] > 0
    ]

    sorted_regions = sorted(valid_regions, key=lambda x: x['total'], reverse=True)

    top_10 = {r['id']: r['total'] for r in sorted_regions[:10]}

    return top_10


    


        



