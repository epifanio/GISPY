from pyproj import CRS, Transformer
from ipyleaflet import projections
from owslib.wms import WebMapService
from pyproj import CRS
from shapely import geometry
from pyproj.exceptions import CRSError
# from IPython.core.display import display


EPSG_32661 = {
    "name": "EPSG:32661",
    "custom": True,  # This is important, it tells ipyleaflet that this projection is not on the predefined ones.
    "proj4def": "+proj=stere +lat_0=90 +lat_ts=90 +lon_0=0 +k=0.994 +x_0=2000000 +y_0=2000000 +datum=WGS84 +units=m +no_defs",
    "origin": [2000000, 2000000],
    "bounds": [[1994055.62, 5405875.53], [2000969.46, 2555456.55]],
}

EPSG_25833 = {
    "name": "EPSG:25833",
    "custom": True,  # This is important, it tells ipyleaflet that this projection is not on the predefined ones.
    "proj4def": "+proj=utm +zone=33 +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs",
    "origin": [327639.79, 6490960.92],
    "bounds": [[-2465144.80, 4102893.55], [776625.76, 9408555.22]],
}

EPSG_4326 = {
    "name": "EPSG:4326",
    "custom": True,  # This is important, it tells ipyleaflet that this projection is not on the predefined ones.
    "proj4def": "+proj=longlat +datum=WGS84 +no_defs",
    "origin": [0, 0],
}


def basemap(prj):
    pass

def get_ring(bounds):
    ring_bounds = [
        [bounds[0], bounds[1]],
        [bounds[0], bounds[3]],
        [bounds[2], bounds[3]],
        [bounds[2], bounds[1]],
    ]
    return ring_bounds


def get_crs_intersection(epsg, wms_layer, verbose=False):
    try:
        crs = CRS.from_epsg(epsg)
        crs_bounds = crs.area_of_use.bounds
        crs_ring = geometry.Polygon(get_ring(crs_bounds))
        wms_ring = geometry.Polygon(get_ring(wms_layer.boundingBoxWGS84))
        if verbose:
            print(f'{epsg} over {wms_layer.title}')
            # display(geometry.GeometryCollection([crs_ring, wms_ring]))
        return (crs_ring.intersection(wms_ring).area / wms_ring.area) * 100
    except CRSError:
        print(f"crs EPSG:{epsg} not found")
        return 0


def get_center(ll, ur):
    c_lat = ((max(ll[0], ur[0]) - min(ll[0], ur[0])) / 2) + min(ll[0], ur[0])
    c_lon = ((max(ll[1], ur[1]) - min(ll[1], ur[1])) / 2) + min(ll[1], ur[1])
    return [c_lon, c_lat]


def get_projection(epsg_code):
    print(epsg_code)
    if epsg_code == 900913:
        epsg_code = 3857
    if epsg_code in [3857, 3395, 4326, 3413, 3031]:
        return projections[f'EPSG{epsg_code}']
    crs = CRS.from_epsg(epsg_code)
    proj = Transformer.from_crs(crs.geodetic_crs, crs)
    ll_lon, ll_lat, ur_lon, ur_lat = crs.area_of_use.bounds
    ll = proj.transform(ll_lat, ll_lon)
    ur = proj.transform(ur_lat, ur_lon)
    origin = get_center(ll, ur)
    ipyl_projection = {
        "name": f"EPSG:{epsg_code}",
        "custom": True,
        "proj4def": crs.to_proj4(),
        "origin": origin,
        "bounds": [[ll[1], ll[0]], [ur[1], ur[0]]],
        "resolutions": [16384.0, 8192.0, 4096.0, 2048.0, 1024.0, 512.0, 256.0],
    }
    return ipyl_projection


def get_common_crs(urls):
    crs = []
    for url in urls:
        wms = WebMapService(url)
        crs_list = []
        for i in list(wms.contents.keys()):
            crs_layer = []
            for j in wms.contents[i].crsOptions:
                if "EPSG" in j:
                    epsg_code = j.split(":")[1]
                    if get_crs_intersection(epsg_code, wms.contents[i]) >= 50.0:
                        crs_layer.append(j)
            crs_list.append(crs_layer)
        crs.append(set().union(*crs_list))
    return list(set.intersection(*map(set, crs)))


def get_baselayer():
    urls = []
    pass