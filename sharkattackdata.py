import os, math
import jinja2, webapp2, json, cgi, logging, datetime, urllib

from google.appengine.api import memcache, users
from google.appengine.ext import ndb

from utils import StringUtils
from siteinformation import SiteInformation

import sitemap, rssfeeds, api, tasks

from pages import *
from gsaf_pages import *
from serviceops import *

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Place2AttackRedirect(webapp2.RequestHandler):
    # Used to provide redirects for bad URLs introduced in previous sitemap.xml.
    def get(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def head(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def respond(self, countryId, areaId, attackId):
        self.response.status = "301 Moved Permanently"
        self.response.headers["Location"] = "/attack/%s/%s/%s" % (countryId, areaId, attackId)

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
    ('/site-maintenance', SiteMaintenancePage),
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
    ('/serviceops/set-site-information', SetSiteInformation),
    ('/serviceops/authenticate', Authenticate)
    ], debug=debug)

application.error_handlers[404] = ErrorHandlers.handle404
if not debug:
    application.error_handlers[500] = ErrorHandlers.handle500
