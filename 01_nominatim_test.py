import requests

url = "https://nominatim.openstreetmap.org/search"
params = {"q": "Shoreditch, London", "format": "json", "limit": 1}
headers = {"User-Agent": "EatWhere/0.1 (your-email@email.com)"}

response = requests.get(url, params=params, headers=headers, timeout=10)

print("Status:", response.status_code)

if response.status_code == 200:
    print(response.json())
else:
    print("Request failed. Server said:")
    print(response.text[:500])