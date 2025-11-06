import math
import re


def dms_to_dd(degrees: int, minutes: int, seconds: int, direction: str) -> float:
    """Convert degrees, minutes and seconds to decimal degrees."""
    dd = degrees + minutes / 60 + seconds / 3600
    if direction in ['S', 'Ю', 'ю', 's', 'w', 'W', 'З', 'з']:
        dd *= -1
    return dd


def parse_dms_string(string: str) -> tuple[float, float]:
    """Convert string in format `59°49′12″ с. ш. 30°25′58″ в. д.` to a pair of decimal degrees."""
    pattern = r'(\d+)°(\d+)′(\d+)″\s*([сСnNюЮwWeEвВзЗ\.]*)'
    parts = re.findall(pattern, string)

    if len(parts) != 2:
        raise ValueError('Failed to parse coordinates.')

    lat_deg, lat_min, lat_sec, lat_dir = parts[0]
    lon_deg, lon_min, lon_sec, lon_dir = parts[1]

    lat = dms_to_dd(int(lat_deg), int(lat_min), int(lat_sec), lat_dir)
    lon = dms_to_dd(int(lon_deg), int(lon_min), int(lon_sec), lon_dir)

    return lat, lon


def get_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Haversine distance, the shortest distance between two points on the surface of a sphere."""
    earth_radius_km = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c
