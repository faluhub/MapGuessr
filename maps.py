import requests, random, json, streetview, os, dotenv, projection
from PIL import Image

dotenv.load_dotenv()

countries = json.load(open("./data/countries.json"))
api_key = os.environ["GOOGLE_API_KEY"]

class Location:
    def __init__(self, country: str, image: Image.Image, year: int) -> None:
        self.country = country
        self.image = image
        self.year = year
    
    def dump(self):
        with open("./data/location.json", "w") as f:
            json.dump({"country": self.country, "year": self.year}, f)

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
    panorama = None
    for p in results:
        if "year" in p:
            if panorama is None or int(p["year"]) > int(panorama["year"]):
                panorama = p
    pano_img = streetview.download_panorama(panoid=panorama["panoid"])
    projected = projection.Equirectangular(pano_img).get_perspective(100, panorama["heading"] - 180, -10, 1920, 1080)
    return add_compass(projected, panorama["heading"]), panorama["year"]

def gen_country():
    country = countries[random.randint(0, len(countries) - 1)]
    while True:
        positions = get_positions(country["id"])
        random.shuffle(positions)
        for pos in positions:
            panorama = get_panorama(float(pos[0]), float(pos[1]))
            if not panorama is None:
                location = Location(country["name"], panorama[0], panorama[1])
                return location

def get_country_names():
    return [country["name"] for country in countries]

def get_old_location():
    path = "./data/location.json"

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        try:
            data = json.load(f)
            return Location(data["country"], Image.open("./data/challenge.jpg"), data["year"])
        except:
            return None
