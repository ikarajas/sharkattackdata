import os, math
import jinja2, webapp2, json, cgi, logging, datetime

from google.appengine.api import memcache, users
from google.appengine.ext import ndb

from models import SharkAttack, Country

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class DisplayCountry:
    def __init__(self, str):
        self.name = str
        self.urlPart = str.replace(" ", "_")

class CountrySummary:
    def __init__(self, countryName, totalCount, fatalCount, provokedCount, fatalAndProvokedCount):
        self._countryName = countryName
        self._totalCount = totalCount
        self._fatalCount = fatalCount
        self._provokedCount = provokedCount
        self._fatalAndProvokedCount = fatalAndProvokedCount

class Helper():
    def __init__(self):
        self._attacksPerPart = 1000

    def br(self, response):
        response.write("<br />")

    def getCountries(self):
        countries = memcache.get("countries")
        if countries is None:
            query = Country.query()
            countries = [DisplayCountry(y.name) for y in query.iter()]
            logging.info(len(countries))
            if not memcache.add("countries", countries):
                logging.error("Couldn't save countries to memcache.")
        return countries

    def getCountriesAsDict(self):
        displayCountries = self.getCountries()
        return dict([[y.name, y] for y in displayCountries])

    def getAttacksForCountry(self, countryName):
        displayCountry = self.getCountriesAsDict()[countryName]
        if displayCountry is None:
            raise ValueError("displayCountry cannot be None")
        attacks = self.readAttacksForCountryFromCache(displayCountry)
        if attacks is None:
            query = SharkAttack.query(
                SharkAttack.country == displayCountry.name,
                ).order(SharkAttack.date)
            attacks = [y for y in query.iter()]
            self.writeAttacksForCountryToCache(displayCountry, attacks)
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
        fatalCount = len([y for y in attacks if y.fatal])
        unprovokedCount = len([y for y in attacks if not y.provoked])
        fatalAndUnprovokedCount = len([y for y in attacks if not y.provoked and y.fatal])
        summary = CountrySummary(displayCountry.name, len(attacks), fatalCount, unprovokedCount, fatalAndUnprovokedCount)
        if not memcache.add(self.getCountrySummaryKey(displayCountry), summary):
            raise Exception("Unable to write country summary to memcache.")
        numParts = int(math.ceil(float(summary._totalCount)/float(self._attacksPerPart)))
        for i in range(numParts):
            cacheKey = self.getCountryAttacksPartKey(displayCountry, i)
            logging.info("Writing to cache: %s" % cacheKey)
            if not memcache.add(cacheKey, attacks[i:(i*self._attacksPerPart)]):
                raise Exception("Unable to write country summary to memcache.")
            
        


class BasePage(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.helper = Helper()

    def doIt(self, **kwargs):
        template_values = {
            "title": "Shark Attack Data",
            "subtemplate": "templates/basepage.html",
            "countries": sorted(self.helper.getCountries(), key=lambda c: c.name)
            }
        
        for key, value in kwargs.iteritems():
            template_values[key] = value

        template = JINJA_ENVIRONMENT.get_template('templates/main.html')
        self.response.write(template.render(template_values))

class MainPage(BasePage):
    def get(self):
        self.doIt()

class CountryPage(BasePage):
    def __init__(self, request, response):
        super(CountryPage, self).__init__(request, response)

    def get(self, country):
        countryName = country.replace("_", " ")
        attacks = [y for y in self.helper.getAttacksForCountry(countryName)]
        
        self.doIt(
            title="Shark Attack Data: %s" % countryName,
            subtemplate="templates/country.html",
            country=countryName,
            attacks=attacks,
            totalAttacksCount=len(attacks),
            totalFatalCount=len([y for y in attacks if y.fatal]),
            totalUnprovokedCount=len([y for y in attacks if not y.provoked]),
            totalFatalUnprovokedCount=len([y for y in attacks if not y.provoked and y.fatal]))

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
            toStore.location = attackrow[4]
            toStore.activity = attackrow[5]
            toStore.name = attackrow[6]
            toStore.sex = attackrow[7]
            toStore.age = attackrow[8]
            toStore.injury = attackrow[9]
            toStore.time = attackrow[10]
            toStore.species = attackrow[11]
            toStore.investigator_or_source = attackrow[12]
            toStore.date_is_approximate = attackrow[13] == "True"
            toStore.fatal = attackrow[14] == "True"
            toStore.provoked = attackrow[15] == "True"
            toStore.put()

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
    ('/country/([A-Za-z_]+)', CountryPage),
    ('/serviceops/post_countries', PostCountries),
    ('/serviceops/post_sharkattacks', PostSharkAttacks),
    ('/serviceops/delete_countries', DeleteCountries),
    ('/serviceops/delete_sharkattacks', DeleteSharkAttacks),
    ('/serviceops/authenticate', Authenticate)
    ], debug=debug)
