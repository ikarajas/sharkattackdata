import pickle
from models.native import *
from repositories.data.common import *

class DataStore:
    """
    Contains static fields with in-memory attack data.
    """
    attacks_list = {}
    attacks_dict = {}
    countries_dict = {}

    @classmethod
    def get_countries_list(cls):
        return [cls.countries_dict[y] for y in cls.countries_dict.keys()]

class SharkAttackRepository:
    def __init__(self):
        pass

    def getDescendantAttacksForCountry(self, countryId):
        return DataStore.countries_dict[countryId].attacks

    def getDescendantAttacksForNode(self, node):
        return node.attacks

    def getLastTenAttacks(self):
        #TODO: FIX!!
        return DataStore.attacks_list[-10:]

    def getFullyResolvedAttack(self, countryId, areaId, attackId):
        country = None
        area = None
        attack = None
        if countryId in DataStore.countries_dict:
            country = DataStore.countries_dict[countryId]
            if areaId in country.areas_dict:
                area = country.areas_dict[areaId]
                if attackId in area.attacks_dict:
                    attack = area.attacks_dict[attackId]

        if attack is not None:
            return FullyResolvedAttackResponse(
                FullyResolvedAttackStatus.Found,
                attack.countryNormalised,
                attack.area_normalised,
                attack)

        if attackId in DataStore.attacks_dict:
            attack = DataStore.attacks_dict[attackId]
            return FullyResolvedAttackResponse(
                FullyResolvedAttackStatus.FoundInDifferentLocation,
                attack.parent.parent.id,
                attack.parent.id,
                attack)

        return FullyResolvedAttackResponse(FullyResolvedAttackStatus.NotFound, None, None, None)


class CountryRepository:
    def __init__(self):
        pass

    def getCountries(self):
        return DataStore.get_countries_list()

    def getCountry(self, countryId):
        return DataStore.countries_dict[countryId]

class AreaRepository:
    def __init__(self):
        pass

    def getArea(self, countryId, areaId):
        return DataStore.countries_dict[countryId].areas_dict[areaId]

    def getAreasOfCountryForId(self, countryId):
        return DataStore.countries_dict[countryId].areas

    def getAreasOfCountry(self, country):
        return country.areas

class DataHelper:
    def nodeIsSharkAttack(self, node):
        return isinstance(node, SharkAttack)

    def nodeIsCountry(self, node):
        return isinstance(node, Country)

    def nodeIsArea(self, node):
        return isinstance(node, Area)

    def getNodeId(self, node):
        return node.id

    def getNodeName(self, node):
        return node.name

    def getNodeParent(self, node):
        return node.parent
