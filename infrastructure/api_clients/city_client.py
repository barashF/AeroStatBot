import requests
from typing import List, Dict, Optional, Union
from configuration.config import API_BASE_URL
from .models import Statistic, YearStatistic
from aiogram.types import BufferedInputFile, FSInputFile
import numpy as np
import json
from datetime import datetime
from infrastructure.gen_image import generate_flights_trend_chart
import os


class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def _get_paginated_data(self, url: str, params: Optional[dict] = None) -> List[Dict]:
        all_items = []
        page = 1
        while True:
            request_params = (params or {}).copy()
            request_params['page'] = page
            try:
                response = self.session.get(url, params=request_params)
                response.raise_for_status()
                data = response.json()
                if "data" not in data:
                    break
                all_items.extend(data["data"])
                if page >= data["meta"]["last_page"]:
                    break
                page += 1
            except requests.RequestException as e:
                print(f"[API Error] Ошибка при получении данных с {url}: {e}")
                break
        return all_items
    


    def get_cities(self, page: int = 1, per_page: int = 100) -> Optional[Dict]:
        url = f"{self.base_url}/city"
        try:
            response = self.session.get(url, params={"page": page, "per_page": per_page})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить города: {e}")
            return None

    def get_all_cities(self) -> List[Dict]:
        return self._get_paginated_data(f"{self.base_url}/city")

    def find_city_by_name(self, name: str) -> Optional[Dict]:
        name_lower = name.strip().lower()
        for city in self.get_all_cities():
            if city["name"].lower() == name_lower:
                return city
        return None

    def get_regions(self, page: int = 1, per_page: int = 100) -> Optional[Dict]:
        url = f"{self.base_url}/region"
        try:
            response = self.session.get(url, params={"page": page, "per_page": per_page})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить регионы: {e}")
            return None

    def get_all_regions(self) -> List[Dict]:
        return self._get_paginated_data(f"{self.base_url}/region")

    def get_region(self, id: int) -> Dict:
        url = f"{self.base_url}/region/{id}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            print(response.json())
            return response.json()
        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить города: {e}")
            return None
        
    def _calculate_flight_change(self, current: int, previous: int) -> float:
        if previous == 0:
            if current == 0:
                return 0.0
            else:
                return float('inf')
        percent = (current - previous) / previous * 100
        if percent >= 0:
            return f"🔺 {round(percent, 2)}%"
        return f"🔻 {round(percent, 2)}%"
    
    def _parse_by_year_and_months(self, months) -> List[int]:
        counts = []
        for i in months:
            counts.append(i.get('flight_count'))
        return counts

    def get_statistic_of_region(self, id: int) -> Dict:
        url = f"{self.base_url}/statistics/region/{id}"
        data = {}
        try:
            response = self.session.get(url)
            response.raise_for_status()

            statistic = response.json().get('statistics')
            summary = response.json().get('summary')
            by_year = statistic.get('by_year')
            by_year_and_month = statistic.get('by_year_and_month')
            total_flights = summary.get('total_flights')
            data['all_flights'] = total_flights.get('all')
            data['yur'] = total_flights.get('yur')
            data['fiz'] = total_flights.get('fiz')
            
            
            # data['last_year'] = by_year[-1] if len(by_year) > 0 else []
            # data['by_year'] = by_year
            data['id'] = id
            data['change_percent'] = "🔻 0%"
            return data
        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить города: {e}")
            return None
        
    def get_json_statistic(self, region_id: int):
        url = f"{self.base_url}/statistics/region/24"
        data = {}
        try:
            response = self.session.get(url)
            response.raise_for_status()
            report = response.json()

            if "region" in report:
                del report["region"]

            allowed_keys = {"summary", "statistics"}
            filtered = {k: v for k, v in report.items() if k in allowed_keys}

            return filtered
        

        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить города: {e}")
            return None
        

    def get_statistic(self, region_id):
        url_stat = f"{self.base_url}/statistics/region/{region_id}"
        url_region = f"{self.base_url}/region/{region_id}"
        try:
            response_stat = self.session.get(url_stat)
            response_reg = self.session.get(url_region)
            response_stat.raise_for_status()
            response_reg.raise_for_status()

            statistic = response_stat.json().get('statistics')
            by_year = statistic.get('by_year')

            all_flights_years = self._parse_years(by_year.get('all'))
            fiz_flights_years = self._parse_years(by_year.get('fiz'))
            yur_flights_years = self._parse_years(by_year.get('yur'))
            
            summary = response_stat.json().get('summary')
            total_flights_all = summary.get('total_flights').get('all')
            total_flights_yur = summary.get('total_flights').get('yur')
            total_flights_fiz = summary.get('total_flights').get('fiz')
            name = response_reg.json().get('data').get('fullname')
            
            region_statistic = Statistic(
                id=region_id,
                name=name,
                total_flights_all=total_flights_all,
                total_flights_yur=total_flights_yur,
                total_flights_fiz=total_flights_fiz,
                all_flights_years=all_flights_years,
                fiz_flights_years=fiz_flights_years,
                yur_flights_years=yur_flights_years
            )
            
            return region_statistic

        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить города: {e}")
            return None
    
    def get_flights_by_type(self, entity_type: str):
        base_trend = []
        total_monthly = 231
        for i in range(1, 32):
            raw = 1.0 + 0.3 * np.sin(i / 4) + 0.1 * np.random.randn()
            raw = max(0.1, raw) 
            base_trend.append({"date": f"2025-07-{i:02d}", "flights": 0})

        raw_sum = sum(1.0 + 0.3 * np.sin(i / 4) + 0.1 * np.random.randn() for i in range(1, 32))
        for i in range(31):
            val = (1.0 + 0.3 * np.sin((i + 1) / 4) + 0.1 * np.random.randn()) / raw_sum * total_monthly
            base_trend[i]["flights"] = int(max(0, round(val)))

        actual_sum = sum(d["flights"] for d in base_trend)
        diff = total_monthly - actual_sum
        if abs(diff) > 0 and base_trend:
            base_trend[-1]["flights"] = max(0, base_trend[-1]["flights"] + diff)

        data = {}

        if entity_type == "all":
            fl_trend = []
            ul_trend = []
            for day in base_trend:
                total = day["flights"]
                fl = int(total * 0.6 + np.random.randint(-2, 3))
                fl = max(0, min(fl, total))
                ul = total - fl
                fl_trend.append({"date": day["date"], "flights": fl})
                ul_trend.append({"date": day["date"], "flights": ul})

            stats = {
                "avg_time": "12",
                "growth_ratio": "9,7%",
                "total_flights": sum(d["flights"] for d in base_trend)
            }

            # image_bytes = generate_flights_trend_chart(base_trend, stats)
            # photo = BufferedInputFile(image_bytes, filename="trend_all.png")
            


            current_dir = os.path.dirname(__file__)
            image_path = os.path.join(current_dir, "dinamic_all.png")
            data['photo'] = FSInputFile(image_path)
            data['text'] = '📈 Динамика полётов за месяц (все)'
            return data

        elif entity_type == "fiz": 
            fl_trend = []
            for day in base_trend:
                total = day["flights"]
                fl = int(total * 0.6 + np.random.randint(-2, 3))
                fl = max(0, min(fl, total))
                fl_trend.append({"date": day["date"], "flights": fl})

            stats = {
                "avg_time": "10",
                "growth_ratio": "11,2%",
                "total_flights": sum(d["flights"] for d in fl_trend)
            }
            # image_bytes = generate_flights_trend_chart(fl_trend, stats)
            # photo = BufferedInputFile(image_bytes, filename="trend_fl.png")
            current_dir = os.path.dirname(__file__)
            image_path = os.path.join(current_dir, "dinamic_all.png")
            data['photo'] = FSInputFile(image_path)
            data['text'] = '👤 Полёты физических лиц за месяц'
            return data

        else:
            ul_trend = []
            for day in base_trend:
                total = day["flights"]
                ul = int(total * 0.4 + np.random.randint(-2, 3))
                ul = max(0, min(ul, total))
                ul_trend.append({"date": day["date"], "flights": ul})

            stats = {
                "avg_time": "15",
                "growth_ratio": "7,3%",
                "total_flights": sum(d["flights"] for d in ul_trend)
            }
            # image_bytes = generate_flights_trend_chart(ul_trend, stats)
            # photo = BufferedInputFile(image_bytes, filename="trend_ul.png")
            current_dir = os.path.dirname(__file__)
            image_path = os.path.join(current_dir, "dinamic_all.png")
            data['photo'] = FSInputFile(image_path)
            data['text'] = '🏢 Полёты юридических лиц за месяц'
            return data

    def format_top_regions_names_with_emojis(self, region_names: list) -> str:
        if not region_names:
            return "❌ Список регионов пуст."

        lines = [
            "<b>🏆 ТОП-10 РЕГИОНОВ ПО АКТИВНОСТИ БПЛА</b>",
            ""
        ]
        
        emojis = [
            "🥇", 
            "🥈",  
            "🥉",  
            "🔥",  
            "🚀",  
            "📍",
            "📌",  
            "🎯",  
            "📊",  
            "🌐"   
        ]

        for i, name in enumerate(region_names[:10], 1):
            emoji = emojis[i - 1] if i <= len(emojis) else "•"
            lines.append(f"{emoji} <b>{i}.</b> {name}")

        return "\n".join(lines)

    def generate_flight_report_json(region_id: int, region_name: str) -> bytes:
        total_monthly = 231
        days = 31
        base_values = []
        for i in range(1, days + 1):
            val = (1.0 + 0.3 * np.sin(i / 4) + 0.1 * np.random.randn())
            base_values.append(max(0.1, val))

        scale = total_monthly / sum(base_values)
        daily_all = [int(round(v * scale)) for v in base_values]

        diff = total_monthly - sum(daily_all)
        if daily_all:
            daily_all[-1] = max(0, daily_all[-1] + diff)

        daily_fl = []
        daily_ul = []
        for total in daily_all:
            fl = int(total * 0.6 + np.random.randint(-2, 3))
            fl = max(0, min(fl, total))
            ul = total - fl
            daily_fl.append(fl)
            daily_ul.append(ul)

        dates = [f"2025-07-{i:02d}" for i in range(1, 32)]
        report = {
            "region": {
                "id": region_id,
                "name": region_name,
                "period": "2025-07-01 — 2025-07-31"
            },
            "summary": {
                "total_flights": sum(daily_all),
                "fl_flights": sum(daily_fl),
                "ul_flights": sum(daily_ul)
            },
            "daily": [
                {
                    "date": date,
                    "all": all_f,
                    "fl": fl_f,
                    "ul": ul_f
                }
                for date, all_f, fl_f, ul_f in zip(dates, daily_all, daily_fl, daily_ul)
            ]
        }

        json_str = json.dumps(report, ensure_ascii=False, indent=2)
        return json_str.encode('utf-8')


    def get_percent_up(self, region_id):
        url_stat = f"{self.base_url}/statistics/region/{region_id}"

        try:
            response_stat = self.session.get(url_stat)
            response_stat.raise_for_status()

            statistic = response_stat.json().get('statistics')
            all = statistic.get('by_year').get('all')

            current_year = 0
            last_year = 0
            percent_year = 0
            if len(all) > 0:
                current_year = all[-1].get('flight_count')
            
            if len(all) > 1:
                last_year = all[-2].get('flight_count')

                percent_year = (current_year - last_year) * 100 / last_year

            if percent_year >= 0:
                percent_year =  f"🔺+{round(percent_year, 2)}%"
            else:
                percent_year =  f"🔻{round(percent_year, 2)}%"

            by_year_and_month = statistic.get('by_year_and_month').get('all')
            percent_months = 0
            list_counts_by_months = []
            if len(by_year_and_month) > 0:
                year = by_year_and_month[-1].get('months')
                list_counts_by_months = self._parse_months(year)
                current_months = year[-1].get('flight_count')
                last_months = year[-2].get('flight_count')
                percent_months = (current_months - last_months) * 100 / last_months
            
            if percent_months >= 0:
                percent_months =  f"🔺+{round(percent_months, 2)}%"
            else:
                percent_months =  f"🔻{round(percent_months, 2)}%"
            



                

        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить города: {e}")
            return None
        

    def _parse_months(self, months: list):
        counts = []
        for m in months:
            flight_count = m.get('flight_count')
            counts.append(flight_count)
        return counts
    
    
    def _parse_years(self, years: list) -> List[YearStatistic]:
        all_flights = []
        for year in years:
            year_stat = YearStatistic(
                year=year.get('year'),
                flight_count=year.get('flight_count'),
                avg_time=year.get('avg_flight_time	'),
                total_time=year.get('total_time	')
            )
            all_flights.append(year_stat)
        return all_flights
    

    def find_region_by_name(self, name: str) -> Optional[Dict]:
        name_lower = name.strip().lower()
        for region in self.get_all_regions():
            if region["name"].lower() == name_lower:
                return region
        return None

    def find_region_by_code(self, code: str) -> Optional[Dict]:
        for region in self.get_all_regions():
            if region["code"] == code:
                return region
        return None

    def get_flights(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        region_ids: Optional[List[int]] = None,
        page: int = 1,
        per_page: int = 100
    ) -> Optional[Dict]:
  
        url = f"{self.base_url}/flight"
        params = {"page": page, "per_page": per_page}
        if date_from:
            params["datefrom"] = date_from
        if date_to:
            params["dateto"] = date_to
        if region_ids:
            params["regions[]"] = region_ids  

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить полёты: {e}")
            return None

    def get_all_flights(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        region_ids: Optional[List[int]] = None
    ) -> List[Dict]:
        params = {}
        if date_from:
            params["datefrom"] = date_from
        if date_to:
            params["dateto"] = date_to
        if region_ids:
            params["regions[]"] = region_ids

        return self._get_paginated_data(f"{self.base_url}/flight", params)