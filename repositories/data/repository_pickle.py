import pickle

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

    def getDescendantAttacksForKey(self, key):
        #TODO: what do we do here??
        return None

    def getLastTenAttacks(self):
        #TODO: FIX!!
        return DataStore.attacks_list[-10:]

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
        return node._get_kind() == "SharkAttack"

    def nodeIsCountry(self, node):
        return node._get_kind() == "Country"

    def nodeIsArea(self, node):
        return node._get_kind() == "Area"

    def getNodeId(self, node):
        return node.id

    def getNodeName(self, node):
        return node.name

    def getNodeParent(self, node):
        return node.parent
