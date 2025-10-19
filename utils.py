import aiohttp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
from typing import List
from configuration.config import API_BASE_URL
from infrastructure.api_clients.city_client import APIClient
import random


REGIONS = []
RATING_REGIONS = {'72': '🔻1', '47': '🔻2', '79': '🔻3', '49': '🔻4', '70': '🔻5', '55': '🔻6', '7': '🔺7', '2': '🔺8', '10': '🔺9', '26': '🔻10', '83': '🔺11', '75': '🔻12', '37': '🔻13', '34': '🔺14', '35': '🔻15', '68': '🔺16', '40': '🔺17', '17': '🔻18', '69': '🔺19', '45': '🔺20', '56': '🔻21', '42': '🔺22', '19': '🔻23', '54': '🔻24', '59': '🔻25', '16': '🔺26', '66': '🔻27', '52': '🔻28', '1': '🔺29', '39': '🔻30', '22': '🔺31', '46': '🔺32', '80': '🔻33', '33': '🔺34', '14': '🔻35', '43': '🔺36', '5': '🔺37', '29': '🔻38', '76': '🔻39', '6': '🔺40', '23': '🔻41', '73': '🔺42', '41': '🔺43', '4': '🔺44', '51': '🔻45', '82': '🔻46', '81': '🔻47', '36': '🔻48', '24': '🔺49', '50': '🔺50', '77': '🔺51', '64': '🔺52', '63': '🔻53', '57': '🔻54', '15': '🔻55', '53': '🔺56', '32': '🔻57', '62': '🔻58', '38': '🔻59', '65': '🔺60', '3': '🔻61', '28': '🔺62', '71': '🔻63', '44': '🔻64', '13': '🔻65', '27': '🔺66', '25': '🔺67', '74': '🔻68', '58': '🔻69', '20': '🔻70', '21': '🔻71', '30': '🔻72', '8': '🔻73', '78': '🔺74', '60': '🔻75', '9': '🔺76', '18': '🔻77', '61': '🔻78', '48': '🔺79', '31': '🔺80', '67': '🔻81', '11': '🔻82', '12': '🔻83'}
STATISTICS = []
TOP = [{'id': 38, 'total': 2986, '2024': 2957, '2025': 29}, {'id': 38, 'total': 2986, '2024': 2957, '2025': 29}, {'id': 39, 'total': 1292, '2024': 1292}, {'id': 24, 'total': 4362, '2024': 2225, '2025': 2137}, {'id': 24, 'total': 4362, '2024': 2225, '2025': 2137}, {'id': 49, 'total': 441, '2025': 441}, {'id': 50, 'total': 14270, '2025': 14270}, {'id': 54, 'total': 4849, '2025': 4849}, {'id': 61, 'total': 5302, '2025': 5302}, {'id': 63, 'total': 7318, '2025': 7318}, {'id': 78, 'total': 9104, '2025': 9104}, {'id': 14, 'total': 1473, '2024': 1029, '2025': 444}, {'id': 14, 'total': 1473, '2024': 1029, '2025': 444}, {'id': 66, 'total': 9455, '2025': 9455}, {'id': 72, 'total': 40862, '2024': 22059, '2025': 18803}, {'id': 72, 'total': 40862, '2024': 22059, '2025': 18803}, {'id': 27, 'total': 3198, '2025': 3198}]


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

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    plt.close() 
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
    print('получен топ регионов')
    print(TOP)



def get_top_10_by_total() -> dict:
    for i in range(10):
        region = RATING_REGIONS[i]
    valid_regions = [
        r for r in TOP
        if r.get('id') is not None and isinstance(r.get('total'), int) and r['total'] > 0
    ]

    sorted_regions = sorted(valid_regions, key=lambda x: x['total'], reverse=True)

    top_10 = {r['id']: r['total'] for r in sorted_regions[:10]}
    return top_10


    



