import os, math
import jinja2, webapp2, json, cgi, logging, datetime

from google.appengine.api import memcache, users
from google.appengine.ext import ndb

from models import SharkAttack, Country, Country, Area
from utils import StringUtils

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)



class CountrySummary:
    def __init__(self, country, attacks):
        self._totalCount = len(attacks)
        # self._countryName = displayLocationForCountry.name
        # self._fatalCount = len([y for y in attacks if y.fatal])
        # self._unprovokedCount = len([y for y in attacks if not y.provoked])
        # self._fatalAndUnprovokedCount = len([y for y in attacks if not y.provoked and y.fatal])

class LocationSummary:
    def __init__(self, countryOrArea, attacks):
        self._totalCount = len(attacks)
        self._countryName = countryOrArea.name
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
        countries = None #memcache.get("countries")
        if countries is None:
            query = Country.query()
            countries = [y for y in query.iter()]
            # if not memcache.add("countries", countries):
            #     logging.error("Couldn't save countries to memcache.")
        return countries

    def getNormalisedCountryName(self, countryName):
        return StringUtils.normaliseName(countryName, toLower=True, spacesToUnderscore=True)

    def getCountriesAsDict(self):
        displayCountries = self.getCountries()
        return dict([[self.getNormalisedCountryName(y.name), y] for y in displayCountries])

    def getCountrySummaryKey(self, country):
        return "attacks_%s_summary" % displayCountry.urlPart

    def getCountryAttacksPartKey(self, displayCountry, part):
        return "attacks_%s_part_%s" % (displayCountry.urlPart, part)

    def getUrlForNode(self, site, node):
        path = "/"
        if site == "gsaf":
            path = os.path.join(path, "gsaf")
        if node is None:
            return path
        if node._get_kind() == "Area":
            return os.path.join(path, "place", node.key.parent().get().key.id(), node.key.id())
        if node._get_kind() == "Country":
            return os.path.join(path, "place", node.key.id())

    def readAttacksForCountryFromCache(self, country):
        summary = memcache.get(self.getCountrySummaryKey(country))
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
        
    def writeAttacksForCountryToCache(self, country, attacks):
        summary = CountrySummary(country, attacks)
        if not memcache.add(self.getCountrySummaryKey(country), summary):
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

    def isGsaf(self):
        return self.__class__.__name__.startswith("Gsaf")

    def getBreadcrumbData(self, node):
        retval = []
        firstRun = True
        site = ""
        if self.isGsaf():
            site = "gsaf"
        while node is not None:
            if firstRun:
                if node._get_kind() == "SharkAttack":
                    retval.append({ "name": node.key.id(), "url": "" })
                else:
                    retval.append({ "name": node.name, "url": "" })
            else:
                retval.append({ "name": node.name, "url": self.helper.getUrlForNode(site, node) })
            firstRun = False
            parentKey = node.key.parent()
            if parentKey is None:
                node = None
            else:
                node = parentKey.get()

        if self.isGsaf():
            retval.append({ "name": "Countries", "url": "" if firstRun else self.helper.getUrlForNode(site, None) })

        retval.reverse()
        return retval

    def resolveTemplatePath(self, relativePath):
        root = "templates"
        if self.isGsaf():
            root = os.path.join(root, "gsaf")
        else:
            root = os.path.join(root, "sharkattackdata")
        return os.path.join(root, relativePath)

    def doIt(self, *args, **kwargs):
        template_values = {
            "title": "Shark Attack Data",
            "subtemplate": self.resolveTemplatePath("basepage.html"),
            "countries": sorted(self.helper.getCountries(), key=lambda c: c.name)
            }
        
        previousKwargs = args[0]
        for key, value in (dict(previousKwargs.items() + kwargs.items())).iteritems():
            template_values[key] = value

        template = JINJA_ENVIRONMENT.get_template(self.resolveTemplatePath("main.html"))
        self.response.write(template.render(template_values))

class MainPage(BasePage):
    def get(self):
        self.doIt(
            {},
            breadcrumb_data=self.getBreadcrumbData(None)
            )

class AttackPage(BasePage):
    def __init__(self, request, response):
        super(AttackPage, self).__init__(request, response)

    def get(self, countryId, areaId, attackId):
        key = ndb.Key("Country", countryId, "Area", areaId, "SharkAttack", attackId)
        attack = key.get()
        area = attack.key.parent().get()
        country = area.key.parent().get()
        
        super(AttackPage, self).doIt(
            {},
            subtemplate=self.resolveTemplatePath("attack.html"),
            title="Shark Attack at %s in %s, %s" % (attack.location, area.name, country.name),
            attack=attack,
            breadcrumb_data=self.getBreadcrumbData(attack)
            )

