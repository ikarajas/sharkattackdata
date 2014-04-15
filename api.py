#!/usr/bin/env python

import os, webapp2, logging, datetime, json

from models import SharkAttack, Country, Country, Area
from utils import StringUtils
from repositories import CountryRepository, AreaRepository, SharkAttackRepository

import google.appengine.ext.ndb.model

class Attacks(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        isGsaf = request.path.startswith("/gsaf")
        self._hostName = os.environ.get("HTTP_HOST")
        self._urlScheme = os.environ.get("wsgi.url_scheme")
        self._sharkAttackRepository = SharkAttackRepository()
        self._countryRepository = CountryRepository()
        self._areaRepository = AreaRepository()

    def getItems(self):
        countryKey = None
        areaKey = None
        try:
            countryKey = self.request.GET["country"]
        except KeyError:
            pass
            
        try:
            areaKey = self.request.GET["area"]
        except KeyError:
            pass

        parentCountry = None
        if areaKey is None:
            node = self._countryRepository.getCountry(countryKey)
            if node is None:
                return []
        else:
            node = self._areaRepository.getArea(countryKey, areaKey)
            if node is None:
                return []
            parentCountry = node.key.parent().get()

        retval = []
        for attack in self._sharkAttackRepository.getDescendantAttacksForKey(node.key):
            try:
                dateTemp = None if attack.date_is_approximate else attack.date
            except google.appengine.ext.ndb.model.UnprojectedPropertyError as e:
                logging.warning("Shouldn't happen.")
                dateTemp = None

            retval.append({
                "gsafCaseNumber": attack.gsaf_case_number,
                "date": None if dateTemp is None else dateTemp.isoformat(),
                "dateOrig": attack.date_orig,
                "dateIsApproximate": attack.date_is_approximate,
                "dateUserFriendly": attack.date_userfriendly,
                "area": attack.area,
                "areaNormalised": attack.area_normalised,
                "location": attack.location,
                "activity": attack.activity,
                "unprovoked": attack.unprovoked,
                "fatal": attack.fatal
            })

        return retval

    def get(self):
        self.response.headers["Content-Type"] = "application/json"
        items = self.getItems()
        self.response.out.write(json.dumps(items))
