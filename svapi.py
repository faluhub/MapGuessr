# Modified version of https://github.com/cplusx/google-street-view-panorama-download/blob/master/streetview.py
# Also referenced https://github.com/ZPdesu/lsaa-dataset/blob/master/streetview/__init__.py

import re, requests, time, itertools, os
from datetime import datetime
from PIL import Image
from io import BytesIO

def _panoids_url(lat, lon):
    url = "https://maps.googleapis.com/maps/api/js/GeoPhotoService.SingleImageSearch?pb=!1m5!1sapiv3!5sUS!11m2!1m1!1b0!2m4!1m2!3d{0:}!4d{1:}!2d50!3m10!2m2!1sen!i2sGB!9m1!1e2!11m4!1m3!1e2!2b1!3e2!4m10!1e1!1e2!1e3!1e4!1e8!1e6!5m1!1e2!6m1!1e2&callback=_xdc_._v2mub5"
    return url.format(lat, lon)

def _panoids_data(lat, lon):
    url = _panoids_url(lat, lon)
    return requests.get(url, proxies=None)

def pano_ids(lat, lon, closest=False):
    resp = _panoids_data(lat, lon)
    pans = re.findall(r"\[2,\"(.+?)\"\].+?\[\[null,null,(-?[0-9]+.[0-9]+),(-?[0-9]+.[0-9]+)\],\[-?[0-9]+.[0-9]+\],\[(-?[0-9]+.[0-9]+),(-?[0-9]+.[0-9]+),(-?[0-9]+.[0-9]+)", resp.text)
    pans = [{
        "panoid": p[0],
        "lat": float(p[1]),
        "lon": float(p[2]),
        "heading": float(p[3]),
        "tilt": float(p[4]),
        "roll": float(p[5])
    } for p in pans]

    pans = [p for i, p in enumerate(pans) if p not in pans[:i]]

    dates = re.findall("([0-9]?[0-9]?[0-9])?,?\[(20[0-9][0-9]),([0-9]+)\]", resp.text)
    dates = [list(d)[1:] for d in dates]

    if len(dates) > 0:
        dates = [[int(v) for v in d] for d in dates]
        dates = [d for d in dates if d[1] <= 12 and d[1] >= 1]
        year, month = dates.pop(-1)
        pans[0].update({"year": year, "month": month})
        dates.reverse()
        for i, (year, month) in enumerate(dates):
            pans[-1 - i].update({"year": year, "month": month})

    def func(x):
        if "year" in x:
            return datetime(year=x["year"], month=x["month"], day=1)
        else:
            return datetime(year=3000, month=1, day=1)
    pans.sort(key=func)

    if closest:
        return [pans[i] for i in range(len(dates))]
    else:
        return pans
