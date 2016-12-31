import os
import jinja2
import urllib
import webapp2

from custom_exceptions import PageNotFoundException
from constants import Constants
from helper import Helper
from repositories.general import SiteInformationRepository
from repositories.data.repository_ndb import SharkAttackRepository
from siteinformation import SiteInformation

# FIXME - Duplication
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class BasePage(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)
        self.helper = Helper()
        self._siteInformationRepository = SiteInformationRepository()
        self._sharkAttackRepository = SharkAttackRepository()
        self._pageTemplate = "main.html"
        self._host = os.environ.get("HTTP_HOST")
        self._urlScheme = os.environ.get("wsgi.url_scheme")
        self._path = os.environ.get("PATH_INFO")
        self._fullUrl = "%s://%s%s" % (self._urlScheme, self._host, self._path)
        self._isSiteMaintenancePage = False

    def isGsaf(self):
        return self.__class__.__name__.startswith("Gsaf")

    def get(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def head(self, *args, **kwargs):
        self.respond(*args, **kwargs)

    def respond(self, *args, **kwargs):
        siteInfo = self._siteInformationRepository.get()
        if siteInfo.status == SiteInformation.STATUS_OFFLINE and not self._isSiteMaintenancePage:
            self.response.status = "307 Temporary Redirect"
            self.response.headers["Location"] = "/site-maintenance?%s" % urllib.urlencode({ "referrer": self._path })
            return
        else:
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

