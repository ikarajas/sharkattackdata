import os, math
import jinja2, webapp2, json, cgi, logging, datetime

from google.appengine.api import memcache, users
from google.appengine.ext import ndb

from models import SharkAttack, Country
from utils import StringUtils

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class DisplayLocation:
    def __init__(self, str, urlFriendlyName=None):
        self.name = str
        if urlFriendlyName is not None:
            self.urlPart = urlFriendlyName
        else:
            self.urlPart = str.replace(" ", "_").lower()

    def __repr__(self):
        return "DisplayLocation -- name: %s, urlPart: %s" % (self.name, self.urlPart)

class CountrySummary:
    def __init__(self, displayLocationForCountry, attacks):
        self._totalCount = len(attacks)
        # self._countryName = displayLocationForCountry.name
        # self._fatalCount = len([y for y in attacks if y.fatal])
        # self._unprovokedCount = len([y for y in attacks if not y.provoked])
        # self._fatalAndUnprovokedCount = len([y for y in attacks if not y.provoked and y.fatal])

class LocationSummary:
    def __init__(self, displayLocation, attacks):
        self._totalCount = len(attacks)
        self._countryName = displayLocation.name
        self._fatalCount = len([y for y in attacks if y.fatal])
        self._unprovokedCount = len([y for y in attacks if not y.provoked])
        self._fatalAndUnprovokedCount = len([y for y in attacks if not y.provoked and y.fatal])


class Helper():
    def __init__(self):
        self._attacksPerPart = 1000

    def uniqueify(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]

    def getCountries(self):
        countries = memcache.get("countries")
        if countries is None:
            query = Country.query()
            countries = [DisplayLocation(y.name) for y in query.iter()]
            if not memcache.add("countries", countries):
                logging.error("Couldn't save countries to memcache.")
        return countries

    def getNormalisedCountryName(self, countryName):
        return StringUtils.normaliseName(countryName, toLower=True, spacesToUnderscore=True)

    def getCountriesAsDict(self):
        displayCountries = self.getCountries()
        return dict([[self.getNormalisedCountryName(y.name), y] for y in displayCountries])

    def getDisplayLocationForCountryNameKey(self, countryNameKey):
        countriesDict = self.getCountriesAsDict()
        if not countriesDict.has_key(countryNameKey):
            raise ValueError("No record for country: %s." % countryNameKey)
        return countriesDict[countryNameKey]

    def getAttacksForLocation(self, countryName, areaNormalised=None):
        countryNameNormalised = self.getNormalisedCountryName(countryName)
        if not self.getCountriesAsDict().has_key(countryNameNormalised):
            raise ValueError("displayCountry cannot be None")
        displayCountry = self.getCountriesAsDict()[countryNameNormalised]
        attacks = self.readAttacksForCountryFromCache(displayCountry)
        if attacks is None:
            query = SharkAttack.query(
                SharkAttack.country == displayCountry.name,
                ).order(SharkAttack.date)
            attacks = [y for y in query.iter()]
            self.writeAttacksForCountryToCache(displayCountry, attacks)

        if areaNormalised is not None:
            attacks = [y for y in attacks if y.area_normalised == areaNormalised]
        return attacks

    def getCountrySummaryKey(self, displayCountry):
        return "attacks_%s_summary" % displayCountry.urlPart

    def getCountryAttacksPartKey(self, displayCountry, part):
        return "attacks_%s_part_%s" % (displayCountry.urlPart, part)

    def readAttacksForCountryFromCache(self, displayCountry):
        summary = memcache.get(self.getCountrySummaryKey(displayCountry))
        if summary is None:
            return None
        attacks = []
        numParts = int(math.ceil(float(summary._totalCount)/float(self._attacksPerPart)))
        for i in range(numParts):
            cacheKey = self.getCountryAttacksPartKey(displayCountry, i)
            logging.info("Retrieving from cache: %s" % cacheKey)
            theseAttacks = memcache.get(cacheKey)
            if theseAttacks is None:
                return None
            attacks.extend(theseAttacks)
        return attacks
        
    def writeAttacksForCountryToCache(self, displayCountry, attacks):
        summary = CountrySummary(displayCountry, attacks)
        if not memcache.add(self.getCountrySummaryKey(displayCountry), summary):
            raise Exception("Unable to write country summary to memcache.")
        numParts = int(math.ceil(float(summary._totalCount)/float(self._attacksPerPart)))
        for i in range(numParts):
            cacheKey = self.getCountryAttacksPartKey(displayCountry, i)
            logging.info("Writing to cache: %s" % cacheKey)
            if not memcache.add(cacheKey, attacks[(i*self._attacksPerPart):((i+1)*self._attacksPerPart)]):
                raise Exception("Unable to write country summary to memcache.")
            
        


