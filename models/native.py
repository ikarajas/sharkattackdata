import pickle
from blobs import attacks
from models.common import *
from utils import StringUtils

MonthsDict = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
    }

class DataNode:
    def __init__(self):
        self.parent = None

class SharkAttack(DataNode):
    def __init__(self, sa_dict):
        #TODO: set parent
        self.gsaf_case_number = sa_dict["gsaf_case_number"]
        self.date = sa_dict["date"]
        self.date_orig = sa_dict["date_string"]
        self.date_userfriendly = self.getUserFriendlyDate(sa_dict["date"], sa_dict["date_string"])
        self.country = sa_dict["country"]
        self.countryNormalised = self.getNormalisedCountryName(sa_dict["country"])
        self.area = sa_dict["area"]
        self.area_normalised = sa_dict["area_normalised"]
        self.incident_type = sa_dict["incident_type"]
        self.location = sa_dict["location"]
        self.activity = sa_dict["activity"]
        self.name = sa_dict["name"]
        self.sex = sa_dict["sex"]
        self.age = sa_dict["age"]
        self.injury = sa_dict["injury"]
        self.time = sa_dict["time"]
        self.species = sa_dict["species"]
        self.investigator_or_source = sa_dict["investigator_or_source"]
        self.date_is_approximate = sa_dict["date_is_approximate"]
        self.fatal = sa_dict["fatal"]

        self.unprovoked = self.incident_type == GsafIncidentType.UNPROVOKED
        self.provoked = self.incident_type == GsafIncidentType.PROVOKED
        self.boating = self.incident_type == GsafIncidentType.BOATING
        self.sea_disaster = self.incident_type == GsafIncidentType.SEA_DISASTER
        self.invalid = self.incident_type == GsafIncidentType.INVALID
        self.valid = self.incident_type != GsafIncidentType.INVALID

        self.unpovokedUserFriendly = "Unprovoked" if not self.provoked else "Provoked"
        self.fatalUserFriendly = "Fatal" if self.fatal else "Not fatal"
        self.fatalYesOrNo = "Yes" if self.fatal else "No"

    @property
    def id(self):
        return self.gsaf_case_number

    def getUserFriendlyDate(self, dt, date_orig):
        if dt is None:
            return date_orig  or "Unknown"
        else:
            year, month, day = dt.isoformat().split("T")[0].split("-")
            return "%s %s %s" % (day, MonthsDict[int(month)], year)

    def getNormalisedCountryName(self, country):
        return StringUtils.normaliseName(country, toLower=True, spacesToUnderscore=True, dashesToUnderscore=True)
       


class Country(DataNode):
    def __repr__(self):
        return self.name

    def __init__(self, name, urlPart):
        self.name = name
        self.urlPart = urlPart
        self.place_summary = None
        self.areas_dict = {}
        self.attacks = []

    @property
    def id(self):
        return self.urlPart

    @property
    def areas(self):
        return [self.areas_dict[y] for y in self.areas_dict.keys()]

        #These have the potential to return incorrect data if place_summary is not updated.
        # count_total_including_irrelevant = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.totalCountAll)
        # count_unprovoked = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.unprovokedCount)
        # count_fatal_and_unprovoked = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.fatalAndUnprovokedCount)
        # count_non_fatal_and_unprovoked = ndb.ComputedProperty(lambda c: 0 if not c.place_summary else c.place_summary.nonFatalAndUnprovokedCount)

class Area(DataNode):
    def __repr__(self):
        return self.name

    def __init__(self, country, name, urlPart):
        self.parent = country
        self.country = country
        self.name = name
        self.urlPart = urlPart
        self.attacks = []

    @property
    def id(self):
        return self.urlPart

if __name__ == "__main__":
    print SharkAttack()