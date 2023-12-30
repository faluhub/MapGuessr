import requests, random, json, streetview, os, dotenv, projection
from PIL import Image

dotenv.load_dotenv()

countries = json.load(open("./data/countries.json"))
api_key = os.environ["GOOGLE_API_KEY"]

class Location:
    def __init__(self, country: str, image: Image.Image) -> None:
        self.country = country
        self.image = image

def add_compass(pano: Image.Image, heading: float):
    base = Image.new(mode="RGBA", size=(64, 64))
    compass = Image.open("./data/compass.png")
    compass = compass.rotate(heading)
    bg = Image.open("./data/compass_bg.png")
    bg = bg.resize(size=(50, 50))
    base.paste(bg, (6, 6), bg.convert("RGBA"))
    base.paste(compass, (0, 0), compass.convert("RGBA"))
    base = base.resize(size=(80, 80))
    pano.paste(base, (10, 10), base.convert("RGBA"))
    return pano

def get_positions(country: int):
    url = f"https://www.mapcrunch.com/_r/?c={country}&d=1&i=0"
    text = requests.get(url).text
    return json.loads(text.replace("while(1);", ""))["points"]

def get_panorama(lat: float, lon: float):
    results = streetview.panoids(lat=lat, lon=lon)
    if len(results) == 0:
        return None
    panorama = {'panoid': 'hEHAJ9SrLhjTeYmmz92TkQ', 'lat': 15.47088874353598, 'lon': -90.38136989038406, 'heading': 181.3594970703125, 'tilt': 86.67817687988281, 'roll': 358.681640625, 'year': 2016, 'month': 8}
    print(panorama)
    pano_img = streetview.download_panorama(panoid=panorama["panoid"])
    projected = projection.Equirectangular(pano_img).get_perspective(100, panorama["heading"] - 180, -10, 1920, 1080)
    return add_compass(projected, panorama["heading"])

def gen_country():
    country = countries[random.randint(0, len(countries) - 1)]
    while True:
        positions = get_positions(country["id"])
        for pos in positions:
            panorama = get_panorama(float(pos[0]), float(pos[1]))
            if not panorama is None:
                return Location(country["name"], panorama)

def get_country_names():
    return [country["name"] for country in countries]
