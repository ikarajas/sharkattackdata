import datetime
import pickle
import unittest
from blobs import attacks
from models.common import *
from utils import StringUtils

MonthsDict = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
    }

class DataNode(object):
    def __init__(self):
        self.parent = None

class SharkAttack(DataNode):
    def __init__(self, sa_dict):
        super(SharkAttack, self).__init__()
        self.gsaf_case_number = StringUtils.toAscii(sa_dict["gsaf_case_number"])
        self.date = sa_dict["date"]
        self.date_orig = sa_dict["date_string"]
        self.date_userfriendly = self.getUserFriendlyDate(sa_dict["date"], sa_dict["date_string"])
        self.country = sa_dict["country"]
        self.countryNormalised = self.getNormalisedPlaceName(sa_dict["country"])
        self.area = sa_dict["area"]
        self.area_normalised = self.getNormalisedPlaceName(sa_dict["area_normalised"])
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

    @staticmethod
    def compareByDate(x, y):
        if x.date is None and y.date is not None:
            return -1
        elif y.date is None and x.date is not None:
            return 1
        elif y.date is None and x.date is None:
            return 0
        else:
            if x.date > y.date:
                return 1
            elif y.date > x.date:
                return -1
            else:
                return 0

    def getUserFriendlyDate(self, dt, date_orig):
        if dt is None:
            return date_orig  or "Unknown"
        else:
            year, month, day = dt.isoformat().split("T")[0].split("-")
            return "%s %s %s" % (day, MonthsDict[int(month)], year)

    def getNormalisedPlaceName(self, country):
        return StringUtils.normaliseName(country, toLower=True, spacesToUnderscore=True, dashesToUnderscore=True, unicodeToAscii=True)
       


class Country(DataNode):
    def __repr__(self):
        return self.name

    def __init__(self, name, urlPart):
        super(Country, self).__init__()
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

    @property
    def count_total_including_irrelevant(self):
        return 0 if not self.place_summary else self.place_summary.totalCountAll

    @property
    def count_unprovoked(self):
        return 0 if not self.place_summary else self.place_summary.unprovokedCount

    @property
    def count_fatal_and_unprovoked(self):
        return 0 if not self.place_summary else self.place_summary.fatalAndUnprovokedCount

    @property
    def count_non_fatal_and_unprovoked(self):
        return 0 if not self.place_summary else self.place_summary.nonFatalAndUnprovokedCount


class Area(DataNode):
    def __repr__(self):
        return self.name

    def __init__(self, country, name, urlPart):
        super(Area, self).__init__()
        self.parent = country
        self.country = country
        self.name = name
        self.urlPart = urlPart
        self.attacks_dict = {}
        self.attacks = []

    @property
    def id(self):
        return self.urlPart

#################################################
### Unit tests (should be moved elsewhere)
#################################################

class MockSharkAttack:
    def __init__(self):
        self.date = None
        pass

class SharkAttackUnitTest(unittest.TestCase):
    def test_sort_by_date_should_sort_from_earlier_to_later(self):
        earlier = datetime.date(2000, 1, 1)
        later = datetime.date(2000, 1, 2)
        sa1 = MockSharkAttack()
        sa1.date = earlier
        sa2 = MockSharkAttack()
        sa2.date = later
        unsorted = [sa2, sa1]
        sorted_attacks = sorted(unsorted, cmp=SharkAttack.compareByDate)
        self.assertEqual(earlier, sorted_attacks[0].date)
        self.assertEqual(later, sorted_attacks[1].date)



if __name__ == "__main__":
    unittest.main()
