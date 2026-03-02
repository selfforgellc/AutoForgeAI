
import os
import requests

BING_ENDPOINT = "https://api.bing.microsoft.com/v7.0/images/search"
BING_KEY = os.getenv("BING_API_KEY")

def resolve_vehicle_image(year, make, model):
    if not BING_KEY:
        return None

    query = f"{year} {make} {model} car side view"

    headers = {"Ocp-Apim-Subscription-Key": BING_KEY}
    params = {
        "q": query,
        "count": 5,
        "imageType": "Photo",
        "size": "Large"
    }

    response = requests.get(BING_ENDPOINT, headers=headers, params=params)
    if response.status_code != 200:
        return None

    data = response.json()
    images = data.get("value", [])
    for img in images:
        if img.get("width", 0) > 800:
            return img.get("contentUrl")

    return None
