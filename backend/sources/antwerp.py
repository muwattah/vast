import re
ANTWERP_POSTCODES = {
    "2000", "2018", "2020", "2030", "2040", "2050", "2060",
    "2100", "2140", "2150", "2160", "2170", "2180",
    "2600", "2610", "2620", "2630", "2640", "2650", "2660",
}
ANTWERP_CITIES = {
    "antwerpen", "antwerp", "berchem", "borgerhout", "deurne", "hoboken",
    "merksem", "wilrijk", "ekeren", "borsbeek", "wommelgem", "wijnegem",
}
def is_antwerp_postcode(pc):
    if not pc: return False
    m = re.search(r"(\d{4})", str(pc))
    return bool(m and m.group(1) in ANTWERP_POSTCODES)
def is_antwerp_city(city):
    return bool(city and city.lower().strip() in ANTWERP_CITIES)
def in_antwerp_area(postal_code=None, city=None):
    if is_antwerp_postcode(postal_code): return True
    if is_antwerp_city(city) and not postal_code: return True
    return False
