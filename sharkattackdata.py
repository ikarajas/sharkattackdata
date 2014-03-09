import os
import jinja2, webapp2, json, cgi, logging, datetime

from google.appengine.api import memcache

from models import SharkAttack, Country


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class DisplayCountry:
    def __init__(self, str):
        self.name = str
        self.urlPart = str.replace(" ", "_")

class Helper():
    def __init__(self):
        pass

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

    def getAttacksForCountry(self, country):
        if country is None:
            country = ""
        key = "attacks_%s" % country
        attacks = memcache.get(key)
        if attacks is None:
            query = SharkAttack.query(
                SharkAttack.country == country,
                ).order(SharkAttack.date)
            attacks = [y for y in query.iter()]
            if not memcache.add(key, attacks):
                logging.error("Couldn't save countries to memcache.")
        return attacks


class BasePage(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.helper = Helper()

    def doIt(self, **kwargs):
        template_values = {
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
            subtemplate="templates/country.html",
            country=countryName,
            attacks=attacks,
            totalAttacksCount=len(attacks),
            totalFatalCount=len([y for y in attacks if y.fatal]),
            totalUnprovokedCount=len([y for y in attacks if not y.provoked]),
            totalFatalUnprovokedCount=len([y for y in attacks if not y.provoked and y.fatal]))

class PostCountry(webapp2.RequestHandler):
    def post(self):
        data = self.request.body
        countries = json.loads(data)
        #logging.info(attacks)
        for countryrow in countries:
            tostore = Country()
            tostore.name = countryrow[0]
            tostore.put()


class PostSharkAttack(webapp2.RequestHandler):
    def post(self):
        data = self.request.body
        attacks = json.loads(data)
        #logging.info(attacks)
        for attackrow in attacks:
            tostore = SharkAttack()
            dateStr = attackrow[0]
            if dateStr == "":
                dateValue = None
            else:
                dateValue = datetime.datetime.strptime(dateStr, '%Y-%m-%d').date()
            tostore.date = dateValue
            tostore.date_orig = attackrow[1]
            tostore.country = attackrow[2]
            tostore.area = attackrow[3]
            tostore.location = attackrow[4]
            tostore.activity = attackrow[5]
            tostore.name = attackrow[6]
            tostore.sex = attackrow[7]
            tostore.age = attackrow[8]
            tostore.injury = attackrow[9]
            tostore.time = attackrow[10]
            tostore.species = attackrow[11]
            tostore.investigator_or_source = attackrow[12]
            tostore.date_is_approximate = attackrow[13] == "True"
            tostore.fatal = attackrow[14] == "True"
            tostore.provoked = attackrow[15] == "True"
            tostore.put()




debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
application = webapp2.WSGIApplication([
    ('/', MainPage, "main"),
    ('/post_country', PostCountry),
    ('/post_sharkattack', PostSharkAttack),
    ('/country/([A-Za-z_]+)', CountryPage)
    ], debug=debug)
