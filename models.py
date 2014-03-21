from google.appengine.ext import ndb

MonthsDict = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun", 7: "Jul", 8: "Aug", 9: "Sept", 10: "Oct", 11: "Nov", 12: "Dec"
    }

class SharkAttack(ndb.Model):

    def getUserFriendlyDate(sa):
        if sa.date is None:
            return sa.date_orig or "Unknown"
        else:
            year, month, day = sa.date.isoformat().split("T")[0].split("-")
            return "%s %s %s" % (day, MonthsDict[int(month.replace("0", ""))], year)

    date = ndb.DateProperty()
    date_orig = ndb.StringProperty()
    date_userfriendly = ndb.ComputedProperty(getUserFriendlyDate)
    country = ndb.StringProperty()
    area = ndb.StringProperty()
    area_normalised = ndb.StringProperty()
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
    provoked = ndb.BooleanProperty()
    identifier = ndb.StringProperty(indexed=True)

class Country(ndb.Model):
    name = ndb.StringProperty()
