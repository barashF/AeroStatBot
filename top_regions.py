import requests
import aiohttp
from configuration.config import API_BASE_URL
import asyncio


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


def get_statistic_of_region(id: int):
    try:
        url = f"{API_BASE_URL}/statistics/region/{id}"
        data = {}

        
        session = requests.Session()
        response = session.get(url)
        response.raise_for_status()

        statistic = response.json().get('statistics')
        summary = response.json().get('summary')
        by_year = statistic.get('by_year')

        data['total_flights'] = summary.get('total_flights')
                
        data['last_year'] = by_year[-1] if len(by_year) > 0 else []
        data['by_year'] = by_year
        data['id'] = id

        return data
    except:
        return None
        
    

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


def get_statistics_of_regions():
    global STATISTICS
    
    for region in REGIONS:
        region_id = region.get('id')
        statistic = get_statistic_of_region(region_id)
        STATISTICS.append(statistic)
    
    print('get stats')
    find_top_regions()


async def main():
    await fetch_regions()
    get_statistics_of_regions()


if __name__ == "__main__":
    asyncio.run(main())