import requests

HEADERS = {"User-Agent": "EatWhere/0.1 (your-email@email.com)"}

def geocode(place):
    """Turn a place name into latitude and longitude."""
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": place, "format": "json", "limit": 1},
        headers=HEADERS,
        timeout=10,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Geocoding failed: {response.status_code}")
    results = response.json()
    if not results:
        raise ValueError(f"No location found for '{place}'")
    return float(results[0]["lat"]), float(results[0]["lon"])

def find_restaurants(lat, lon, radius_m=500):
    """Find restaurants within radius_m metres of a point."""
    query = f"""
    [out:json][timeout:25];
    node["amenity"="restaurant"](around:{radius_m},{lat},{lon});
    out 30;
    """
    response = requests.post(
        "https://overpass-api.de/api/interpreter",
        data={"data": query},
        headers=HEADERS,
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Restaurant search failed: {response.status_code}")
    return response.json()["elements"]

if __name__ == "__main__":
    place = "Shoreditch, London"
    lat, lon = geocode(place)
    print(f"{place} is at {lat}, {lon}\n")

    restaurants = find_restaurants(lat, lon)
    print(f"Found {len(restaurants)} restaurants:\n")

    for r in restaurants:
        tags = r.get("tags", {})
        name = tags.get("name", "(no name)")
        cuisine = tags.get("cuisine", "unknown")
        print(f"- {name} | cuisine: {cuisine}")
        