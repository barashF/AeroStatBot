from dataclasses import dataclass
from typing import List


@dataclass
class YearStatistic:
    year: int
    flight_count: int
    avg_time: str
    total_time: str


@dataclass
class Statistic:
    id: int
    name: str
    total_flights_all: int
    total_flights_yur: int
    total_flights_fiz: int
    all_flights_years: List[YearStatistic]
    fiz_flights_years: List[YearStatistic]
    yur_flights_years: List[YearStatistic]

