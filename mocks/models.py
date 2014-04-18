if __name__ == "__main__":
    import dev_appserver
    dev_appserver.fix_sys_path()

from google.appengine.ext import ndb

class Country:
    name = None
    urlPart = None
    __areas = None
    def __init__(self, name, urlPart, areas):
        self.name = name
        self.urlPart = urlPart
        self.__areas = areas

class Area:
    name = None
    urlPart = None
    __attacks = None
    def __init__(self, name, countryId, urlPart, attacks):
        self.name = name
        self.urlPart = urlPart
        self.__attacks = attacks
        self.key = ndb.Key("Country", countryId, "Area", self.urlPart)

class SharkAttack:
    gsaf_case_number = None
    date = None
    date_orig = None
    date_userfriendly = None
    country = None
    countryNormalised = None
    area = None
    area_normalised = None
    location = None
    activity = None
    name = None
    sex = None
    age = None
    injury = None
    time = None
    species = None
    investigator_or_source = None
    date_is_approximate = None
    fatal = None
    provoked = None
    identifier = None

    def __init__(self, gsaf_case_number):
        self.gsaf_case_number = gsaf_case_number
        #self.unprovoked = ndb.ComputedProperty(lambda sa: False if sa.provoked else True)
        #self.unprovokedUserFriendly = ndb.ComputedProperty(lambda sa: "Unprovoked" if not sa.provoked else "Provoked")
        #self.fatalUserFriendly = ndb.ComputedProperty(lambda sa: "Fatal" if sa.fatal else "Not fatal")

