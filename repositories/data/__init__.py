import pickle

from blobs import attacks
from models.native import SharkAttack, Country, Area
from repository_pickle import DataStore
from utils import MiscUtils

input_attacks_dict = pickle.loads(attacks.data.decode("base64"))
DataStore.attacks_list = [SharkAttack(y) for y in input_attacks_dict]
#TODO: create attacks_dict

country_tuples = MiscUtils.uniqueify([(y.countryNormalised, y.country) for y in DataStore.attacks_list])
area_tuples = MiscUtils.uniqueify([(y.countryNormalised, y.area_normalised, y.area) for y in DataStore.attacks_list])

country_objects = []

for country_tuple in country_tuples:
    country_normalised = country_tuple[0]
    country_name = country_tuple[1]
    c = Country(country_name, country_normalised, None) #TODO: add place summary
    country_areas = []
    for area_tuple in [y for y in area_tuples if y[0] == country_normalised]:
        area_normalised = area_tuple[1]
        area_name = area_tuple[2]
        country_areas.append(Area(c, area_name, area_normalised))
    c.areas = country_areas
    country_objects.append(c)


for c in country_objects:
    print c
    for a in c.areas:
        print u' '.join((" - ", a.name)).encode('utf-8').strip()
