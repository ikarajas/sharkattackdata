import os, math
import jinja2, webapp2, json, cgi, logging, datetime

from google.appengine.api import memcache, users
from google.appengine.ext import ndb

from custom_exceptions import PageNotFoundException
from models import SharkAttack, Country, Country, Area
from utils import StringUtils
from repositories import SharkAttackRepository, CountryRepository

import sitemap, rssfeeds, api, tasks

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Helper():
    def __init__(self):
        self._countryRepository = CountryRepository()

    def uniqueify(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]

    def getCountries(self):
        return self._countryRepository.getCountries()

    def getNormalisedCountryName(self, countryName):
        return StringUtils.normalisePlaceName(countryName)

    def getCountriesAsDict(self):
        displayCountries = self.getCountries()
        return dict([[self.getNormalisedCountryName(y.name), y] for y in displayCountries])

    def getUrlForNode(self, site, node):
        path = "/"
        isGsaf = site == "gsaf"
        if isGsaf:
            path = os.path.join(path, "gsaf")
        if node is None:
            return path if isGsaf else os.path.join(path, "place")
        if node._get_kind() == "Area":
            return os.path.join(path, "place", node.key.parent().get().key.id(), node.key.id())
        if node._get_kind() == "Country":
            return os.path.join(path, "place" if isGsaf else "country-overview", node.key.id())

    def resolveTemplatePath(self, relativePath, isGsaf):
        root = "templates"
        if isGsaf:
            root = os.path.join(root, "gsaf")
        else:
            root = os.path.join(root, "sharkattackdata")
        return os.path.join(root, relativePath)

