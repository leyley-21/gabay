"""Local point-in-polygon lookup. Coordinates never go to an external provider."""
from functools import lru_cache
import json,math
from app.config import BASE_DIR

@lru_cache(maxsize=1)
def boundaries():
    return json.loads((BASE_DIR/'data/geography/ph_provinces.geojson').read_text())['features']

def inside_ring(x,y,ring):
    inside=False
    for i,a in enumerate(ring):
        b=ring[i-1]
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside

def locate_province(latitude,longitude):
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in (latitude,longitude)):
        raise ValueError('Supply valid latitude and longitude numbers.')
    if not -90<=latitude<=90 or not -180<=longitude<=180:raise ValueError('Invalid coordinates.')
    for f in boundaries():
        lo,la,hi,ha=f['bbox']
        if not (lo<=longitude<=hi and la<=latitude<=ha):continue
        g=f['geometry'];polygons=[g['coordinates']] if g['type']=='Polygon' else g['coordinates']
        for rings in polygons:
            if inside_ring(longitude,latitude,rings[0]) and not any(inside_ring(longitude,latitude,r) for r in rings[1:]):
                return f['properties']['name']
    return None

def province_names():
    # This snapshot predates some administrative changes; names remain editable.
    return sorted({f['properties']['name'] for f in boundaries()})
