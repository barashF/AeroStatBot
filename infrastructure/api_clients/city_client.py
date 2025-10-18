import requests
from typing import List, Dict, Optional, Union
from configuration.config import API_BASE_URL


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

            data['total_flights'] = summary.get('total_flights')
            try:
                count_flights_by_months = self._parse_by_year_and_months(by_year_and_month[-1].get('months'))
                data['count_flights_by_months'] = count_flights_by_months
            except:
                data['count_flights_by_months'] = []
            data['last_year'] = by_year[-1] if len(by_year) > 0 else []
            data['by_year'] = by_year
            data['id'] = id
            if len(by_year) > 1:
                data['change_percent'] = self._calculate_flight_change(by_year[-1].get('flight_count'), 
                                                                   by_year[-2].get('flight_count'))
            else:
                data['change_percent'] = "🔻 0%"
            return data
        except requests.RequestException as e:
            print(f"[API Error] Не удалось получить города: {e}")
            return None
        
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