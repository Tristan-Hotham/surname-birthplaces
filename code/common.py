"""Shared paths and helpers for the surname birthplaces study.

Inputs (read in place; override with environment variables):
  WD_BUNDLE  Wikidata people bundle (CC0) with a few Wikipedia articles (CC BY-SA 4.0), gathered with code/00_gather.js
  NRS_XLSX   National Records of Scotland, Most common surnames 2025 (Open Government Licence v3.0)
  OSNAMES    OS Open Names, Great Britain (Open Government Licence v3.0), as a tab separated file
Temporary files go to WORK (default /dev/shm/surname-birthplaces-work), outside the repository.
"""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
DATA = os.path.join(ROOT, "data")
SRC = os.environ.get("SRC", "/home/claude/hist/_data18/surname-birthplaces")
WD_BUNDLE = os.environ.get("WD_BUNDLE", os.path.join(SRC, "surname_birthplaces_wd.json.gz"))
NRS_XLSX = os.environ.get("NRS_XLSX", os.path.join(SRC, "nrs_most_common_surnames_2025.xlsx"))
OSNAMES = os.environ.get("OSNAMES", "/home/claude/hist/osnames_gb.tsv")
WORK = os.environ.get("WORK", "/dev/shm/surname-birthplaces-work")
os.makedirs(DATA, exist_ok=True); os.makedirs(WORK, exist_ok=True)

ERAS = ["1700s", "1800s", "1900to1949", "since1950"]
ERA_LABEL = {"1700s": "born 1700 to 1799", "1800s": "born 1800 to 1899", "1900to1949": "born 1900 to 1949", "since1950": "born 1950 or later"}
A, B = "1800s", "since1950"   # the two eras compared throughout


def era_of(y):
    return "1700s" if y < 1800 else "1800s" if y < 1900 else "1900to1949" if y < 1950 else "since1950"


REGIONS = ["Scotland", "North East", "North West", "Yorkshire and the Humber", "East Midlands", "West Midlands",
           "Eastern", "London", "South East", "South West", "Wales"]
REGION_SHORT = {"Yorkshire and the Humber": "Yorkshire", "Eastern": "East of England"}


def km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(min(1, a)))


def xy(lat, lon):
    """Simple equirectangular km coordinates centred on Britain, good enough for nearest-neighbour work."""
    import numpy as np
    lat = np.asarray(lat, float); lon = np.asarray(lon, float)
    return np.c_[lon * 111.32 * math.cos(math.radians(54.5)), lat * 110.57]


def nodash(s):
    return "—" not in s and "–" not in s and "--" not in s
