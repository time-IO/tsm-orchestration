from fastapi import APIRouter, HTTPException, Depends
from ..models.neutron_monitor_stations import NeutronMonitorStations
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/neutron-monitor-stations",
    tags=["neutron-monitor-stations"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)]
)

entity_name = "neutron monitor station"

list_of_neutron_monitor_stations = {
    1: {"id": 1, "station_id": "AATA", "description": "Alma-Ata A (R=5.90, Alt=897 m)"},
    2: {"id": 2, "station_id": "AATB", "description": "Alma-Ata B (R=5.90, Alt=3340 m)"},
    3: {"id": 3, "station_id": "AHMD", "description": "Ahmedabad (R=15.94, Alt=50 m)"},
    4: {"id": 4, "station_id": "APTY", "description": "Apatity (R=0.65, Alt=181 m)"},
    5: {"id": 5, "station_id": "ARNM", "description": "Aragats (R=7.10, Alt=3200 m)"},
    6: {"id": 6, "station_id": "ATHN", "description": "Athens (R=8.53, Alt=260 m)"},
    7: {"id": 7, "station_id": "BKSN", "description": "Baksan (R=5.70, Alt=1700 m)"},
    8: {"id": 8, "station_id": "CALG", "description": "Calgary (R=1.08, Alt=1123 m)"},
    9: {"id": 9, "station_id": "CALM", "description": "NM de Castilla la Mancha (R=6.95, Alt=708 m)"},
    10: {"id": 10, "station_id": "CLMX", "description": "Climax (R=3.00, Alt=3400 m)"},
    11: {"id": 11, "station_id": "DJON", "description": "Daejeon (R=11.20, Alt=200 m)"},
    12: {"id": 12, "station_id": "DOMB", "description": "Dome C mini NM (bare) (R=0.01, Alt=3233 m)"},
    13: {"id": 13, "station_id": "DOMC", "description": "Dome C mini NM (R=0.01, Alt=3233 m)"},
    14: {"id": 14, "station_id": "DRBS", "description": "Dourbes (R=3.18, Alt=225 m)"},
    15: {"id": 15, "station_id": "ESOI", "description": "Emilio Segre Obs. Israel (R=10.75, Alt=2055 m)"},
    16: {"id": 16, "station_id": "FSMT", "description": "Fort Smith (R=0.30, Alt=180 m)"},
    17: {"id": 17, "station_id": "HRMS", "description": "Hermanus (R=4.58, Alt=26 m)"},
    18: {"id": 18, "station_id": "HUAN", "description": "Huancayo (R=12.92, Alt=3400 m)"},
    19: {"id": 19, "station_id": "INVK", "description": "Inuvik (R=0.30, Alt=21 m)"},
    20: {"id": 20, "station_id": "IRK2", "description": "Irkustk 2 (R=3.64, Alt=2000 m)"},
    21: {"id": 21, "station_id": "IRK3", "description": "Irkutsk 3 (R=3.64, Alt=3000 m)"},
    22: {"id": 22, "station_id": "IRKT", "description": "Irkustk (R=3.64, Alt=435 m)"},
    23: {"id": 23, "station_id": "JBGO", "description": "JangBogo (R=0.30, Alt=29 m)"},
    24: {"id": 24, "station_id": "JUNG", "description": "IGY Jungfraujoch (R=4.49, Alt=3570 m)"},
    25: {"id": 25, "station_id": "JUNG1", "description": "NM64 Jungfraujoch (R=4.49, Alt=3475 m)"},
    26: {"id": 26, "station_id": "KERG", "description": "Kerguelen (R=1.14, Alt=33 m)"},
    27: {"id": 27, "station_id": "KGSN", "description": "Kingston (R=1.88, Alt=65 m)"},
    28: {"id": 28, "station_id": "KIEL", "description": "Kiel (R=2.36, Alt=54 m)"},
    29: {"id": 29, "station_id": "KIEL2", "description": "KielRT (R=2.36, Alt=54 m)"},
    30: {"id": 30, "station_id": "LMKS", "description": "Lomnicky Stit (R=3.84, Alt=2634 m)"},
    31: {"id": 31, "station_id": "MCMU", "description": "Mc Murdo (R=0.30, Alt=48 m)"},
    32: {"id": 32, "station_id": "MCRL", "description": "Mobile Cosmic Ray Laboratory (R=2.46, Alt=200 m)"},
    33: {"id": 33, "station_id": "MGDN", "description": "Magadan (R=2.10, Alt=220 m)"},
    34: {"id": 34, "station_id": "MOSC", "description": "Moscow (R=2.43, Alt=200 m)"},
    35: {"id": 35, "station_id": "MRNY", "description": "Mirny (R=0.03, Alt=30 m)"},
    36: {"id": 36, "station_id": "MWSB", "description": "Mawson Bare (R=0.22, Alt=30 m)"},
    37: {"id": 37, "station_id": "MWSN", "description": "Mawson (R=0.22, Alt=30 m)"},
    38: {"id": 38, "station_id": "MXCO", "description": "Mexico (R=8.28, Alt=2274 m)"},
    39: {"id": 39, "station_id": "NAIN", "description": "Nain (R=0.30, Alt=46 m)"},
    40: {"id": 40, "station_id": "NANM", "description": "Nor-Amberd (R=7.10, Alt=2000 m)"},
    41: {"id": 41, "station_id": "NEU3", "description": "Neumayer III mini neutron monitor (R=0.10, Alt=40 m)"},
    42: {"id": 42, "station_id": "NEWK", "description": "Newark (R=2.40, Alt=50 m)"},
    43: {"id": 43, "station_id": "NRLK", "description": "Norilsk (R=0.63, Alt=0 m)"},
    44: {"id": 44, "station_id": "NVBK", "description": "Novosibirsk (R=2.91, Alt=163 m)"},
    45: {"id": 45, "station_id": "OULU", "description": "Oulu (R=0.81, Alt=15 m)"},
    46: {"id": 46, "station_id": "PSNM", "description": "Doi Inthanon (Princess Sirindhorn NM) (R=16.80, Alt=2565 m)"},
    47: {"id": 47, "station_id": "PTFM", "description": "Potchefstroom (R=6.98, Alt=1351 m)"},
    48: {"id": 48, "station_id": "PWNK", "description": "Peawanuck (R=0.30, Alt=53 m)"},
    49: {"id": 49, "station_id": "ROME", "description": "Rome (R=6.27, Alt=0 m)"},
    50: {"id": 50, "station_id": "SANB", "description": "Sanae D (R=0.73, Alt=52 m)"},
    51: {"id": 51, "station_id": "SNAE", "description": "Sanae IV (R=0.73, Alt=856 m)"},
    52: {"id": 52, "station_id": "SOPB", "description": "South Pole Bare (R=0.10, Alt=2820 m)"},
    53: {"id": 53, "station_id": "SOPO", "description": "South Pole (R=0.10, Alt=2820 m)"},
    54: {"id": 54, "station_id": "TERA", "description": "Terre Adelie (R=0.01, Alt=32 m)"},
    55: {"id": 55, "station_id": "THUL", "description": "Thule (R=0.30, Alt=26 m)"},
    56: {"id": 56, "station_id": "TSMB", "description": "Tsumeb (R=9.15, Alt=1240 m)"},
    57: {"id": 57, "station_id": "TXBY", "description": "Tixie Bay (R=0.48, Alt=0 m)"},
    58: {"id": 58, "station_id": "UFSZ", "description": "Zugspitze (R=4.10, Alt=2650 m)"},
    59: {"id": 59, "station_id": "YKTK", "description": "Yakutsk (R=1.65, Alt=105 m)"},
    60: {"id": 60, "station_id": "ZUGS", "description": "Zugspitze (R=4.24, Alt=2960 m)"}
}


@router.get("/", response_model=list[NeutronMonitorStations], summary=f"Get a list of {entity_name}")
def read_list():
    return list_of_neutron_monitor_stations.values()


@router.get("/{id}", response_model=NeutronMonitorStations, summary=f"Get one {entity_name}")
def read_one(*, id: int):
    entity = list_of_neutron_monitor_stations.get(id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{entity_name} not found")
    return entity