class LocationPage(BasePage):
    def __init__(self, request, response):
        super(LocationPage, self).__init__(request, response)

    def doIt(self, **kwargs):
        logging.info("In LocationPage")
        attacks = [y for y in self.getAttacksForLocation()]
        
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

    def getAttacksForLocation(self):
        return self._attacks

    def get(self, countryNameKey):
        country = Country.get_by_id(self.helper.getNormalisedCountryName(countryNameKey))
        areas = [y for y in Area.query(ancestor=country.key).iter()]
        self._attacks = []
        self._attacks.extend(SharkAttack.query(ancestor=country.key).order(SharkAttack.date))

        self.doIt(
            title="Shark Attack Data: %s" % country.name,
            subtemplate=self.resolveTemplatePath("country.html"),
            country=country,
            breadcrumb_data=self.getBreadcrumbData(country),
            areas = sorted(areas, key=lambda a: a.name))

class AreaPage(LocationPage):
    def __init__(self, request, response):
        super(AreaPage, self).__init__(request, response)

    def getAttacksForLocation(self):
        return self._attacks

    def get(self, countryNameKey, areaNameKey):
        country = Country.get_by_id(self.helper.getNormalisedCountryName(countryNameKey))
        area = country.getAreaForName(areaNameKey)
        self._attacks = [y for y in SharkAttack.query(ancestor=area.key).order(SharkAttack.date).iter()]

        self.doIt(
            subtemplate=self.resolveTemplatePath("area.html"),
            title="Shark Attack Data: %s, %s" % (area.name, country.name),
            country=country,
            area=area,
            breadcrumb_data=self.getBreadcrumbData(area))

class GsafMainPage(MainPage):
    def __init__(self, *args):
        super(GsafMainPage, self).__init__(*args)
        
class GsafAttackPage(AttackPage):
    def __init__(self, *args):
        super(GsafAttackPage, self).__init__(*args)

    def get(self, *args):
        super(GsafAttackPage, self).get(*args)
        
class GsafAreaPage(AreaPage):
    def __init__(self, *args):
        super(GsafAreaPage, self).__init__(*args)

    def get(self, *args):
        super(GsafAreaPage, self).get(*args)
        
class GsafCountryPage(CountryPage):
    def __init__(self, *args):
        super(GsafCountryPage, self).__init__(*args)

    def get(self, *args):
        super(GsafCountryPage, self).get(*args)


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
            countryId = StringUtils.normaliseName(attackrow[2], toLower=True, spacesToUnderscore=True)
            areaId = StringUtils.normaliseName(attackrow[3], toLower=True, spacesToUnderscore=True)
            if areaId == "":
                # E.g. if the area only contains unicode characters.
                attackrow[3] = "Area unknown"
                areaId = StringUtils.normaliseName(attackrow[3], toLower=True, spacesToUnderscore=True)
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
                                  provoked = attackrow[16] == "True")
            attacksToStore.append(toStore)
        ndb.put_multi(attacksToStore)
        memcache.add("countryDict", self._countries)
        memcache.add("areaDict", self._areas)


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


class Constants:
    UrlPartCountryRegex = r"([A-Za-z\-_]+)"
    UrlPartAreaRegex = r"([A-Za-z0-9\-_]+)"
    UrlPartGsafCaseNumberRegex = r"([A-Za-z0-9\-\._]+)"

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/place/%s' % (Constants.UrlPartCountryRegex), CountryPage),
    ('/place/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex), AreaPage),
    ('/attack/%s/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex, Constants.UrlPartGsafCaseNumberRegex), AttackPage),
    ('/gsaf', GsafMainPage, "main"),
    ('/gsaf/place/%s' % (Constants.UrlPartCountryRegex), GsafCountryPage),
    ('/gsaf/place/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex), GsafAreaPage),
    ('/gsaf/attack/%s/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex, Constants.UrlPartGsafCaseNumberRegex), GsafAttackPage),
    ('/serviceops/post_sharkattacks', PostSharkAttacks),
    ('/serviceops/delete_sharkattacks', DeleteSharkAttacks),
    ('/serviceops/authenticate', Authenticate)
    ], debug=debug)