class BasePage(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.helper = Helper()

    def doIt(self, *args, **kwargs):
        template_values = {
            "title": "Shark Attack Data",
            "subtemplate": "templates/basepage.html",
            "countries": sorted(self.helper.getCountries(), key=lambda c: c.name)
            }
        
        previousKwargs = args[0]
        for key, value in (dict(previousKwargs.items() + kwargs.items())).iteritems():
            template_values[key] = value

        #logging.info(template_values)
        template = JINJA_ENVIRONMENT.get_template('templates/main.html')
        self.response.write(template.render(template_values))

class LocationData:
    def __init__(self, countryName=None, areaName=None, urlFriendlyAreaName=None):
        self.countryName = countryName.replace("_", " ")
        self.areaName = None if areaName is None else areaName.replace("_", " ")
        self.urlFriendlyAreaName = urlFriendlyAreaName

    def __repr__(self):
        return "LocationData (countryName: %s, areaName: %s, urlFriendlyAreaName: %s)" % (self.countryName, self.areaName, self.urlFriendlyAreaName)

class MainPage(BasePage):
    def get(self):
        self.doIt({})

class LocationPage(BasePage):
    def __init__(self, request, response):
        super(LocationPage, self).__init__(request, response)

    def doIt(self, locationData, **kwargs):
        logging.info("In LocationPage")
        attacks = [y for y in self.getAttacksForLocation(locationData)]
        
        super(LocationPage, self).doIt(
            kwargs,
            attacks=attacks,
            totalAttacksCount=len(attacks),
            totalFatalCount=len([y for y in attacks if y.fatal]),
            totalUnprovokedCount=len([y for y in attacks if not y.provoked]),
            totalFatalUnprovokedCount=len([y for y in attacks if not y.provoked and y.fatal])
            )

class CountryPage(LocationPage):
    def __init__(self, request, response):
        super(CountryPage, self).__init__(request, response)
        self._attacks = None

    def getAttacksForLocation(self, locationData):
        if self._attacks is None:
            self._attacks = [y for y in self.helper.getAttacksForLocation(locationData.countryName)]
        return self._attacks

    def getAreas(self, locationData):
        areas = [DisplayLocation(y[0], urlFriendlyName=y[1]) for y in
                 self.helper.uniqueify([(y.area, y.area_normalised) for y in self.getAttacksForLocation(locationData) if not y.area == ""])]
        areas.sort(key=lambda a: a.name)
        return areas

    def get(self, countryNameKey):
        countryDisplayLocation = self.helper.getDisplayLocationForCountryNameKey(countryNameKey)

        locationData = LocationData(countryDisplayLocation.name)
        
        self.doIt(locationData,
                  title="Shark Attack Data: %s" % locationData.countryName,
                  subtemplate="templates/country.html",
                  country=countryDisplayLocation,
                  areas = self.getAreas(locationData)
                  )

class AreaPage(LocationPage):
    def __init__(self, request, response):
        super(AreaPage, self).__init__(request, response)

    def getAttacksForLocation(self, locationData):
        print locationData
        attacks = [y for y in self.helper.getAttacksForLocation(locationData.countryName, areaNormalised=locationData.urlFriendlyAreaName)]
        return attacks

    def get(self, countryNameKey, areaNameKey):
        countryDisplayLocation = self.helper.getDisplayLocationForCountryNameKey(countryNameKey)

        if areaNameKey == "No_area_given":
            areaName = ""
        else:
            #This causes the attacks cache to be hit just to obtain the area name. Improve...
            tempLocationData = LocationData(countryDisplayLocation.name, areaNameKey, urlFriendlyAreaName=areaNameKey)
            areaName = self.getAttacksForLocation(tempLocationData)[0].area

        areaData = LocationData(countryDisplayLocation.name, areaName, urlFriendlyAreaName=areaNameKey)
        
        logging.info(areaData)

        self.doIt(areaData,
            subtemplate="templates/area.html",
            title="Shark Attack Data: %s, %s" % (areaData.areaName, areaData.countryName),
            country=DisplayLocation(areaData.countryName),
            area=DisplayLocation(areaData.areaName if not areaName == "" else "\"No area given\"",
                                 areaName))

class JsonServiceHandler(webapp2.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        self.handle(data)

class DeleteCountries(JsonServiceHandler):
    def handle(self, data):
        memcache.add("countries", None)
        query = Country.query()
        results = query.fetch(1000)

        while results:
            ndb.delete_multi([m.key for m in results])
            results = query.fetch(1000)
        
class DeleteSharkAttacks(JsonServiceHandler):
    def handle(self, data):
        query = SharkAttack.query()
        results = query.fetch(1000)

        while results:
            ndb.delete_multi([m.key for m in results])
            results = query.fetch(1000)

class PostCountries(webapp2.RequestHandler):
    def post(self):
        data = self.request.body
        countries = json.loads(data)
        for countryrow in countries:
            toStore = Country()
            toStore.name = countryrow[0]
            toStore.put()

class PostSharkAttacks(webapp2.RequestHandler):
    def post(self):
        data = self.request.body
        attacks = json.loads(data)
        toStoreList = []
        for attackrow in attacks:
            toStore = SharkAttack()
            dateStr = attackrow[0]
            if dateStr == "":
                dateValue = None
            else:
                dateValue = datetime.datetime.strptime(dateStr, '%Y-%m-%d').date()
            toStore.date = dateValue
            toStore.date_orig = attackrow[1]
            toStore.country = attackrow[2]
            toStore.area = attackrow[3]
            toStore.area_normalised = attackrow[4]
            toStore.location = attackrow[5]
            toStore.activity = attackrow[6]
            toStore.name = attackrow[7]
            toStore.sex = attackrow[8]
            toStore.age = attackrow[9]
            toStore.injury = attackrow[10]
            toStore.time = attackrow[11]
            toStore.species = attackrow[12]
            toStore.investigator_or_source = attackrow[13]
            toStore.date_is_approximate = attackrow[14] == "True"
            toStore.fatal = attackrow[15] == "True"
            toStore.provoked = attackrow[16] == "True"
            toStore.identifier = attackrow[17]
            toStoreList.append(toStore)
        ndb.put_multi(toStoreList)

class Authenticate(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            greeting = ('Welcome, %s! (<a href="%s">sign out</a>)' %
                        (user.nickname(), users.create_logout_url('/')))
        else:
            greeting = ('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))

        self.response.out.write('<html><body>%s</body></html>' % greeting)


debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

application = webapp2.WSGIApplication([
    ('/', MainPage, "main"),
    ('/place/([A-Za-z_]+)', CountryPage),
    ('/place/([A-Za-z_]+)/([A-Za-z0-9_]+)', AreaPage),
    ('/serviceops/post_countries', PostCountries),
    ('/serviceops/post_sharkattacks', PostSharkAttacks),
    ('/serviceops/delete_countries', DeleteCountries),
    ('/serviceops/delete_sharkattacks', DeleteSharkAttacks),
    ('/serviceops/authenticate', Authenticate)
    ], debug=debug)