class BasePage(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.helper = Helper()
        self._sharkAttackRepository = SharkAttackRepository()
        self._pageTemplate = "main.html"
        self._host = os.environ.get("HTTP_HOST")
        self._urlScheme = os.environ.get("wsgi.url_scheme")
        self._path = os.environ.get("PATH_INFO")
        self._fullUrl = "%s://%s%s" % (self._urlScheme, self._host, self._path)

    def isGsaf(self):
        return self.__class__.__name__.startswith("Gsaf")

    def get(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def head(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def respond(self, *args, **kwargs):
        try:
            pageDict = self.handle(*args)
        except PageNotFoundException as nfe:
            if nfe.correctPath is not None:
                self.response.status = "301 Moved Permanently"
                self.response.headers["Location"] = nfe.correctPath
            else:
                ErrorHandlers.generate404(self.request, self.response, 404)
            return

        template_values = {
            "title": "Shark Attack Data",
            "subtemplate": self.resolveTemplatePath("basepage.html"),
            "show_social_media_buttons": True,
            "og_image": "%s://%s/assets/images/Sharks-1920-1200.jpg" % (self._urlScheme, self._host),
            "meta_description": Constants.SiteDescription,
            "full_url": self._fullUrl
            }
        
        for key, value in pageDict.iteritems():
            template_values[key] = value

        template = JINJA_ENVIRONMENT.get_template(self.resolveTemplatePath(self._pageTemplate))
        self.response.write(template.render(template_values))

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

        retval.append({ "name": "Countries", "url": "" if firstRun else self.helper.getUrlForNode(site, None) })

        retval.reverse()
        return retval

    def resolveTemplatePath(self, relativePath):
        return self.helper.resolveTemplatePath(relativePath, self.isGsaf())

class MainPage(BasePage):
    def handle(self):
        return {
            "breadcrumb_data": self.getBreadcrumbData(None),
            "last_attacks": self._sharkAttackRepository.getLastNAttacks(10, provoked=False)
            }

class LinksPage(BasePage):
    def handle(self):
        return {
            "subtemplate": self.resolveTemplatePath("links.html")
            }

class SharkAttacksByLocationPage(BasePage):
    def __init__(self, request, response):
        super(SharkAttacksByLocationPage, self).__init__(request, response)

    def handle(self):
        return {
            "subtemplate": self.resolveTemplatePath("places.html"),
            "title": "Shark Attacks by Country",
            "meta_description": "A list of countries in which shark attacks are recorded. Click on a country to show more information.",
            "highest_total": sorted(self.helper.getCountries(), key=lambda c: c.count_total, reverse=True)[0].count_total,
            "countries": sorted(self.helper.getCountries(), key=lambda c: c.count_total, reverse=True)
            }

class AttackPage(BasePage):
    def __init__(self, request, response):
        super(AttackPage, self).__init__(request, response)

    def getUrlForAttack(self, attack, isGsaf):
        path = [""]
        if isGsaf:
            path.append("gsaf")
        path.extend(["attack", attack.countryNormalised, attack.area_normalised, attack.gsaf_case_number])
        return "/".join(path)

    def handle(self, countryId, areaId, attackId):
        key = ndb.Key("Country", countryId, "Area", areaId, "SharkAttack", attackId)
        attack = key.get()

        if attack is None:
            attackById = SharkAttack.query(SharkAttack.gsaf_case_number == attackId).get()
            if attackById is not None:
                raise PageNotFoundException(correctPath=self.getUrlForAttack(attackById, False))
            raise PageNotFoundException()

        area = attack.key.parent().get()
        country = area.key.parent().get()
        
        return {
            "subtemplate": self.resolveTemplatePath("attack.html"),
            "title": "Shark attack at %s in %s, %s" % (attack.location, area.name, country.name),
            "meta_description": "Details of a shark attack that occurred %s at %s in %s, %s." % \
                (attack.date_userfriendly, attack.location, area.name, country.name),
            "attack": attack,
            "breadcrumb_data": self.getBreadcrumbData(attack)
            }

class LocationPage(BasePage):
    def __init__(self, request, response):
        super(LocationPage, self).__init__(request, response)

    def handle(self):
        return {}

class CountryPage(LocationPage):
    def __init__(self, request, response):
        super(CountryPage, self).__init__(request, response)

    def onGet(self, countryNameKey):
        self._country = Country.get_by_id(self.helper.getNormalisedCountryName(countryNameKey))
        if self._country is None:
            return
        self._areas = [y for y in Area.query(ancestor=self._country.key).fetch()]

    def handle(self, countryNameKey):
        self.onGet(countryNameKey)
        if self._country is None:
            raise PageNotFoundException()

        return {
            "title": "Shark Attack Data: %s" % self._country.name,
            "subtemplate": self.resolveTemplatePath("country.html"),
            "country": self._country,
            "areas": sorted(self._areas, key=lambda a: a.name), #needed by GSAF page
            "breadcrumb_data": self.getBreadcrumbData(self._country),
            "meta_description": "A complete list of the shark attacks that have occurred in %s." % self._country.name
            }

class CountryOverviewPage(CountryPage):
    def __init__(self, request, response):
        super(CountryOverviewPage, self).__init__(request, response)

    def handle(self, countryNameKey):
        self.onGet(countryNameKey)
        if self._country is None:
            raise PageNotFoundException()

        return {
            "title": "Shark Attack Data: %s" % self._country.name,
            "subtemplate": self.resolveTemplatePath("countryOverview.html"),
            "country": self._country,
            "breadcrumb_data": self.getBreadcrumbData(self._country),
            "areas": sorted(self._areas, key=lambda a: a.name),
            "meta_description": "An overview of the shark attacks that have occurred in %s. " % (self._country.name) + \
                "Provides statistical information including a timeline of unprovoked attacks as well as a graph of overall trends." 
            }

class AreaPage(LocationPage):
    def __init__(self, request, response):
        super(AreaPage, self).__init__(request, response)

    def handle(self, countryNameKey, areaNameKey):
        country = Country.get_by_id(self.helper.getNormalisedCountryName(countryNameKey))
        if country is None:
            raise PageNotFoundException()

        area = country.getAreaForName(areaNameKey)
        if area is None:
            raise PageNotFoundException()

        return {
            "subtemplate": self.resolveTemplatePath("area.html"),
            "title": "Shark Attack Data: %s, %s" % (area.name, country.name),
            "country": country,
            "area": area,
            "breadcrumb_data": self.getBreadcrumbData(area),
            "meta_description": "A complete list of the shark attacks that have occurred in %s, %s." % (area.name, country.name)
            }

class GsafMainPage(MainPage):
    def handle(self):
        return {
            "breadcrumb_data": self.getBreadcrumbData(None),
            "countries": sorted(self.helper.getCountries(), key=lambda c: c.name)
            }

    def __init__(self, *args):
        super(GsafMainPage, self).__init__(*args)
        
class GsafAttackPage(AttackPage):
    def __init__(self, *args):
        super(GsafAttackPage, self).__init__(*args)
        
class GsafAreaPage(AreaPage):
    def __init__(self, *args):
        super(GsafAreaPage, self).__init__(*args)
        
class GsafCountryPage(CountryPage):
    def __init__(self, *args):
        super(GsafCountryPage, self).__init__(*args)

class Place2AttackRedirect(webapp2.RequestHandler):
    # Used to provide redirects for bad URLs introduced in previous sitemap.xml.
    def get(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def head(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def respond(self, countryId, areaId, attackId):
        self.response.status = "301 Moved Permanently"
        self.response.headers["Location"] = "/attack/%s/%s/%s" % (countryId, areaId, attackId)

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
            countryId = StringUtils.normalisePlaceName(attackrow[2])
            areaId = StringUtils.normalisePlaceName(attackrow[3])
            if areaId == "":
                # E.g. if the area only contains unicode characters.
                attackrow[3] = "Area unknown"
                areaId = StringUtils.normalisePlaceName(attackrow[3])
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
        logging.info("put_multi() started.")
        ndb.put_multi(attacksToStore)
        logging.info("put_multi() complete.")
        memcache.add("countryDict", self._countries)
        memcache.add("areaDict", self._areas)


class FlushMemcache(webapp2.RequestHandler):
    def get(self):
        memcache.flush_all()

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
    SiteDescription = "Welcome to Shark Attack Data. The aim of this website is to increase understanding, and promote an informed " + \
    "discussion on the subject of shark attacks; when, where and how they occur. Through visualisation of the data, it aims to help " + \
    "identify where patterns exist in terms of both geography and time."
    UrlPartCountryRegex = r"([A-Za-z\-_]+)"
    UrlPartAreaRegex = r"([A-Za-z0-9\-_]+)"
    UrlPartGsafCaseNumberRegex = r"([A-Za-z0-9\-\._]+)"

class ErrorHandlers:
    @staticmethod
    def generateErrorResponse(request, response, title, subTemplate, responseStatus):
        isGsaf = request.path.startswith("/gsaf")
        helper = Helper()
        template_values = {
            "title": title,
            "subtemplate": subTemplate
            }

        template = JINJA_ENVIRONMENT.get_template(helper.resolveTemplatePath("main.html", isGsaf))
        response.set_status(responseStatus)
        response.write(template.render(template_values))

    @staticmethod
    def generate404(request, response, responseStatus):
        ErrorHandlers.generateErrorResponse(request, response, "Page not found", "/templates/common/404_error.html", responseStatus)

    @staticmethod
    def handle404(request, response, exception):
        ErrorHandlers.generate404(request, response, 404)

    @staticmethod
    def handle500(request, response, exception):
        ErrorHandlers.generateErrorResponse(request, response, "Error", "/templates/common/500_error.html", 500)

debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/links', LinksPage),
    ('/place', SharkAttacksByLocationPage),
    ('/country-overview/%s' % (Constants.UrlPartCountryRegex), CountryOverviewPage),
    ('/place/%s' % (Constants.UrlPartCountryRegex), CountryPage),
    ('/place/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex), AreaPage),
    ('/attack/%s/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex, Constants.UrlPartGsafCaseNumberRegex), AttackPage),

    # Used to provide redirects for bad URLs introduced in previous sitemap.xml.
    ('/place/%s/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex, Constants.UrlPartGsafCaseNumberRegex), Place2AttackRedirect),

    ('/gsaf', GsafMainPage),
    ('/gsaf/place', GsafMainPage),
    ('/gsaf/place/%s' % (Constants.UrlPartCountryRegex), GsafCountryPage),
    ('/gsaf/place/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex), GsafAreaPage),
    ('/gsaf/attack/%s/%s/%s' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex, Constants.UrlPartGsafCaseNumberRegex), GsafAttackPage),

    ('/feeds/places\.xml', rssfeeds.CountryFeed),
    ('/feeds/places/%s\.xml' % (Constants.UrlPartCountryRegex), rssfeeds.AreaFeed),
    ('/feeds/attacks/%s\.xml' % (Constants.UrlPartCountryRegex), rssfeeds.SharkAttackFeed),
    ('/feeds/attacks/%s/%s\.xml' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex), rssfeeds.SharkAttackFeed),

    ('/gsaf/feeds/places\.xml', rssfeeds.CountryFeed),
    ('/gsaf/feeds/places/%s\.xml' % (Constants.UrlPartCountryRegex), rssfeeds.AreaFeed),
    ('/gsaf/feeds/attacks/%s\.xml' % (Constants.UrlPartCountryRegex), rssfeeds.SharkAttackFeed),
    ('/gsaf/feeds/attacks/%s/%s\.xml' % (Constants.UrlPartCountryRegex, Constants.UrlPartAreaRegex), rssfeeds.SharkAttackFeed),

    ('/sitemap.xml', sitemap.SiteMap),

    ('/api/countries', api.Countries),
    ('/api/attacks', api.Attacks),

    ('/serviceops/generate-summaries', tasks.GenerateSummaries),
    ('/serviceops/post-sharkattacks', PostSharkAttacks),
    ('/serviceops/delete-sharkattacks', DeleteSharkAttacks),
    ('/serviceops/flush-memcache', FlushMemcache),
    ('/serviceops/authenticate', Authenticate)
    ], debug=debug)

application.error_handlers[404] = ErrorHandlers.handle404
if not debug:
    application.error_handlers[500] = ErrorHandlers.handle500
