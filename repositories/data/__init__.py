import pickle

from blobs import attacks
from models.common import PlaceSummary
from models.native import SharkAttack, Country, Area
from repository_pickle import DataStore
from utils import MiscUtils


def process_attack_country(attack):
    if not attack.countryNormalised in DataStore.countries_dict:
        DataStore.countries_dict[attack.countryNormalised] = Country(attack.country, attack.countryNormalised)
    DataStore.countries_dict[attack.countryNormalised].attacks.append(attack)

def process_attack_area(attack):
    country = DataStore.countries_dict[attack.countryNormalised]
    if not attack.area_normalised in country.areas_dict:
        country.areas_dict[attack.area_normalised] = Area(country, attack.area, attack.area_normalised)
    area = country.areas_dict[attack.area_normalised]
    attack.parent = area
    area.attacks.append(attack)

def generate_place_summary(country):
    ps = PlaceSummary(country.attacks)
    country.place_summary = ps

def process():
    input_attacks_list = pickle.loads(attacks.data.decode("base64"))
    DataStore.attacks_list = [SharkAttack(y) for y in input_attacks_list]

    for a in DataStore.attacks_list:
        DataStore.attacks_dict[a.gsaf_case_number] = a
        process_attack_country(a)
        process_attack_area(a)

    for c in DataStore.get_countries_list():
        generate_place_summary(c)


process()


