#/usr/bin/env python
import sys, os

if __name__ == "__main__":
    import dev_appserver
    dev_appserver.fix_sys_path()

from google.appengine.ext import ndb

from models import Country, Area, SharkAttack

sys.path.append(os.path.abspath("..")) #yuck
from utils import StringUtils

testData = \
[
    {
        "name": "Elbonia",
        "areas": [
            {
                "name": "Qwerty",
                "attacks": [
                    { "gsaf_case_number": "123.123.123" }
                    ]
                },
            {
                "name": "Uiop",
                "attacks": [
                    ]
                }
            ]
        },
    {
        "name": "The Land of Chocolate",
        "areas": [
            {
                "name": "Smarties County",
                "attacks": [
                    ]
                }
            ]
        },
    {
        "name": "Middle Earth",
        "areas": [
            {
                "name": "Mordor",
                "attacks": [
                    ]
                }
            ]
        }
    ]

class CountryRepository:
    def __init__(self):
        countriesList = [Country(y["name"], StringUtils.normalisePlaceName(y["name"]), self.__mapAreas(y["name"], y["areas"])) for y in testData]
        self._countries = dict([(v.urlPart, v) for v in countriesList])

    def __mapAreas(self, countryName, areaRawList):
        objList = [Area(areaRaw["name"], StringUtils.normalisePlaceName(countryName), StringUtils.normalisePlaceName(areaRaw["name"]), self.__mapAttacks(areaRaw["attacks"]))
                   for areaRaw in areaRawList]
        return dict([(areaObj.urlPart, areaObj) for areaObj in objList])

    def __mapAttacks(self, attackRawList):
        objList = [SharkAttack(attackRaw["gsaf_case_number"]) for attackRaw in attackRawList]
        return dict([(attackObj.gsaf_case_number, attackObj) for attackObj in objList])

    def __getCountriesDict(self):
        return self._countries

    def getCountries(self):
        return self._countries.values()

    def getCountry(self, countryId):
        return self._countries[countryId]

    def updatePlaceSummary(self, country, placeSummary):
        country.place_summary = placeSummary

class AreaRepository:
    def getArea(self, countryId, areaId):
        return CountryRepository()._CountryRepository__getCountriesDict()[countryId]._Country__areas[areaId]

    def getAreasOfCountryForId(self, countryId):
        return CountryRepository()._CountryRepository__getCountriesDict()[countryId]._Country__areas.values()
    

class SharkAttackRepository:
    def getDescendantAttacksForCountry(self, countryId):
        attacks = []
        for area in AreaRepository().getAreasOfCountryForId(countryId):
            key = ndb.Key("Country", countryId, "Area", area.urlPart)
            attacks.extend(self.getDescendantAttacksForKey(key))
        return attacks

    def getDescendantAttacksForKey(self, key):
        #Assumes that key defines an area...
        countryId = key.flat()[1]
        areaId = key.flat()[3]
        return AreaRepository().getArea(countryId, areaId)._Area__attacks.values()

if __name__ == "__main__":
    countryRepo = CountryRepository()
    areaRepo = AreaRepository()
    attackRepo = SharkAttackRepository()
    print countryRepo.getCountries()
    print countryRepo.getCountry("middle_earth").name
    print attackRepo.getDescendantAttacksForCountry("elbonia")
    print attackRepo.getDescendantAttacksForKey(ndb.Key("Country", "elbonia", "Area", "qwerty"))

    print areaRepo.getArea("the_land_of_chocolate", "smarties_county").name
    print [y.name for y in areaRepo.getAreasOfCountryForId("elbonia")]
