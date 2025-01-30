import datetime
import matplotlib.pyplot as plt
import pandas as pd
from bdew.elec_slp import ElecSlp

def get_load_profile_df(year, annual_consumption_kwh):
    holidays = get_bavarian_holidays(year)
    elec_slp = ElecSlp(year=year, holidays=holidays)
    annual_demand = {'h0_dyn': annual_consumption_kwh}
    load_profile = elec_slp.get_profile(annual_demand)
    return load_profile
def get_bavarian_holidays(year):
    holidays = []
    if year == 2020:
        holidays = [
            datetime.datetime(year, 1, 1),  # New Year's Day
            datetime.datetime(year, 1, 6),  # Heilige Drei Könige
            datetime.datetime(year, 4, 10),  # Karfreitag
            datetime.datetime(year, 4, 13),  # Easter Monday
            datetime.datetime(year, 5, 1),  # Labour Day
            datetime.datetime(year, 5, 21),  # Ascension Day
            datetime.datetime(year, 6, 1),  # Whit Monday
            datetime.datetime(year, 6, 11),  # Corpus Christi
            datetime.datetime(year, 8, 15),  # Assumption Day
            datetime.datetime(year, 10, 3),  # German Unity Day
            datetime.datetime(year, 11, 1),  # All Saints' Day
            datetime.datetime(year, 12, 25),  # Christmas Day
            datetime.datetime(year, 12, 26)  # Boxing Day
        ]

    elif year == 2021:
        holidays = [
            datetime.datetime(year, 1, 1),  # New Year's Day
            datetime.datetime(year, 1, 6),  # Heilige Drei Könige
            datetime.datetime(year, 4, 2),  # Karfreitag
            datetime.datetime(year, 4, 5),  # Easter Monday
            datetime.datetime(year, 5, 1),  # Labour Day
            datetime.datetime(year, 5, 13),  # Ascension Day
            datetime.datetime(year, 5, 24),  # Whit Monday
            datetime.datetime(year, 6, 3),  # Corpus Christi
            datetime.datetime(year, 8, 15),  # Assumption Day
            datetime.datetime(year, 10, 3),  # German Unity Day
            datetime.datetime(year, 11, 1),  # All Saints' Day
            datetime.datetime(year, 12, 25),  # Christmas Day
            datetime.datetime(year, 12, 26)  # Boxing Day
        ]


    elif year == 2022:
        holidays = [
            datetime.datetime(year, 1, 1),  # New Year's Day
            datetime.datetime(year, 1, 6),  # Heilige Drei Könige
            datetime.datetime(year, 4, 15),  # Karfreitag
            datetime.datetime(year, 4, 18),  # Easter Monday
            datetime.datetime(year, 5, 1),  # Labour Day
            datetime.datetime(year, 5, 26),  # Ascension Day
            datetime.datetime(year, 6, 6),  # Whit Monday
            datetime.datetime(year, 6, 16),  # Corpus Christi
            datetime.datetime(year, 8, 15),  # Assumption Day
            datetime.datetime(year, 10, 3),  # German Unity Day
            datetime.datetime(year, 11, 1),  # All Saints' Day
            datetime.datetime(year, 12, 25),  # Christmas Day
            datetime.datetime(year, 12, 26)  # Boxing Day
        ]

    elif year == 2023:
        holidays = [
            datetime.datetime(year, 1, 1),   # New Year's Day
            datetime.datetime(year, 1, 6),   # Heilige Drei Könige
            datetime.datetime(year, 4, 7),  # Karfreitag
            datetime.datetime(year, 4, 10),   # Easter Monday
            datetime.datetime(year, 5, 1),   # Labour Day
            datetime.datetime(year, 5, 18),   # Ascension Day
            datetime.datetime(year, 5, 29),  # Whit Monday
            datetime.datetime(year, 6, 8),  # Corpus Christi
            datetime.datetime(year, 8, 15),  # Assumption Day
            datetime.datetime(year, 10, 3),  # German Unity Day
            datetime.datetime(year, 11, 1),  # All Saints' Day
            datetime.datetime(year, 12, 25), # Christmas Day
            datetime.datetime(year, 12, 26)  # Boxing Day
        ]

    elif year == 2024:
        holidays = [
            datetime.datetime(year, 1, 1),   # New Year's Day
            datetime.datetime(year, 1, 6),   # Heilige Drei Könige
            datetime.datetime(year, 3, 29),  # Karfreitag
            datetime.datetime(year, 4, 1),   # Ostermontag
            datetime.datetime(year, 5, 1),   # Tag der Arbeit
            datetime.datetime(year, 5, 9),   # Christi Himmelfahrt
            datetime.datetime(year, 5, 20),  # Pfingstmontag
            datetime.datetime(year, 5, 30),  # Fronleichnam
            datetime.datetime(year, 8, 15),  # Maria Himmelfahrt
            datetime.datetime(year, 10, 3),  # Tag der Deutschen Einheit
            datetime.datetime(year, 11, 1),  # Allerheiligen
            datetime.datetime(year, 12, 25), # 1. Weihnachtstag
            datetime.datetime(year, 12, 26)  # 2. Weihnachtstag
        ]

    return holidays
