import os, math, logging, datetime

from google.appengine.api import memcache
from google.appengine.ext import ndb

from models import SharkAttack, Country, Country, Area, PlaceSummary, SingletonStore
from utils import StringUtils


class SharkAttackRepository:
    def __init__(self):
        self._attacksPerPart = 1000

    def getAttackNodeId(self, key):
        return "|".join(key.flat())

    def getPlaceSummaryKey(self, key):
        return "attackPlaceSummary_%s" % self.getAttackNodeId(key)

    def getAttacksPartKey(self, key, part):
        return "attacks_%s_part_%s" % (self.getAttackNodeId(key), part)

    def readAttackSummary(self, key):
        summary = memcache.get(self.getPlaceSummaryKey(key))
        if summary is None:
            summary, attacks = self.__getDescendantAttackDataInternal(key)
        return summary

    def readAttacksFromCache(self, key):
        summary = self.readAttackSummary(key)
        if summary is None or summary.totalCount is None:
            summary, attacks = self.__getDescendantAttackDataInternal(key)
            return attacks
        
        numParts = int(math.ceil(float(summary.totalCount)/float(self._attacksPerPart)))
        attacks = []
        for i in range(numParts):
            cacheKey = self.getAttacksPartKey(key, i)
            theseAttacks = memcache.get(cacheKey)
            if theseAttacks is None:
                #Should we delete the place summary if this happens?
                return None
            attacks.extend(theseAttacks)
        return attacks
        
    def writeAttacksToCache(self, key, attacks):
        summary = PlaceSummary(attacks)
        if not memcache.set(self.getPlaceSummaryKey(key), summary):
            raise Exception("Unable to write attack parent node summary to memcache.")
        numParts = int(math.ceil(float(summary.totalCount)/float(self._attacksPerPart)))
        for i in range(numParts):
            cacheKey = self.getAttacksPartKey(key, i)
            #logging.info("Writing to cache: %s" % cacheKey)
            if not memcache.set(cacheKey, attacks[(i*self._attacksPerPart):((i+1)*self._attacksPerPart)]):
                raise Exception("Unable to write attack place summary to memcache.")
        return summary

    def __getDescendantAttackDataInternal(self, key):
        query = SharkAttack.query(ancestor=key).order(SharkAttack.date)
        attacks = query.fetch(
            projection=[SharkAttack.date, SharkAttack.date_orig, SharkAttack.date_userfriendly, SharkAttack.date_is_approximate,
                        SharkAttack.area, SharkAttack.location,SharkAttack.activity, SharkAttack.fatal, SharkAttack.provoked])
        summary = self.writeAttacksToCache(key, attacks)
        return summary, attacks

    def getDescendantAttacksForCountry(self, countryId):
        return self.readAttacksFromCache(ndb.Key("Country", countryId))

    def getDescendantAttacksForKey(self, key):
        attacks = self.readAttacksFromCache(key)

        if attacks is None:
            logging.info("Cache miss: %s" % self.getAttackNodeId(key))
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
        

    def __getLastNAttacks(self, number, ancestorKey=None, provoked=False):
        return SharkAttack \
            .query(
            ndb.AND(
                SharkAttack.date != None,
                SharkAttack.date > datetime.date.today() - datetime.timedelta(days=365),
                SharkAttack.provoked == provoked),
            ancestor=ancestorKey) \
            .order(-SharkAttack.date) \
            .fetch(number,
                   projection=[SharkAttack.date, SharkAttack.date_userfriendly, SharkAttack.country, SharkAttack.area,
                               SharkAttack.countryNormalised, SharkAttack.area_normalised, SharkAttack.gsaf_case_number, SharkAttack.fatal])


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

class SiteInformationRepository:
    siteInformationKey = "SiteInformation"

    def __init__(self):
        self.singletonRepository = SingletonRepository()

    def get(self):
        retval = None
        retval = self.singletonRepository.get(SiteInformationRepository.siteInformationKey)
        if retval is None:
            retval = SiteInformation(SiteInformation.STATUS_ONLINE, "")
        return retval

    def set(self, siteInformation):
        logging.info("Setting status... %s" % siteInformation.status)
        self.singletonRepository.put(SiteInformationRepository.siteInformationKey, siteInformation)

class SingletonRepository:
    def _getMemcacheKey(self, id):
        return "SingletonStore_%s" % id

    def _getFromMemcache(self, id):
        return memcache.get(self._getMemcacheKey(id))

    def _putIntoMemcache(self, id, data):
        return memcache.set(self._getMemcacheKey(id), data)

    def put(self, id, data):
        s = SingletonStore(id=id, data=data)
        s.put()
        self._putIntoMemcache(id, data)

    def get(self, id):
        data = self._getFromMemcache(id)
        if data is None:
            singletonStore = ndb.Key("SingletonStore", id).get()
            if singletonStore is not None:
                data = singletonStore.data
                self._putIntoMemcache(id, data)
        return data
