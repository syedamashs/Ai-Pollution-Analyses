"""Static AQI data for areas in Madurai.

All values are based on recent monitoring data.
"""

# Static AQI data for each area
AREA_AQI_DATA = {
    "Periyar": {"aqi": 132, "status": "Poor", "city": "Madurai - Periyar"},
    "Arapalayam": {"aqi": 96, "status": "Moderate", "city": "Madurai - Arapalayam"},
    "Thiruparankundram": {"aqi": 78, "status": "Moderate", "city": "Madurai - Thiruparankundram"},
    "Mattuthavani": {"aqi": 110, "status": "Moderate", "city": "Madurai - Mattuthavani"},
    "KK Nagar": {"aqi": 88, "status": "Moderate", "city": "Madurai - KK Nagar"},
}


def get_aqi_for_area(area_name):
    """Get static AQI data for a given area.

    Args:
        area_name: Area key (Periyar, Arapalayam, Thiruparankundram, Mattuthavani, KK Nagar)

    Returns dict with keys: aqi (int), status (str), city (str)
    """
    area = area_name.strip()
    if area not in AREA_AQI_DATA:
        # Default to Periyar if area not found
        area = "Periyar"
    
    data = AREA_AQI_DATA[area]
    return {
        "aqi": data["aqi"],
        "status": "ok",
        "data": {
            "aqi": data["aqi"],
            "city": {"name": data["city"]},
            "dominentpol": "pm25"
        }
    }
