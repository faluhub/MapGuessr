import requests, random, json, svapi, os, dotenv
from datetime import datetime
from PIL import Image
from svdl import Location

dotenv.load_dotenv()

countries = json.load(open("./data/countries.json"))
api_key = os.environ["GOOGLE_API_KEY"]

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

async def get_panorama(lat: float, lon: float):
    results = svapi.pano_ids(lat, lon)
    if len(results) == 0:
        return None, None
    pano = None
    for p in results:
        if "year" in p:
            if pano is None or int(p["year"]) > int(pano["year"]):
                pano = p
    loc = Location(pano["panoid"], pano["heading"])
    image = await loc.download()
    return add_compass(image, pano["heading"]), pano["year"]

async def gen_country():
    country = countries[random.randint(0, len(countries) - 1)]
    while True:
        positions = get_positions(country["id"])
        random.shuffle(positions)
        for pos in positions:
            image, year = await get_panorama(float(pos[0]), float(pos[1]))
            if not image is None and not year is None:
                return {
                    "country": country["name"],
                    "image": image,
                    "year": year,
                    "timestamp": datetime.now()
                }

def get_country_names():
    return [country["name"] for country in countries]
