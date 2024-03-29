import os, math, logging, datetime

from google.appengine.api import memcache
from google.appengine.ext import ndb

from models.common import PlaceSummary
from models.ndb import SharkAttack, Country, Country, Area
from utils import StringUtils
from repositories.data.common import *


class SharkAttackRepository:
    def __init__(self):
        self._attacksPerPart = 1000

    def __getAttackNodeId(self, key):
        return "|".join(key.flat())

    def __getPlaceSummaryKey(self, key):
        return "attackPlaceSummary_%s" % self.__getAttackNodeId(key)

    def __getAttacksPartKey(self, key, part):
        return "attacks_%s_part_%s" % (self.__getAttackNodeId(key), part)

    def __readAttackSummary(self, key):
        summary = memcache.get(self.__getPlaceSummaryKey(key))
        if summary is None:
            summary, attacks = self.__getDescendantAttackDataInternal(key)
        return summary

    def __readAttacksFromCache(self, key):
        summary = self.__readAttackSummary(key)
        if summary is None or summary.totalCountAll is None:
            summary, attacks = self.__getDescendantAttackDataInternal(key)
            return attacks
        
        numParts = int(math.ceil(float(summary.totalCountAll)/float(self._attacksPerPart)))
        attacks = []
        for i in range(numParts):
            cacheKey = self.__getAttacksPartKey(key, i)
            theseAttacks = memcache.get(cacheKey)
            if theseAttacks is None:
                #Should we delete the place summary if this happens?
                return None
            attacks.extend(theseAttacks)
        return attacks
        
    def __writeAttacksToCache(self, key, attacks):
        summary = PlaceSummary(attacks)
        if not memcache.set(self.__getPlaceSummaryKey(key), summary):
            raise Exception("Unable to write attack parent node summary to memcache.")
        numParts = int(math.ceil(float(summary.totalCountAll)/float(self._attacksPerPart)))
        for i in range(numParts):
            cacheKey = self.__getAttacksPartKey(key, i)
            #logging.info("Writing to cache: %s" % cacheKey)
            if not memcache.set(cacheKey, attacks[(i*self._attacksPerPart):((i+1)*self._attacksPerPart)]):
                raise Exception("Unable to write attack place summary to memcache.")
        return summary

    def __getDescendantAttackDataInternal(self, key):
        query = SharkAttack.query(ancestor=key).order(SharkAttack.date)
        attacks = query.fetch(
            projection=[SharkAttack.date, SharkAttack.date_orig, SharkAttack.date_userfriendly, SharkAttack.date_is_approximate,
                        SharkAttack.area, SharkAttack.location,SharkAttack.activity, SharkAttack.fatal, SharkAttack.incident_type])
        summary = self.__writeAttacksToCache(key, attacks)
        return summary, attacks

    def getDescendantAttacksForCountry(self, countryId):
        return self.__readAttacksFromCache(ndb.Key("Country", countryId))

    def getDescendantAttacksForKey(self, key):
        attacks = self.__readAttacksFromCache(key)

        if attacks is None:
            logging.info("Cache miss: %s" % self.__getAttackNodeId(key))
            summary, attacks = self.__getDescendantAttackDataInternal(key)

        return attacks

    def getLastTenAttacks(self):
        key = "last_ten_attacks"
        val = memcache.get(key)
        if val is None:
            val = self.__getLastNAttacks(10)
            if not memcache.set(key, val):
                raise Exception("Unable to write %s to memcache." % key)
        return val
        

    def __getLastNAttacks(self, number, ancestorKey=None):
        return SharkAttack \
            .query(
            ndb.AND(
                SharkAttack.date != None,
                SharkAttack.date > datetime.date.today() - datetime.timedelta(days=365),
                SharkAttack.unprovoked == True, SharkAttack.valid == True),
            ancestor=ancestorKey) \
            .order(-SharkAttack.date) \
            .fetch(number,
                   projection=[SharkAttack.date, SharkAttack.date_userfriendly, SharkAttack.country, SharkAttack.area,
                               SharkAttack.countryNormalised, SharkAttack.area_normalised, SharkAttack.gsaf_case_number, SharkAttack.fatal])

    def getFullyResolvedAttack(self, countryId, areaId, attackId):
        key = ndb.Key("Country", countryId, "Area", areaId, "SharkAttack", attackId)
        attack = key.get()

        if attack is None:
            attackById = SharkAttack.query(SharkAttack.gsaf_case_number == attackId).get()
            if attackById is not None:
                return FullyResolvedAttackResponse(
                    FullyResolvedAttackStatus.FoundInDifferentLocation,
                    attackById.countryNormalised,
                    attackById.area_normalised,
                    attackById)
            return FullyResolvedAttackResponse(FullyResolvedAttackStatus.NotFound, None, None, None)

        return FullyResolvedAttackResponse(
            FullyResolvedAttackStatus.Found,
            attack.countryNormalised,
            attack.area_normalised,
            attack)


class CountryRepository:
    def getCountries(self):
        query = Country.query().order(Country.name)
        countries = query.fetch()
        return countries

    def getCountry(self, countryId):
        country = ndb.Key("Country", countryId).get()
        return country

    def updatePlaceSummary(self, country, placeSummary):
        country.place_summary = placeSummary
        country.put()

class AreaRepository:
    def getArea(self, countryId, areaId):
        return ndb.Key("Country", countryId, "Area", areaId).get()

    def getAreasOfCountryForId(self, countryId):
        query = Area.query(ancestor=ndb.Key("Country", countryId)).order(Area.name)
        areas = query.fetch()
        return areas

    def getAreasOfCountry(self, country):
        #Coupling of method interface with NDB-based model... remove.
        if not country.key.kind() == "Country":
            raise ValueError("key must refer to an instance of Country.")
        query = Area.query(ancestor=country.key).order(Area.name)
        areas = query.fetch()
        return areas

class DataHelper:
    def nodeIsSharkAttack(self, node):
        return node._get_kind() == "SharkAttack"

    def nodeIsCountry(self, node):
        return node._get_kind() == "Country"

    def nodeIsArea(self, node):
        return node._get_kind() == "Area"

    def getNodeId(self, node):
        return node.key.id()

    def getNodeName(self, node):
        return node.name

    def getNodeParent(self, node):
        parentKey = node.key.parent()
        if parentKey is None:
            return None
        else:
            return parentKey.get()
