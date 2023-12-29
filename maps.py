import requests, random, json, streetview, os, dotenv
from PIL.Image import Image

dotenv.load_dotenv()

countries = json.load(open("./data/countries.json"))
api_key = os.environ["GOOGLE_API_KEY"]

class Location:
    def __init__(self, country: str, image: Image) -> None:
        self.country = country
        self.image = image

def get_positions(country: int, inside: bool):
    url = f"https://www.mapcrunch.com/_r/?c={country}&d=1&i={1 if inside else 0}"
    text = requests.get(url).text
    return json.loads(text.replace("while(1);", ""))["points"]

def get_panorama(lat: float, lon: float):
    results = streetview.search_panoramas(lat, lon)
    if len(results) == 0:
        return None
    panorama = results[0]
    return streetview.get_streetview(
        width=1080,
        height=1080,
        pano_id=panorama.pano_id,
        api_key=api_key,
        heading=panorama.heading,
        pitch=0
    )

def gen_country():
    country = countries[random.randint(0, len(countries))]
    while True:
        positions = get_positions(country["id"], country["inside"])
        for pos in positions:
            panorama = get_panorama(float(pos[0]), float(pos[1]))
            if not panorama is None:
                return Location(country["name"], panorama)

def get_country_names():
    return [country["name"] for country in countries]
