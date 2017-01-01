import logging
from utils import StringUtils
from google.appengine.ext import ndb
from models.common import *

MonthsDict = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
    }

class SharkAttack(ndb.Model):

    def getUserFriendlyDate(sa):
        if sa.date is None:
            return sa.date_orig or "Unknown"
        else:
            year, month, day = sa.date.isoformat().split("T")[0].split("-")
            return "%s %s %s" % (day, MonthsDict[int(month)], year)

    def getNormalisedCountryName(sa):
        return StringUtils.normaliseName(sa.country, toLower=True, spacesToUnderscore=True, dashesToUnderscore=True)

    gsaf_case_number = ndb.ComputedProperty(lambda sa: sa.key.id())
    date = ndb.DateProperty()
    date_orig = ndb.StringProperty()
    date_userfriendly = ndb.ComputedProperty(getUserFriendlyDate)
    country = ndb.ComputedProperty(lambda sa: sa.key.parent().parent().get().name) #make more efficient
    countryNormalised = ndb.ComputedProperty(lambda sa: sa.key.parent().parent().id())
    area = ndb.ComputedProperty(lambda sa: sa.key.parent().get().name) #make more efficient
    area_normalised = ndb.ComputedProperty(lambda sa: sa.key.parent().id())
    incident_type = ndb.StringProperty()
    location = ndb.StringProperty()
    activity = ndb.StringProperty()
    name = ndb.StringProperty()
    sex = ndb.StringProperty()
    age = ndb.StringProperty()
    injury = ndb.StringProperty()
    time = ndb.StringProperty()
    species = ndb.StringProperty()
    investigator_or_source = ndb.StringProperty()
    date_is_approximate = ndb.BooleanProperty()
    fatal = ndb.BooleanProperty()

    unprovoked = ndb.ComputedProperty(lambda sa: sa.incident_type == GsafIncidentType.UNPROVOKED)
    provoked = ndb.ComputedProperty(lambda sa: sa.incident_type == GsafIncidentType.PROVOKED)
    boating = ndb.ComputedProperty(lambda sa: sa.incident_type == GsafIncidentType.BOATING)
    sea_disaster = ndb.ComputedProperty(lambda sa: sa.incident_type == GsafIncidentType.SEA_DISASTER)
    invalid = ndb.ComputedProperty(lambda sa: sa.incident_type == GsafIncidentType.INVALID)
    valid = ndb.ComputedProperty(lambda sa: sa.incident_type != GsafIncidentType.INVALID)

    unprovokedUserFriendly = ndb.ComputedProperty(lambda sa: "Unprovoked" if not sa.provoked else "Provoked")
    fatalUserFriendly = ndb.ComputedProperty(lambda sa: "Fatal" if sa.fatal else "Not fatal")
    fatalYesOrNo = ndb.ComputedProperty(lambda sa: "Yes" if sa.fatal else "No")

class Country(ndb.Model):
    name = ndb.StringProperty()
    urlPart = ndb.ComputedProperty(lambda c: c.key.id())
    place_summary = ndb.PickleProperty()

    #These have the potential to return incorrect data if place_summary is not updated.
    count_total_including_irrelevant = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.totalCountAll)
    count_unprovoked = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.unprovokedCount)
    count_fatal_and_unprovoked = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.fatalAndUnprovokedCount)
    count_non_fatal_and_unprovoked = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.nonFatalAndUnprovokedCount)

    @staticmethod
    def forName(name):
        id = StringUtils.normaliseName(name, toLower=True, spacesToUnderscore=True)
        newCountry = Country.get_by_id(id)

    def getOrCreateArea(self, name):
        area = self.getAreaForName(name)
        if area is None:
            areaId = StringUtils.normaliseName(name, toLower=True, spacesToUnderscore=True)
            area = Area(id=areaId, name=name, parent=ndb.Key("Country", self.key.id()))
            area.put()
        return area

    def getAreas(self):
        return Area.query(ancestor=self.key).order(Area.name).iter()

    def getAreaForName(self, areaName):
        areaId = StringUtils.normaliseName(areaName, toLower=True, spacesToUnderscore=True)
        area = Area.get_by_id(areaId, parent=self.key)
        return area

class Area(ndb.Model):
    name = ndb.StringProperty()
    urlPart = ndb.ComputedProperty(lambda a:a.key.id())

    def getAttacks(self):
        return SharkAttack.query(ancestor=self.key).order(SharkAttack.date)

class SingletonStore(ndb.Model):
    data = ndb.PickleProperty()

