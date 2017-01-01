import json
import webapp2
import datetime
import logging

from google.appengine.api import memcache, users
from google.appengine.ext import ndb

from models.ndb import Area, Country, SharkAttack
from repositories.general import SiteInformationRepository
from utils import StringUtils
from siteinformation import SiteInformation

class JsonServiceHandler(webapp2.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        self.handle(data)

class DeleteSharkAttacks(JsonServiceHandler):
    def handle(self, data):
        query = SharkAttack.query()
        results = query.fetch(1000)
        while results:
            ndb.delete_multi([m.key for m in results])
            results = query.fetch(1000)

        query = Area.query()
        results = query.fetch(1000)
        while results:
            ndb.delete_multi([m.key for m in results])
            results = query.fetch(1000)

        memcache.add("countries", None)
        query = Country.query()
        results = query.fetch(1000)
        while results:
            ndb.delete_multi([m.key for m in results])
            results = query.fetch(1000)


class PostSharkAttacks(JsonServiceHandler):
    _countries = memcache.get("countryDict") or {}
    _areas = memcache.get("areaDict") or {}

    def getCountry(self, countryId, name):
        if self._countries.has_key(countryId):
            return self._countries[countryId]
        else:
            country = Country.forName(countryId)
            if country is None:
                country = Country(id=countryId, name=name)
                country.put()
            self._countries[countryId] = country
            return country

    def getArea(self, country, areaId, name):
        areaKey = country.key.id() + "|" + areaId
        if self._areas.has_key(areaKey):
            return self._areas[areaKey]
        else:
            area = country.getOrCreateArea(name)
            self._areas[areaKey] = area
            return area

    def handle(self, attacks):
        attacksToStore = []
        for attackrow in attacks:
            countryId = StringUtils.normalisePlaceName(attackrow[2])
            areaId = StringUtils.normalisePlaceName(attackrow[3])
            if areaId == "":
                # E.g. if the area only contains unicode characters.
                attackrow[3] = "Area unknown"
                areaId = StringUtils.normalisePlaceName(attackrow[3])
            newCountry = self.getCountry(countryId, attackrow[2])
            newArea = self.getArea(newCountry, areaId, attackrow[3])

            dateStr = attackrow[0]
            if dateStr == "":
                dateValue = None
            else:
                dateValue = datetime.datetime.strptime(dateStr, '%Y-%m-%d').date()

            toStore = SharkAttack(id = attackrow[18],
                                  parent = newArea.key,
                                  date = dateValue,
                                  date_orig = attackrow[1],
                                  location = attackrow[5],
                                  activity = attackrow[6],
                                  name = attackrow[7],
                                  sex = attackrow[8],
                                  age = attackrow[9],
                                  injury = attackrow[10],
                                  time = attackrow[11],
                                  species = attackrow[12],
                                  investigator_or_source = attackrow[13],
                                  date_is_approximate = attackrow[14] == "True",
                                  fatal = attackrow[15] == "True",
                                  incident_type = attackrow[19])
            attacksToStore.append(toStore)
        logging.info("put_multi() started.")
        ndb.put_multi(attacksToStore)
        logging.info("put_multi() complete.")
        memcache.add("countryDict", self._countries)
        memcache.add("areaDict", self._areas)


class FlushMemcache(webapp2.RequestHandler):
    def get(self):
        memcache.flush_all()

class SetSiteInformation(JsonServiceHandler):
    def handle(self, data):
        siteInformationRepository = SiteInformationRepository()
        si = SiteInformation(data["status"], data["message"])
        siteInformationRepository.set(si)

