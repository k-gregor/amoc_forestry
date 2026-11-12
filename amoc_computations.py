lon_lat_to_area = {}

import numpy as np
from math import sin, cos, pi, radians, sqrt

# calculation from https://en.wikipedia.org/wiki/Longitude#Length_of_a_degree_of_longitude
def compute_length_of_longitude(degree_lat):
    a = 6378137.0
    b = 6356752.3142
    e = sqrt((a**2 - b**2)/a**2)
    return (pi * a * cos(radians(degree_lat))) / (180 * sqrt(1 - e ** 2 * (sin(radians(degree_lat)) ** 2)))


# calculation from https://en.wikipedia.org/wiki/Longitude#Length_of_a_degree_of_longitude
def compute_length_of_latitude(degree_lat):
    l_lat = np.abs(111132.954 - 559.822 * cos(2 * radians(degree_lat)) + 1.175 * cos(4 * radians(degree_lat)))
    return l_lat

def get_area_for_lon_and_lat_with_formulas_specific_gc_size(lat, lat_frac = 0.5, lon_frac = 0.5):
    if lat not in lon_lat_to_area:
        lat_length = compute_length_of_latitude(lat) * lat_frac
        lon_top_length = compute_length_of_longitude(lat + lat_frac / 2)
        lon_bottom_length = compute_length_of_longitude(lat - lat_frac / 2)
        small_length = min(lon_top_length, lon_bottom_length) * lon_frac
        long_length = max(lon_top_length, lon_bottom_length) * lon_frac
        area = lat_length * small_length + lat_length * (long_length - small_length) / 2 #last 2 is for the triangle area
        lon_lat_to_area[lat] = area

    return lon_lat_to_area[lat]