import logging

from google.appengine.api import memcache
from google.appengine.ext import ndb

from models import SingletonStore
from siteinformation import SiteInformation

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
